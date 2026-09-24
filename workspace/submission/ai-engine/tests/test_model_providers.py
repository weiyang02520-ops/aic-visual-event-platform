from datetime import datetime, timezone

from visual_event_ai.frame_pipeline import Frame
from visual_event_ai.model_providers import DetectorProviderRegistry


def test_registry_reports_explicit_model_fallback():
    registry = DetectorProviderRegistry(requested="onnx")
    selected = registry.for_source("camera.mp4")
    assert selected.provider_id == "motion_cpu"
    statuses = {item.provider_id: item for item in registry.statuses("camera.mp4")}
    assert statuses["motion_cpu"].selected is True
    assert statuses["onnx"].available is False
    assert statuses["onnx"].reason


def test_jsonl_source_selects_fixture_provider():
    registry = DetectorProviderRegistry(requested="motion_cpu")
    assert registry.for_source("objects.jsonl").provider_id == "fixture"


def test_motion_cpu_sessions_keep_independent_history_when_sources_interleave():
    registry = DetectorProviderRegistry(requested="motion_cpu")
    session_a = registry.session_for_source("camera-a")
    session_b = registry.session_for_source("camera-b")
    assert session_a is not session_b

    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def frame(source, index, value):
        return Frame(
            source,
            index,
            timestamp,
            {"gray": [[value, value], [value, value]]},
            {"provider": "session-test"},
        )

    assert session_a.detect(frame("camera-a", 0, 0)) == []
    assert session_b.detect(frame("camera-b", 0, 0)) == []
    assert session_a.detect(frame("camera-a", 1, 50))
    assert session_b.detect(frame("camera-b", 1, 50))


def test_onnx_never_claims_available_without_verified_adapter(monkeypatch, tmp_path):
    model = tmp_path / "model.onnx"
    model.write_bytes(b"not-a-real-model")
    monkeypatch.setattr("visual_event_ai.model_providers.importlib.util.find_spec", lambda name: object())
    registry = DetectorProviderRegistry(requested="onnx")
    registry.providers["onnx"] = registry.providers["onnx"].__class__(str(model))
    assert registry.providers["onnx"].available() is False
    assert "adapter" in (registry.providers["onnx"].reason() or "")
    assert any(item.provider_id == "motion_cpu" and item.selected for item in registry.statuses())
