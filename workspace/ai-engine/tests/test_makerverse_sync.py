from __future__ import annotations

import json
import threading
import time

import httpx
from fastapi.testclient import TestClient

from visual_event_ai.app import create_app
from visual_event_ai.makerverse_client import MakerverseClient


def test_testclient_background_sync_worker_pushes_and_review_is_idempotent(
    monkeypatch, tmp_path
):
    calls: list[dict] = []
    pushed = threading.Event()

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        calls.append(payload)
        pushed.set()
        return httpx.Response(
            201,
            json={"event_id": payload.get("event_id")},
            request=request,
        )

    original_init = MakerverseClient.__init__

    def init_with_mock_transport(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(MakerverseClient, "__init__", init_with_mock_transport)
    monkeypatch.setenv("AI_DB_PATH", str(tmp_path / "sync.db"))
    monkeypatch.setenv("PLUGIN_DIR", "plugins")
    monkeypatch.setenv("MAKERVERSE_URL", "http://makerverse")
    monkeypatch.setenv("MAKERVERSE_LIVE_ID", "live-sync-test")
    monkeypatch.setenv("MAKERVERSE_RETRIES", "0")

    with TestClient(create_app()) as client:
        created = client.post(
            "/api/v1/analysis/jobs",
            json={"source": "mock://elderly-medication"},
        )
        assert created.status_code == 202

        # The request runs the synchronous BackgroundTask, which must enqueue
        # its event on SQLiteStore's worker thread rather than drop it.
        assert pushed.wait(3.0)
        assert len(calls) == 1
        event_id = calls[0]["event_id"]

        # Wait for the worker to record the successful receipt before issuing
        # review updates.  Repeated review calls must not POST the same event.
        store = client.app.state.analysis.store
        deadline = time.monotonic() + 3.0
        while event_id not in store._makerverse_synced and time.monotonic() < deadline:
            time.sleep(0.01)
        assert event_id in store._makerverse_synced

        patch_review = client.patch(
            f"/api/v1/events/{event_id}/review",
            json={"status": "confirmed", "note": "sync test"},
        )
        post_review = client.post(
            f"/api/v1/events/{event_id}/review",
            json={"status": "confirmed", "note": "sync test"},
        )
        assert patch_review.status_code == 200
        assert post_review.status_code == 200
        assert patch_review.json()["review_status"] == "confirmed"
        assert post_review.json()["review_status"] == "confirmed"
        assert len(calls) == 1

