from datetime import datetime, timedelta, timezone
import json

import pytest

from visual_event_ai.fact_pipeline import FrameFactExtractor
from visual_event_ai.frame_pipeline import Frame, FramePipeline
from visual_event_ai.medication_plan import MedicationPlan, MedicationPlanEntry, MedicationPlanEvaluator
from visual_event_ai.model_providers import DetectorProviderRegistry
from visual_event_ai.models import PrimitiveFact
from visual_event_ai.temporal_memory import TemporalVisualMemory
from visual_event_ai.ultralytics_provider import (
    CombinedUltralyticsProvider,
    UltralyticsObjectProvider,
    UltralyticsProvider,
)


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


class _Boxes:
    xyxy = [[0.0, 0.0, 40.0, 100.0], [18.0, 20.0, 26.0, 30.0], [60.0, 20.0, 90.0, 50.0]]
    conf = [0.95, 0.85, 0.8]
    cls = [0, 2, 3]


class _Keypoints:
    xy = [[[20.0, 20.0] for _ in range(17)]]
    conf = [[0.9 for _ in range(17)]]


class _Result:
    boxes = _Boxes()
    keypoints = _Keypoints()
    names = {0: "person", 2: "medicine bottle", 3: "tool box"}


class _Model:
    def predict(self, *, source, verbose):
        return [_Result()]


def _fact(kind, seconds=0, *, source="camera-a", segment=0, object=None, subject=None, confidence=0.9):
    return PrimitiveFact(
        fact_type=kind,
        timestamp=BASE + timedelta(seconds=seconds),
        confidence=confidence,
        subject=subject or {"id": "p1", "label": "老人"},
        object=object,
        metadata={"source_id": source, "continuity_segment": segment},
    )


def test_combined_ultralytics_provider_keeps_pose_and_arbitrary_semantic_objects():
    provider = CombinedUltralyticsProvider(UltralyticsProvider(model=_Model()), UltralyticsObjectProvider(model=_Model()))

    detections = provider.detect(Frame("camera-a", 0, BASE, {"image": object()}))

    assert [item.label for item in detections] == ["person", "medicine bottle", "tool box"]
    assert detections[1].metadata["component"] == "semantic_object"
    assert "keypoints" not in detections[1].metadata


def test_combined_provider_does_not_require_optional_object_model_for_pose():
    provider = CombinedUltralyticsProvider(UltralyticsProvider(model=_Model()), UltralyticsObjectProvider())

    assert provider.available() is True
    assert len(provider.detect(Frame("camera-a", 0, BASE, {"image": object()}))) == 1
    assert provider.component_status()["semantic_object"]["available"] is False


def test_registry_reports_separate_pose_and_object_configuration(monkeypatch, tmp_path):
    pose = tmp_path / "pose.pt"
    objects = tmp_path / "objects.pt"
    pose.write_bytes(b"pose")
    objects.write_bytes(b"objects")
    monkeypatch.setenv("AI_DETECTOR_PROVIDER", "ultralytics")
    monkeypatch.setenv("AI_ULTRALYTICS_POSE_MODEL_PATH", str(pose))
    monkeypatch.setenv("AI_ULTRALYTICS_OBJECT_MODEL_PATH", str(objects))
    monkeypatch.setattr("visual_event_ai.ultralytics_provider.importlib.util.find_spec", lambda name: object())

    registry = DetectorProviderRegistry()
    status = next(item for item in registry.statuses("camera.mp4") if item.provider_id == "ultralytics")

    assert status.available is True
    assert status.pose_available is True
    assert status.object_available is True
    assert status.model_path == str(pose)
    assert status.object_model_path == str(objects)


def test_combined_provider_reaches_normal_pipeline_with_object_fact():
    provider = CombinedUltralyticsProvider(UltralyticsProvider(model=_Model()), UltralyticsObjectProvider(model=_Model()))

    class OneFrame:
        def iter_frames(self, source, *, interval, max_frames, token, recover):
            yield Frame(source, 0, BASE, {"image": object()}, {"provider": "combined-test"})

    class Registry:
        def session_for_source(self, _source):
            return provider

    facts = FrameFactExtractor(pipeline=FramePipeline(providers={"mock": OneFrame()}), detectors=Registry()).extract("mock://camera")

    objects = [fact for fact in facts if fact.fact_type == "object_detected"]
    assert {fact.subject["label"] for fact in objects} == {"person", "medicine bottle", "tool box"}
    assert all(fact.subject["label"] != "person" or "skeleton" in fact.metadata for fact in objects)


def test_object_provider_fails_closed_on_bad_box():
    class BadBoxes:
        xyxy = [[0.0, 0.0, float("nan"), 2.0]]
        conf = [0.9]
        cls = [2]

    class BadResult:
        boxes = BadBoxes()
        names = {2: "tool"}

    class BadModel:
        def predict(self, *, source, verbose):
            return [BadResult()]

    with pytest.raises(ValueError, match="bbox x2"):
        UltralyticsObjectProvider(model=BadModel()).detect(Frame("camera-a", 0, BASE, {"image": object()}))


def test_temporal_memory_preserves_source_segment_identity_and_visual_location():
    memory = TemporalVisualMemory(max_records=20)
    object_value = {"id": "tool-1", "label": "tool box", "bbox": [1, 2, 5, 6]}
    memory.ingest(
        [
            _fact("object_detected", object=object_value, subject={"id": "tool-1", "label": "tool box"}),
            _fact("object_in_zone", seconds=1, object={"id": "tool-1", "label": "区域 A", "zone_id": "a"}, subject={"id": "tool-1", "label": "tool box"}),
            _fact("hand_near_object", seconds=2, object=object_value),
            _fact("observation_gap", seconds=3, segment=1),
            _fact("hand_near_object", seconds=4, segment=1, object=object_value),
            _fact("hand_near_object", seconds=5, source="camera-b", object=object_value),
        ]
    )

    assert len(memory.recent_actions()) == 4
    assert {item.continuity_segment for item in memory.query(object_id="tool-1")} == {0, 1}
    assert len(memory.query(source_id="camera-b")) == 1
    assert memory.last_seen_object_candidates("tool box", source_id="camera-a")[0].source_id == "camera-a"


def test_temporal_memory_is_bounded_and_rejects_boolean_limits():
    with pytest.raises(ValueError):
        TemporalVisualMemory(max_records=True)
    memory = TemporalVisualMemory(max_records=2, max_records_per_identity=1)
    memory.ingest([_fact("hand_to_face", seconds=i, object={"id": "m", "label": "药盒"}) for i in range(4)])
    assert len(memory.records()) == 1


def test_temporal_memory_redacts_raw_pixels():
    memory = TemporalVisualMemory()
    record = memory.update(_fact("hand_to_face", object={"id": "m", "label": "药盒"}, subject={"id": "p", "label": "老人"}))
    assert record is not None
    assert "rawPixels" not in record.metadata


def test_frame_fact_extractor_can_ingest_directly_into_temporal_memory(tmp_path):
    fixture = tmp_path / "temporal.jsonl"
    fixture.write_text(
        json.dumps(
            {
                "timestamp": "2026-01-01T00:00:00Z",
                "payload": {"objects": [{"label": "tool box", "confidence": 0.9, "bbox": [2, 2, 5, 5]}]},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    memory = TemporalVisualMemory()
    facts = FrameFactExtractor(temporal_memory=memory).extract(str(fixture))

    assert facts
    assert memory.visual_memory.last_seen_candidates("tool box", source_id=str(fixture))


def _plan(label="药盒", scheduled=BASE, early=60, late=60):
    return MedicationPlan(entries=[MedicationPlanEntry(entry_id="morning", medicine_label=label, scheduled_at=scheduled, early_tolerance_seconds=early, late_tolerance_seconds=late, note="configured", dose="1")])


def _action(seconds=0, label="药盒", object_id="m1", source="camera-a", segment=0):
    return _fact("hand_to_face", seconds, source=source, segment=segment, object={"id": object_id, "label": label})


@pytest.mark.parametrize(
    ("offset", "expected"),
    [(-120, "early_candidate"), (0, "plan_match_candidate"), (120, "late_candidate")],
)
def test_medication_plan_time_window_cues(offset, expected):
    evaluator = MedicationPlanEvaluator(_plan())
    reviews = evaluator.evaluate([_action(seconds=offset)])
    assert reviews[0].cue == expected
    assert reviews[0].metadata["plan_note"] == "configured"
    assert reviews[0].metadata["plan_dose"] == "1"


def test_medication_plan_wrong_item_and_insufficient_evidence():
    evaluator = MedicationPlanEvaluator(_plan())
    assert evaluator.evaluate([_action(label="tool box")])[0].cue == "wrong_item_candidate"
    assert evaluator.evaluate([])[0].cue == "unresolved_candidate"


def test_medication_plan_keeps_parallel_same_label_objects_and_source_gap_separate():
    evaluator = MedicationPlanEvaluator(_plan())
    reviews = evaluator.evaluate([
        _action(seconds=0, object_id="m1"),
        _action(seconds=0, object_id="m2"),
        _action(seconds=1, object_id="m1", source="camera-b"),
    ])
    assert reviews[0].cue == "unresolved_candidate"
    assert len(reviews) >= 2


def test_medication_plan_does_not_pair_cross_source_or_post_gap_context():
    evaluator = MedicationPlanEvaluator(_plan())
    facts = [
        _fact("pickup_candidate", 0, source="camera-a", segment=0, object={"id": "m1", "label": "药盒"}),
        _action(seconds=1, source="camera-b", segment=0),
    ]
    assert evaluator.evaluate(facts)[0].cue == "unresolved_candidate"
    facts = [
        _fact("pickup_candidate", 0, source="camera-a", segment=0, object={"id": "m1", "label": "药盒"}),
        _action(seconds=1, source="camera-a", segment=1),
    ]
    assert evaluator.evaluate(facts)[0].cue == "unresolved_candidate"


def test_medication_plan_rejects_boolean_tolerance_and_naive_schedule():
    with pytest.raises(ValueError):
        MedicationPlanEntry(entry_id="a", medicine_label="药盒", scheduled_at=BASE, early_tolerance_seconds=True)
    with pytest.raises(ValueError):
        MedicationPlanEntry(entry_id="a", medicine_label="药盒", scheduled_at="2026-01-01T08:00:00")
