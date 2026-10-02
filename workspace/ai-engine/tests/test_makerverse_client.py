import asyncio
import json

import httpx
import pytest

from visual_event_ai.makerverse_client import MakerverseClient


def test_makerverse_payload_uses_configured_live_id_and_whitelists_fields():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(201, json={"event_id": captured["event_id"]}, request=request)

    client = MakerverseClient("http://makerverse", live_id="live-001", retries=0)
    asyncio.run(client.client.aclose())
    client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = asyncio.run(client.push_event({
            "event_id": "evt-1",
            "source_id": "camera-01",
            "schema_version": "1.0",
            "live_id": None,
            "plugin_id": "elderly_care",
            "plugin_version": "0.1.0",
            "event_type": "suspected_medication",
            "title": "疑似服药",
            "started_at": "2026-01-01T00:00:00Z",
            "ended_at": "2026-01-01T00:00:05Z",
            "review_status": "pending",
            "facts": [],
            "evidence": [],
        }))
    finally:
        asyncio.run(client.client.aclose())
    assert result["event_id"] == "evt-1"
    assert captured["live_id"] == "live-001"
    assert "source_id" not in captured
    assert "schema_version" not in captured
    assert "facts" not in captured
    assert "evidence" not in captured


def test_makerverse_client_requires_live_id():
    client = MakerverseClient("http://makerverse", retries=0)
    try:
        with pytest.raises(ValueError, match="MAKERVERSE_LIVE_ID"):
            asyncio.run(client.push_event({"event_id": "evt-1"}))
    finally:
        asyncio.run(client.client.aclose())
