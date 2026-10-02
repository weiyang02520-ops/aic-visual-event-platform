from datetime import datetime, timezone

import pytest

from visual_event_ai.evidence_capture import UnavailableClipUploader, build_evidence_window


START = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
END = datetime(2026, 1, 1, 8, 0, 5, tzinfo=timezone.utc)


def test_event_window_defaults_to_ten_seconds_each_side():
    window = build_evidence_window("camera-01", START, END)
    assert (window.ended_at - window.started_at).total_seconds() == 25
    assert window.started_at == datetime(2026, 1, 1, 7, 59, 50, tzinfo=timezone.utc)
    assert window.ended_at == datetime(2026, 1, 1, 8, 0, 15, tzinfo=timezone.utc)


def test_event_window_rejects_invalid_input():
    with pytest.raises(ValueError):
        build_evidence_window("", START, END)
    with pytest.raises(ValueError):
        build_evidence_window("camera-01", END, START)
    with pytest.raises(ValueError):
        build_evidence_window("camera-01", START, END, pre_seconds=-1)


def test_unavailable_uploader_does_not_fabricate_uri():
    result = __import__("asyncio").run(UnavailableClipUploader().upload(build_evidence_window("camera-01", START, END)))
    assert result.status == "unavailable"
    assert result.uri is None
