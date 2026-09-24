from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse


@dataclass(frozen=True)
class EvidenceResolutionResult:
    source_id: str
    started_at: datetime
    ended_at: datetime
    resolver: str
    status: str
    uri: str | None
    reason: str | None = None


class EvidenceResolver:
    """Resolves evidence conservatively without guessing archive URLs."""

    def resolve(self, source_id: str, started_at: datetime, ended_at: datetime, uri: str | None = None) -> EvidenceResolutionResult:
        if ended_at < started_at:
            raise ValueError("ended_at must be greater than or equal to started_at")
        if uri:
            scheme = urlparse(uri).scheme.lower()
            if scheme in {"http", "https", "hls", "rtmp", "rtsp"}:
                return EvidenceResolutionResult(
                    source_id,
                    started_at,
                    ended_at,
                    "caller-uri",
                    "provided_unverified",
                    uri,
                    "URI was supplied by the caller; retention, authorization and timestamp alignment are not verified",
                )
            return EvidenceResolutionResult(source_id, started_at, ended_at, "caller-uri", "unsupported", uri, f"unsupported evidence URI scheme: {scheme or 'none'}")
        if source_id.startswith("mock://") or source_id.startswith("fixture://"):
            return EvidenceResolutionResult(
                source_id,
                started_at,
                ended_at,
                "fixture-resolver",
                "fixture",
                f"{source_id}#start={started_at.isoformat()}&end={ended_at.isoformat()}",
                "deterministic fixture reference; not a real video archive",
            )
        return EvidenceResolutionResult(
            source_id,
            started_at,
            ended_at,
            "unconfigured",
            "unavailable",
            None,
            "no verified archive/segment resolver is configured for this source",
        )
