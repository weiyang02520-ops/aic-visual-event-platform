"""Rolling evidence recording and clip export.

The recorder deliberately sits below the event/reasoning layers.  It accepts
frames from any source that can provide a source id, timestamp and payload;
it does not open a camera or invent an archive URL.  A real clip is exported
only when an OpenCV ``VideoWriter`` (or an explicitly injected test writer)
can encode the buffered image frames.

``FramePipeline`` currently exposes OpenCV frames as ``{"image": image,
...}`` payloads.  The recorder understands that shape, a bare OpenCV image,
and a small ``{"frame": image}`` adapter shape.  Other payloads remain useful
for buffering and diagnostics but return ``unsupported`` on export.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
import math
import os
from pathlib import Path
import tempfile
from typing import Any, Callable, Iterable, Protocol

from .evidence_capture import EvidenceUploadResult, EvidenceWindow, build_evidence_window


CLIP_AVAILABLE = "available"
CLIP_UNAVAILABLE = "unavailable"
CLIP_UNSUPPORTED = "unsupported"
CLIP_ERROR = "error"


@dataclass(frozen=True)
class EvidenceClipResult:
    """Result of exporting one evidence window.

    ``clip`` is a path owned by the recorder when ``status`` is ``available``.
    It remains usable until :meth:`RollingEvidenceRecorder.close` (or
    :meth:`RollingEvidenceRecorder.cleanup_clip`) is called.  ``uri`` is kept
    explicitly ``None`` here: URI creation belongs to the configured uploader
    and is never guessed by this local recorder.
    """

    status: str
    window: EvidenceWindow | None = None
    clip: Path | None = None
    reason: str | None = None
    bytes_written: int = 0
    frame_count: int = 0
    uri: str | None = None

    @property
    def available(self) -> bool:
        return self.status == CLIP_AVAILABLE and self.clip is not None

    @property
    def path(self) -> Path | None:
        """Compatibility alias for callers that call exported clips paths."""

        return self.clip

    @property
    def clip_path(self) -> Path | None:
        return self.clip


@dataclass(frozen=True)
class BufferedEvidenceFrame:
    """A source-independent frame retained in the rolling buffer."""

    source_id: str
    timestamp: datetime
    payload: Any


class EvidenceWriter(Protocol):
    def isOpened(self) -> bool: ...

    def write(self, frame: Any) -> None: ...

    def release(self) -> None: ...


WriterFactory = Callable[[Path, float, tuple[int, int], str], EvidenceWriter]


def _default_output_dir() -> Path:
    """Return the project-owned evidence directory, never the OS temp dir."""

    configured = os.getenv("AI_EVIDENCE_DIR")
    if isinstance(configured, str) and configured.strip():
        return Path(configured.strip())
    # evidence_recorder.py -> visual_event_ai -> src -> ai-engine.
    return Path(__file__).resolve().parents[2] / "runtime" / "evidence"


def _validate_source_id(source_id: str) -> str:
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be a non-empty string")
    return source_id.strip()


def _validate_non_negative_int(value: Any, name: str, *, allow_none: bool = False) -> int | None:
    if allow_none and value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        suffix = " or None" if allow_none else ""
        raise ValueError(f"{name} must be a non-negative integer{suffix}")
    return value


def _estimate_frame_shape(frame: Any) -> tuple[int, int] | None:
    shape = getattr(frame, "shape", None)
    if not isinstance(shape, (tuple, list)) or len(shape) < 2:
        return None
    try:
        height, width = int(shape[0]), int(shape[1])
    except (TypeError, ValueError, OverflowError):
        return None
    if height <= 0 or width <= 0:
        return None
    return width, height


def _image_payload(payload: Any) -> Any | None:
    """Extract an OpenCV image from the supported provider payload shapes."""

    if isinstance(payload, dict):
        candidate = payload.get("image")
        if candidate is None:
            candidate = payload.get("frame")
        return candidate
    return payload


def _try_import_cv2() -> Any | None:
    try:
        import cv2  # type: ignore[import-not-found]
    except (ImportError, OSError):
        return None
    return cv2


def _unlink_quiet(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _default_writer_factory(cv2: Any) -> WriterFactory:
    def create(path: Path, fps: float, frame_size: tuple[int, int], codec: str) -> EvidenceWriter:
        fourcc_factory = getattr(cv2, "VideoWriter_fourcc", None)
        if callable(fourcc_factory):
            fourcc = fourcc_factory(*codec)
        else:
            # Test doubles may accept the codec string directly.  Real OpenCV
            # exposes VideoWriter_fourcc, so this branch remains conservative.
            fourcc = codec
        return cv2.VideoWriter(str(path), fourcc, fps, frame_size)

    return create


class RollingEvidenceRecorder:
    """Bounded rolling frame buffer with conservative clip export.

    The recorder never reads a source itself.  Call :meth:`append_frame` for
    each observed frame, then call :meth:`export_event` when the post-event
    frames are available.  ``export_event`` requires the buffer to cover the
    complete requested window; :meth:`export` can be used for an intentionally
    partial window by leaving ``require_full_window`` at ``False``.
    """

    def __init__(
        self,
        source_id: str,
        *,
        max_seconds: int = 60,
        max_frames: int | None = 3000,
        max_bytes: int | None = 50 * 1024 * 1024,
        output_dir: str | Path | None = None,
        file_prefix: str = "evidence",
        codec: str = "mp4v",
        fps: float = 25.0,
        writer_factory: WriterFactory | None = None,
    ) -> None:
        self.source_id = _validate_source_id(source_id)
        self.max_seconds = int(_validate_non_negative_int(max_seconds, "max_seconds"))
        self.max_frames = _validate_non_negative_int(max_frames, "max_frames", allow_none=True)
        self.max_bytes = _validate_non_negative_int(max_bytes, "max_bytes", allow_none=True)
        if not isinstance(file_prefix, str) or not file_prefix.strip():
            raise ValueError("file_prefix must be a non-empty string")
        self.file_prefix = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in file_prefix.strip())
        if not isinstance(codec, str) or len(codec) != 4:
            raise ValueError("codec must be a four-character OpenCV codec")
        self.codec = codec
        if isinstance(fps, bool):
            raise ValueError("fps must be a finite positive number")
        try:
            self.fps = float(fps)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("fps must be a finite positive number") from exc
        if not math.isfinite(self.fps) or self.fps <= 0:
            raise ValueError("fps must be a finite positive number")
        self.output_dir = Path(output_dir) if output_dir is not None else _default_output_dir()
        self.writer_factory = writer_factory
        self._frames: deque[BufferedEvidenceFrame] = deque()
        self._owned_clips: set[Path] = set()
        self._closed = False
        self._timezone_aware: bool | None = None

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def buffered_frames(self) -> int:
        return len(self._frames)

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("evidence recorder is closed")

    def _validate_timestamp(self, timestamp: datetime) -> datetime:
        if not isinstance(timestamp, datetime):
            raise TypeError("timestamp must be a datetime")
        aware = timestamp.tzinfo is not None and timestamp.utcoffset() is not None
        if self._timezone_aware is None:
            self._timezone_aware = aware
        elif self._timezone_aware != aware:
            raise ValueError("all recorder timestamps must use the same timezone awareness")
        return timestamp

    def append_frame(
        self,
        timestamp: datetime,
        payload: Any,
        *,
        source_id: str | None = None,
    ) -> BufferedEvidenceFrame:
        """Append one frame and evict frames outside the rolling bounds."""

        self._ensure_open()
        timestamp = self._validate_timestamp(timestamp)
        observed_source = self.source_id if source_id is None else _validate_source_id(source_id)
        if observed_source != self.source_id:
            raise ValueError(f"frame source_id {observed_source!r} does not match recorder source_id {self.source_id!r}")
        item = BufferedEvidenceFrame(self.source_id, timestamp, payload)
        self._frames.append(item)
        self._trim()
        return item

    def append(self, frame: Any, timestamp: datetime | None = None, *, source_id: str | None = None) -> BufferedEvidenceFrame:
        """Append either a ``Frame``-like object or a bare payload.

        A ``Frame``-like object only needs ``timestamp`` and optionally
        ``payload``/``source_id`` attributes, keeping the recorder independent
        from ``frame_pipeline.py``.
        """

        candidate_timestamp = timestamp if timestamp is not None else getattr(frame, "timestamp", None)
        if candidate_timestamp is None:
            raise TypeError("timestamp is required when appending a bare payload")
        candidate_payload = getattr(frame, "payload", frame)
        candidate_source = source_id if source_id is not None else getattr(frame, "source_id", None)
        return self.append_frame(candidate_timestamp, candidate_payload, source_id=candidate_source)

    record_frame = append_frame
    add_frame = append_frame

    def _trim(self) -> None:
        if not self._frames:
            return
        # A network source can deliver a late frame after a reconnect.  Keep
        # retention deterministic even when append order is not timestamp order.
        newest = max(item.timestamp for item in self._frames)
        cutoff = newest - timedelta(seconds=self.max_seconds)
        retained = [item for item in self._frames if item.timestamp >= cutoff]
        if self.max_frames is not None:
            # ``[-0:]`` means "the complete list" in Python.  Treat a zero
            # frame limit as an intentionally disabled buffer instead of
            # accidentally retaining every frame and defeating the memory
            # bound.
            if self.max_frames == 0:
                retained = []
            else:
                retained = sorted(retained, key=lambda item: item.timestamp)[-self.max_frames :]
        self._frames = deque(retained)

    def window_for_event(
        self,
        event_started_at: datetime,
        event_ended_at: datetime,
        *,
        pre_seconds: int = 10,
        post_seconds: int = 10,
    ) -> EvidenceWindow:
        return build_evidence_window(
            self.source_id,
            event_started_at,
            event_ended_at,
            pre_seconds=pre_seconds,
            post_seconds=post_seconds,
        )

    build_event_window = window_for_event

    def _sorted_frames(self) -> list[BufferedEvidenceFrame]:
        return sorted(self._frames, key=lambda item: item.timestamp)

    def _frames_for_window(self, window: EvidenceWindow) -> list[BufferedEvidenceFrame]:
        if window.source_id != self.source_id:
            raise ValueError(
                f"evidence window source_id {window.source_id!r} does not match recorder source_id {self.source_id!r}"
            )
        if window.ended_at < window.started_at:
            raise ValueError("evidence window ended_at must be greater than or equal to started_at")
        return [
            item
            for item in self._sorted_frames()
            if window.started_at <= item.timestamp <= window.ended_at
        ]

    def export(
        self,
        window: EvidenceWindow,
        *,
        require_full_window: bool = False,
    ) -> EvidenceClipResult:
        """Encode buffered image frames falling inside ``window``.

        ``unavailable`` means a required runtime dependency is absent or the
        buffer has no usable frames.  ``unsupported`` means a dependency was
        present but the payload/codec cannot be encoded.  ``error`` represents
        an I/O, writer, or size-limit failure.  All failure results keep
        ``clip`` and ``uri`` as ``None``.
        """

        self._ensure_open()
        frames = self._frames_for_window(window)
        if not frames:
            return EvidenceClipResult(CLIP_UNAVAILABLE, window, reason="no buffered frames fall inside evidence window")
        ordered = self._sorted_frames()
        if require_full_window:
            if ordered[0].timestamp > window.started_at or ordered[-1].timestamp < window.ended_at:
                return EvidenceClipResult(
                    CLIP_UNAVAILABLE,
                    window,
                    reason="rolling buffer does not cover the complete evidence window",
                    frame_count=len(frames),
                )

        cv2 = None
        if self.writer_factory is None:
            cv2 = _try_import_cv2()
            if cv2 is None:
                return EvidenceClipResult(
                    CLIP_UNAVAILABLE,
                    window,
                    reason="OpenCV/FFmpeg is unavailable; install the optional media dependency",
                    frame_count=len(frames),
                )
            writer_factory = _default_writer_factory(cv2)
        else:
            writer_factory = self.writer_factory

        # A CFR writer has no timestamp channel.  Build a small timestamp
        # index and feed it one frame for every target output tick.  The
        # latest source frame at or before a target tick is carried forward;
        # this preserves gaps without ever placing a future frame before its
        # capture time.  Include one carry-in frame before the window start so
        # a sparse stream can still cover the first output interval.
        ordered_all = self._sorted_frames()
        source_items = [item for item in ordered_all if item.timestamp <= window.ended_at]
        start_index = -1
        for index, item in enumerate(source_items):
            if item.timestamp <= window.started_at:
                start_index = index
            else:
                break
        if start_index < 0:
            return EvidenceClipResult(
                CLIP_UNAVAILABLE,
                window,
                reason="no buffered frame is available at or before evidence window start",
                frame_count=len(frames),
            )

        # Validate every source frame that could be selected by the timeline.
        # This keeps the old conservative unsupported result for mixed payloads
        # instead of silently dropping a bad frame in the middle of a gap.
        images_by_item: dict[int, tuple[Any, tuple[int, int]]] = {}
        for index, item in enumerate(source_items):
            image = _image_payload(item.payload)
            shape = _estimate_frame_shape(image)
            if image is None or shape is None:
                return EvidenceClipResult(
                    CLIP_UNSUPPORTED,
                    window,
                    reason="buffered frame payload does not contain a usable OpenCV image",
                    frame_count=len(frames),
                )
            images_by_item[index] = (image, shape)

        frame_size = images_by_item[start_index][1]
        if any(shape != frame_size for _, shape in images_by_item.values()):
            return EvidenceClipResult(
                CLIP_UNSUPPORTED,
                window,
                reason="buffered frames have inconsistent image dimensions",
                frame_count=len(frames),
            )

        target_dir = self.output_dir
        try:
            if target_dir is not None:
                target_dir.mkdir(parents=True, exist_ok=True)
                if not target_dir.is_dir():
                    raise OSError(f"output_dir is not a directory: {target_dir}")
            fd, raw_path = tempfile.mkstemp(
                prefix=f"{self.file_prefix}-",
                suffix=".mp4",
                dir=str(target_dir),
            )
            os.close(fd)
            path = Path(raw_path)
        except (OSError, TypeError, ValueError) as exc:
            return EvidenceClipResult(CLIP_ERROR, window, reason=f"could not allocate clip output: {exc}", frame_count=len(frames))

        writer: EvidenceWriter | None = None
        release_error: Exception | None = None
        writer_failure: EvidenceClipResult | None = None
        duration_seconds = max(0.0, (window.ended_at - window.started_at).total_seconds())
        # A video with N CFR frames at fps has a physical duration of N/fps.
        # Rounding to the nearest frame keeps the encoded duration within one
        # output frame of the requested evidence window.
        output_frame_count = max(1, int(round(duration_seconds * self.fps)))
        tick_seconds = 1.0 / self.fps
        try:
            writer = writer_factory(path, self.fps, frame_size, self.codec)
            is_open = getattr(writer, "isOpened", None)
            if callable(is_open) and not is_open():
                writer_failure = EvidenceClipResult(
                    CLIP_UNSUPPORTED,
                    window,
                    reason="OpenCV/FFmpeg could not open a video writer for the selected codec",
                    frame_count=len(frames),
                )
            else:
                write = getattr(writer, "write", None)
                if not callable(write):
                    writer_failure = EvidenceClipResult(
                        CLIP_UNSUPPORTED,
                        window,
                        reason="video writer has no write method",
                        frame_count=len(frames),
                    )
                else:
                    source_index = start_index
                    for output_index in range(output_frame_count):
                        target_seconds = output_index * tick_seconds
                        target_timestamp = window.started_at + timedelta(seconds=target_seconds)
                        while (
                            source_index + 1 < len(source_items)
                            and source_items[source_index + 1].timestamp <= target_timestamp
                        ):
                            source_index += 1
                        # ``start_index`` is guaranteed to be at or before the
                        # window start, so this branch cannot use a future
                        # frame.  Keep the guard for unusual datetime/codec
                        # integrations and fail closed if it is ever reached.
                        if source_index < 0 or source_items[source_index].timestamp > target_timestamp:
                            writer_failure = EvidenceClipResult(
                                CLIP_ERROR,
                                window,
                                reason="cannot resample evidence without a frame at or before target timestamp",
                                frame_count=output_index,
                            )
                            break
                        write(images_by_item[source_index][0])
        except Exception as exc:
            writer_failure = EvidenceClipResult(CLIP_ERROR, window, reason=f"video writer failed: {exc}", frame_count=0)
        finally:
            if writer is not None:
                try:
                    writer.release()
                except Exception as exc:  # pragma: no cover - defensive cleanup path
                    release_error = exc

        # Release first, then clean up the allocated path.  Some writers flush
        # their container trailer during ``release``; deleting earlier can
        # leave a leaked handle or a partially written file on Windows.
        if writer_failure is not None:
            _unlink_quiet(path)
            return writer_failure

        if release_error is not None:
            _unlink_quiet(path)
            return EvidenceClipResult(CLIP_ERROR, window, reason=f"video writer release failed: {release_error}", frame_count=output_frame_count)

        try:
            size = path.stat().st_size
        except OSError as exc:
            _unlink_quiet(path)
            return EvidenceClipResult(CLIP_ERROR, window, reason=f"encoded clip is not readable: {exc}", frame_count=len(frames))
        if size <= 0:
            _unlink_quiet(path)
            return EvidenceClipResult(CLIP_ERROR, window, reason="video writer produced an empty clip", frame_count=len(frames))
        if self.max_bytes is not None and size > self.max_bytes:
            _unlink_quiet(path)
            return EvidenceClipResult(
                CLIP_ERROR,
                window,
                reason=f"encoded clip exceeds max_bytes={self.max_bytes}",
                bytes_written=size,
                frame_count=output_frame_count,
            )
        self._owned_clips.add(path)
        return EvidenceClipResult(CLIP_AVAILABLE, window, path, bytes_written=size, frame_count=output_frame_count)

    def export_event(
        self,
        event_started_at: datetime,
        event_ended_at: datetime,
        *,
        pre_seconds: int = 10,
        post_seconds: int = 10,
    ) -> EvidenceClipResult:
        """Build the event window and require complete rolling coverage."""

        window = self.window_for_event(
            event_started_at,
            event_ended_at,
            pre_seconds=pre_seconds,
            post_seconds=post_seconds,
        )
        return self.export(window, require_full_window=True)

    capture_event = export_event
    export_clip = export

    def cleanup_clip(self, clip: EvidenceClipResult | Path | str | None) -> None:
        """Remove a generated clip, ignoring an already-cleaned path."""

        path: Path | None
        if isinstance(clip, EvidenceClipResult):
            path = clip.clip
        elif clip is None:
            path = None
        else:
            path = Path(clip)
        if path is None:
            return
        # Only paths allocated by this recorder may be removed.  Callers can
        # pass fixture or externally managed paths to upload_event; those are
        # never owned by the recorder and must survive cleanup calls.
        if path not in self._owned_clips:
            return
        self._owned_clips.discard(path)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

    async def upload_event(
        self,
        event_started_at: datetime,
        event_ended_at: datetime,
        uploader: Any,
        *,
        pre_seconds: int = 10,
        post_seconds: int = 10,
        clip: Any | None = None,
    ) -> EvidenceUploadResult:
        """Export an event and pass the local clip to an existing uploader.

        ``clip`` is an explicit escape hatch for byte or fixture-path tests and
        already-captured media.  It is passed through unchanged, preserving
        ``HttpEvidenceClipUploader``'s public contract.
        """

        window = self.window_for_event(
            event_started_at,
            event_ended_at,
            pre_seconds=pre_seconds,
            post_seconds=post_seconds,
        )
        exported: EvidenceClipResult | None = None
        supplied = clip
        if supplied is None:
            exported = self.export(window, require_full_window=True)
            if not exported.available:
                return EvidenceUploadResult(exported.status, None, exported.reason)
            supplied = exported.clip
        try:
            return await uploader.upload(window, supplied)
        except (OSError, TypeError, ValueError, RuntimeError) as exc:
            return EvidenceUploadResult(CLIP_ERROR, None, f"evidence upload failed: {exc}")
        finally:
            if exported is not None:
                self.cleanup_clip(exported)

    upload = upload_event

    def close(self) -> None:
        if self._closed:
            return
        for path in list(self._owned_clips):
            self.cleanup_clip(path)
        self._frames.clear()
        self._closed = True

    def __enter__(self) -> "RollingEvidenceRecorder":
        self._ensure_open()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()


__all__ = [
    "BufferedEvidenceFrame",
    "CLIP_AVAILABLE",
    "CLIP_ERROR",
    "CLIP_UNAVAILABLE",
    "CLIP_UNSUPPORTED",
    "EvidenceClipResult",
    "RollingEvidenceRecorder",
]
