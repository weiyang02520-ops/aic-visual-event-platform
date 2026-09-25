"""Rule-based action facts from explicit pose keypoints.

This module consumes keypoints supplied by a pose detector or fixture. It does
not infer pose from pixels. The rule associates a wrist-near-face pose with a
medication object only when the same wrist is also near that object's box.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from math import hypot, isfinite
from numbers import Integral, Real
from typing import Any

from .entity_labels import is_medication_entity, is_person_label
from .models import PrimitiveFact
from .providers import Observation
from .skeleton import SkeletonKeypoint, SkeletonObservation


def _finite_real(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    try:
        numeric = float(value)
    except (ValueError, OverflowError):
        return None
    return numeric if isfinite(numeric) else None


class MedicationActionAdapter:
    """Compatibility adapter that links generic actions to medication facts.

    Geometry-only primitives live in :class:`GenericActionPrimitiveExtractor`.
    This adapter keeps the existing medication reasoner contract and is the
    only place where medication labels are consulted.
    """

    _relation_types = {"near", "pickup_candidate"}

    def __init__(
        self,
        *,
        max_face_distance_fraction: float = 0.2,
        min_keypoint_confidence: float = 0.5,
        max_missing_frames: int = 1,
    ) -> None:
        face_fraction = _finite_real(max_face_distance_fraction)
        if face_fraction is None or not 0.0 < face_fraction <= 1.0:
            raise ValueError("max_face_distance_fraction must be finite and in (0, 1]")
        minimum_confidence = _finite_real(min_keypoint_confidence)
        if minimum_confidence is None or not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError("min_keypoint_confidence must be between 0 and 1")
        if isinstance(max_missing_frames, bool) or not isinstance(max_missing_frames, Integral) or max_missing_frames < 0:
            raise ValueError("max_missing_frames must be a non-negative integer")
        self.max_face_distance_fraction = face_fraction
        self.min_keypoint_confidence = minimum_confidence
        self.max_missing_frames = int(max_missing_frames)
        self._last_seen_frames: dict[tuple[str, str], int] = {}
        self._last_frame_index: int | None = None
        self._implicit_frame_index = 0
        self._last_source_id: str | None = None

    @staticmethod
    def _utc_timestamp(value: Any) -> datetime:
        if not isinstance(value, datetime):
            raise ValueError("keypoint action timestamps must be datetimes")
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _entity_key(entity: Mapping[str, Any] | None) -> str | None:
        if not isinstance(entity, Mapping):
            return None
        value = entity.get("track_id")
        if value is None or (isinstance(value, str) and not value.strip()):
            value = entity.get("id")
        if value is None or isinstance(value, bool):
            return None
        key = str(value).strip()
        return key or None

    def _point(self, keypoints: Mapping[str, Any], name: str) -> tuple[float, float, float] | None:
        point = SkeletonKeypoint.from_value(name, keypoints.get(name), strict=False)
        if point is None:
            return None
        if point.confidence < self.min_keypoint_confidence:
            return None
        return point.x, point.y, point.confidence

    @staticmethod
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
        if width <= 0 or height <= 0:
            return None
        if not isfinite(x + width) or not isfinite(y + height):
            return None
        return x, y, width, height

    @staticmethod
    def _point_to_bbox_distance(point: tuple[float, float], bbox: tuple[float, float, float, float]) -> float:
        px, py = point
        x, y, width, height = bbox
        dx = max(x - px, 0.0, px - (x + width))
        dy = max(y - py, 0.0, py - (y + height))
        return hypot(dx, dy)

    def extract(
        self,
        observations: list[Observation],
        relation_facts: list[PrimitiveFact],
        *,
        frame_index: int | None = None,
    ) -> list[PrimitiveFact]:
        observation_timestamps = {self._utc_timestamp(observation.timestamp) for observation in observations}
        if len(observation_timestamps) > 1:
            raise ValueError("keypoint action observations must come from one frame timestamp")
        frame_timestamp = next(iter(observation_timestamps), None)
        source_ids = {observation.source_id for observation in observations if observation.source_id}
        if len(source_ids) > 1:
            raise ValueError("keypoint action observations must come from one source")
        source_id = next(iter(source_ids), None)
        if source_id is not None and self._last_source_id is not None and source_id != self._last_source_id:
            self._last_seen_frames.clear()
            self._last_frame_index = None
            self._implicit_frame_index = 0
        if source_id is not None:
            self._last_source_id = source_id
        relation_source_ids: set[str] = set()
        for fact in relation_facts:
            metadata = fact.metadata
            if not isinstance(metadata, Mapping) or "source_id" not in metadata:
                continue
            relation_source_id = metadata.get("source_id")
            if not isinstance(relation_source_id, str) or not relation_source_id.strip():
                raise ValueError("keypoint action relation source_id must be a non-empty string")
            relation_source_ids.add(relation_source_id.strip())
        if len(relation_source_ids) > 1 or (
            source_id is not None and relation_source_ids and source_id not in relation_source_ids
        ):
            raise ValueError("keypoint action relations must come from one source")
        if frame_index is None:
            frame_index = self._implicit_frame_index
            self._implicit_frame_index += 1
        else:
            if isinstance(frame_index, bool) or not isinstance(frame_index, Integral) or frame_index < 0:
                raise ValueError("frame_index must be a non-negative integer")
            frame_index = int(frame_index)
            self._implicit_frame_index = max(self._implicit_frame_index, frame_index + 1)
        if self._last_frame_index is not None and frame_index < self._last_frame_index:
            raise ValueError("keypoint action frame indexes must be non-decreasing")
        self._last_frame_index = frame_index

        observations_by_entity: dict[str, Observation] = {}
        people: list[tuple[str, Observation]] = []
        for observation in observations:
            subject = observation.subject
            if not isinstance(subject, Mapping):
                continue
            track_id = subject.get("track_id")
            if track_id is None or (isinstance(track_id, str) and not track_id.strip()):
                track_id = subject.get("id")
            if track_id is None or isinstance(track_id, bool):
                continue
            if isinstance(track_id, Integral):
                track_key = str(int(track_id))
            elif isinstance(track_id, str):
                track_key = track_id.strip()
            else:
                continue
            if not track_key:
                continue
            entity_id = track_key if track_key.startswith("track-") else f"track-{track_key}"
            observations_by_entity[entity_id] = observation
            if is_person_label(subject.get("label")):
                people.append((entity_id, observation))

        medication_relations: dict[tuple[str, str], PrimitiveFact] = {}
        for fact in relation_facts:
            if fact.fact_type not in self._relation_types:
                continue
            if frame_timestamp is None or self._utc_timestamp(fact.timestamp) != frame_timestamp:
                continue
            person_id = self._entity_key(fact.subject)
            object_id = self._entity_key(fact.object)
            if person_id is None or object_id is None or not is_medication_entity(fact.object):
                continue
            pair = (person_id, object_id)
            current = medication_relations.get(pair)
            if current is None or fact.fact_type == "pickup_candidate":
                medication_relations[pair] = fact

        emitted: list[PrimitiveFact] = []
        for person_id, observation in people:
            metadata = observation.metadata
            skeleton = SkeletonObservation.from_metadata(
                metadata,
                source_id=observation.source_id,
                timestamp=observation.timestamp,
                strict=False,
            )
            keypoints = skeleton.keypoints if skeleton is not None else None
            person_bbox = self._bbox(observation)
            if not isinstance(keypoints, Mapping) or person_bbox is None:
                continue
            nose = self._point(keypoints, "nose")
            wrists = [
                (name, point)
                for name in ("left_wrist", "right_wrist")
                if (point := self._point(keypoints, name)) is not None
            ]
            if nose is None or not wrists:
                continue
            face_x, face_y, face_confidence = nose
            face_radius = person_bbox[3] * self.max_face_distance_fraction
            close_wrists = [
                (name, point, hypot(point[0] - face_x, point[1] - face_y))
                for name, point in wrists
                if hypot(point[0] - face_x, point[1] - face_y) <= face_radius
            ]
            if not close_wrists:
                continue

            for (relation_person_id, object_id), relation in medication_relations.items():
                if relation_person_id != person_id:
                    continue
                object_observation = observations_by_entity.get(object_id)
                object_bbox = self._bbox(object_observation) if object_observation else None
                if object_observation is None or object_bbox is None:
                    continue
                close_pairs = [
                    (name, point, face_distance, self._point_to_bbox_distance((point[0], point[1]), object_bbox))
                    for name, point, face_distance in close_wrists
                ]
                hand = min(close_pairs, key=lambda item: item[3])
                hand_name, wrist, face_distance, object_distance = hand
                object_radius = max(4.0, person_bbox[3] * 0.1)
                if object_distance > object_radius:
                    continue

                pair = (person_id, object_id)
                last_seen = self._last_seen_frames.get(pair)
                if last_seen is not None and frame_index - last_seen <= self.max_missing_frames + 1:
                    self._last_seen_frames[pair] = frame_index
                    continue
                self._last_seen_frames[pair] = frame_index
                confidence = min(
                    observation.confidence,
                    object_observation.confidence,
                    relation.confidence,
                    face_confidence,
                    wrist[2],
                )
                emitted.append(
                    PrimitiveFact(
                        fact_type="hand_to_face",
                        timestamp=observation.timestamp,
                        confidence=round(confidence, 3),
                        subject={"id": person_id, "label": observation.subject["label"]},
                        object=dict(relation.object),
                        metadata={
                            "action_extractor": "keypoint-distance-v1",
                            **({"source_id": source_id} if source_id is not None else {}),
                            "hand_keypoint": hand_name,
                            "face_reference": "nose",
                            "face_distance_px": round(face_distance, 3),
                            "hand_object_distance_px": round(object_distance, 3),
                            "review_required": True,
                        },
                    )
                )

        for pair, last_seen in list(self._last_seen_frames.items()):
            if frame_index - last_seen > self.max_missing_frames + 1:
                del self._last_seen_frames[pair]
        return emitted


# Existing callers keep the stable name while the implementation is explicit
# about being a scene-specific compatibility adapter.
KeypointActionExtractor = MedicationActionAdapter
