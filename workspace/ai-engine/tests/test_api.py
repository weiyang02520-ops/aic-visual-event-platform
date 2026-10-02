import json

from fastapi.testclient import TestClient

import visual_event_ai.app as app_module
from visual_event_ai.app import create_app
from visual_event_ai.providers import Observation


def test_api_health_plugins_and_job(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_DB_PATH", str(tmp_path / "api.db"))
    monkeypatch.setenv("PLUGIN_DIR", "plugins")
    client = TestClient(create_app())

    assert client.get("/health").json()["status"] == "ok"
    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["ready"] is True
    assert ready.json()["database"] == "ok"
    assert ready.json()["plugin_manager"] == "ok"
    assert ready.json()["detector"] == "ok"
    assert ready.json()["tracker"] == "ok"
    plugins = client.get("/api/v1/plugins").json()
    assert {item["plugin_id"] for item in plugins} == {"elderly_care", "workshop"}

    response = client.post("/api/v1/analysis/jobs", json={"source": "mock://elderly-medication"})
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    job = client.get(f"/api/v1/analysis/jobs/{job_id}").json()
    assert job["status"] in {"queued", "running", "completed"}

    events = client.get("/api/v1/events").json()
    assert len(events) == 1
    event_id = events[0]["event_id"]
    reviewed = client.post(
        f"/api/v1/events/{event_id}/review",
        json={"status": "confirmed", "note": "API fixture"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["review_status"] == "confirmed"

    inspection = client.get(
        "/api/v1/sources/inspect",
        params={"source": "rtmp://127.0.0.1/live/demo"},
    )
    assert inspection.status_code == 200
    assert inspection.json()["provider"] == "opencv-stream-provider"
    frames = client.get(
        "/api/v1/sources/frames",
        params={"source": "mock://elderly-medication?frames=2", "max_frames": 2},
    )
    assert frames.status_code == 200
    assert [frame["frame_index"] for frame in frames.json()] == [0, 1]

    vision = client.get(
        "/api/v1/vision/preview",
        params={"source": "mock://elderly-medication?frames=2", "detector": "fixture"},
    )
    assert vision.status_code == 200
    assert vision.json() == []

    evidence = client.get(
        "/api/v1/evidence/resolve",
        params={
            "source_id": "mock://elderly-medication",
            "started_at": "2026-01-01T00:00:00Z",
            "ended_at": "2026-01-01T00:00:05Z",
        },
    )
    assert evidence.status_code == 200
    assert evidence.json()["status"] == "fixture"

    providers = client.get("/api/v1/providers/detectors").json()
    assert {item["provider_id"] for item in providers} == {"motion_cpu", "fixture", "onnx", "ultralytics"}
    assert any(item["provider_id"] == "motion_cpu" and item["selected"] for item in providers)


def test_api_frame_preview_redacts_fixture_pixel_matrices(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_DB_PATH", str(tmp_path / "redacted.db"))
    monkeypatch.setenv("PLUGIN_DIR", "plugins")
    fixture = tmp_path / "gray.jsonl"
    fixture.write_text(
        json.dumps(
            {
                "timestamp": "2026-01-01T00:00:00Z",
                "payload": {
                    "gray": [[1, 2], [3, 4]],
                    "bgr": [[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]],
                    "objects": [],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    client = TestClient(create_app())

    response = client.get(
        "/api/v1/sources/frames",
        params={"source": str(fixture), "max_frames": 1},
    )

    assert response.status_code == 200
    payload = response.json()[0]["payload"]
    assert payload["gray"] == {
        "encoding": "redacted-grayscale",
        "shape": [2, 2],
    }
    assert payload["bgr"] == {
        "encoding": "redacted-bgr",
        "shape": [2, 2, 3],
    }
    assert payload["objects"] == []


def test_api_frame_preview_redacts_nested_image_and_sensor_arrays(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_DB_PATH", str(tmp_path / "nested-redacted.db"))
    monkeypatch.setenv("PLUGIN_DIR", "plugins")
    fixture = tmp_path / "nested-frames.jsonl"
    fixture.write_text(
        json.dumps(
            {
                "timestamp": "2026-01-01T00:00:00Z",
                "payload": {
                    "observations": [
                        {
                            "Image-Data": [[1, 2], [3, 4]],
                            "depth_map": [[5, 6], [7, 8]],
                            "Thermal-Map": [[11, 12], [13, 14]],
                            "pose": {"keypoints": [[10, 20, 0.9]]},
                            "label": "person",
                        }
                    ],
                    "debug": {"rawPixels": [[9, 10]]},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    client = TestClient(create_app())

    response = client.get(
        "/api/v1/sources/frames",
        params={"source": str(fixture), "max_frames": 1},
    )

    assert response.status_code == 200
    payload = response.json()[0]["payload"]
    observation = payload["observations"][0]
    assert observation["Image-Data"] == {
        "encoding": "redacted-image",
        "shape": [2, 2],
    }
    assert observation["depth_map"] == {
        "encoding": "redacted-depth",
        "shape": [2, 2],
    }
    assert observation["Thermal-Map"] == {
        "encoding": "redacted-thermal",
        "shape": [2, 2],
    }
    assert observation["pose"]["keypoints"] == [[10, 20, 0.9]]
    assert observation["label"] == "person"
    assert payload["debug"]["rawPixels"] == {
        "encoding": "redacted-pixels",
        "shape": [1, 2],
    }


def test_api_vision_preview_redacts_detector_metadata(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_DB_PATH", str(tmp_path / "vision-redacted.db"))
    monkeypatch.setenv("PLUGIN_DIR", "plugins")
    fixture = tmp_path / "vision-redacted.jsonl"
    fixture.write_text(
        json.dumps(
            {
                "payload": {
                    "objects": [
                        {"label": "person", "confidence": 0.9, "bbox": [0, 0, 20, 40]}
                    ]
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    def fake_normalize(frame, _detections, _tracks):
        return [
            Observation(
                source_id=frame.source_id,
                timestamp=frame.timestamp,
                fact_type="object_detected",
                confidence=0.9,
                subject={"label": "person"},
                object={"bbox": [0, 0, 20, 40]},
                metadata={
                    "rawPixels": [[1, 2]],
                    "pose": {"keypoints": [[10, 20, 0.9]]},
                },
            )
        ]

    monkeypatch.setattr(app_module, "normalize_observations", fake_normalize)
    client = TestClient(create_app())

    response = client.get(
        "/api/v1/vision/preview",
        params={"source": str(fixture), "detector": "fixture", "max_frames": 1},
    )

    assert response.status_code == 200
    metadata = response.json()[0]["metadata"]
    assert metadata["rawPixels"] == {
        "encoding": "redacted-pixels",
        "shape": [1, 2],
    }
    assert metadata["pose"]["keypoints"] == [[10, 20, 0.9]]



def test_api_fails_invalid_fixture_score_without_persisting_events(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_DB_PATH", str(tmp_path / "invalid-score.db"))
    monkeypatch.setenv("PLUGIN_DIR", "plugins")
    monkeypatch.setenv("AI_ZONES_JSON", "[]")
    fixture = tmp_path / "invalid-score.jsonl"
    record = {
        "timestamp": "2026-01-01T00:00:00Z",
        "payload": {
            "objects": [
                {"label": "电钻", "confidence": 1.2, "bbox": [5, 5, 4, 4]}
            ]
        },
    }
    fixture.write_text(json.dumps(record) + "\n", encoding="utf-8")
    client = TestClient(create_app())

    created = client.post("/api/v1/analysis/jobs", json={"source": str(fixture)})
    assert created.status_code == 202
    job = client.get(f"/api/v1/analysis/jobs/{created.json()['job_id']}").json()

    assert job["status"] == "failed"
    assert "fixture object at index 0" in job["error"]
    assert "confidence" in job["error"]
    assert client.get("/api/v1/events").json() == []


def test_api_fails_malformed_fixture_detection_without_persisting_events(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_DB_PATH", str(tmp_path / "invalid-object.db"))
    monkeypatch.setenv("PLUGIN_DIR", "plugins")
    monkeypatch.setenv("AI_ZONES_JSON", "[]")
    fixture = tmp_path / "invalid-object.jsonl"
    record = {
        "timestamp": "2026-01-01T00:00:00Z",
        "payload": {"objects": [{"label": "电钻"}]},
    }
    fixture.write_text(json.dumps(record) + "\n", encoding="utf-8")
    client = TestClient(create_app())

    created = client.post("/api/v1/analysis/jobs", json={"source": str(fixture)})
    assert created.status_code == 202
    job = client.get(f"/api/v1/analysis/jobs/{created.json()['job_id']}").json()

    assert job["status"] == "failed"
    assert "fixture object at index 0" in job["error"]
    assert client.get("/api/v1/events").json() == []

def test_plugin_toggle_and_registry_crud(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_DB_PATH", str(tmp_path / "crud.db"))
    monkeypatch.setenv("PLUGIN_DIR", "plugins")
    client = TestClient(create_app())

    disabled = client.post("/api/v1/plugins/workshop/disable")
    assert disabled.status_code == 200
    assert disabled.json()["state"] == "disabled"
    enabled = client.post("/api/v1/plugins/workshop/enable")
    assert enabled.status_code == 200
    assert enabled.json()["state"] == "enabled"
    assert client.post("/api/v1/plugins/missing/enable").status_code == 404

    created_object = client.post(
        "/api/v1/objects",
        json={"name": "测试药盒", "reference_uris": ["fixture://medicine-box/front"]},
    )
    assert created_object.status_code == 201
    object_id = created_object.json()["object_id"]
    assert len(client.get("/api/v1/objects").json()) == 1
    assert client.delete(f"/api/v1/objects/{object_id}").status_code == 204

    created_person = client.post(
        "/api/v1/persons",
        json={"display_name": "测试人员", "role": "family"},
    )
    assert created_person.status_code == 201
    person_id = created_person.json()["person_id"]
    assert len(client.get("/api/v1/persons").json()) == 1
    assert client.delete(f"/api/v1/persons/{person_id}").status_code == 204


def test_registry_match_uses_registered_embeddings(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_DB_PATH", str(tmp_path / "embedding.db"))
    monkeypatch.setenv("PLUGIN_DIR", "plugins")
    client = TestClient(create_app())

    created = client.post("/api/v1/objects", json={"name": "药盒", "embedding": [1, 0]})
    assert created.status_code == 201
    response = client.post(
        "/api/v1/registry/match",
        json={"kind": "object", "embedding": [0.98, 0.02], "threshold": 0.8},
    )
    assert response.status_code == 200
    assert response.json()[0]["label"] == "药盒"
    assert response.json()[0]["accepted"] is True

    assert client.post("/api/v1/registry/match", json={"kind": "object"}).status_code == 400


def test_registry_api_rejects_boolean_and_string_feature_values(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_DB_PATH", str(tmp_path / "invalid-embedding.db"))
    monkeypatch.setenv("PLUGIN_DIR", "plugins")
    client = TestClient(create_app())

    invalid_registrations = [
        ("/api/v1/objects", {"name": "bad object", "embedding": [True, 0]}),
        ("/api/v1/objects", {"name": "bad object", "embedding": ["1", 0]}),
        ("/api/v1/persons", {"display_name": "bad person", "embedding": [False, 1]}),
        ("/api/v1/persons", {"display_name": "bad person", "embedding": ["0.8", 0.2]}),
    ]
    for path, payload in invalid_registrations:
        assert client.post(path, json=payload).status_code == 422
    assert client.post("/api/v1/objects", json={"name": "empty", "embedding": []}).status_code == 400
    assert client.post("/api/v1/persons", json={"display_name": "zero", "embedding": [0, 0]}).status_code == 400
    assert client.get("/api/v1/objects").json() == []
    assert client.get("/api/v1/persons").json() == []

    invalid_queries = [
        {"kind": "object", "embedding": [True, 0]},
        {"kind": "object", "embedding": ["1", 0]},
        {"kind": "object", "embedding": [1, 0], "threshold": True},
        {"kind": "object", "embedding": [1, 0], "threshold": "0.8"},
        {"kind": "object", "gray": [[True]]},
        {"kind": "object", "gray": [["0"]]},
    ]
    for payload in invalid_queries:
        assert client.post("/api/v1/registry/match", json=payload).status_code == 422
    assert client.post(
        "/api/v1/registry/match",
        json={"kind": "object", "embedding": [0, 0]},
    ).status_code == 400

    # Numeric pixels outside the grayscale contract reach the algorithm validator.
    assert client.post(
        "/api/v1/registry/match",
        json={"kind": "object", "gray": [[256]]},
    ).status_code == 400


def test_api_uses_environment_zone_config_for_workshop_events(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_DB_PATH", str(tmp_path / "zones.db"))
    monkeypatch.setenv("PLUGIN_DIR", "plugins")
    monkeypatch.setenv(
        "AI_ZONES_JSON",
        json.dumps(
            [{"zone_id": "shelf-a", "label": "工具架 A", "x": 0, "y": 0, "width": 20, "height": 20}],
            ensure_ascii=False,
        ),
    )
    fixture = tmp_path / "zone-transition.jsonl"
    records = [
        {"timestamp": "2026-01-01T00:00:00Z", "payload": {"objects": [{"label": "电钻", "confidence": 0.9, "bbox": [5, 5, 4, 4] }]}},
        {"timestamp": "2026-01-01T00:00:01Z", "payload": {"objects": [{"label": "电钻", "confidence": 0.9, "bbox": [25, 5, 4, 4] }]}},
        {"timestamp": "2026-01-01T00:00:02Z", "payload": {"objects": [{"label": "电钻", "confidence": 0.9, "bbox": [5, 5, 4, 4] }]}},
    ]
    fixture.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    client = TestClient(create_app())

    created = client.post("/api/v1/analysis/jobs", json={"source": str(fixture)})
    assert created.status_code == 202
    job = client.get(f"/api/v1/analysis/jobs/{created.json()['job_id']}").json()
    assert job["status"] == "completed"
    events = client.get("/api/v1/events").json()
    assert [event["event_type"] for event in events] == ["object_removed", "object_returned"]
    assert events[0]["object"]["id"] == events[1]["object"]["id"]
