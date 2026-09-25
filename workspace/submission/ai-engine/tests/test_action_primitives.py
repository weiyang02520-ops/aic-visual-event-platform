from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import pytest

from visual_event_ai.action_primitives import GenericActionPrimitiveExtractor
from visual_event_ai.fact_pipeline import FrameFactExtractor
from visual_event_ai.models import PrimitiveFact
from visual_event_ai.providers import Observation
from visual_event_ai.relations import Zone


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def person(*, source="fixture://cam-01", timestamp=BASE, wrist=(20, 25, 0.9), label="person", track=1):
    return Observation(
        source,
        timestamp,
        "object_detected",
        0.95,
        {"track_id": track, "label": label},
        {"bbox": (0, 0, 40, 100)},
        {"keypoints": {"nose": [20, 20, 0.95], "left_wrist": list(wrist), "right_wrist": [35, 75, 0.9]}},
    )


def object_observation(*, source="fixture://cam-01", timestamp=BASE, label="tool box", track=2, bbox=(18, 20, 8, 10)):
    return Observation(
        source,
        timestamp,
        "object_detected",
        0.85,
        {"track_id": track, "label": label},
        {"bbox": bbox},
        {},
    )


def test_generic_extractor_emits_hand_near_arbitrary_non_medication_object():
    facts = GenericActionPrimitiveExtractor(emit_hand_to_face=False).extract(
        [person(), object_observation()], [], frame_index=0
    )

    action = next(fact for fact in facts if fact.fact_type == "hand_near_object")
    assert action.subject == {"id": "track-1", "label": "person"}
    assert action.object == {"id": "track-2", "label": "tool box"}
    assert action.metadata["hand_keypoint"] == "left_wrist"
    assert action.metadata["source_id"] == "fixture://cam-01"
    assert action.metadata["evidence_level"] == "observation"


def test_generic_extractor_rejects_far_or_low_confidence_wrist():
    extractor = GenericActionPrimitiveExtractor(emit_hand_to_face=False)
    assert extractor.extract([person(wrist=(80, 80, 0.9)), object_observation()], [], frame_index=0) == []
    assert extractor.extract([person(wrist=(20, 25, 0.2)), object_observation()], [], frame_index=1) == []


def test_hand_near_object_does_not_require_wrist_near_face():
    facts = GenericActionPrimitiveExtractor(emit_hand_to_face=True).extract(
        [person(wrist=(70, 80, 0.9)), object_observation(bbox=(68, 78, 8, 10))],
        [],
        frame_index=0,
    )

    assert any(fact.fact_type == "hand_near_object" for fact in facts)
    assert not any(fact.fact_type == "hand_to_face" for fact in facts)


def test_generic_extractor_emits_hand_to_face_without_an_object():
    facts = GenericActionPrimitiveExtractor().extract([person()], [], frame_index=0)

    action = next(fact for fact in facts if fact.fact_type == "hand_to_face")
    assert action.object is None
    assert action.metadata["face_reference"] == "nose"
    assert action.metadata["hand_keypoint"] == "left_wrist"


def test_generic_extractor_keeps_same_label_objects_distinct_and_deterministic():
    facts = GenericActionPrimitiveExtractor(emit_hand_to_face=False).extract(
        [person(), object_observation(track=2), object_observation(track=3, bbox=(25, 20, 8, 10))],
        [],
        frame_index=0,
    )

    assert [(fact.object["id"], fact.metadata["hand_keypoint"]) for fact in facts] == [
        ("track-2", "left_wrist"),
        ("track-3", "left_wrist"),
    ]


def test_generic_extractor_rejects_cross_source_and_mixed_timestamp_inputs():
    extractor = GenericActionPrimitiveExtractor(emit_hand_to_face=False)
    with pytest.raises(ValueError, match="one source"):
        extractor.extract([person(), replace(object_observation(), source_id="fixture://cam-02")], [], frame_index=0)
    with pytest.raises(ValueError, match="one frame timestamp"):
        GenericActionPrimitiveExtractor(emit_hand_to_face=False).extract(
            [person(), replace(object_observation(), timestamp=BASE + timedelta(seconds=1))], [], frame_index=0
        )


def test_generic_extractor_does_not_reuse_old_episode_after_source_change():
    extractor = GenericActionPrimitiveExtractor()
    assert any(fact.fact_type == "hand_to_face" for fact in extractor.extract([person()], [], frame_index=5))
    other = replace(person(), source_id="fixture://cam-02")
    assert any(fact.fact_type == "hand_to_face" for fact in extractor.extract([other], [], frame_index=0))


def test_frame_fact_extractor_emits_generic_action_primitive(tmp_path):
    fixture = tmp_path / "generic-action.jsonl"
    records = [
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "payload": {
                "objects": [
                    {"label": "person", "confidence": 0.95, "bbox": [0, 0, 40, 100], "keypoints": {"nose": [20, 20, 0.95], "left_wrist": [20, 25, 0.9], "right_wrist": [35, 75, 0.9]}},
                    {"label": "tool box", "confidence": 0.85, "bbox": [18, 20, 8, 10]},
                ]
            },
        }
    ]
    fixture.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

    facts = FrameFactExtractor().extract(str(fixture))
    action = next(fact for fact in facts if fact.fact_type == "hand_near_object")
    assert action.object["label"] == "tool box"
    assert action.metadata["source_id"] == str(fixture)
    assert action.metadata["continuity_segment"] == 0
    assert all(key not in action.metadata for key in ("image", "gray", "rgb", "bgr", "pixels"))


def test_frame_fact_extractor_resets_action_episode_after_observation_gap():
    from visual_event_ai.frame_pipeline import Frame, FramePipeline
    from visual_event_ai.model_providers import DetectorProviderRegistry

    class DiscontinuousProvider:
        def iter_frames(self, source, *, interval, max_frames, token, recover):
            payload = {
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
                    {"label": "medicine bottle", "confidence": 0.85, "bbox": [18, 20, 8, 10]},
                ]
            }
            yield Frame(source, 0, BASE, payload, {"provider": "fixture"})
            yield Frame(
                source,
                1,
                BASE + timedelta(seconds=1),
                payload,
                {"provider": "fixture", "discontinuity_before": True, "discontinuity_reason": "test_gap"},
            )

    facts = FrameFactExtractor(
        pipeline=FramePipeline(providers={"file": DiscontinuousProvider()}),
        detectors=DetectorProviderRegistry(requested="fixture"),
    ).extract("gap.jsonl")

    assert sum(fact.fact_type == "observation_gap" for fact in facts) == 1
    assert sum(fact.fact_type == "hand_to_face" for fact in facts) == 2
    assert {fact.metadata["continuity_segment"] for fact in facts if fact.fact_type == "hand_to_face"} == {0, 1}
