from datetime import datetime, timezone

import pytest

from visual_event_ai.evidence import EvidenceResolver


START = datetime(2026, 1, 1, tzinfo=timezone.utc)
END = datetime(2026, 1, 1, 0, 0, 5, tzinfo=timezone.utc)


def test_evidence_resolver_is_conservative():
    resolver = EvidenceResolver()
    assert resolver.resolve("mock://cam", START, END).status == "fixture"
    assert resolver.resolve("camera-01", START, END).status == "unavailable"
    provided = resolver.resolve("camera-01", START, END, "https://example.invalid/segment.m3u8")
    assert provided.status == "provided_unverified"
    with pytest.raises(ValueError):
        resolver.resolve("camera-01", END, START)
