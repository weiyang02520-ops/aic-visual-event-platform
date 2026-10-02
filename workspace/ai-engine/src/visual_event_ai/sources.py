from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class SourceDescriptor:
    """Transport-neutral source description; decoding remains provider-owned."""

    source_id: str
    kind: str
    provider: str
    status: str
    uri: str
    capabilities: tuple[str, ...]
    reason: str | None = None


class SourceResolver:
    def inspect(self, source: str) -> SourceDescriptor:
        value = source.strip()
        if not value:
            return SourceDescriptor("", "unknown", "none", "invalid", value, (), "source is empty")

        parsed = urlparse(value)
        scheme = parsed.scheme.lower()
        # ``urlparse`` treats a Windows drive letter (``C:/...``) as a URI
        # scheme; normalize it back to a local path before dispatching.
        if len(scheme) == 1 and len(value) > 2 and value[1] == ":":
            scheme = ""
        if scheme == "mock":
            return SourceDescriptor(value, "mock", "mock-provider", "available", value, ("facts", "events"))
        if scheme in {"rtmp", "rtsp", "http", "https", "hls"}:
            return SourceDescriptor(
                value,
                "stream",
                "opencv-stream-provider",
                "configured",
                value,
                ("realtime-frames", "evidence-uri"),
                "stream connectivity is verified when the OpenCV/FFmpeg provider opens the source",
            )
        if scheme == "file":
            candidate = Path(parsed.path)
        else:
            candidate = Path(value)
        if candidate.exists() and candidate.is_file():
            return SourceDescriptor(
                value,
                "file",
                "local-file-provider",
                "available",
                value,
                ("metadata", "frames-pending"),
                "frame decoding is intentionally provider-owned",
            )
        if scheme in {"", "file"}:
            return SourceDescriptor(value, "file", "local-file-provider", "unavailable", value, (), "file does not exist")
        return SourceDescriptor(value, "unknown", "none", "unsupported", value, (), f"unsupported source scheme: {scheme}")
