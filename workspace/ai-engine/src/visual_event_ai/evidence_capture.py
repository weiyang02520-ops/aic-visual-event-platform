from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol


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
