from datetime import datetime, timezone

import pytest

from visual_event_ai.frame_pipeline import Frame
from visual_event_ai.providers import CentroidTracker, Detection, FixtureDetector, MotionDetector, normalize_observations


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _frame(index, payload):
    return Frame("fixture://cam-01", index, BASE, payload)


class _ArrayLikeImage:
    def __init__(self, rows):
        self.rows = rows
        self.shape = (len(rows), len(rows[0]) if rows else 0)

    def __getitem__(self, slices):
        rows, columns = slices
        return _ArrayLikeImage([row[columns] for row in self.rows[rows]])

    def tolist(self):
        return self.rows


def test_motion_detector_finds_connected_cpu_region():
    detector = MotionDetector(threshold=10, min_area=2)
    detector.detect(_frame(0, {"gray": [[0] * 6 for _ in range(5)]}))
    detections = detector.detect(_frame(1, {"gray": [[0, 0, 0, 0, 0, 0], [0, 0, 50, 50, 0, 0], [0, 0, 50, 50, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]}))
    assert len(detections) == 1
    assert detections[0].bbox == (2, 1, 2, 2)
    assert detections[0].metadata["algorithm"] == "frame-difference"
    assert detections[0].metadata["score_kind"] == "heuristic_area"


def test_motion_detector_resets_for_new_source_and_new_analysis_job():
    detector = MotionDetector(threshold=10, min_area=1)
    dark = {"gray": [[0, 0], [0, 0]]}
    bright = {"gray": [[50, 50], [50, 50]]}
    assert detector.detect(Frame("cam-a", 0, BASE, dark)) == []
    assert detector.detect(Frame("cam-a", 1, BASE, bright))

    # A new source must not be compared with the previous camera's last frame.
    assert detector.detect(Frame("cam-b", 0, BASE, dark)) == []
    # Reusing frame index zero starts a fresh job even for the same source ID.
    assert detector.detect(Frame("cam-b", 0, BASE, bright)) == []


def test_motion_detector_rejects_ragged_or_non_finite_matrices_and_resets_history():
    detector = MotionDetector(threshold=10, min_area=1)
    assert detector.detect(_frame(0, {"gray": [[0, 0], [0, 0]]})) == []
    assert detector.detect(_frame(1, {"gray": [[0, 0], [0]]})) == []
    assert detector.detect(_frame(2, {"gray": [[50, 50], [50, 50]]})) == []
    assert detector.detect(_frame(3, {"gray": [[0, 0], [float("nan"), 0]]})) == []
    assert detector.detect(_frame(4, {"gray": [[100, 100], [100, 100]]})) == []


@pytest.mark.parametrize("invalid_pixel", [True, False, -0.01, 255.01, float("inf"), float("nan"), "10"])
def test_motion_detector_rejects_invalid_pixel_values_and_resets_history(invalid_pixel):
    detector = MotionDetector(threshold=1, min_area=1)
    assert detector.detect(_frame(0, {"gray": [[0]]})) == []
    assert detector.detect(_frame(1, {"gray": [[invalid_pixel]]})) == []
    # An invalid sample resets history instead of participating in frame difference.
    assert detector.detect(_frame(2, {"gray": [[1]]})) == []
    assert detector.detect(_frame(3, {"gray": [[0]]}))


def test_motion_detector_preserves_fractional_grayscale_thresholds():
    below = MotionDetector(threshold=20, min_area=1)
    assert below.detect(_frame(0, {"gray": [[100.9]]})) == []
    assert below.detect(_frame(1, {"gray": [[120.0]]})) == []

    at_threshold = MotionDetector(threshold=20, min_area=1)
    assert at_threshold.detect(_frame(0, {"gray": [[100.9]]})) == []
    assert at_threshold.detect(_frame(1, {"gray": [[120.9]]}))


def test_motion_detector_maps_sampled_image_boxes_back_to_source_pixels():
    detector = MotionDetector(threshold=20, min_area=2)
    dark = _ArrayLikeImage([[0] * 320 for _ in range(320)])
    changed = [[0] * 320 for _ in range(320)]
    for y in range(20, 24):
        for x in range(30, 34):
            changed[y][x] = 50
    bright_patch = _ArrayLikeImage(changed)

    assert detector.detect(Frame("image-cam", 0, BASE, {"image": dark})) == []
    detection = detector.detect(Frame("image-cam", 1, BASE, {"image": bright_patch}))[0]

    assert detection.bbox == (30.0, 20.0, 4.0, 4.0)
    assert detection.metadata["sample_stride"] == [2, 2]


def test_motion_detector_resets_history_when_image_geometry_changes_but_sample_shape_does_not():
    detector = MotionDetector(threshold=20, min_area=1)
    first = _ArrayLikeImage([[0] * 320 for _ in range(320)])
    # Both images sample to 160x160, but the second uses a larger source pixel stride.
    second = _ArrayLikeImage([[50] * 480 for _ in range(480)])

    assert detector.detect(Frame("image-cam", 0, BASE, {"image": first})) == []
    assert detector.detect(Frame("image-cam", 1, BASE, {"image": second})) == []


@pytest.mark.parametrize("kwargs", [{"threshold": 0}, {"threshold": 256}, {"min_area": 0}, {"threshold": True}, {"threshold": "20"}, {"min_area": True}, {"min_area": 1.5}])
def test_motion_detector_rejects_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        MotionDetector(**kwargs)


def test_tracker_keeps_id_and_normalizes_fact():
    tracker = CentroidTracker(max_distance=10)
    first = Detection("person", 0.9, (10, 10, 4, 4))
    second = Detection("person", 0.8, (12, 10, 4, 4))
    tracks_a = tracker.update([first])
    tracks_b = tracker.update([second])
    assert tracks_a[0].track_id == tracks_b[0].track_id
    frame = _frame(4, {"objects": []})
    observations = normalize_observations(frame, [second], tracks_b)
    assert observations[0].source_id == "fixture://cam-01"
    assert observations[0].subject["track_id"] == tracks_b[0].track_id



def test_tracker_preserves_person_id_across_shared_label_aliases():
    tracker = CentroidTracker(max_distance=10, max_missed=0)
    first = tracker.update([Detection("Person", 0.9, (0, 0, 4, 4))])
    second = tracker.update([Detection("person", 0.9, (1, 0, 4, 4))])
    third = tracker.update([Detection("工作人员", 0.9, (2, 0, 4, 4))])

    assert first[0].track_id == second[0].track_id == third[0].track_id


def test_tracker_matches_non_person_labels_case_insensitively_but_keeps_classes_separate():
    tracker = CentroidTracker(max_distance=10, max_missed=0)
    medicine = tracker.update([Detection("Medicine Bottle", 0.9, (0, 0, 4, 4))])
    same_class = tracker.update([Detection("medicine bottle", 0.9, (1, 0, 4, 4))])
    person = tracker.update([Detection("Person", 0.9, (2, 0, 4, 4))])

    assert medicine[0].track_id == same_class[0].track_id
    assert person[0].track_id != same_class[0].track_id

def test_tracker_minimizes_total_distance_instead_of_committing_to_greedy_edge():
    tracker = CentroidTracker(max_distance=20, max_missed=0)
    first = tracker.update([
        Detection("person", 0.9, (-1, 0, 2, 2)),
        Detection("person", 0.9, (9, 0, 2, 2)),
    ])
    assert [track.track_id for track in first] == [1, 2]

    updated = tracker.update([
        Detection("person", 0.9, (5, 0, 2, 2)),
        Detection("person", 0.9, (13, 0, 2, 2)),
    ])
    by_id = {track.track_id: track.bbox for track in updated}
    # Distances are [[6, 14], [4, 4]]. Greedy takes track 2 -> detection 1,
    # forcing a total distance of 18; the global optimum totals 10.
    assert by_id == {1: (5, 0, 2, 2), 2: (13, 0, 2, 2)}


def test_tracker_maximizes_gated_match_count_before_minimizing_distance():
    tracker = CentroidTracker(max_distance=3, max_missed=0)
    tracker.update([
        Detection("tool", 0.9, (-1, 0, 2, 2)),
        Detection("tool", 0.9, (1, 0, 2, 2)),
    ])

    updated = tracker.update([
        Detection("tool", 0.9, (0, 0, 2, 2)),
        Detection("tool", 0.9, (-4, 0, 2, 2)),
    ])
    by_id = {track.track_id: track.bbox for track in updated}
    # Track 2 can only reach the first detection; track 1 can reach both.
    # Keep both IDs by assigning track 2 to the first and track 1 to the second.
    assert by_id == {1: (-4, 0, 2, 2), 2: (0, 0, 2, 2)}


def test_normalize_observations_keeps_duplicate_boxes_on_distinct_tracks():
    tracker = CentroidTracker()
    detections = [
        Detection("person", 0.9, (10, 10, 4, 4)),
        Detection("person", 0.8, (10, 10, 4, 4)),
    ]
    tracks = tracker.update(detections)
    observations = normalize_observations(_frame(0, {}), detections, tracks)
    ids = [observation.subject["track_id"] for observation in observations]
    assert len(set(ids)) == 2


@pytest.mark.parametrize("kwargs", [{"max_distance": -1}, {"max_distance": float("inf")}, {"max_distance": True}, {"max_distance": "10"}, {"max_missed": -1}, {"max_missed": True}])
def test_centroid_tracker_rejects_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        CentroidTracker(**kwargs)


def test_centroid_tracker_rejects_unrepresentable_max_distance():
    with pytest.raises(ValueError):
        CentroidTracker(max_distance=10**1000)


def test_fixture_detector_normalizes_objects():
    frame = _frame(0, {"objects": [{"label": "药盒", "confidence": 0.75, "bbox": [1, 2, 3, 4]}]})
    detections = FixtureDetector().detect(frame)
    assert detections[0].label == "药盒"
    assert detections[0].bbox == (1, 2, 3, 4)

@pytest.mark.parametrize(
    "confidence",
    [float("nan"), float("inf"), -0.1, 1.1, True, "0.8", None],
)
def test_fixture_detector_rejects_invalid_confidence_instead_of_clamping(confidence):
    frame = _frame(
        0,
        {"objects": [{"label": "tool", "confidence": confidence, "bbox": [1, 2, 3, 4]}]},
    )
    with pytest.raises(ValueError, match="confidence"):
        FixtureDetector().detect(frame)


def test_fixture_detector_preserves_fractional_box_coordinates():
    frame = _frame(
        0,
        {"objects": [{"label": "tool", "confidence": 0.9, "bbox": [1.25, 2.5, 3.75, 4]}]},
    )

    detection = FixtureDetector().detect(frame)[0]

    assert detection.bbox == (1.25, 2.5, 3.75, 4.0)


def test_detection_rejects_finite_coordinates_with_overflowing_bbox_extent():
    with pytest.raises(ValueError, match="extents"):
        Detection("tool", 0.9, (1e308, 0, 1e308, 4))


@pytest.mark.parametrize(
    "bbox,confidence",
    [
        ((10**1000, 0, 1, 1), 0.9),
        ((0, 0, 1, 1), 10**1000),
    ],
)
def test_detection_rejects_unrepresentable_integer_values_with_value_error(bbox, confidence):
    with pytest.raises(ValueError):
        Detection("tool", confidence, bbox)


@pytest.mark.parametrize(
    "payload",
    [
        {"objects": [None]},
        {"objects": [{"label": "电钻"}]},
        {"objects": [{"label": "电钻", "bbox": [0, 0, 4]}]},
        {"objects": "not-an-array"},
    ],
)
def test_fixture_detector_rejects_malformed_object_records(payload):
    with pytest.raises(ValueError, match="fixture"):
        FixtureDetector().detect(_frame(0, payload))
