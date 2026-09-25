"""Scene-independent skeleton/object action primitives.

This layer knows only geometry, identities and provenance. Scene plugins may
later interpret these observations as medication, workshop or other events.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from math import hypot, isfinite
from numbers import Integral, Real
from typing import Any

from .entity_labels import is_person_label
from .models import PrimitiveFact
from .providers import Observation
from .skeleton import SkeletonObservation


def _finite_real(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if isfinite(number) else None


def _utc_timestamp(value: Any) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("action primitive timestamps must be datetimes")
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _entity_key(entity: Mapping[str, Any] | None) -> str | None:
    if not isinstance(entity, Mapping):
        return None
    value = entity.get("track_id")
    if value is None or (isinstance(value, str) and not value.strip()):
        value = entity.get("id")
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Integral):
        return f"track-{int(value)}"
    if isinstance(value, str) and value.strip():
        value = value.strip()
        return value if value.startswith("track-") else f"track-{value}"
    return None


def _bbox(observation: Observation) -> tuple[float, float, float, float] | None:
    if not isinstance(observation.object, Mapping):
        return None
    value = observation.object.get("bbox")
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    converted = [_finite_real(item) for item in value]
    if any(item is None for item in converted):
        return None
    x, y, width, height = converted
    if width <= 0 or height <= 0 or not isfinite(x + width) or not isfinite(y + height):
        return None
    return x, y, width, height


def _point_to_bbox_distance(point: tuple[float, float], bbox: tuple[float, float, float, float]) -> float:
    px, py = point
    x, y, width, height = bbox
    dx = max(x - px, 0.0, px - (x + width))
    dy = max(y - py, 0.0, py - (y + height))
    return hypot(dx, dy)


class GenericActionPrimitiveExtractor:
    """Extract geometry-only actions from skeleton/object observations."""

    def __init__(
        self,
        *,
        max_face_distance_fraction: float = 0.2,
        min_keypoint_confidence: float = 0.5,
        max_missing_frames: int = 1,
        emit_hand_to_face: bool = True,
    ) -> None:
        face_fraction = _finite_real(max_face_distance_fraction)
        minimum_confidence = _finite_real(min_keypoint_confidence)
        if face_fraction is None or not 0.0 < face_fraction <= 1.0:
            raise ValueError("max_face_distance_fraction must be finite and in (0, 1]")
        if minimum_confidence is None or not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError("min_keypoint_confidence must be between 0 and 1")
        if isinstance(max_missing_frames, bool) or not isinstance(max_missing_frames, Integral) or max_missing_frames < 0:
            raise ValueError("max_missing_frames must be a non-negative integer")
        self.max_face_distance_fraction = face_fraction
        self.min_keypoint_confidence = minimum_confidence
        self.max_missing_frames = int(max_missing_frames)
        self.emit_hand_to_face = bool(emit_hand_to_face)
        self._last_seen_frames: dict[tuple[str, str], int] = {}
        self._last_frame_index: int | None = None
        self._implicit_frame_index = 0
        self._last_source_id: str | None = None

    def _point(self, keypoints: Mapping[str, Any], name: str) -> tuple[float, float, float] | None:
        skeleton = SkeletonObservation.from_keypoints(keypoints, strict=False)
        value = skeleton.keypoints.get(name)
        if value is None or value[2] < self.min_keypoint_confidence:
            return None
        return value[0], value[1], value[2]

    def _prepare_frame(
        self,
        observations: list[Observation],
        relation_facts: list[PrimitiveFact],
        frame_index: int | None,
    ) -> tuple[int, datetime | None, str | None, dict[str, Observation], list[tuple[str, Observation]], list[tuple[str, Observation]]]:
        timestamps = {_utc_timestamp(observation.timestamp) for observation in observations}
        if len(timestamps) > 1:
            raise ValueError("action primitive observations must come from one frame timestamp")
        frame_timestamp = next(iter(timestamps), None)
        source_ids = {observation.source_id for observation in observations if observation.source_id}
        if len(source_ids) > 1:
            raise ValueError("action primitive observations must come from one source")
        source_id = next(iter(source_ids), None)
        relation_source_ids = {
            fact.metadata.get("source_id")
            for fact in relation_facts
            if isinstance(fact.metadata, Mapping) and "source_id" in fact.metadata
        }
        if any(not isinstance(value, str) or not value.strip() for value in relation_source_ids):
            raise ValueError("action primitive relation source_id must be a non-empty string")
        if len(relation_source_ids) > 1 or (source_id is not None and relation_source_ids and source_id not in relation_source_ids):
            raise ValueError("action primitive relations must come from one source")
        if frame_index is None:
            frame_index = self._implicit_frame_index
            self._implicit_frame_index += 1
        else:
            if isinstance(frame_index, bool) or not isinstance(frame_index, Integral) or frame_index < 0:
                raise ValueError("frame_index must be a non-negative integer")
            frame_index = int(frame_index)
            self._implicit_frame_index = max(self._implicit_frame_index, frame_index + 1)
        if source_id is not None and source_id != self._last_source_id:
            self._last_seen_frames.clear()
            self._last_frame_index = None
            self._implicit_frame_index = frame_index + 1
        if self._last_frame_index is not None and frame_index < self._last_frame_index:
            raise ValueError("action primitive frame indexes must be non-decreasing")
        self._last_source_id = source_id or self._last_source_id
        self._last_frame_index = frame_index

        by_entity: dict[str, Observation] = {}
        people: list[tuple[str, Observation]] = []
        objects: list[tuple[str, Observation]] = []
        for observation in observations:
            subject = observation.subject
            if not isinstance(subject, Mapping):
                continue
            entity_id = _entity_key(subject)
            if entity_id is None:
                continue
            by_entity[entity_id] = observation
            if is_person_label(subject.get("label")):
                people.append((entity_id, observation))
            else:
                objects.append((entity_id, observation))
        return frame_index, frame_timestamp, source_id, by_entity, people, objects

    def extract(
        self,
        observations: list[Observation],
        relation_facts: list[PrimitiveFact] = (),
        *,
        frame_index: int | None = None,
    ) -> list[PrimitiveFact]:
        frame_index, frame_timestamp, source_id, by_entity, people, objects = self._prepare_frame(
            observations, list(relation_facts), frame_index
        )
        emitted: list[PrimitiveFact] = []
        for person_id, person in people:
            metadata = person.metadata if isinstance(person.metadata, Mapping) else {}
            skeleton = SkeletonObservation.from_metadata(
                metadata,
                source_id=person.source_id,
                timestamp=person.timestamp,
                track_id=person_id,
                strict=False,
            )
            person_bbox = _bbox(person)
            if skeleton is None or person_bbox is None:
                continue
            nose = self._point(skeleton.keypoints, "nose")
            if nose is None:
                continue
            face_radius = person_bbox[3] * self.max_face_distance_fraction
            valid_wrists = []
            for hand_name in ("left_wrist", "right_wrist"):
                wrist = self._point(skeleton.keypoints, hand_name)
                if wrist is None:
                    continue
                face_distance = hypot(wrist[0] - nose[0], wrist[1] - nose[1])
                valid_wrists.append((hand_name, wrist, face_distance))
            close_wrists = [item for item in valid_wrists if item[2] <= face_radius]
            for hand_name, wrist, face_distance in close_wrists:
                if self.emit_hand_to_face:
                    pair = (person_id, hand_name)
                    last_seen = self._last_seen_frames.get(pair)
                    if last_seen is None or frame_index - last_seen > self.max_missing_frames + 1:
                        emitted.append(
                            PrimitiveFact(
                                fact_type="hand_to_face",
                                timestamp=person.timestamp,
                                confidence=round(min(person.confidence, nose[2], wrist[2]), 3),
                                subject={"id": person_id, "label": person.subject["label"]},
                                metadata={
                                    "action_extractor": "skeleton-distance-v1",
                                    "source_id": source_id,
                                    "continuity_segment": metadata.get("continuity_segment"),
                                    "hand_keypoint": hand_name,
                                    "face_reference": "nose",
                                    "face_distance_px": round(face_distance, 3),
                                    "threshold_px": round(face_radius, 3),
                                    "evidence_level": "observation",
                                },
                            )
                        )
                    self._last_seen_frames[pair] = frame_index
            # Object proximity is independent of face proximity: a hand may
            # be interacting with a tool while nowhere near the face.
            for hand_name, wrist, face_distance in valid_wrists:
                for object_id, object_observation in objects:
                    object_bbox = _bbox(object_observation)
                    if object_bbox is None:
                        continue
                    object_distance = _point_to_bbox_distance((wrist[0], wrist[1]), object_bbox)
                    threshold = max(4.0, person_bbox[3] * 0.1)
                    if object_distance > threshold:
                        continue
                    object_subject = object_observation.subject or {}
                    emitted.append(
                        PrimitiveFact(
                            fact_type="hand_near_object",
                            timestamp=person.timestamp,
                            confidence=round(min(person.confidence, object_observation.confidence, wrist[2]), 3),
                            subject={"id": person_id, "label": person.subject["label"]},
                            object={"id": object_id, "label": object_subject.get("label")},
                            metadata={
                                "action_extractor": "skeleton-object-distance-v1",
                                "source_id": source_id,
                                "continuity_segment": metadata.get("continuity_segment"),
                                "hand_keypoint": hand_name,
                                "wrist_object_distance_px": round(object_distance, 3),
                                "threshold_px": round(threshold, 3),
                                "object_bbox": list(object_bbox),
                                "evidence_level": "observation",
                            },
                        )
                    )
        for pair, last_seen in list(self._last_seen_frames.items()):
            if frame_index - last_seen > self.max_missing_frames + 1:
                del self._last_seen_frames[pair]
        return emitted
