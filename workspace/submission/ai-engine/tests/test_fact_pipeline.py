import json
from datetime import datetime, timedelta, timezone

import pytest

from visual_event_ai.fact_pipeline import FrameFactExtractor
from visual_event_ai.frame_pipeline import Frame, FramePipeline
from visual_event_ai.model_providers import DetectorProviderRegistry
from visual_event_ai.plugins import PluginManager
from visual_event_ai.providers import Detection
from visual_event_ai.relations import Zone


def test_local_jsonl_frames_become_unified_facts(tmp_path):
    fixture = tmp_path / "objects.jsonl"
    fixture.write_text(
        json.dumps({"payload": {"objects": [{"label": "药盒", "confidence": 0.9, "bbox": [1, 1, 4, 4]}]}}) + "\n",
        encoding="utf-8",
    )
    facts = FrameFactExtractor().extract(str(fixture))
    assert len(facts) == 1
    assert facts[0].fact_type == "object_detected"
    assert facts[0].metadata.get("provider") == "fixture"
    assert facts[0].metadata.get("source_id") == str(fixture)


def test_frame_fact_pipeline_redacts_pixel_metadata_before_fact_storage():
    class OneFrame:
        def iter_frames(self, source, *, interval, max_frames, token, recover):
            yield Frame(
                source,
                0,
                datetime(2026, 1, 1, tzinfo=timezone.utc),
                {},
                {"provider": "privacy-test"},
            )

    class PixelDetector:
        def detect(self, _frame):
            return [
                Detection(
                    label="person",
                    confidence=0.9,
                    bbox=(0, 0, 20, 40),
                    metadata={
                        "rawPixels": [[1, 2], [3, 4]],
                        "pose": {"keypoints": [[10, 20, 0.9]]},
                    },
                )
            ]

    class Registry:
        def session_for_source(self, _source):
            return PixelDetector()

    facts = FrameFactExtractor(
        pipeline=FramePipeline(providers={"file": OneFrame()}),
        detectors=Registry(),
    ).extract("privacy.jsonl")

    assert facts[0].metadata["rawPixels"] == {
        "encoding": "redacted-pixels",
        "shape": [2, 2],
    }
    assert facts[0].metadata["pose"]["keypoints"] == [[10, 20, 0.9]]


def test_frame_fact_pipeline_marks_degraded_quality_without_blocking_usable_channel(tmp_path):
    fixture = tmp_path / "degraded-quality.jsonl"
    fixture.write_text(
        json.dumps(
            {
                "metadata": {
                    "channel_quality": {
                        "rgb": {"available": True, "score": 0.9},
                        "thermal": {"available": True, "score": 0.2},
                    }
                },
                "payload": {
                    "objects": [{"label": "工具", "confidence": 0.9, "bbox": [1, 1, 4, 4]}]
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    facts = FrameFactExtractor().extract(str(fixture))

    detected = next(fact for fact in facts if fact.fact_type == "object_detected")
    assert detected.metadata["quality_gate"]["degraded"] is True
    assert detected.metadata["quality_gate"]["channels"][1]["usable"] is False


def test_frame_fact_pipeline_blocks_inference_when_required_channel_is_unusable(tmp_path):
    fixture = tmp_path / "blocked-quality.jsonl"
    fixture.write_text(
        json.dumps(
            {
                "metadata": {
                    "channel_quality": {
                        "rgb": {"available": True, "score": 0.9},
                        "thermal": {"available": False, "score": 0.0},
                    },
                    "quality_required_channels": ["thermal"],
                },
                "payload": {
                    "objects": [{"label": "工具", "confidence": 0.9, "bbox": [1, 1, 4, 4]}]
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    facts = FrameFactExtractor().extract(str(fixture))

    assert [fact.fact_type for fact in facts] == ["observation_gap"]
    assert facts[0].metadata["reason"] == "quality_gate"
    assert facts[0].metadata["quality_gate"]["allow_inference"] is False



def test_fractional_fixture_boxes_keep_relation_distance_and_threshold(tmp_path):
    fixture = tmp_path / "fractional_boxes.jsonl"
    fixture.write_text(
        json.dumps(
            {
                "payload": {
                    "objects": [
                        {"label": "person", "confidence": 0.9, "bbox": [0, 0, 4, 4]},
                        {"label": "medicine_box", "confidence": 0.9, "bbox": [50.8, 0, 4, 4]},
                    ]
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    facts = FrameFactExtractor().extract(str(fixture))
    distance_fact = next(fact for fact in facts if fact.fact_type == "person_object_distance")
    relation_types = {fact.fact_type for fact in facts}

    assert distance_fact.object["distance"] == 50.8
    assert "near" not in relation_types
    assert "pickup_candidate" not in relation_types


def test_frame_pipeline_preserves_track_id_across_person_label_aliases(tmp_path):
    fixture = tmp_path / "person_label_aliases.jsonl"
    records = [
        {"timestamp": "2026-01-01T00:00:00Z", "payload": {"objects": [{"label": "Person", "confidence": 0.9, "bbox": [0, 0, 20, 40]}]}},
        {"timestamp": "2026-01-01T00:00:01Z", "payload": {"objects": [{"label": "工作人员", "confidence": 0.9, "bbox": [1, 0, 20, 40]}]}},
    ]
    fixture.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

    facts = FrameFactExtractor().extract(str(fixture))
    people = [
        fact.subject
        for fact in facts
        if fact.fact_type == "object_detected"
        and fact.subject
        and fact.subject.get("label") in {"Person", "工作人员"}
    ]

    assert [person["label"] for person in people] == ["Person", "工作人员"]
    assert people[0]["track_id"] == people[1]["track_id"]


def test_frame_pipeline_does_not_infer_events_across_detection_gap(tmp_path):
    fixture = tmp_path / "detection_gap.jsonl"
    records = [
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "payload": {
                "objects": [
                    {"label": "person", "confidence": 0.9, "bbox": [0, 0, 4, 4]},
                    {"label": "medicine_box", "confidence": 0.9, "bbox": [30, 0, 4, 4]},
                ]
            },
        },
        {
            "timestamp": "2026-01-01T00:00:01Z",
            "payload": {"objects": [{"label": "person", "confidence": 0.9, "bbox": [0, 0, 4, 4]}]},
        },
        {
            "timestamp": "2026-01-01T00:00:02Z",
            "payload": {
                "objects": [
                    {"label": "person", "confidence": 0.9, "bbox": [0, 0, 4, 4]},
                    {"label": "medicine_box", "confidence": 0.9, "bbox": [60, 0, 4, 4]},
                ]
            },
        },
    ]
    fixture.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

    facts = FrameFactExtractor(zones=[Zone("shelf-a", "药品架", 0, 0, 40, 20)]).extract(str(fixture))
    fact_types = {fact.fact_type for fact in facts}

    assert "pickup_candidate" in fact_types
    assert "putdown_candidate" not in fact_types
    assert "left_zone" not in fact_types
    assert "motion" not in fact_types


def test_frame_fact_extractor_resets_temporal_state_after_recovered_jsonl_gap(tmp_path):
    fixture = tmp_path / "recovered_gap.jsonl"
    first = {
        "timestamp": "2026-01-01T00:00:00Z",
        "payload": {
                "objects": [
                    {"label": "person", "confidence": 0.9, "bbox": [0, 0, 4, 4]},
                    {"label": "tool", "confidence": 0.9, "bbox": [18, 0, 4, 4]},
            ]
        },
    }
    last = {
        "timestamp": "2026-01-01T00:00:02Z",
        "payload": {
                "objects": [
                    {"label": "person", "confidence": 0.9, "bbox": [0, 0, 4, 4]},
                    {"label": "tool", "confidence": 0.9, "bbox": [58, 0, 4, 4]},
            ]
        },
    }
    fixture.write_text(json.dumps(first) + "\nnot-json\n" + json.dumps(last) + "\n", encoding="utf-8")

    facts = FrameFactExtractor(zones=[Zone("workbench", "工作台", 0, 0, 24, 20)]).extract(str(fixture))

    assert "pickup_candidate" in {fact.fact_type for fact in facts}
    assert not {"putdown_candidate", "motion", "left_zone"} & {fact.fact_type for fact in facts}
    post_gap = [fact for fact in facts if fact.metadata.get("frame_discontinuity_before")]
    assert post_gap


def test_boolean_keypoint_fixture_cannot_create_a_suspected_medication_event(tmp_path):
    fixture = tmp_path / "boolean_keypoints.jsonl"
    record = {
        "timestamp": "2026-01-01T00:00:00Z",
        "payload": {
            "objects": [
                {
                    "label": "person",
                    "confidence": 0.95,
                    "bbox": [0, 0, 40, 100],
                    "keypoints": {
                        "nose": [20, 20, 0.95],
                        "left_wrist": [True, 25, 0.9],
                        "right_wrist": [35, 75, 0.9],
                    },
                },
                {"label": "medicine bottle", "confidence": 0.9, "bbox": [18, 20, 8, 10]},
            ]
        },
    }
    fixture.write_text(json.dumps(record) + "\n", encoding="utf-8")

    facts = FrameFactExtractor().extract(str(fixture))
    manager = PluginManager("plugins")
    manager.scan()
    events = manager.evaluate(facts, str(fixture))

    assert "pickup_candidate" in {fact.fact_type for fact in facts}
    assert "hand_to_face" not in {fact.fact_type for fact in facts}
    assert "suspected_medication" not in {event.event_type for event in events}


@pytest.mark.parametrize("object_label", ["medicine cabinet", "药品说明书"])
def test_non_medicine_fixture_label_cannot_create_medication_action_or_event(tmp_path, object_label):
    fixture = tmp_path / "non_medicine_target.jsonl"
    record = {
        "timestamp": "2026-01-01T00:00:00Z",
        "payload": {
            "objects": [
                {
                    "label": "person",
                    "confidence": 0.95,
                    "bbox": [0, 0, 40, 100],
                    "keypoints": {
                        "nose": [20, 20, 0.95],
                        "left_wrist": [20, 25, 0.9],
                        "right_wrist": [35, 75, 0.9],
                    },
                },
                {"label": object_label, "confidence": 0.9, "bbox": [18, 20, 8, 10]},
            ]
        },
    }
    fixture.write_text(json.dumps(record) + "\n", encoding="utf-8")

    facts = FrameFactExtractor().extract(str(fixture))
    manager = PluginManager("plugins")
    manager.scan()
    events = manager.evaluate(facts, str(fixture))

    assert "pickup_candidate" in {fact.fact_type for fact in facts}
    assert "hand_to_face" not in {fact.fact_type for fact in facts}
    assert events == []


def test_frame_fact_extractor_requests_job_local_motion_provider_sessions():
    class TwoGrayFrames:
        def iter_frames(self, source, *, interval, max_frames, token, recover):
            start = datetime(2026, 1, 1, tzinfo=timezone.utc)
            for index, value in enumerate((0, 50)):
                token.raise_if_cancelled()
                yield Frame(
                    source,
                    index,
                    start + interval * index,
                    {"gray": [[value, value], [value, value]]},
                    {"provider": "session-test"},
                )

    class RecordingRegistry(DetectorProviderRegistry):
        def __init__(self):
            super().__init__(requested="motion_cpu")
            self.sessions = []

        def session_for_source(self, source):
            session = super().session_for_source(source)
            self.sessions.append(session)
            return session

    registry = RecordingRegistry()
    extractor = FrameFactExtractor(
        pipeline=FramePipeline(providers={"file": TwoGrayFrames()}),
        detectors=registry,
    )

    facts_a = extractor.extract("camera-a")
    facts_b = extractor.extract("camera-b")

    assert len(registry.sessions) == 2
    assert registry.sessions[0] is not registry.sessions[1]
    assert any(fact.fact_type == "object_detected" and fact.subject["label"] == "motion_region" for fact in facts_a)
    assert any(fact.fact_type == "object_detected" and fact.subject["label"] == "motion_region" for fact in facts_b)


def test_frame_fact_extractor_starts_new_detector_session_after_discontinuity():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    class DiscontinuousPipeline:
        def iter_frames(self, source, *, max_frames, token):
            yield Frame(source, 0, start, {}, {"provider": "test"})
            yield Frame(
                source,
                1,
                start + timedelta(seconds=1),
                {},
                {"provider": "test", "discontinuity_before": True},
            )

    class EmptyDetector:
        def detect(self, _frame):
            return []

    class SessionRegistry:
        def __init__(self):
            self.session_count = 0

        def session_for_source(self, _source):
            self.session_count += 1
            return EmptyDetector()

    registry = SessionRegistry()
    facts = FrameFactExtractor(
        pipeline=DiscontinuousPipeline(),
        detectors=registry,
    ).extract("fixture://discontinuous")

    gaps = [fact for fact in facts if fact.fact_type == "observation_gap"]
    assert registry.session_count == 2
    assert len(gaps) == 1
    assert gaps[0].metadata["continuity_segment"] == 1


def test_configured_zone_transitions_reach_workshop_state_reasoner(tmp_path):
    fixture = tmp_path / "tool_zone.jsonl"
    records = [
        {"timestamp": "2026-01-01T00:00:00Z", "payload": {"objects": [{"label": "电钻", "confidence": 0.9, "bbox": [5, 5, 4, 4]}]}},
        {"timestamp": "2026-01-01T00:00:01Z", "payload": {"objects": [{"label": "电钻", "confidence": 0.9, "bbox": [25, 5, 4, 4]}]}},
        {"timestamp": "2026-01-01T00:00:02Z", "payload": {"objects": [{"label": "电钻", "confidence": 0.9, "bbox": [5, 5, 4, 4]}]}},
    ]
    fixture.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

    facts = FrameFactExtractor(zones=[Zone("shelf-a", "工具架 A", 0, 0, 20, 20)]).extract(str(fixture))
    zone_types = [fact.fact_type for fact in facts if fact.fact_type in {"left_zone", "entered_zone"}]
    assert zone_types == ["left_zone", "entered_zone"]
    assert all(fact.metadata["zone_id"] == "shelf-a" for fact in facts if fact.fact_type in {"left_zone", "entered_zone"})

    manager = PluginManager("plugins")
    manager.scan()
    events = manager.evaluate(facts, "fixture://workshop")
    assert [event.event_type for event in events] == ["object_removed", "object_returned"]
    assert events[-1].object["id"] == events[0].object["id"]


def test_jsonl_frame_extraction_fails_closed_on_timestamp_regression(tmp_path):
    fixture = tmp_path / "out_of_order.jsonl"
    records = [
        {"timestamp": "2026-01-01T00:00:02Z", "payload": {"objects": []}},
        {"timestamp": "2026-01-01T00:00:01Z", "payload": {"objects": []}},
    ]
    fixture.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="non-decreasing"):
        FrameFactExtractor().extract(str(fixture))


def test_jsonl_unrepresentable_keypoint_is_treated_as_missing_action_evidence(tmp_path):
    fixture = tmp_path / "extreme_keypoint.jsonl"
    record = {
        "timestamp": "2026-01-01T00:00:00Z",
        "payload": {
            "objects": [
                {
                    "label": "person",
                    "confidence": 0.95,
                    "bbox": [0, 0, 40, 100],
                    "keypoints": {
                        "nose": [20, 20, 0.95],
                        "left_wrist": [10 ** 1000, 25, 0.9],
                        "right_wrist": [35, 75, 0.9],
                    },
                },
                {"label": "medicine bottle", "confidence": 0.9, "bbox": [18, 20, 8, 10]},
            ]
        },
    }
    fixture.write_text(json.dumps(record) + "\n", encoding="utf-8")

    facts = FrameFactExtractor().extract(str(fixture))
    manager = PluginManager("plugins")
    manager.scan()
    events = manager.evaluate(facts, str(fixture))

    assert "pickup_candidate" in {fact.fact_type for fact in facts}
    assert "hand_to_face" not in {fact.fact_type for fact in facts}
    assert all(event.event_type != "suspected_medication" for event in events)
