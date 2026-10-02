from datetime import datetime, timezone

import httpx
import pytest

from visual_event_ai.evidence_capture import (
    HttpEvidenceClipUploader,
    UnavailableClipUploader,
    build_evidence_window,
)


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


def test_http_uploader_without_endpoint_is_explicitly_unavailable():
    uploader = HttpEvidenceClipUploader(event_id="event-001")
    result = __import__("asyncio").run(uploader.upload(build_evidence_window("camera-01", START, END), b"clip"))
    assert result.status == "unavailable"
    assert result.uri is None
    __import__("asyncio").run(uploader.aclose())


def test_http_uploader_posts_multipart_clip_and_returns_real_uri():
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["body"] = request.content
        return httpx.Response(200, json={"status": "available", "uri": "http://makerverse/evidence/1"}, request=request)

    async def run():
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        uploader = HttpEvidenceClipUploader(
            "http://makerverse/api/v1/events/event-001/evidence",
            client=client,
        )
        try:
            result = await uploader.upload(build_evidence_window("camera-01", START, END), b"video-bytes")
            return result
        finally:
            await uploader.aclose()

    result = __import__("asyncio").run(run())
    assert result.status == "available"
    assert result.uri == "http://makerverse/evidence/1"
    assert seen["method"] == "POST"
    assert str(seen["url"]) == "http://makerverse/api/v1/events/event-001/evidence"
    assert b' name="clip"' in seen["body"]  # type: ignore[operator]
