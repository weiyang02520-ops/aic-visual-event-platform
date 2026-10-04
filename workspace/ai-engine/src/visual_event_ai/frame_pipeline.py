from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from math import isfinite
from numbers import Integral
from pathlib import Path
from threading import Event
from typing import Any, Iterator, Protocol
from urllib.parse import parse_qs, unquote, urlparse


class FramePipelineError(RuntimeError):
    pass


@dataclass(frozen=True)
class Frame:
    source_id: str
    frame_index: int
    timestamp: datetime
    payload: Any
    metadata: dict[str, Any] = field(default_factory=dict)


class CancellationToken:
    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self.cancelled:
            raise FramePipelineError("frame pipeline cancelled")


class FrameProvider(Protocol):
    def iter_frames(
        self,
        source: str,
        *,
        interval: timedelta,
        max_frames: int | None,
        token: CancellationToken,
        recover: bool,
    ) -> Iterator[Frame]: ...


def _finite_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if isfinite(number) else None


def _source_path(source: str) -> Path:
    parsed = urlparse(source)
    if parsed.scheme.lower() == "file":
        path = unquote(parsed.path)
        if len(path) > 3 and path[0] == "/" and path[2] == ":":
            path = path[1:]
        return Path(path)
    # urlparse interprets C:/... as scheme C; Windows drive paths are files.
    if len(parsed.scheme) == 1 and len(source) > 2 and source[1] == ":":
        return Path(source)
    return Path(source)


def _camera_index(source: str) -> int:
    """Return the device index encoded by a ``camera://`` style URI.

    Camera sources deliberately use a URI instead of accepting a bare integer
    so they cannot be confused with local file paths.  The authority form
    (``camera://0``) is the public spelling; ``camera:///0`` is accepted as a
    URI-equivalent spelling for callers that build URIs mechanically.
    """

    parsed = urlparse(source)
    scheme = parsed.scheme.lower() or "camera"
    raw_index: str | None
    if parsed.netloc:
        # A device URI has no path, query, or fragment.  Rejecting extra
        # components keeps the selected device unambiguous.
        raw_index = parsed.netloc if parsed.path in {"", "/"} else None
    elif parsed.path.startswith("/") and parsed.path.count("/") == 1:
        raw_index = parsed.path[1:]
    else:
        raw_index = None
    if (
        not raw_index
        or not raw_index.isascii()
        or not raw_index.isdigit()
        or parsed.query
        or parsed.fragment
    ):
        raise FramePipelineError(
            f"{scheme} source must use a non-negative integer camera index, "
            f"for example {scheme}://0"
        )
    try:
        index = int(raw_index)
    except (TypeError, ValueError, OverflowError) as exc:
        raise FramePipelineError(
            f"{scheme} source camera index is not a representable non-negative integer"
        ) from exc
    if index < 0:
        raise FramePipelineError(
            f"{scheme} source must use a non-negative integer camera index, "
            f"for example {scheme}://0"
        )
    return index


class MockFrameProvider:
    def iter_frames(self, source: str, *, interval: timedelta, max_frames: int | None, token: CancellationToken, recover: bool) -> Iterator[Frame]:
        query = parse_qs(urlparse(source).query)
        count = int(query.get("frames", [max_frames or 8])[0])
        if max_frames is not None:
            count = min(count, max_frames)
        start = datetime.now(timezone.utc)
        for index in range(max(count, 0)):
            token.raise_if_cancelled()
            yield Frame(
                source_id=source,
                frame_index=index,
                timestamp=start + interval * index,
                payload={"fixture": urlparse(source).netloc or "default", "index": index},
                metadata={"provider": "mock", "synthetic": True},
            )


class JsonlFrameProvider:
    """Reads lightweight local frame fixtures without requiring FFmpeg.

    Each non-empty line is JSON. A line may contain ``timestamp`` (ISO-8601)
    and ``payload``; other fields are retained in metadata. This is a test and
    integration fixture format, not a claim that MP4 decoding is available.
    """

    def iter_frames(self, source: str, *, interval: timedelta, max_frames: int | None, token: CancellationToken, recover: bool) -> Iterator[Frame]:
        path = _source_path(source)
        if not path.exists() or not path.is_file():
            raise FramePipelineError(f"local source does not exist: {path}")
        if path.suffix.lower() not in {".jsonl", ".ndjson"}:
            raise FramePipelineError("local media decoding requires an optional FFmpeg/OpenCV provider")
        start = datetime.now(timezone.utc)
        emitted = 0
        recovered_line: int | None = None
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, start=1):
                token.raise_if_cancelled()
                if max_frames is not None and emitted >= max_frames:
                    break
                if not raw.strip():
                    continue
                try:
                    item = json.loads(raw)
                    if not isinstance(item, dict):
                        raise ValueError("frame fixture must be a JSON object")
                    timestamp = datetime.fromisoformat(str(item["timestamp"]).replace("Z", "+00:00")) if item.get("timestamp") else start + interval * emitted
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                    payload = item.get("payload", item)
                    metadata = dict(item.get("metadata", {}))
                    metadata.update({"provider": "jsonl", "line": line_number})
                except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                    if recover:
                        recovered_line = line_number
                        continue
                    raise FramePipelineError(f"invalid frame fixture line {line_number}: {exc}") from exc
                if recovered_line is not None:
                    metadata.update(
                        {
                            "discontinuity_before": True,
                            "discontinuity_reason": "malformed_jsonl_record",
                            "skipped_line": recovered_line,
                        }
                    )
                    recovered_line = None
                yield Frame(source, emitted, timestamp, payload, metadata)
                emitted += 1


class OpenCVFrameProvider:
    """Optional OpenCV provider for local files and network media streams.

    OpenCV is imported lazily so the service still starts in minimal
    environments. The payload carries the decoded BGR image for model
    providers plus a list-based grayscale helper for the CPU motion baseline;
    API responses summarize both instead of serializing pixels.
    """

    extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}
    stream_schemes = {"rtsp", "rtmp", "http", "https", "hls"}
    camera_schemes = {"camera", "webcam"}

    def iter_frames(self, source: str, *, interval: timedelta, max_frames: int | None, token: CancellationToken, recover: bool) -> Iterator[Frame]:
        parsed = urlparse(source)
        scheme = parsed.scheme.lower()
        is_stream = scheme in self.stream_schemes
        is_camera = scheme in self.camera_schemes
        camera_index = _camera_index(source) if is_camera else None
        path = _source_path(source)
        if not is_stream and not is_camera and (not path.exists() or not path.is_file()):
            raise FramePipelineError(f"local source does not exist: {path}")
        try:
            import cv2
        except ImportError as exc:
            if is_camera:
                raise FramePipelineError(
                    "OpenCV provider unavailable; install visual-event-ai[media] "
                    "to capture webcam sources"
                ) from exc
            raise FramePipelineError(
                "OpenCV/FFmpeg provider unavailable; install visual-event-ai[media] "
                "to decode local, RTSP, RTMP, HTTP, or HLS sources"
            ) from exc
        capture_target = camera_index if is_camera else source if is_stream else str(path)
        capture = cv2.VideoCapture(capture_target)
        if not capture.isOpened():
            capture.release()
            if is_camera:
                raise FramePipelineError(
                    f"OpenCV could not open camera index {camera_index}; check camera "
                    f"connection and permissions: {source}"
                )
            if is_stream:
                raise FramePipelineError(
                    "OpenCV could not open stream; check URL reachability and "
                    f"FFmpeg/GStreamer codec support: {source}"
                )
            raise FramePipelineError(f"OpenCV could not open local video: {path}")
        reported_fps = _finite_float(capture.get(cv2.CAP_PROP_FPS))
        fps = reported_fps if reported_fps is not None and reported_fps > 0 else 25.0
        interval_seconds = interval.total_seconds()
        samples_per_interval = interval_seconds * fps
        if not isfinite(samples_per_interval):
            capture.release()
            raise FramePipelineError("OpenCV FPS and frame interval exceed the supported sampling range")
        step = max(1, round(samples_per_interval)) if interval_seconds > 0 else 1
        start = datetime.now(timezone.utc)
        read_index = 0
        emitted = 0
        try:
            while max_frames is None or emitted < max_frames:
                token.raise_if_cancelled()
                ok, image = capture.read()
                if not ok:
                    if is_stream or is_camera:
                        if is_camera:
                            state = "returned no frames" if emitted == 0 else "ended before the requested frame limit"
                            raise FramePipelineError(
                                f"OpenCV camera index {camera_index} {state}; check camera "
                                f"availability and permissions: {source}"
                            )
                        state = "returned no frames" if emitted == 0 else "ended before the requested frame limit"
                        raise FramePipelineError(
                            f"OpenCV stream {state}; check "
                            f"stream availability and decoder support: {source}"
                        )
                    break
                if read_index % step != 0:
                    read_index += 1
                    continue
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                position_ms = _finite_float(capture.get(cv2.CAP_PROP_POS_MSEC))
                position_seconds = position_ms / 1000.0 if position_ms is not None and position_ms > 0 else None
                frame_offset: timedelta | None = None
                if position_seconds is not None and isfinite(position_seconds):
                    try:
                        frame_offset = timedelta(seconds=position_seconds)
                    except (OverflowError, ValueError):
                        frame_offset = None
                if frame_offset is None:
                    fallback_seconds = read_index / fps
                    if not isfinite(fallback_seconds):
                        raise FramePipelineError("OpenCV frame timestamp is not finite")
                    try:
                        frame_offset = timedelta(seconds=fallback_seconds)
                    except (OverflowError, ValueError) as exc:
                        raise FramePipelineError("OpenCV frame timestamp exceeds the supported range") from exc
                try:
                    frame_timestamp = start + frame_offset
                except OverflowError as exc:
                    raise FramePipelineError("OpenCV frame timestamp exceeds the supported range") from exc
                image_shape = getattr(image, "shape", None) or getattr(gray, "shape", None)
                if not isinstance(image_shape, (list, tuple)) or len(image_shape) < 2:
                    raise FramePipelineError("OpenCV frame has no usable image shape")
                try:
                    height, width = int(image_shape[0]), int(image_shape[1])
                except (TypeError, ValueError, OverflowError) as exc:
                    raise FramePipelineError("OpenCV frame shape is invalid") from exc
                gray_payload = gray.tolist() if callable(getattr(gray, "tolist", None)) else gray
                channels = int(image_shape[2]) if len(image_shape) >= 3 else 1
                yield Frame(
                    source_id=source,
                    frame_index=emitted,
                    timestamp=frame_timestamp,
                    payload={
                        "image": image,
                        "gray": gray_payload,
                        "shape": [height, width],
                        "channels": channels,
                    },
                    metadata={
                        "provider": "opencv",
                        "source_kind": "camera" if is_camera else "stream" if is_stream else "file",
                        **(
                            {"stream_transport": "webcam", "camera_index": camera_index}
                            if is_camera
                            else {"stream_transport": scheme}
                            if is_stream
                            else {}
                        ),
                        "fps": fps,
                        "read_index": read_index,
                    },
                )
                emitted += 1
                read_index += 1
        finally:
            capture.release()


class FramePipeline:
    def __init__(self, providers: dict[str, FrameProvider] | None = None) -> None:
        self.providers = providers or {"mock": MockFrameProvider(), "file": JsonlFrameProvider(), "opencv": OpenCVFrameProvider()}

    def provider_for(self, source: str) -> FrameProvider:
        scheme = urlparse(source).scheme.lower()
        if len(scheme) == 1 and len(source) > 2 and source[1] == ":":
            scheme = "file"
        if scheme == "mock":
            return self.providers["mock"]
        if scheme in OpenCVFrameProvider.camera_schemes:
            if "opencv" not in self.providers:
                raise FramePipelineError("OpenCV provider is not configured for camera sources")
            return self.providers["opencv"]
        if scheme in OpenCVFrameProvider.stream_schemes:
            if "opencv" not in self.providers:
                raise FramePipelineError(
                    "OpenCV provider is not configured for RTSP/RTMP/HTTP/HLS stream sources"
                )
            return self.providers["opencv"]
        if scheme in {"", "file"}:
            path = _source_path(source)
            if path.suffix.lower() in OpenCVFrameProvider.extensions:
                if "opencv" not in self.providers:
                    raise FramePipelineError("OpenCV provider is not configured for local video sources")
                return self.providers["opencv"]
            return self.providers["file"]
        raise FramePipelineError(f"no frame provider configured for source scheme: {scheme}")

    def iter_frames(
        self,
        source: str,
        *,
        interval_ms: int = 1000,
        max_frames: int | None = None,
        token: CancellationToken | None = None,
        recover: bool = True,
    ) -> Iterator[Frame]:
        if isinstance(interval_ms, bool) or not isinstance(interval_ms, Integral) or interval_ms < 0:
            raise ValueError("interval_ms must be a non-negative integer")
        if max_frames is not None and (
            isinstance(max_frames, bool) or not isinstance(max_frames, Integral) or max_frames < 0
        ):
            raise ValueError("max_frames must be a non-negative integer or None")
        try:
            interval = timedelta(milliseconds=int(interval_ms))
        except (OverflowError, ValueError) as exc:
            raise ValueError("interval_ms exceeds the supported duration range") from exc
        cancellation = token or CancellationToken()
        provider = self.provider_for(source)
        yield from provider.iter_frames(
            source,
            interval=interval,
            max_frames=None if max_frames is None else int(max_frames),
            token=cancellation,
            recover=recover,
        )
