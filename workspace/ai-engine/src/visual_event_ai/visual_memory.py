"""Conservative source-local memory of the last observed object location."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from numbers import Real
from typing import Any

from .entity_labels import is_person_label
from .models import PrimitiveFact


MemoryKey = tuple[str, int, str]


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _identity_part(value: Any, field: str) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError(f"visual memory {field} must be a non-empty string or integer")


def _continuity(metadata: Mapping[str, Any]) -> int | None:
    value = metadata.get("continuity_segment")
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("visual memory continuity_segment must be a non-negative integer")
    return value


def _bbox(value: Any) -> tuple[float, float, float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    if any(isinstance(component, bool) or not isinstance(component, Real) for component in value):
        return None
    try:
        numbers = tuple(float(component) for component in value)
    except (TypeError, ValueError, OverflowError):
        return None
    if any(not isfinite(component) for component in numbers) or numbers[2] <= 0 or numbers[3] <= 0:
        return None
    if not isfinite(numbers[0] + numbers[2]) or not isfinite(numbers[1] + numbers[3]):
        return None
    return numbers  # type: ignore[return-value]


@dataclass(frozen=True)
class ObjectMemoryRecord:
    source_id: str
    continuity_segment: int
    track_id: str
    label: str
    last_seen_at: datetime
    last_bbox: tuple[float, float, float, float] | None
    current_zone_id: str | None
    current_location: str | None
    last_observed_zone_id: str | None
    last_observed_location: str | None
    confidence: float
    state: str
    provenance: str

    @property
    def identity_key(self) -> MemoryKey:
        return self.source_id, self.continuity_segment, self.track_id


class VisualMemory:
    """Track source/continuity-local last-known object observations.

    The memory never merges identities by label. A label query returns separate
    candidates so callers can present history without claiming re-identification.
    """

    def __init__(self) -> None:
        self._records: dict[MemoryKey, ObjectMemoryRecord] = {}

    @staticmethod
    def _key(fact: PrimitiveFact) -> tuple[MemoryKey, str, str] | None:
        metadata = fact.metadata if isinstance(fact.metadata, Mapping) else {}
        source = metadata.get("source_id")
        source_id = _identity_part(source, "source_id")
        continuity = _continuity(metadata)
        subject = fact.subject if isinstance(fact.subject, Mapping) else {}
        raw_track_id = subject.get("track_id")
        track = raw_track_id if raw_track_id is not None else subject.get("id")
        track_id = _identity_part(track, "track_id")
        if raw_track_id is not None and track_id is not None and not track_id.startswith("track-"):
            track_id = f"track-{track_id}"
        label = subject.get("label")
        if source_id is None or continuity is None or track_id is None or not isinstance(label, str) or not label.strip():
            return None
        if is_person_label(label):
            return None
        return (source_id, continuity, track_id), track_id, label.strip()

    @staticmethod
    def _zone(fact: PrimitiveFact) -> tuple[str | None, str | None]:
        metadata = fact.metadata if isinstance(fact.metadata, Mapping) else {}
        object_value = fact.object if isinstance(fact.object, Mapping) else {}
        zone_id = object_value.get("zone_id", metadata.get("zone_id"))
        location = fact.location or object_value.get("label")
        return (
            zone_id.strip() if isinstance(zone_id, str) and zone_id.strip() else None,
            location.strip() if isinstance(location, str) and location.strip() else None,
        )

    def update(self, fact: PrimitiveFact) -> None:
        if fact.fact_type == "observation_gap":
            return
        identity = self._key(fact)
        if identity is None:
            return
        key, track_id, label = identity
        previous = self._records.get(key)
        metadata = fact.metadata if isinstance(fact.metadata, Mapping) else {}
        bbox = _bbox((fact.object or {}).get("bbox")) if isinstance(fact.object, Mapping) else None
        if bbox is None:
            raw_bbox = metadata.get("bbox")
            bbox = _bbox(raw_bbox)
        confidence = float(fact.confidence)
        if fact.fact_type == "object_detected":
            self._records[key] = ObjectMemoryRecord(
                source_id=key[0],
                continuity_segment=key[1],
                track_id=track_id,
                label=label,
                last_seen_at=_utc(fact.timestamp),
                last_bbox=bbox if bbox is not None else (previous.last_bbox if previous else None),
                current_zone_id=previous.current_zone_id if previous else None,
                current_location=previous.current_location if previous else None,
                last_observed_zone_id=previous.last_observed_zone_id if previous else None,
                last_observed_location=previous.last_observed_location if previous else None,
                confidence=confidence,
                state="observed",
                provenance="direct_observation",
            )
            return
        if fact.fact_type not in {"object_in_zone", "entered_zone", "left_zone"}:
            return
        zone_id, location = self._zone(fact)
        if previous is None:
            previous = ObjectMemoryRecord(
                source_id=key[0],
                continuity_segment=key[1],
                track_id=track_id,
                label=label,
                last_seen_at=_utc(fact.timestamp),
                last_bbox=bbox,
                current_zone_id=None,
                current_location=None,
                last_observed_zone_id=None,
                last_observed_location=None,
                confidence=confidence,
                state="last_known",
                provenance="direct_observation",
            )
        left = fact.fact_type == "left_zone"
        self._records[key] = ObjectMemoryRecord(
            source_id=previous.source_id,
            continuity_segment=previous.continuity_segment,
            track_id=previous.track_id,
            label=label,
            last_seen_at=_utc(fact.timestamp),
            last_bbox=bbox if bbox is not None else previous.last_bbox,
            current_zone_id=None if left else zone_id,
            current_location=None if left else location,
            last_observed_zone_id=zone_id if zone_id is not None else previous.last_observed_zone_id,
            last_observed_location=location if location is not None else previous.last_observed_location,
            confidence=confidence,
            state="last_known" if left else "observed",
            provenance="direct_observation",
        )

    def ingest(self, facts: Iterable[PrimitiveFact]) -> None:
        for fact in facts:
            self.update(fact)

    def get(self, source_id: str, continuity_segment: int, track_id: str | int) -> ObjectMemoryRecord | None:
        source = _identity_part(source_id, "source_id") or ""
        identity = _identity_part(track_id, "track_id") or ""
        candidates = [identity]
        if not identity.startswith("track-"):
            candidates.append(f"track-{identity}")
        for candidate in candidates:
            record = self._records.get((source, continuity_segment, candidate))
            if record is not None:
                return record
        return None

    def records(self) -> list[ObjectMemoryRecord]:
        return list(self._records.values())

    def last_seen_candidates(self, label: str, *, source_id: str | None = None) -> list[ObjectMemoryRecord]:
        normalized = label.strip().casefold()
        source = source_id.strip() if isinstance(source_id, str) and source_id.strip() else None
        return sorted(
            [
                record
                for record in self._records.values()
                if record.label.casefold() == normalized and (source is None or record.source_id == source)
            ],
            key=lambda record: record.last_seen_at,
            reverse=True,
        )
