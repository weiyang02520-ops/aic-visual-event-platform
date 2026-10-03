from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import mimetypes
import os
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import quote

import httpx


@dataclass(frozen=True)
class EvidenceWindow:
    source_id: str
    started_at: datetime
    ended_at: datetime


@dataclass(frozen=True)
class EvidenceUploadResult:
    status: str
    uri: str | None
    reason: str | None = None


def build_evidence_window(source_id: str, event_started_at: datetime, event_ended_at: datetime, *, pre_seconds: int = 10, post_seconds: int = 10) -> EvidenceWindow:
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be a non-empty string")
    if event_ended_at < event_started_at:
        raise ValueError("event_ended_at must be greater than or equal to event_started_at")
    if isinstance(pre_seconds, bool) or not isinstance(pre_seconds, int) or pre_seconds < 0:
        raise ValueError("pre_seconds must be a non-negative integer")
    if isinstance(post_seconds, bool) or not isinstance(post_seconds, int) or post_seconds < 0:
        raise ValueError("post_seconds must be a non-negative integer")
    return EvidenceWindow(source_id.strip(), event_started_at - timedelta(seconds=pre_seconds), event_ended_at + timedelta(seconds=post_seconds))


class EvidenceClipUploader(Protocol):
    async def upload(self, window: EvidenceWindow, clip: Any | None = None) -> EvidenceUploadResult: ...


class UnavailableClipUploader:
    """Explicit fallback until a recording/export endpoint is configured."""

    async def upload(self, window: EvidenceWindow, clip: Any | None = None) -> EvidenceUploadResult:
        return EvidenceUploadResult("unavailable", None, "no evidence clip uploader is configured")


class HttpEvidenceClipUploader:
    """Upload a captured clip to Makerverse's event evidence endpoint.

    The uploader is deliberately opt-in. Construct it with an explicit endpoint URL,
    or use :meth:`from_env` with both a Makerverse URL and event id. Missing endpoint
    configuration returns the same explicit ``unavailable`` result as the fallback
    uploader and never invents an object-store URI.
    """

    def __init__(
        self,
        endpoint_url: str | None = None,
        *,
        event_id: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
        retries: int = 0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.event_id = event_id.strip() if isinstance(event_id, str) and event_id.strip() else None
        endpoint = endpoint_url.strip() if isinstance(endpoint_url, str) and endpoint_url.strip() else None
        if endpoint is None and isinstance(base_url, str) and base_url.strip() and self.event_id:
            endpoint = f"{base_url.rstrip('/')}/api/v1/events/{quote(self.event_id, safe='')}/evidence"
        self.endpoint_url = endpoint
        self.retries = max(0, int(retries))
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(timeout=timeout)

    @classmethod
    def from_env(
        cls,
        event_id: str | None = None,
        *,
        timeout: float = 30.0,
        retries: int = 0,
        client: httpx.AsyncClient | None = None,
    ) -> "HttpEvidenceClipUploader":
        """Build an uploader from explicit endpoint or Makerverse base URL settings."""

        configured_endpoint = (
            os.getenv("MAKERVERSE_EVIDENCE_ENDPOINT")
            or os.getenv("MAKERVERSE_EVIDENCE_URL")
        )
        base_url = os.getenv("MAKERVERSE_URL") or os.getenv("MAKERVERSE_BASE_URL")
        if configured_endpoint and event_id:
            configured_endpoint = configured_endpoint.replace("{event_id}", quote(event_id, safe=""))
        elif configured_endpoint and "{event_id}" in configured_endpoint:
            configured_endpoint = None
        return cls(
            configured_endpoint,
            event_id=event_id,
            base_url=base_url,
            timeout=timeout,
            retries=retries,
            client=client,
        )

    @property
    def configured(self) -> bool:
        return bool(self.endpoint_url)

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def upload(self, window: EvidenceWindow, clip: Any | None = None) -> EvidenceUploadResult:
        if not self.endpoint_url:
            return EvidenceUploadResult("unavailable", None, "Makerverse evidence endpoint is not configured")
        if clip is None:
            return EvidenceUploadResult("unavailable", None, "no evidence clip was supplied")

        try:
            file_name, file_content, content_type, close_content = _clip_payload(clip)
        except (OSError, TypeError, ValueError) as exc:
            return EvidenceUploadResult("unavailable", None, f"evidence clip is not readable: {exc}")

        data = {
            "started_at": window.started_at.isoformat(),
            "ended_at": window.ended_at.isoformat(),
            "source_id": window.source_id,
        }
        files = {"clip": (file_name, file_content, content_type)}
        last_error: Exception | None = None
        try:
            for attempt in range(self.retries + 1):
                try:
                    if hasattr(file_content, "seek"):
                        file_content.seek(0)
                    response = await self.client.post(self.endpoint_url, data=data, files=files)
                    response.raise_for_status()
                    payload = response.json()
                    uri = payload.get("uri") if isinstance(payload, dict) else None
                    status = payload.get("status") if isinstance(payload, dict) else None
                    if not isinstance(uri, str) or not uri.strip():
                        return EvidenceUploadResult("error", None, "Makerverse evidence response has no URI")
                    return EvidenceUploadResult(str(status or "available"), uri, None)
                except (httpx.HTTPError, ValueError, TypeError) as exc:
                    last_error = exc
                    if attempt < self.retries:
                        await asyncio.sleep(0.2 * (attempt + 1))
            assert last_error is not None
            return EvidenceUploadResult("error", None, str(last_error))
        finally:
            if close_content:
                file_content.close()


def _clip_payload(clip: Any) -> tuple[str, Any, str, bool]:
    """Return ``(filename, file object/bytes, MIME, should_close)`` for httpx."""

    if isinstance(clip, (str, Path)):
        path = Path(clip)
        if not path.is_file():
            raise OSError(f"clip path does not exist: {path}")
        handle = path.open("rb")
        return path.name, handle, mimetypes.guess_type(path.name)[0] or "application/octet-stream", True

    if isinstance(clip, (bytes, bytearray, memoryview)):
        return "evidence.mp4", bytes(clip), "video/mp4", False

    if isinstance(clip, tuple) and len(clip) in (2, 3):
        filename = str(clip[0])
        content = clip[1]
        content_type = str(clip[2]) if len(clip) == 3 else mimetypes.guess_type(filename)[0]
        if isinstance(content, (str, Path)):
            path = Path(content)
            if not path.is_file():
                raise OSError(f"clip path does not exist: {path}")
            handle = path.open("rb")
            return filename or path.name, handle, content_type or "application/octet-stream", True
        if not isinstance(content, (bytes, bytearray, memoryview)) and not hasattr(content, "read"):
            raise TypeError("clip tuple content must be bytes or a readable file object")
        return filename or "evidence.mp4", content, content_type or "application/octet-stream", False

    if hasattr(clip, "read"):
        filename = str(getattr(clip, "name", "evidence.mp4"))
        return Path(filename).name or "evidence.mp4", clip, mimetypes.guess_type(filename)[0] or "application/octet-stream", False

    raise TypeError("clip must be a path, bytes, tuple, or readable file object")


# Short aliases keep the uploader discoverable for callers that use the generic
# ``ClipUploader`` terminology already present in this module.
HttpClipUploader = HttpEvidenceClipUploader


def build_evidence_uploader(event_id: str | None = None, **kwargs: Any) -> EvidenceClipUploader:
    """Return the configured HTTP uploader, or an explicit unavailable fallback."""

    uploader = HttpEvidenceClipUploader.from_env(event_id, **kwargs)
    return uploader if uploader.configured else UnavailableClipUploader()


# Additive lazy exports keep the original uploader/window contract intact while
# allowing integrations that already import evidence adapters from this module
# to discover the rolling recorder without introducing an import cycle.
_RECORDER_EXPORTS = {
    "BufferedEvidenceFrame",
    "CLIP_AVAILABLE",
    "CLIP_ERROR",
    "CLIP_UNAVAILABLE",
    "CLIP_UNSUPPORTED",
    "EvidenceClipResult",
    "RollingEvidenceRecorder",
}


def __getattr__(name: str) -> Any:
    if name in _RECORDER_EXPORTS:
        from . import evidence_recorder

        return getattr(evidence_recorder, name)
    raise AttributeError(name)
