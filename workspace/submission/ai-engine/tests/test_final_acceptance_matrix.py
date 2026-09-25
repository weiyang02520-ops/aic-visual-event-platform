"""Final deterministic AI acceptance matrix for the frontend handoff."""

import json
from datetime import datetime, timedelta, timezone

from visual_event_ai.action_primitives import GenericActionPrimitiveExtractor
from visual_event_ai.algorithm_reasoner import MedicationSequenceReasoner, WorkshopStateReasoner
from visual_event_ai.fact_pipeline import FrameFactExtractor
from visual_event_ai.frame_pipeline import Frame, FramePipeline
from visual_event_ai.medication_plan import MedicationPlan, MedicationPlanEntry, MedicationPlanEvaluator
from visual_event_ai.models import PrimitiveFact
from visual_event_ai.privacy import sanitize_sensitive_payload
from visual_event_ai.providers import Observation
from visual_event_ai.relations import Zone
from visual_event_ai.skeleton import SkeletonObservation
from visual_event_ai.temporal_memory import TemporalVisualMemory
from visual_event_ai.ultralytics_provider import CombinedUltralyticsProvider, UltralyticsObjectProvider, UltralyticsProvider
from visual_event_ai.visual_memory import VisualMemory


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


class _Boxes:
    xyxy = [[0.0, 0.0, 40.0, 100.0], [18.0, 20.0, 26.0, 30.0]]
    conf = [0.95, 0.85]
    cls = [0, 2]


class _Keypoints:
    xy = [[[20.0, 20.0] for _ in range(17)]]
    conf = [[0.9 for _ in range(17)]]


class _Result:
    boxes = _Boxes()
    keypoints = _Keypoints()
    names = {0: "person", 2: "medicine bottle"}


class _Model:
    def predict(self, *, source, verbose):
        return [_Result()]


def _fact(kind, seconds=0, *, source="camera-a", segment=0, subject=None, object=None, location=None, metadata=None):
    return PrimitiveFact(
        fact_type=kind,
        timestamp=BASE + timedelta(seconds=seconds),
        subject=subject,
        object=object,
        location=location,
        confidence=0.9,
        metadata={"source_id": source, "continuity_segment": segment, **(metadata or {})},
    )


def _fixture_frame_provider(records):
    class Provider:
        def iter_frames(self, source, *, interval, max_frames, token, recover):
            for index, record in enumerate(records):
                yield Frame(
                    source,
                    index,
                    datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00")),
                    record["payload"],
                    record.get("metadata", {}),
                )

    return Provider()


def test_matrix_pose_provider_to_canonical_person_fact():
    class Registry:
        def session_for_source(self, source):
            return UltralyticsProvider(model=_Model())

    class OneFrame:
        def iter_frames(self, source, *, interval, max_frames, token, recover):
            yield Frame(source, 0, BASE, {"image": object()}, {"provider": "matrix"})

    facts = FrameFactExtractor(pipeline=FramePipeline(providers={"mock": OneFrame()}), detectors=Registry()).extract("mock://pose")
    person = next(fact for fact in facts if fact.fact_type == "object_detected" and fact.subject["label"] == "person")
    assert person.metadata["keypoint_schema"] == "coco17"
    assert person.metadata["skeleton"]["schema"] == "coco17"


def test_matrix_semantic_object_reaches_tracker_and_object_fact():
    provider = UltralyticsObjectProvider(model=_Model())

    class OneFrame:
        def iter_frames(self, source, *, interval, max_frames, token, recover):
            yield Frame(source, 0, BASE, {"image": object()}, {"provider": "matrix"})

    class Registry:
        def session_for_source(self, source):
            return provider

    facts = FrameFactExtractor(pipeline=FramePipeline(providers={"mock": OneFrame()}), detectors=Registry()).extract("mock://object")
    item = next(fact for fact in facts if fact.fact_type == "object_detected")
    assert item.subject["label"] == "medicine bottle"
    assert item.subject["track_id"] == 1


def test_matrix_combined_person_and_object_are_one_frame_stream():
    provider = CombinedUltralyticsProvider(UltralyticsProvider(model=_Model()), UltralyticsObjectProvider(model=_Model()))
    detections = provider.detect(Frame("camera-a", 0, BASE, {"image": object()}))
    assert [item.label for item in detections] == ["person", "medicine bottle"]


def test_matrix_hand_near_object_is_independent_from_hand_to_face():
    person = Observation("camera-a", BASE, "object_detected", 0.9, {"track_id": 1, "label": "person"}, {"bbox": [0, 0, 40, 100]}, {"keypoints": {"nose": [20, 20, 0.9], "left_wrist": [70, 80, 0.9]}})
    tool = Observation("camera-a", BASE, "object_detected", 0.9, {"track_id": 2, "label": "tool box"}, {"bbox": [68, 78, 8, 10]}, {})
    facts = GenericActionPrimitiveExtractor().extract([person, tool], [], frame_index=0)
    assert any(fact.fact_type == "hand_near_object" for fact in facts)
    assert not any(fact.fact_type == "hand_to_face" for fact in facts)


def test_matrix_skeleton_upper_path_has_no_raw_pixels():
    payload = sanitize_sensitive_payload({"image": [[1, 2]], "gray": [[3, 4]], "keypoints": {"nose": [1, 2, 0.9]}})
    skeleton = SkeletonObservation.from_keypoints({"nose": [1, 2, 0.9]}, source_id="camera-a", timestamp=BASE, track_id=1, strict=True)
    assert payload["image"]["encoding"] == "server-side-image"
    assert "gray" in payload and skeleton is not None
    assert "pixels" not in skeleton.as_dict()


def test_matrix_object_zone_updates_last_known_visual_memory():
    memory = VisualMemory()
    memory.ingest([
        _fact("object_detected", subject={"id": "track-1", "label": "tool box"}, object={"bbox": [1, 1, 5, 5]}),
        _fact("object_in_zone", seconds=1, subject={"id": "track-1", "label": "tool box"}, object={"zone_id": "b", "label": "Zone B"}, location="Zone B"),
    ])
    record = memory.get("camera-a", 0, 1)
    assert record is not None and record.current_zone_id == "b"


def test_matrix_temporal_memory_queries_source_continuity_identity():
    memory = TemporalVisualMemory()
    memory.ingest([_fact("hand_near_object", subject={"id": "p1", "label": "person"}, object={"id": "m1", "label": "medicine bottle"})])
    recent = memory.recent_actions()
    assert len(recent) == 1 and recent[0].source_id == "camera-a" and recent[0].continuity_segment == 0


def test_matrix_observation_gap_separates_temporal_identity_history():
    memory = TemporalVisualMemory()
    memory.ingest([
        _fact("hand_to_face", subject={"id": "p1", "label": "person"}, object={"id": "m1", "label": "药盒"}),
        _fact("observation_gap", seconds=1, segment=1),
        _fact("hand_to_face", seconds=2, segment=1, subject={"id": "p1", "label": "person"}, object={"id": "m1", "label": "药盒"}),
    ])
    assert {record.continuity_segment for record in memory.timeline(subject_id="p1", object_id="m1")} == {0, 1}


def test_matrix_same_label_parallel_objects_remain_distinct():
    memory = VisualMemory()
    memory.ingest([
        _fact("object_detected", subject={"id": "track-1", "label": "box"}, object={"bbox": [1, 1, 5, 5]}),
        _fact("object_detected", subject={"id": "track-2", "label": "box"}, object={"bbox": [2, 2, 5, 5]}),
    ])
    assert {item.track_id for item in memory.last_seen_candidates("box")} == {"track-1", "track-2"}


def test_matrix_medication_sequence_is_review_only():
    facts = [
        _fact("pickup_candidate", subject={"id": "p1", "label": "person"}, object={"id": "m1", "label": "药盒"}),
        _fact("hand_to_face", seconds=2, subject={"id": "p1", "label": "person"}, object={"id": "m1", "label": "药盒"}),
    ]
    event = MedicationSequenceReasoner().infer(facts)[0]
    assert event.event_type == "suspected_medication"
    assert event.metadata["medical_diagnosis"] is False


def test_matrix_medication_plan_emits_candidate_cue_only():
    plan = MedicationPlan(entries=[MedicationPlanEntry(entry_id="morning", medicine_label="药盒", scheduled_at=BASE, early_tolerance_seconds=10, late_tolerance_seconds=10)])
    review = MedicationPlanEvaluator(plan).evaluate([_fact("hand_to_face", object={"id": "m1", "label": "药盒"})])[0]
    assert review.cue == "plan_match_candidate"
    assert review.metadata["medical_diagnosis"] is False


def test_matrix_cross_source_and_post_gap_medication_evidence_fails_closed():
    plan = MedicationPlan(entries=[MedicationPlanEntry(entry_id="morning", medicine_label="药盒", scheduled_at=BASE, early_tolerance_seconds=10, late_tolerance_seconds=10)])
    facts = [
        _fact("pickup_candidate", object={"id": "m1", "label": "药盒"}, source="camera-a", segment=0),
        _fact("hand_to_face", seconds=1, object={"id": "m1", "label": "药盒"}, source="camera-b", segment=0),
    ]
    assert MedicationPlanEvaluator(plan).evaluate(facts)[0].cue == "unresolved_candidate"


def test_matrix_privacy_sanitizer_blocks_pixel_metadata_from_fact_boundary():
    facts = FrameFactExtractor(pipeline=FramePipeline(providers={"mock": _fixture_frame_provider([
        {"timestamp": "2026-01-01T00:00:00Z", "payload": {"objects": [{"label": "box", "bbox": [1, 1, 2, 2]}], "image": [[1]]}},
    ])})).extract("mock://privacy")
    assert all("image" not in fact.metadata for fact in facts)


def test_matrix_unavailable_object_model_does_not_disable_pose():
    provider = CombinedUltralyticsProvider(UltralyticsProvider(model=_Model()), UltralyticsObjectProvider())
    assert provider.available() is True
    assert provider.component_status()["semantic_object"]["available"] is False
    assert len(provider.detect(Frame("camera-a", 0, BASE, {"image": object()}))) == 1


def test_matrix_quality_hard_failure_creates_observation_gap(tmp_path):
    fixture = tmp_path / "quality.jsonl"
    fixture.write_text(
        json.dumps({"timestamp": "2026-01-01T00:00:00Z", "metadata": {"channel_quality": {"rgb": {"available": False, "score": 0.0}} , "quality_required_channels": ["rgb"]}, "payload": {"objects": [{"label": "box", "bbox": [1, 1, 2, 2]}]}}) + "\n",
        encoding="utf-8",
    )
    facts = FrameFactExtractor().extract(str(fixture))
    assert any(fact.fact_type == "observation_gap" for fact in facts)


def test_matrix_workshop_reasoner_stays_conservative():
    facts = [
        _fact("object_removed", subject={"id": "track-1", "label": "tool box"}, object={"id": "tool-1", "label": "tool box"}),
        _fact("entered_zone", seconds=1, subject={"id": "track-1", "label": "tool box"}, object={"id": "tool-1", "label": "tool box"}, metadata={"zone_id": "other"}),
    ]
    assert not any(event.event_type == "object_returned" for event in WorkshopStateReasoner().infer(facts))
