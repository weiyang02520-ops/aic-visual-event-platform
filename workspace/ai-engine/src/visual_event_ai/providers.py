from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from math import hypot, isfinite, inf
from numbers import Integral, Real
from typing import Any, Protocol

from .frame_pipeline import Frame
from .entity_labels import is_person_label


BBox = tuple[float, float, float, float]


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    bbox: BBox
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("detection label must be a non-empty string")
        object.__setattr__(self, "label", self.label.strip())
        try:
            raw_bbox = tuple(self.bbox)
        except TypeError as exc:
            raise ValueError("detection bbox must contain four finite coordinates") from exc
        if len(raw_bbox) != 4:
            raise ValueError("detection bbox must contain four finite coordinates")
        coordinates: list[float] = []
        for value in raw_bbox:
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ValueError("detection bbox must contain numeric coordinates")
            try:
                coordinate = float(value)
            except (ValueError, OverflowError) as exc:
                raise ValueError("detection bbox must contain finite coordinates") from exc
            if not isfinite(coordinate):
                raise ValueError("detection bbox must contain finite coordinates")
            coordinates.append(coordinate)
        if coordinates[2] <= 0 or coordinates[3] <= 0:
            raise ValueError("detection bbox width and height must be positive")
        if not isfinite(coordinates[0] + coordinates[2]) or not isfinite(coordinates[1] + coordinates[3]):
            raise ValueError("detection bbox extents must be finite")
        object.__setattr__(self, "bbox", tuple(coordinates))
        if isinstance(self.confidence, bool) or not isinstance(self.confidence, Real):
            raise ValueError("detection confidence must be numeric")
        try:
            confidence = float(self.confidence)
        except (ValueError, OverflowError) as exc:
            raise ValueError("detection confidence must be finite and between 0 and 1") from exc
        if not isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise ValueError("detection confidence must be finite and between 0 and 1")
        object.__setattr__(self, "confidence", confidence)
        if not isinstance(self.metadata, dict):
            raise ValueError("detection metadata must be a dictionary")


@dataclass(frozen=True)
class Track:
    track_id: int
    label: str
    confidence: float
    bbox: BBox
    age: int
    missed: int


@dataclass(frozen=True)
class Observation:
    source_id: str
    timestamp: datetime
    fact_type: str
    confidence: float
    subject: dict[str, Any] | None
    object: dict[str, Any] | None
    metadata: dict[str, Any] = field(default_factory=dict)


class Detector(Protocol):
    def detect(self, frame: Frame) -> list[Detection]: ...


class Tracker(Protocol):
    def update(self, detections: list[Detection]) -> list[Track]: ...


@dataclass(frozen=True)
class _GrayMatrix:
    values: list[list[float]]
    source_width: int
    source_height: int
    stride_x: int
    stride_y: int


def _matrix_from_payload(payload: Any) -> _GrayMatrix | None:
    if not isinstance(payload, dict):
        return None
    matrix = payload.get("gray")
    source_width: int | None = None
    source_height: int | None = None
    stride_x = 1
    stride_y = 1
    if matrix is None and payload.get("image") is not None:
        image = payload["image"]
        if hasattr(image, "shape") and hasattr(image, "tolist"):
            try:
                source_height, source_width = int(image.shape[0]), int(image.shape[1])
                step = max(1, max(source_height, source_width) // 160)
                sampled = image[::step, ::step]
                matrix = sampled.tolist()
                stride_x = stride_y = step
            except (IndexError, TypeError, ValueError, OverflowError):
                return None
    if not isinstance(matrix, list) or not matrix or not all(isinstance(row, list) and row for row in matrix):
        return None
    width = len(matrix[0])
    if width == 0 or any(len(row) != width for row in matrix):
        return None
    height = len(matrix)
    if source_width is None:
        source_width = width
        source_height = height
    normalized: list[list[float]] = []
    for row in matrix:
        normalized_row: list[float] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, Real):
                return None
            try:
                intensity = float(value)
            except (OverflowError, ValueError):
                return None
            if not isfinite(intensity) or not 0.0 <= intensity <= 255.0:
                return None
            normalized_row.append(intensity)
        normalized.append(normalized_row)
    return _GrayMatrix(normalized, source_width, source_height, stride_x, stride_y)


class MotionDetector:
    """Small, explainable CPU baseline based on frame differencing.

    It expects a fixture payload containing ``gray`` (a 2-D intensity matrix).
    Real image decoders can map their output to this payload without changing
    the detector protocol.
    """

    def __init__(self, threshold: int = 20, min_area: int = 2) -> None:
        if isinstance(threshold, bool) or not isinstance(threshold, Integral) or not 1 <= threshold <= 255:
            raise ValueError("threshold must be an integer between 1 and 255")
        if isinstance(min_area, bool) or not isinstance(min_area, Integral) or min_area < 1:
            raise ValueError("min_area must be a positive integer")
        self.threshold = int(threshold)
        self.min_area = int(min_area)
        self._previous: list[list[float]] | None = None
        self._previous_geometry: tuple[int, int, int, int] | None = None
        self._source_id: str | None = None

    def reset(self) -> None:
        self._previous = None
        self._previous_geometry = None
        self._source_id = None

    def detect(self, frame: Frame) -> list[Detection]:
        if frame.frame_index == 0 or frame.source_id != self._source_id:
            self.reset()
        self._source_id = frame.source_id
        current = _matrix_from_payload(frame.payload)
        if current is None:
            self._previous = None
            self._previous_geometry = None
            return []
        geometry = (current.source_width, current.source_height, current.stride_x, current.stride_y)
        if self._previous_geometry != geometry:
            self._previous = None
        previous = self._previous
        self._previous = current.values
        self._previous_geometry = geometry
        if previous is None or len(previous) != len(current.values) or len(previous[0]) != len(current.values[0]):
            return []
        height = len(current.values)
        width = len(current.values[0])
        changed = [[False] * width for _ in range(height)]
        for y in range(height):
            for x in range(width):
                changed[y][x] = abs(current.values[y][x] - previous[y][x]) >= self.threshold

        detections: list[Detection] = []
        for y in range(height):
            for x in range(width):
                if not changed[y][x]:
                    continue
                stack = [(x, y)]
                changed[y][x] = False
                points: list[tuple[int, int]] = []
                while stack:
                    px, py = stack.pop()
                    points.append((px, py))
                    for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                        if 0 <= nx < width and 0 <= ny < height and changed[ny][nx]:
                            changed[ny][nx] = False
                            stack.append((nx, ny))
                if len(points) < self.min_area:
                    continue
                xs = [point[0] for point in points]
                ys = [point[1] for point in points]
                area = len(points)
                x = min(xs) * current.stride_x
                y = min(ys) * current.stride_y
                right = min(current.source_width, (max(xs) + 1) * current.stride_x)
                bottom = min(current.source_height, (max(ys) + 1) * current.stride_y)
                detections.append(
                    Detection(
                        label="motion_region",
                        confidence=min(1.0, 0.5 + area / max(1, width * height)),
                        bbox=(x, y, right - x, bottom - y),
                        metadata={
                            "area": area,
                            "algorithm": "frame-difference",
                            "score_kind": "heuristic_area",
                            "sample_stride": [current.stride_x, current.stride_y],
                        },
                    )
                )
        return detections


class FixtureDetector:
    # Validates precomputed detections without altering their scores or precision.

    def detect(self, frame: Frame) -> list[Detection]:
        if not isinstance(frame.payload, dict) or "objects" not in frame.payload:
            return []
        object_rows = frame.payload["objects"]
        if not isinstance(object_rows, list):
            raise ValueError("fixture payload objects must be a list")
        results: list[Detection] = []
        for index, item in enumerate(object_rows):
            if not isinstance(item, dict):
                raise ValueError(f"fixture object at index {index} must be an object")
            bbox = item.get("bbox")
            if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
                raise ValueError(
                    f"fixture object at index {index}: bbox must contain four coordinates"
                )
            try:
                detection = Detection(
                    label=item.get("label", "object"),
                    confidence=item.get("confidence", 1.0),
                    bbox=tuple(bbox),
                    metadata={
                        "provider": "fixture",
                        **({"embedding": item["embedding"]} if isinstance(item.get("embedding"), list) else {}),
                        **({"keypoints": item["keypoints"]} if isinstance(item.get("keypoints"), dict) else {}),
                    },
                )
            except ValueError as exc:
                raise ValueError(f"fixture object at index {index}: {exc}") from exc
            results.append(detection)
        return results


def _center(bbox: BBox) -> tuple[float, float]:
    x, y, width, height = bbox
    return x + width / 2, y + height / 2


def _same_detection_class(first_label: str, second_label: str) -> bool:
    first = str(first_label).strip()
    second = str(second_label).strip()
    first_is_person = is_person_label(first)
    second_is_person = is_person_label(second)
    if first_is_person or second_is_person:
        return first_is_person and second_is_person
    return first.casefold() == second.casefold()


def _minimum_cost_assignment(costs: list[list[float]]) -> list[int]:
    """Return the minimum-cost column for each row using the Hungarian method.

    The rectangular matrix must have at least as many columns as rows. The
    implementation is local and dependency-free so tracker behavior remains
    available in the CPU-only environment.
    """

    if not costs:
        return []
    row_count = len(costs)
    column_count = len(costs[0])
    if column_count < row_count or any(len(row) != column_count for row in costs):
        raise ValueError("assignment matrix must be rectangular with columns >= rows")

    row_potential = [0.0] * (row_count + 1)
    column_potential = [0.0] * (column_count + 1)
    column_row = [0] * (column_count + 1)
    previous_column = [0] * (column_count + 1)

    for row in range(1, row_count + 1):
        column_row[0] = row
        current_column = 0
        minimum_reduced_cost = [inf] * (column_count + 1)
        used_columns = [False] * (column_count + 1)
        while True:
            used_columns[current_column] = True
            current_row = column_row[current_column]
            delta = inf
            next_column = 0
            for column in range(1, column_count + 1):
                if used_columns[column]:
                    continue
                reduced_cost = (
                    costs[current_row - 1][column - 1]
                    - row_potential[current_row]
                    - column_potential[column]
                )
                if reduced_cost < minimum_reduced_cost[column]:
                    minimum_reduced_cost[column] = reduced_cost
                    previous_column[column] = current_column
                if minimum_reduced_cost[column] < delta:
                    delta = minimum_reduced_cost[column]
                    next_column = column

            if not isfinite(delta):
                raise ValueError("assignment matrix has no finite complete assignment")
            for column in range(column_count + 1):
                if used_columns[column]:
                    row_potential[column_row[column]] += delta
                    column_potential[column] -= delta
                else:
                    minimum_reduced_cost[column] -= delta
            current_column = next_column
            if column_row[current_column] == 0:
                break

        while True:
            next_column = previous_column[current_column]
            column_row[current_column] = column_row[next_column]
            current_column = next_column
            if current_column == 0:
                break

    assignment = [-1] * row_count
    for column in range(1, column_count + 1):
        if column_row[column] != 0:
            assignment[column_row[column] - 1] = column - 1
    return assignment


class CentroidTracker:
    def __init__(self, max_distance: float = 40.0, max_missed: int = 2) -> None:
        if isinstance(max_distance, bool) or not isinstance(max_distance, Real):
            raise ValueError("max_distance must be a finite non-negative real number")
        try:
            max_distance = float(max_distance)
        except (ValueError, OverflowError) as exc:
            raise ValueError("max_distance must be a finite non-negative real number") from exc
        if not isfinite(max_distance):
            raise ValueError("max_distance must be a finite non-negative real number")
        if isinstance(max_missed, bool) or not isinstance(max_missed, Integral) or max_missed < 0:
            raise ValueError("max_missed must be a non-negative integer")
        if max_distance < 0:
            raise ValueError("max_distance must be a finite non-negative real number")
        self.max_distance = max_distance
        self.max_missed = int(max_missed)
        self._next_id = 1
        self._tracks: dict[int, Track] = {}

    def update(self, detections: list[Detection]) -> list[Track]:
        unmatched = set(range(len(detections)))
        updated: dict[int, Track] = {}
        track_ids = sorted(self._tracks)
        if track_ids and detections:
            maximum_matches = min(len(track_ids), len(detections))
            unmatched_cost = (maximum_matches + 1) * (self.max_distance + 1.0)
            if not isfinite(unmatched_cost):
                raise ValueError("max_distance is too large for finite assignment costs")
            forbidden_cost = unmatched_cost * (len(track_ids) + len(detections) + 1)
            if not isfinite(forbidden_cost):
                raise ValueError("tracker state is too large for finite assignment costs")
            distances: list[list[float | None]] = []
            cost_matrix: list[list[float]] = []

            for track_id in track_ids:
                track = self._tracks[track_id]
                track_center = _center(track.bbox)
                row_distances: list[float | None] = []
                row_costs: list[float] = []
                for detection in detections:
                    detection_center = _center(detection.bbox)
                    measured = hypot(
                        track_center[0] - detection_center[0],
                        track_center[1] - detection_center[1],
                    )
                    allowed = _same_detection_class(detection.label, track.label) and measured <= self.max_distance
                    row_distances.append(measured if allowed else None)
                    row_costs.append(measured if allowed else forbidden_cost)
                row_costs.extend([unmatched_cost] * len(track_ids))
                distances.append(row_distances)
                cost_matrix.append(row_costs)

            for row, column in enumerate(_minimum_cost_assignment(cost_matrix)):
                if column < len(detections) and distances[row][column] is not None:
                    track_id = track_ids[row]
                    detection = detections[column]
                    previous = self._tracks[track_id]
                    updated[track_id] = Track(
                        track_id,
                        detection.label,
                        detection.confidence,
                        detection.bbox,
                        previous.age + 1,
                        0,
                    )
                    unmatched.remove(column)
        for track_id, previous in self._tracks.items():
            if track_id not in updated and previous.missed < self.max_missed:
                updated[track_id] = Track(track_id, previous.label, previous.confidence, previous.bbox, previous.age + 1, previous.missed + 1)
        for index in sorted(unmatched):
            detection = detections[index]
            track_id = self._next_id
            self._next_id += 1
            updated[track_id] = Track(track_id, detection.label, detection.confidence, detection.bbox, 1, 0)
        self._tracks = updated
        return sorted(updated.values(), key=lambda track: track.track_id)


def normalize_observations(frame: Frame, detections: list[Detection], tracks: list[Track]) -> list[Observation]:
    tracks_by_detection: dict[tuple[str, BBox], list[Track]] = defaultdict(list)
    for track in sorted(tracks, key=lambda item: item.track_id):
        if track.missed == 0:
            tracks_by_detection[(track.label, track.bbox)].append(track)
    observations: list[Observation] = []
    for detection in detections:
        matching_tracks = tracks_by_detection[(detection.label, detection.bbox)]
        track = matching_tracks.pop(0) if matching_tracks else None
        observations.append(
            Observation(
                source_id=frame.source_id,
                timestamp=frame.timestamp,
                fact_type="object_detected",
                confidence=detection.confidence,
                subject={"track_id": track.track_id, "label": detection.label} if track else {"label": detection.label},
                object={"bbox": detection.bbox},
                metadata={**detection.metadata, "frame_index": frame.frame_index},
            )
        )
    return observations
