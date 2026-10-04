"""Opt-in orchestration for rolling event evidence.

The frame and event pipelines deliberately do not start recording or upload
media by themselves.  :class:`EvidenceCaptureOrchestrator` is an integration
adapter that a caller may explicitly attach to a frame loop with
``observe_frame`` and call after events have been persisted.

The upload operation is intentionally separate from ``AnalysisService`` and
``SQLiteStore.complete_job``.  The store schedules the normal event push to
Makerverse asynchronously after its local transaction.  Calling the evidence
operation from this adapter therefore requires the caller to ensure that the
Makerverse event already exists (and that the event push has completed) before
calling :meth:`capture_events`; the adapter never invents an event URI and
never races the normal event push.

The adapter accepts the existing ``EvidenceClipUploader`` protocol and relies
on ``RollingEvidenceRecorder.upload_event`` for window construction, clip
export, uploader invocation, and generated-clip cleanup.  A caller can supply
an optional ``uploader_factory(event_id)`` to bind a fresh HTTP uploader to
each event; the shared-uploader path remains available for compatibility.  It
does not create media for mock or fixture payloads, and it is disabled by
default.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from .evidence_capture import (
    EvidenceClipUploader,
    EvidenceUploadResult,
    EvidenceWindow,
    UnavailableClipUploader,
)
from .evidence_recorder import BufferedEvidenceFrame, RollingEvidenceRecorder


logger = logging.getLogger(__name__)

CAPTURE_DISABLED = "disabled"
CAPTURE_AVAILABLE = "available"
CAPTURE_UNAVAILABLE = "unavailable"
CAPTURE_ERROR = "error"


# The factory is intentionally additive.  ``EvidenceClipUploader`` itself is
# unchanged; callers that already provide one shared uploader keep the old
# constructor path, while HTTP integrations can construct a fresh event-bound
# uploader for each event.
EvidenceUploaderFactory = Callable[[str], EvidenceClipUploader | Any]


@dataclass(frozen=True)
class EvidenceCaptureResult:
    """Outcome for one explicitly requested event capture/upload.

    ``window`` records the requested time range even when media or the remote
    uploader is unavailable.  ``upload`` is the exact result returned by the
    configured uploader (or by ``RollingEvidenceRecorder`` when export fails)
    and therefore carries the concrete reason without inventing a URI.
    """

    event_id: str | None
    status: str
    window: EvidenceWindow | None = None
    upload: EvidenceUploadResult | Any | None = None
    reason: str | None = None

    @property
    def available(self) -> bool:
        # A remote status of ``available`` without a URI is not a usable
        # evidence result.  Keep this property aligned with capture_event's
        # fail-closed status mapping.
        return self.status == CAPTURE_AVAILABLE and bool(self.uri)

    @property
    def uri(self) -> str | None:
        """Expose the uploader URI without changing its result contract."""

        value = getattr(self.upload, "uri", None)
        return value if isinstance(value, str) and value.strip() else None

    @property
    def upload_result(self) -> EvidenceUploadResult | Any | None:
        """Compatibility alias for callers that prefer an explicit name."""

        return self.upload


# A short alias keeps the result discoverable for callers that use the event
# terminology used by the backend adapter.
EventEvidenceCaptureResult = EvidenceCaptureResult


def _event_value(event: Any, field: str) -> Any:
    if isinstance(event, Mapping):
        return event.get(field)
    return getattr(event, field, None)


def _event_id(event: Any) -> str | None:
    value = _event_value(event, "event_id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _non_negative_seconds(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


class EvidenceCaptureOrchestrator:
    """Explicit frame observation plus event-window capture/upload.

    The default instance is inert.  To use it, construct it with a recorder,
    set ``enabled=True``, call :meth:`observe_frame` for every source frame,
    then call :meth:`capture_events` explicitly after the caller has confirmed
    that the corresponding Makerverse events were persisted and pushed.  The
    method uploads events sequentially, so callers can rely on deterministic
    order and bounded recorder ownership.

    ``capture_events`` is asynchronous because ``EvidenceClipUploader`` is an
    async protocol.  It does not call ``AnalysisService.run_job`` or
    ``SQLiteStore.complete_job`` and is never triggered implicitly.  When
    ``uploader_factory`` is configured, it receives each event id and its
    returned uploader is closed immediately after that event.
    """

    def __init__(
        self,
        recorder: RollingEvidenceRecorder | None = None,
        uploader: EvidenceClipUploader | None = None,
        *,
        uploader_factory: EvidenceUploaderFactory | None = None,
        enabled: bool = False,
        pre_seconds: int = 10,
        post_seconds: int = 10,
    ) -> None:
        if not isinstance(enabled, bool):
            raise TypeError("enabled must be a bool")
        self.pre_seconds = _non_negative_seconds(pre_seconds, "pre_seconds")
        self.post_seconds = _non_negative_seconds(post_seconds, "post_seconds")
        self.recorder = recorder
        if uploader_factory is not None and not callable(uploader_factory):
            raise TypeError("uploader_factory must be callable or None")
        self.uploader_factory = uploader_factory
        # Keep the unavailable fallback explicit so an enabled adapter without
        # an endpoint never fabricates a Makerverse URI.
        self.uploader = uploader or UnavailableClipUploader()
        self.enabled = enabled
        self._observer_error: str | None = None

    @property
    def last_observer_error(self) -> str | None:
        return self._observer_error

    def append_frame(
        self,
        timestamp: datetime,
        payload: Any,
        *,
        source_id: str | None = None,
    ) -> BufferedEvidenceFrame | None:
        """Append a frame when enabled, returning ``None`` for a disabled hook.

        Observation errors are recorded and logged instead of failing the AI
        job.  Evidence capture is an optional adapter and must not turn a
        recorder/source mismatch or a closed recorder into a reasoning error.
        """

        if not self.enabled or self.recorder is None:
            return None
        try:
            return self.recorder.append_frame(timestamp, payload, source_id=source_id)
        except (OSError, TypeError, ValueError, RuntimeError) as exc:
            self._observer_error = str(exc)
            logger.warning("evidence frame observation unavailable: %s", exc)
            return None

    def observe_frame(self, frame: Any) -> BufferedEvidenceFrame | None:
        """Observe a Frame-like object from an integration-owned frame loop."""

        if not self.enabled or self.recorder is None:
            return None
        try:
            return self.recorder.append(frame)
        except (OSError, TypeError, ValueError, RuntimeError) as exc:
            self._observer_error = str(exc)
            logger.warning("evidence frame observation unavailable: %s", exc)
            return None

    async def capture_event(self, event: Any) -> EvidenceCaptureResult:
        """Capture and upload one event after backend event persistence.

        ``event`` may be a ``UnifiedEvent`` or a mapping with ``event_id``,
        ``source_id``, ``started_at`` and ``ended_at`` fields.  Missing fields
        and a recorder/source mismatch fail closed with ``unavailable``.
        """

        event_id = _event_id(event)
        if not self.enabled:
            return EvidenceCaptureResult(event_id, CAPTURE_DISABLED, reason="evidence capture is disabled")
        if self.recorder is None:
            return EvidenceCaptureResult(event_id, CAPTURE_UNAVAILABLE, reason="no evidence recorder is configured")
        if event_id is None:
            return EvidenceCaptureResult(None, CAPTURE_UNAVAILABLE, reason="event_id is required for evidence upload")

        source_id = _event_value(event, "source_id")
        started_at = _event_value(event, "started_at")
        ended_at = _event_value(event, "ended_at")
        if not isinstance(source_id, str) or not source_id.strip():
            return EvidenceCaptureResult(event_id, CAPTURE_UNAVAILABLE, reason="source_id is required for evidence upload")
        if source_id.strip() != self.recorder.source_id:
            return EvidenceCaptureResult(
                event_id,
                CAPTURE_UNAVAILABLE,
                reason=(
                    f"event source_id {source_id.strip()!r} does not match "
                    f"recorder source_id {self.recorder.source_id!r}"
                ),
            )
        if not isinstance(started_at, datetime) or not isinstance(ended_at, datetime):
            return EvidenceCaptureResult(event_id, CAPTURE_UNAVAILABLE, reason="event timestamps are required for evidence upload")

        event_uploader: EvidenceClipUploader | Any = self.uploader
        close_event_uploader = False
        try:
            window = self.recorder.window_for_event(
                started_at,
                ended_at,
                pre_seconds=self.pre_seconds,
                post_seconds=self.post_seconds,
            )

            if self.uploader_factory is not None:
                # A factory may be synchronous (the common case) or an async
                # callable owned by an integration.  Neither form changes the
                # uploader protocol itself.
                event_uploader = self.uploader_factory(event_id)
                if inspect.isawaitable(event_uploader):
                    event_uploader = await event_uploader
                close_event_uploader = True

            if event_uploader is None or not callable(getattr(event_uploader, "upload", None)):
                return EvidenceCaptureResult(
                    event_id,
                    CAPTURE_UNAVAILABLE,
                    window,
                    reason="uploader_factory did not return an evidence uploader",
                )

            # HttpEvidenceClipUploader exposes ``event_id`` when it was built
            # for a specific endpoint.  Reusing such an instance for another
            # event would silently POST both clips to the first event URL, so
            # reject the mismatch before any media upload.  Uploaders with no
            # binding (including explicit custom endpoint instances) retain
            # the existing compatibility behavior.
            bound_event_id = getattr(event_uploader, "event_id", None)
            if isinstance(bound_event_id, str) and bound_event_id.strip() and bound_event_id.strip() != event_id:
                return EvidenceCaptureResult(
                    event_id,
                    CAPTURE_UNAVAILABLE,
                    window,
                    reason=(
                        f"uploader is bound to event_id {bound_event_id.strip()!r}, "
                        f"cannot upload event_id {event_id!r}"
                    ),
                )

            upload = await self.recorder.upload_event(
                started_at,
                ended_at,
                event_uploader,
                pre_seconds=self.pre_seconds,
                post_seconds=self.post_seconds,
            )
        except (OSError, TypeError, ValueError, RuntimeError) as exc:
            return EvidenceCaptureResult(event_id, CAPTURE_ERROR, window if "window" in locals() else None, reason=str(exc))
        except Exception as exc:  # pragma: no cover - defensive integration boundary
            logger.exception("evidence capture failed event_id=%s", event_id)
            return EvidenceCaptureResult(event_id, CAPTURE_ERROR, window if "window" in locals() else None, reason=str(exc))
        finally:
            if close_event_uploader:
                close_uploader = getattr(event_uploader, "aclose", None)
                if callable(close_uploader):
                    try:
                        await close_uploader()
                    except Exception:  # pragma: no cover - defensive resource cleanup
                        logger.warning("event evidence uploader close failed event_id=%s", event_id, exc_info=True)

        upload_status = getattr(upload, "status", None)
        upload_uri = getattr(upload, "uri", None)
        has_uri = isinstance(upload_uri, str) and bool(upload_uri.strip())
        if upload_status == CAPTURE_AVAILABLE and has_uri:
            status = CAPTURE_AVAILABLE
        elif upload_status == CAPTURE_AVAILABLE:
            status = CAPTURE_ERROR
        elif upload_status in {CAPTURE_UNAVAILABLE, "unsupported"}:
            status = CAPTURE_UNAVAILABLE
        else:
            status = CAPTURE_ERROR
        reason = getattr(upload, "reason", None)
        if upload_status == CAPTURE_AVAILABLE and not has_uri and not reason:
            reason = "uploader reported available without a usable URI"
        return EvidenceCaptureResult(
            event_id,
            status,
            window,
            upload,
            reason,
        )

    async def capture_events(self, events: Iterable[Any]) -> list[EvidenceCaptureResult]:
        """Capture events sequentially in iterable order.

        This method does not run automatically after an analysis job.  The
        caller owns the ordering boundary: persist/push each event first, then
        invoke this method when the external evidence endpoint is ready.
        """

        results: list[EvidenceCaptureResult] = []
        for event in events:
            results.append(await self.capture_event(event))
        return results

    async def aclose(self) -> None:
        """Close owned recorder media and an async uploader when supported."""

        self.close()
        close_uploader = getattr(self.uploader, "aclose", None)
        if callable(close_uploader):
            await close_uploader()

    def close(self) -> None:
        """Release buffered frames and any recorder-owned generated clips."""

        if self.recorder is not None:
            self.recorder.close()

    def capture_events_sync(self, events: Iterable[Any]) -> list[EvidenceCaptureResult]:
        """Synchronous convenience wrapper for callers outside an event loop."""

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.capture_events(events))
        raise RuntimeError("capture_events_sync cannot run inside an active event loop; await capture_events instead")

    # Short aliases make the adapter easy to wire into integration code while
    # keeping the explicit event-window method name available.
    capture = capture_event
    capture_all = capture_events

    def __enter__(self) -> "EvidenceCaptureOrchestrator":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    async def __aenter__(self) -> "EvidenceCaptureOrchestrator":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.aclose()


__all__ = [
    "CAPTURE_AVAILABLE",
    "CAPTURE_DISABLED",
    "CAPTURE_ERROR",
    "CAPTURE_UNAVAILABLE",
    "EvidenceUploaderFactory",
    "EventEvidenceCaptureResult",
    "EvidenceCaptureOrchestrator",
    "EvidenceCaptureResult",
]
