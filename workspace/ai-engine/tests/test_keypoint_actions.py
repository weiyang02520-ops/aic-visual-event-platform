from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from visual_event_ai.keypoint_actions import KeypointActionExtractor
from visual_event_ai.models import PrimitiveFact
from visual_event_ai.providers import Observation


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def person_observation(*, wrist=(20, 25, 0.9), label="家属"):
    return Observation(
        source_id="fixture://cam-01",
        timestamp=BASE + timedelta(seconds=1),
        fact_type="object_detected",
        confidence=0.95,
        subject={"track_id": 1, "label": label},
        object={"bbox": (0, 0, 40, 100)},
        metadata={
            "keypoints": {
                "nose": [20, 20, 0.95],
                "left_wrist": list(wrist),
                "right_wrist": [35, 75, 0.9],
            }
        },
    )


def medication_observation(bbox=(18, 20, 8, 10)):
    return Observation(
        source_id="fixture://cam-01",
        timestamp=BASE + timedelta(seconds=1),
        fact_type="object_detected",
        confidence=0.85,
        subject={"track_id": 2, "label": "medicine bottle"},
        object={"bbox": bbox},
        metadata={"provider": "fixture"},
    )


def near_fact(label="medicine bottle"):
    return PrimitiveFact(
        fact_type="near",
        timestamp=BASE + timedelta(seconds=1),
        confidence=0.85,
        subject={"id": "track-1", "label": "家属"},
        object={"id": "track-2", "label": label},
    )


def test_keypoint_action_emits_once_for_wrist_near_face_and_same_medication_object():
    extractor = KeypointActionExtractor()
    observations = [person_observation(), medication_observation()]

    actions = extractor.extract(observations, [near_fact()])
    assert len(actions) == 1
    assert actions[0].fact_type == "hand_to_face"
    assert actions[0].subject == {"id": "track-1", "label": "家属"}
    assert actions[0].object["id"] == "track-2"
    assert actions[0].confidence == 0.85
    assert actions[0].metadata["action_extractor"] == "keypoint-distance-v1"
    assert actions[0].metadata["source_id"] == "fixture://cam-01"

    # Repeated frames in the same gesture do not emit duplicate action edges.
    assert extractor.extract(observations, [near_fact()]) == []


def test_keypoint_action_rearms_after_separation_and_rejects_non_medication_objects():
    extractor = KeypointActionExtractor()
    observations = [person_observation(), medication_observation()]
    relation = [near_fact()]
    assert len(extractor.extract(observations, relation)) == 1
    assert extractor.extract(observations, []) == []
    assert extractor.extract(observations, []) == []
    assert len(extractor.extract(observations, relation)) == 1

    tool_observations = [person_observation(), medication_observation()]
    tool_relation = [near_fact(label="tool box")]
    assert KeypointActionExtractor().extract(tool_observations, tool_relation) == []


def test_keypoint_action_resets_episode_state_when_source_changes():
    extractor = KeypointActionExtractor()
    observations = [person_observation(), medication_observation()]
    other_source = [replace(observation, source_id="fixture://cam-02") for observation in observations]

    assert len(extractor.extract(observations, [near_fact()], frame_index=10)) == 1
    assert len(extractor.extract(other_source, [near_fact()], frame_index=0)) == 1


def test_keypoint_action_rejects_mixed_sources_in_one_frame():
    observations = [person_observation(), replace(medication_observation(), source_id="fixture://cam-02")]

    with pytest.raises(ValueError, match="one source"):
        KeypointActionExtractor().extract(observations, [near_fact()])


def test_keypoint_action_rejects_relation_from_another_source():
    relation = near_fact()
    relation.metadata["source_id"] = "fixture://cam-02"

    with pytest.raises(ValueError, match="relations must come from one source"):
        KeypointActionExtractor().extract(
            [person_observation(), medication_observation()],
            [relation],
        )


def test_keypoint_action_ignores_relation_from_an_older_frame():
    stale_relation = near_fact()
    stale_relation.timestamp = BASE

    actions = KeypointActionExtractor().extract(
        [person_observation(), medication_observation()],
        [stale_relation],
    )

    assert actions == []


def test_keypoint_action_rejects_observations_from_different_frame_timestamps():
    person = person_observation()
    medication = replace(medication_observation(), timestamp=BASE + timedelta(seconds=2))

    with pytest.raises(ValueError, match="one frame timestamp"):
        KeypointActionExtractor().extract([person, medication], [near_fact()])


def test_keypoint_action_matches_equivalent_timezone_timestamps():
    offset = timezone(timedelta(hours=8))
    person = replace(person_observation(), timestamp=(BASE + timedelta(seconds=1)).astimezone(offset))
    medication = replace(medication_observation(), timestamp=(BASE + timedelta(seconds=1)).astimezone(offset))

    actions = KeypointActionExtractor().extract([person, medication], [near_fact()])

    assert len(actions) == 1


def test_keypoint_action_tolerates_one_frame_keypoint_dropout_but_rearms_after_longer_gap():
    extractor = KeypointActionExtractor()
    observations = [person_observation(), medication_observation()]
    relation = [near_fact()]
    assert len(extractor.extract(observations, relation)) == 1

    one_frame_gap = [person_observation(wrist=(38, 70, 0.9)), medication_observation()]
    assert extractor.extract(one_frame_gap, relation) == []
    assert extractor.extract(observations, relation) == []

    assert extractor.extract(one_frame_gap, relation) == []
    assert extractor.extract(one_frame_gap, relation) == []
    assert len(extractor.extract(observations, relation)) == 1


def test_keypoint_action_requires_confident_face_proximity_and_object_contact():
    low_confidence = person_observation(wrist=(20, 25, 0.2))
    assert KeypointActionExtractor().extract([low_confidence, medication_observation()], [near_fact()]) == []

    far_from_face = person_observation(wrist=(38, 70, 0.9))
    assert KeypointActionExtractor().extract([far_from_face, medication_observation()], [near_fact()]) == []

    far_from_object = person_observation(wrist=(20, 25, 0.9))
    distant_object = medication_observation(bbox=(80, 80, 8, 10))
    assert KeypointActionExtractor().extract([far_from_object, distant_object], [near_fact()]) == []


def test_keypoint_action_does_not_borrow_another_persons_medication_relation():
    relation = near_fact()
    relation.subject["id"] = "track-99"
    actions = KeypointActionExtractor().extract(
        [person_observation(), medication_observation()],
        [relation],
    )
    assert actions == []


@pytest.mark.parametrize(
    ("point_name", "point"),
    [
        ("nose", [True, 20, 0.95]),
        ("nose", [20, 20, True]),
        ("left_wrist", [True, 25, 0.9]),
        ("left_wrist", [20, 25, True]),
    ],
)
def test_keypoint_action_rejects_boolean_keypoint_components(point_name, point):
    person = person_observation()
    person.metadata["keypoints"][point_name] = point

    actions = KeypointActionExtractor().extract(
        [person, medication_observation()],
        [near_fact()],
    )

    assert actions == []


def test_keypoint_action_rejects_boolean_object_box_geometry():
    medication = medication_observation(bbox=(18, 20, 1, 10))
    medication.object["bbox"] = (18, 20, True, 10)

    assert KeypointActionExtractor().extract(
        [person_observation(), medication],
        [near_fact()],
    ) == []


def test_keypoint_action_rejects_bbox_with_overflowing_extent():
    medication = medication_observation(bbox=(1e308, 20, 1e308, 10))

    assert KeypointActionExtractor().extract(
        [person_observation(), medication],
        [near_fact()],
    ) == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_face_distance_fraction": True},
        {"max_face_distance_fraction": "0.2"},
        {"max_face_distance_fraction": float("nan")},
        {"max_face_distance_fraction": 10 ** 1000},
        {"min_keypoint_confidence": False},
        {"min_keypoint_confidence": "0.5"},
        {"min_keypoint_confidence": 10 ** 1000},
        {"max_missing_frames": True},
        {"max_missing_frames": 1.0},
    ],
)
def test_keypoint_action_rejects_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        KeypointActionExtractor(**kwargs)


def test_keypoint_action_rejects_boolean_frame_index():
    with pytest.raises(ValueError, match="frame_index"):
        KeypointActionExtractor().extract([], [], frame_index=True)


def test_keypoint_action_uses_valid_fallback_ids_when_track_ids_are_blank():
    person = person_observation()
    person.subject["track_id"] = " "
    person.subject["id"] = "track-1"
    relation = near_fact()
    relation.subject["track_id"] = " "
    relation.object["track_id"] = " "

    actions = KeypointActionExtractor().extract(
        [person, medication_observation()],
        [relation],
    )

    assert len(actions) == 1
    assert actions[0].subject["id"] == "track-1"


def test_keypoint_action_ignores_unrepresentable_integer_geometry():
    person = person_observation()
    person.metadata["keypoints"]["left_wrist"] = [10 ** 1000, 25, 0.9]
    medication = medication_observation()
    medication.object["bbox"] = (18, 20, 10 ** 1000, 10)

    assert KeypointActionExtractor().extract([person, medication], [near_fact()]) == []
