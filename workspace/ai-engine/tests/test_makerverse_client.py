import asyncio
import json
from datetime import datetime, timezone

import httpx
import pytest

from visual_event_ai.makerverse_client import MakerverseClient
from visual_event_ai.models import ReviewStatus, Severity


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
    assert isinstance(captured["metadata"], str)
    assert json.loads(captured["metadata"]) == {"facts": [], "evidence": []}


def test_makerverse_payload_matches_ai_event_json_string_fields_and_preserves_related_data():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(201, json={"event_id": captured["event_id"]}, request=request)

    started_at = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    ended_at = datetime(2026, 1, 1, 0, 0, 5, tzinfo=timezone.utc)
    client = MakerverseClient("http://makerverse", live_id="live-001", retries=0)
    asyncio.run(client.client.aclose())
    client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        asyncio.run(client.push_event({
            "event_id": "evt-2",
            "source_id": "camera-01",
            "schema_version": "1.0",
            "plugin_id": "elderly_care",
            "plugin_version": "0.1.0",
            "event_type": "suspected_medication",
            "title": "疑似服药",
            "description": "待人工复核",
            "started_at": started_at,
            "ended_at": ended_at,
            "created_at": ended_at,
            "confidence": 0.8,
            "severity": Severity.MEDIUM,
            "review_status": ReviewStatus.PENDING,
            "subject": {"id": "person-1", "label": "老人"},
            "object": {"id": "medicine-1", "label": "药盒"},
            "location": None,
            "metadata": {"source_id": "camera-01", "continuity_segment": 2},
            "facts": [{
                "fact_type": "hand_to_face",
                "timestamp": started_at,
                "confidence": 0.9,
                "subject": {"id": "person-1"},
                "metadata": {"source_id": "camera-01"},
            }],
            "evidence": [{
                "source_id": "camera-01",
                "started_at": started_at,
                "ended_at": ended_at,
                "status": "designed",
            }],
        }))
    finally:
        asyncio.run(client.client.aclose())

    # These are the writable fields on LiveService.Models.AiEvent.  Unified
    # source/schema fields remain local-only, while JSON-valued fields are
    # strings containing valid JSON documents for C# model binding.
    assert set(captured).issubset({
        "event_id", "live_id", "plugin_id", "plugin_version", "event_type",
        "title", "description", "started_at", "ended_at", "confidence",
        "severity", "location", "subject", "object", "review_status",
        "metadata", "created_at",
    })
    assert captured["live_id"] == "live-001"
    assert captured["started_at"] == started_at.isoformat()
    assert captured["ended_at"] == ended_at.isoformat()
    assert captured["severity"] == Severity.MEDIUM.value
    assert captured["review_status"] == ReviewStatus.PENDING.value
    assert json.loads(captured["subject"]) == {"id": "person-1", "label": "老人"}
    assert json.loads(captured["object"]) == {"id": "medicine-1", "label": "药盒"}

    metadata = json.loads(captured["metadata"])
    assert metadata["source_id"] == "camera-01"
    assert metadata["continuity_segment"] == 2
    assert metadata["facts"][0]["timestamp"] == started_at.isoformat()
    assert metadata["evidence"][0]["ended_at"] == ended_at.isoformat()


def test_makerverse_client_requires_live_id():
    client = MakerverseClient("http://makerverse", retries=0)
    try:
        with pytest.raises(ValueError, match="MAKERVERSE_LIVE_ID"):
            asyncio.run(client.push_event({"event_id": "evt-1"}))
    finally:
        asyncio.run(client.client.aclose())
