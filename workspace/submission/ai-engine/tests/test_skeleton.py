import json
from datetime import datetime, timezone

import pytest

from visual_event_ai.fact_pipeline import FrameFactExtractor
from visual_event_ai.frame_pipeline import Frame
from visual_event_ai.privacy import sanitize_sensitive_payload
from visual_event_ai.skeleton import (
    COCO17_KEYPOINT_INDICES,
    COCO17_KEYPOINT_NAMES,
    SkeletonKeypoint,
    SkeletonObservation,
)
from visual_event_ai.ultralytics_provider import UltralyticsProvider


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_coco17_contract_has_standard_order_and_indices():
    assert COCO17_KEYPOINT_NAMES == (
        "nose",
        "left_eye",
        "right_eye",
        "left_ear",
        "right_ear",
        "left_shoulder",
        "right_shoulder",
        "left_elbow",
        "right_elbow",
        "left_wrist",
        "right_wrist",
        "left_hip",
        "right_hip",
        "left_knee",
        "right_knee",
        "left_ankle",
        "right_ankle",
    )
    assert COCO17_KEYPOINT_INDICES == {name: index for index, name in enumerate(COCO17_KEYPOINT_NAMES)}


def test_skeleton_allows_partial_points_and_preserves_provenance():
    skeleton = SkeletonObservation.from_keypoints(
        {"nose": [20, 20, 0.95], "left_wrist": [22, 25, 0.8]},
        source_id="fixture://camera-01",
        timestamp=BASE,
        track_id=4,
        continuity_segment=2,
    )

    assert set(skeleton.keypoints) == {"nose", "left_wrist"}
    assert skeleton.as_dict() == {
        "schema": "coco17",
        "version": "1.0",
        "keypoints": {"nose": [20.0, 20.0, 0.95], "left_wrist": [22.0, 25.0, 0.8]},
        "source_id": "fixture://camera-01",
        "timestamp": "2026-01-01T00:00:00+00:00",
        "track_id": 4,
        "continuity_segment": 2,
    }


@pytest.mark.parametrize(
    "value",
    [[True, 2, 0.9], [1, float("nan"), 0.9], [1, 2, 1.1], [1]],
)
def test_skeleton_keypoint_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        SkeletonKeypoint.from_value("nose", value)


def test_privacy_keeps_semantic_skeleton_but_redacts_pixels():
    sanitized = sanitize_sensitive_payload(
        {
            "skeleton": {
                "schema": "coco17",
                "version": "1.0",
                "keypoints": {"nose": [20, 20, 0.95]},
                "source_id": "fixture://camera-01",
            },
            "image": [[1, 2], [3, 4]],
            "gray": [[2, 3]],
        }
    )

    assert sanitized["skeleton"]["keypoints"]["nose"] == [20, 20, 0.95]
    assert sanitized["skeleton"]["source_id"] == "fixture://camera-01"
    assert sanitized["image"]["encoding"] == "server-side-image"
    assert sanitized["gray"]["encoding"] == "redacted-grayscale"


def test_ultralytics_default_pose_path_normalizes_all_available_coco17_points():
    points = [[float(index), float(index + 1)] for index in range(17)]

    class Boxes:
        xyxy = [[0.0, 0.0, 40.0, 100.0]]
        conf = [0.95]
        cls = [0]

    class Keypoints:
        xy = [points]
        conf = [[0.9] * 17]

    class Result:
        boxes = Boxes()
        keypoints = Keypoints()
        names = {0: "person"}

    class Model:
        def predict(self, *, source, verbose):
            return [Result()]

    detections = UltralyticsProvider(model=Model()).detect(
        Frame("fixture://pose", 0, BASE, {"image": object()})
    )

    assert set(detections[0].metadata["keypoints"]) == set(COCO17_KEYPOINT_NAMES)
    assert detections[0].metadata["keypoint_schema"] == "coco17"
    assert detections[0].metadata["keypoint_schema_version"] == "1.0"


def test_skeleton_only_fixture_reaches_action_and_fact_pipeline_without_pixels(tmp_path):
    fixture = tmp_path / "skeleton-only.jsonl"
    records = [
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "payload": {
                "objects": [
                    {
                        "label": "person",
                        "confidence": 0.95,
                        "bbox": [0, 0, 40, 100],
                        "keypoints": {
                            "nose": [20, 20, 0.95],
                            "left_wrist": [70, 80, 0.95],
                            "right_wrist": [35, 75, 0.9],
                        },
                    },
                    {"label": "medicine bottle", "confidence": 0.85, "bbox": [18, 20, 8, 10]},
                ]
            },
        },
        {
            "timestamp": "2026-01-01T00:00:01Z",
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
                    {"label": "medicine bottle", "confidence": 0.85, "bbox": [18, 20, 8, 10]},
                ]
            },
        },
    ]
    fixture.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

    facts = FrameFactExtractor().extract(str(fixture))
    person = next(fact for fact in facts if fact.fact_type == "object_detected" and fact.subject["label"] == "person")
    action = next(fact for fact in facts if fact.fact_type == "hand_to_face")

    skeleton = person.metadata["skeleton"]
    assert skeleton["schema"] == "coco17"
    assert skeleton["source_id"] == str(fixture)
    assert skeleton["track_id"] == 1
    assert skeleton["continuity_segment"] == 0
    assert person.metadata["source_id"] == str(fixture)
    assert person.timestamp.tzinfo is not None
    assert action.metadata["action_extractor"] == "keypoint-distance-v1"
    assert action.metadata["source_id"] == str(fixture)
    assert all(key not in person.metadata for key in ("image", "gray", "rgb", "bgr", "pixels"))
