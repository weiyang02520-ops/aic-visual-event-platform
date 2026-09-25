from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from math import hypot, isfinite
from numbers import Real
from typing import Any

from .entity_labels import is_person_label


BBox = tuple[float, float, float, float]


@dataclass(frozen=True)
class Entity:
    entity_id: str
    label: str
    bbox: BBox
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.entity_id, str) or not self.entity_id.strip():
            raise ValueError("entity_id must be a non-empty string")
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("entity label must be a non-empty string")
        object.__setattr__(self, "entity_id", self.entity_id.strip())
        object.__setattr__(self, "label", self.label.strip())

        try:
            raw_bbox = tuple(self.bbox)
        except TypeError as exc:
            raise ValueError("entity bbox must contain four finite coordinates") from exc
        if len(raw_bbox) != 4:
            raise ValueError("entity bbox must contain four finite coordinates")
        coordinates: list[float] = []
        for value in raw_bbox:
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ValueError("entity bbox must contain numeric coordinates")
            try:
                coordinate = float(value)
            except (ValueError, OverflowError) as exc:
                raise ValueError("entity bbox must contain finite coordinates") from exc
            if not isfinite(coordinate):
                raise ValueError("entity bbox must contain finite coordinates")
            coordinates.append(coordinate)
        if coordinates[2] <= 0 or coordinates[3] <= 0:
            raise ValueError("entity bbox width and height must be positive")
        if not isfinite(coordinates[0] + coordinates[2]) or not isfinite(coordinates[1] + coordinates[3]):
            raise ValueError("entity bbox extents must be finite")
        object.__setattr__(self, "bbox", tuple(coordinates))

        if isinstance(self.confidence, bool) or not isinstance(self.confidence, Real):
            raise ValueError("entity confidence must be numeric")
        try:
            confidence = float(self.confidence)
        except (ValueError, OverflowError) as exc:
            raise ValueError("entity confidence must be finite and between 0 and 1") from exc
        if not isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise ValueError("entity confidence must be finite and between 0 and 1")
        object.__setattr__(self, "confidence", confidence)

@dataclass(frozen=True)
class Zone:
    zone_id: str
    label: str
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        if not isinstance(self.zone_id, str) or not self.zone_id.strip():
            raise ValueError("zone_id must be a non-empty string")
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("zone label must be a non-empty string")
        object.__setattr__(self, "zone_id", self.zone_id.strip())
        object.__setattr__(self, "label", self.label.strip())

        for name in ("x", "y", "width", "height"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ValueError("zone geometry must contain finite numeric coordinates")
            try:
                coordinate = float(value)
            except (ValueError, OverflowError) as exc:
                raise ValueError("zone geometry must contain finite coordinates") from exc
            if not isfinite(coordinate):
                raise ValueError("zone geometry must contain finite coordinates")
            object.__setattr__(self, name, coordinate)
        if self.width <= 0 or self.height <= 0:
            raise ValueError("zone width and height must be positive")
        if not isfinite(self.x + self.width) or not isfinite(self.y + self.height):
            raise ValueError("zone extents must be finite")

    def contains(self, point: tuple[float, float]) -> bool:
        px, py = point
        return self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height

@dataclass(frozen=True)
class RelationFact:
    fact_type: str
    timestamp: datetime
    confidence: float
    subject: dict[str, Any]
    object: dict[str, Any] | None = None
    location: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def center(bbox: BBox) -> tuple[float, float]:
    x, y, width, height = bbox
    return x + width / 2, y + height / 2


def distance(first: Entity, second: Entity) -> float:
    ax, ay = center(first.bbox)
    bx, by = center(second.bbox)
    return hypot(ax - bx, ay - by)


class RelationEngine:
    def __init__(self, *, near_distance: float = 50.0, motion_distance: float = 8.0, cooldown_seconds: float = 1.5) -> None:
        numeric_values: dict[str, float] = {}
        for name, value in (
            ("near_distance", near_distance),
            ("motion_distance", motion_distance),
            ("cooldown_seconds", cooldown_seconds),
        ):
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ValueError(f"{name} must be a finite real number")
            try:
                numeric = float(value)
            except (ValueError, OverflowError) as exc:
                raise ValueError(f"{name} must be a finite real number") from exc
            if not isfinite(numeric):
                raise ValueError(f"{name} must be finite")
            numeric_values[name] = numeric
        near_distance = numeric_values["near_distance"]
        motion_distance = numeric_values["motion_distance"]
        cooldown_seconds = numeric_values["cooldown_seconds"]
        if near_distance <= 0:
            raise ValueError("near_distance must be a finite positive number")
        if motion_distance <= 0:
            raise ValueError("motion_distance must be a finite positive number")
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be a finite non-negative number")
        self.near_distance = near_distance
        self.motion_distance = motion_distance
        self.cooldown = timedelta(seconds=cooldown_seconds)
        self._previous_entities: dict[str, Entity] = {}
        self._previous_near: set[tuple[str, str]] = set()
        self._previous_zones: dict[tuple[str, str], bool] = {}
        self._last_emitted: dict[tuple[str, ...], datetime] = {}
        self._last_timestamp: datetime | None = None

    @staticmethod
    def _utc(timestamp: datetime) -> datetime:
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc)

    def _allow(self, key: tuple[str, ...], timestamp: datetime) -> bool:
        previous = self._last_emitted.get(key)
        if previous is not None and timestamp - previous < self.cooldown:
            return False
        self._last_emitted[key] = timestamp
        return True

    def _prune_cooldowns(
        self,
        observed_entity_ids: set[str],
        observed_pairs: set[tuple[str, str]],
        observed_zone_keys: set[tuple[str, str]],
    ) -> None:
        for key in list(self._last_emitted):
            kind = key[0]
            if kind in {"near", "pickup", "putdown"}:
                if len(key) != 3 or (key[1], key[2]) not in observed_pairs:
                    del self._last_emitted[key]
            elif kind == "motion":
                if len(key) != 2 or key[1] not in observed_entity_ids:
                    del self._last_emitted[key]
            elif kind == "zone":
                if len(key) != 4 or (key[1], key[2]) not in observed_zone_keys:
                    del self._last_emitted[key]

    def reset_after_discontinuity(self) -> None:
        """Discard continuity evidence while retaining the source timestamp guard."""

        self._previous_entities.clear()
        self._previous_near.clear()
        self._previous_zones.clear()
        self._last_emitted.clear()

    def evaluate(self, entities: list[Entity], zones: list[Zone], timestamp: datetime) -> list[RelationFact]:
        entity_ids = [entity.entity_id for entity in entities]
        if len(entity_ids) != len(set(entity_ids)):
            raise ValueError("entity_id values must be unique")
        zone_ids = [zone.zone_id for zone in zones]
        if len(zone_ids) != len(set(zone_ids)):
            raise ValueError("zone_id values must be unique")
        timestamp = self._utc(timestamp)
        if self._last_timestamp is not None and timestamp < self._last_timestamp:
            raise ValueError("relation timestamps must be non-decreasing")
        self._last_timestamp = timestamp
        people = [entity for entity in entities if is_person_label(entity.label)]
        objects = [entity for entity in entities if entity not in people]
        facts: list[RelationFact] = []
        observed_pairs: set[tuple[str, str]] = set()

        for person in people:
            for item in objects:
                pair = (person.entity_id, item.entity_id)
                observed_pairs.add(pair)
                measured = distance(person, item)
                if not isfinite(measured):
                    observed_pairs.discard(pair)
                    self._previous_near.discard(pair)
                    continue
                confidence = min(person.confidence, item.confidence)
                facts.append(RelationFact("person_object_distance", timestamp, confidence, {"id": person.entity_id, "label": person.label}, {"id": item.entity_id, "label": item.label, "distance": round(measured, 3)}))
                is_near = measured <= self.near_distance
                was_near = pair in self._previous_near
                if is_near and self._allow(("near", person.entity_id, item.entity_id), timestamp):
                    facts.append(RelationFact("near", timestamp, confidence, {"id": person.entity_id, "label": person.label}, {"id": item.entity_id, "label": item.label, "distance": round(measured, 3)}))
                if is_near and not was_near and self._allow(("pickup", person.entity_id, item.entity_id), timestamp):
                    facts.append(RelationFact("pickup_candidate", timestamp, confidence, {"id": person.entity_id, "label": person.label}, {"id": item.entity_id, "label": item.label}))
                if not is_near and was_near and self._allow(("putdown", person.entity_id, item.entity_id), timestamp):
                    facts.append(RelationFact("putdown_candidate", timestamp, confidence, {"id": person.entity_id, "label": person.label}, {"id": item.entity_id, "label": item.label}))
                if is_near:
                    self._previous_near.add(pair)
                else:
                    self._previous_near.discard(pair)

        for entity in entities:
            previous = self._previous_entities.get(entity.entity_id)
            if previous is not None:
                moved = distance(previous, entity)
                if not isfinite(moved):
                    self._last_emitted.pop(("motion", entity.entity_id), None)
                elif moved >= self.motion_distance and self._allow(("motion", entity.entity_id), timestamp):
                    facts.append(RelationFact("motion", timestamp, entity.confidence, {"id": entity.entity_id, "label": entity.label}, metadata={"distance": round(moved, 3)}))
            self._previous_entities[entity.entity_id] = entity
            point = center(entity.bbox)
            for zone in zones:
                membership_key = (entity.entity_id, zone.zone_id)
                inside = zone.contains(point)
                previous_inside = self._previous_zones.get(membership_key)
                edge = "inside" if inside else "outside"
                if inside and not is_person_label(entity.label):
                    facts.append(
                        RelationFact(
                            "object_in_zone",
                            timestamp,
                            entity.confidence,
                            {"id": entity.entity_id, "label": entity.label},
                            {"zone_id": zone.zone_id, "label": zone.label},
                            location=zone.label,
                            metadata={
                                "zone_id": zone.zone_id,
                                "direct_observation": True,
                                "bbox": list(entity.bbox),
                            },
                        )
                    )
                if previous_inside is not None and inside != previous_inside and self._allow(("zone", entity.entity_id, zone.zone_id, edge), timestamp):
                    facts.append(RelationFact("entered_zone" if inside else "left_zone", timestamp, entity.confidence, {"id": entity.entity_id, "label": entity.label}, location=zone.label, metadata={"zone_id": zone.zone_id}))
                self._previous_zones[membership_key] = inside

        # A missing detection is an evidence gap, not evidence that an entity
        # stayed in its old position or relation. Drop continuity state so a
        # later reappearance cannot create motion, put-down, or zone-transition
        # facts from two non-adjacent observations.
        observed_entity_ids = set(entity_ids)
        self._previous_entities = {
            entity_id: previous
            for entity_id, previous in self._previous_entities.items()
            if entity_id in observed_entity_ids
        }
        self._previous_near.intersection_update(observed_pairs)
        observed_zone_keys = {
            (entity.entity_id, zone.zone_id)
            for entity in entities
            for zone in zones
        }
        self._previous_zones = {
            key: inside
            for key, inside in self._previous_zones.items()
            if key in observed_zone_keys
        }
        self._prune_cooldowns(observed_entity_ids, observed_pairs, observed_zone_keys)

        return facts
