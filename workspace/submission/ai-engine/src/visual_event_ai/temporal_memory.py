"""Bounded, source-local temporal memory for explainable visual facts.

The memory is deliberately a Python-layer composition over ``VisualMemory``.
It keeps recent action/zone evidence queryable while the object-location memory
continues to own last-known object state.  Identity is always scoped by source,
continuity segment and explicit track/entity IDs; labels are query filters, not
identity keys.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite
from numbers import Integral, Real
from typing import Any

from .models import PrimitiveFact
from .privacy import sanitize_sensitive_payload
from .visual_memory import ObjectMemoryRecord, VisualMemory


TEMPORAL_FACT_TYPES = frozenset(
    {
        "hand_near_object",
        "hand_to_face",
        "pickup_candidate",
        "putdown_candidate",
        "motion",
        "entered_zone",
        "left_zone",
        "object_in_zone",
    }
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _id(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"temporal memory {field} must be a non-empty string or integer")
    if isinstance(value, Integral):
        return str(int(value))
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, str):
        return None
    raise ValueError(f"temporal memory {field} must be a non-empty string or integer")


def _entity_id(entity: Mapping[str, Any] | None, field: str) -> str | None:
    if not isinstance(entity, Mapping):
        return None
    value = entity.get("track_id")
    if value is None or (isinstance(value, str) and not value.strip()):
        value = entity.get("id")
    return _id(value, field)


def _label(entity: Mapping[str, Any] | None) -> str | None:
    value = entity.get("label") if isinstance(entity, Mapping) else None
    return value.strip() if isinstance(value, str) and value.strip() else None


def _source(metadata: Mapping[str, Any]) -> str | None:
    if "source_id" not in metadata:
        return None
    value = metadata.get("source_id")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("temporal memory source_id must be a non-empty string")
    return value.strip()


def _segment(metadata: Mapping[str, Any]) -> int | None:
    if "continuity_segment" not in metadata:
        return None
    value = metadata.get("continuity_segment")
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
        raise ValueError("temporal memory continuity_segment must be a non-negative integer")
    return int(value)


def _confidence(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("temporal memory confidence must be a finite non-Boolean number")
    number = float(value)
    if not isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError("temporal memory confidence must be finite and between 0 and 1")
    return number


@dataclass(frozen=True)
class TemporalFactRecord:
    """Safe, provenance-preserving copy of one temporal primitive fact."""

    fact_type: str
    timestamp: datetime
    source_id: str | None
    continuity_segment: int | None
    confidence: float
    subject_id: str | None
    subject_label: str | None
    object_id: str | None
    object_label: str | None
    location: str | None
    zone_id: str | None
    subject: dict[str, Any] | None = None
    object: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    sequence: int = field(default=0, repr=False, compare=False)

    @property
    def identity_key(self) -> tuple[str | None, int | None, str | None, str | None]:
        return self.source_id, self.continuity_segment, self.subject_id, self.object_id

    @property
    def subject_identity(self) -> str | None:
        return self.subject_id

    @property
    def object_identity(self) -> str | None:
        return self.object_id

    @classmethod
    def from_fact(cls, fact: PrimitiveFact, *, sequence: int = 0) -> TemporalFactRecord | None:
        if fact.fact_type not in TEMPORAL_FACT_TYPES:
            return None
        metadata = fact.metadata if isinstance(fact.metadata, Mapping) else {}
        source_id = _source(metadata)
        segment = _segment(metadata)
        subject = fact.subject if isinstance(fact.subject, Mapping) else None
        object_value = fact.object if isinstance(fact.object, Mapping) else None
        subject_copy = sanitize_sensitive_payload(dict(subject)) if subject is not None else None
        object_copy = sanitize_sensitive_payload(dict(object_value)) if object_value is not None else None
        safe_metadata = sanitize_sensitive_payload(dict(metadata))
        if not isinstance(subject_copy, dict) or not isinstance(object_copy, (dict, type(None))) or not isinstance(safe_metadata, dict):
            raise ValueError("temporal memory fact payload could not be sanitized")
        raw_zone = metadata.get("zone_id")
        if raw_zone is None and isinstance(object_value, Mapping):
            raw_zone = object_value.get("zone_id")
        zone_id = raw_zone.strip() if isinstance(raw_zone, str) and raw_zone.strip() else None
        location = fact.location.strip() if isinstance(fact.location, str) and fact.location.strip() else None
        return cls(
            fact_type=fact.fact_type,
            timestamp=_utc(fact.timestamp),
            source_id=source_id,
            continuity_segment=segment,
            confidence=_confidence(fact.confidence),
            subject_id=_entity_id(subject, "subject_id"),
            subject_label=_label(subject),
            object_id=_entity_id(object_value, "object_id"),
            object_label=_label(object_value),
            location=location,
            zone_id=zone_id,
            subject=subject_copy,
            object=object_copy,
            metadata=safe_metadata,
            sequence=sequence,
        )


class TemporalVisualMemory:
    """Bounded temporal evidence store composed with :class:`VisualMemory`."""

    def __init__(
        self,
        *,
        visual_memory: VisualMemory | None = None,
        max_records: int = 2048,
        max_records_per_identity: int = 256,
        fact_types: Iterable[str] = TEMPORAL_FACT_TYPES,
    ) -> None:
        self.max_records = self._positive_int(max_records, "max_records")
        self.max_records_per_identity = self._positive_int(
            max_records_per_identity, "max_records_per_identity"
        )
        normalized = tuple(dict.fromkeys(str(item).strip() for item in fact_types if str(item).strip()))
        if not normalized:
            raise ValueError("fact_types must contain at least one non-empty type")
        self.fact_types = frozenset(normalized)
        self.visual_memory = visual_memory or VisualMemory()
        self._records: list[TemporalFactRecord] = []
        self._sequence = 0

    @staticmethod
    def _positive_int(value: Any, field: str) -> int:
        if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
            raise ValueError(f"{field} must be a positive integer")
        return int(value)

    @property
    def records_count(self) -> int:
        return len(self._records)

    def update(self, fact: PrimitiveFact) -> TemporalFactRecord | None:
        # VisualMemory sees object_detected and zone facts, while the temporal
        # action list intentionally excludes raw detection rows.
        self.visual_memory.update(fact)
        if fact.fact_type not in self.fact_types:
            return None
        record = TemporalFactRecord.from_fact(fact, sequence=self._sequence)
        self._sequence += 1
        if record is None:
            return None
        self._records.append(record)
        self._evict_identity(record.identity_key)
        if len(self._records) > self.max_records:
            self._records.sort(key=lambda item: (item.timestamp, item.sequence))
            del self._records[: len(self._records) - self.max_records]
        return record

    def _evict_identity(self, identity: tuple[str | None, int | None, str | None, str | None]) -> None:
        scoped = [item for item in self._records if item.identity_key == identity]
        if len(scoped) <= self.max_records_per_identity:
            return
        remove_count = len(scoped) - self.max_records_per_identity
        removed = {item.sequence for item in sorted(scoped, key=lambda item: (item.timestamp, item.sequence))[:remove_count]}
        self._records[:] = [item for item in self._records if item.sequence not in removed]

    def ingest(self, facts: Iterable[PrimitiveFact]) -> list[TemporalFactRecord]:
        added: list[TemporalFactRecord] = []
        for fact in facts:
            record = self.update(fact)
            if record is not None:
                added.append(record)
        return added

    def all_records(self) -> list[TemporalFactRecord]:
        return sorted(self._records, key=lambda item: (item.timestamp, item.sequence))

    def records(self) -> list[TemporalFactRecord]:
        return self.all_records()

    @staticmethod
    def _match_id(actual: str | None, expected: Any) -> bool:
        if expected is None:
            return True
        if isinstance(expected, bool):
            return False
        if isinstance(expected, Integral):
            return actual == str(int(expected))
        return actual == str(expected).strip()

    def query(
        self,
        *,
        source_id: str | None = None,
        continuity_segment: int | None = None,
        subject_id: str | int | None = None,
        object_id: str | int | None = None,
        label: str | None = None,
        fact_types: Iterable[str] | str | None = None,
        newest_first: bool = False,
    ) -> list[TemporalFactRecord]:
        if continuity_segment is not None:
            if isinstance(continuity_segment, bool) or not isinstance(continuity_segment, Integral) or continuity_segment < 0:
                raise ValueError("continuity_segment must be a non-negative integer")
            continuity_segment = int(continuity_segment)
        wanted_types: set[str] | None
        if fact_types is None:
            wanted_types = None
        elif isinstance(fact_types, str):
            wanted_types = {fact_types}
        else:
            wanted_types = {str(item) for item in fact_types}
        normalized_label = label.casefold().strip() if isinstance(label, str) else None
        rows = [
            item
            for item in self._records
            if (source_id is None or item.source_id == str(source_id).strip())
            and (continuity_segment is None or item.continuity_segment == continuity_segment)
            and self._match_id(item.subject_id, subject_id)
            and self._match_id(item.object_id, object_id)
            and (normalized_label is None or normalized_label in {x.casefold() for x in (item.subject_label, item.object_label) if x})
            and (wanted_types is None or item.fact_type in wanted_types)
        ]
        rows.sort(key=lambda item: (item.timestamp, item.sequence), reverse=newest_first)
        return rows

    def recent_actions(self, limit: int = 20, **filters: Any) -> list[TemporalFactRecord]:
        if isinstance(limit, bool) or not isinstance(limit, Integral) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        filters.setdefault("fact_types", self.fact_types)
        return self.query(newest_first=True, **filters)[: int(limit)]

    def last_action(self, **filters: Any) -> TemporalFactRecord | None:
        filters.setdefault("fact_types", self.fact_types)
        rows = self.query(newest_first=True, **filters)
        return rows[0] if rows else None

    def timeline(
        self,
        subject_id: str | int | None = None,
        *,
        source_id: str | None = None,
        continuity_segment: int | None = None,
        object_id: str | int | None = None,
        label: str | None = None,
        fact_types: Iterable[str] | str | None = None,
    ) -> list[TemporalFactRecord]:
        return self.query(
            source_id=source_id,
            continuity_segment=continuity_segment,
            subject_id=subject_id,
            object_id=object_id,
            label=label,
            fact_types=fact_types,
        )

    def timeline_for_identity(
        self,
        source_id: str,
        continuity_segment: int,
        identity: str | int,
    ) -> list[TemporalFactRecord]:
        return self.timeline(source_id=source_id, continuity_segment=continuity_segment, subject_id=identity)

    def last_seen_object_candidates(self, label: str, *, source_id: str | None = None) -> list[ObjectMemoryRecord]:
        return self.visual_memory.last_seen_candidates(label, source_id=source_id)


# Friendly aliases for callers that use the shorter name.
TemporalMemory = TemporalVisualMemory
TemporalMemoryRecord = TemporalFactRecord

