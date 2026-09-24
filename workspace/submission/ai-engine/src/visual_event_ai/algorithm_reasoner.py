"""Explainable, time-ordered reasoning for scene events.

Frame-level detectors and trackers produce primitive facts; these reasoners
combine only explicitly associated facts into reviewable event candidates.
They are deterministic rule baselines, not trained recognition models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import math
from numbers import Integral, Real
from typing import Any, Iterable

from .entity_labels import is_medication_entity, is_person_entity
from .models import PrimitiveFact


@dataclass(frozen=True)
class EventCandidate:
    """A reviewable event hypothesis with its source facts attached."""

    event_type: str
    started_at: datetime
    ended_at: datetime
    confidence: float
    subject: dict[str, Any] | None
    object: dict[str, Any] | None
    evidence_fact_types: tuple[str, ...]
    location: str | None = None
    evidence_facts: tuple[PrimitiveFact, ...] = field(default_factory=tuple, repr=False, compare=False)
    metadata: dict[str, Any] = field(default_factory=dict)


def _utc(value: datetime) -> datetime:
    """Use UTC for comparisons; interpret legacy naive timestamps as UTC."""

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _raw_entity_id(entity: dict[str, Any] | None) -> Any:
    if not isinstance(entity, dict):
        return None
    value = entity.get("track_id")
    if value is None or (isinstance(value, str) and not value.strip()):
        value = entity.get("id")
    return value


def _normalized_entity_id(value: Any) -> str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, Integral):
        return str(int(value))
    return None


def _entity_key(entity: dict[str, Any] | None) -> str | None:
    value = _raw_entity_id(entity)
    if value is None:
        return None
    return _normalized_entity_id(value)


def _has_invalid_entity_id(entity: dict[str, Any] | None) -> bool:
    value = _raw_entity_id(entity)
    if value is None or (isinstance(value, str) and not value.strip()):
        return False
    return _normalized_entity_id(value) is None


def _label(entity: dict[str, Any] | None) -> str:
    return str(entity.get("label", "")).strip() if isinstance(entity, dict) else ""


def _dedup_entity_key(entity: dict[str, Any] | None) -> tuple[str, str] | None:
    entity_id = _entity_key(entity)
    if entity_id is not None:
        return ("id", entity_id)
    label = _label(entity).casefold()
    return ("label", label) if label else None


def _same_entity(first: dict[str, Any] | None, second: dict[str, Any] | None) -> bool:
    first_key = _entity_key(first)
    second_key = _entity_key(second)
    return first_key is not None and first_key == second_key


def _same_object(first: dict[str, Any] | None, second: dict[str, Any] | None) -> bool:
    """Match object IDs exactly, using labels only when neither ID exists."""

    if _has_invalid_entity_id(first) or _has_invalid_entity_id(second):
        return False
    first_key = _entity_key(first)
    second_key = _entity_key(second)
    if first_key is not None or second_key is not None:
        return first_key is not None and first_key == second_key
    first_label = _label(first).casefold()
    second_label = _label(second).casefold()
    return bool(first_label and first_label == second_label)


def _is_person(entity: dict[str, Any] | None) -> bool:
    return is_person_entity(entity)


def _has_person_evidence(entity: dict[str, Any] | None) -> bool:
    if _is_person(entity):
        return True
    # Older action facts may carry a stable subject ID without a label. Keep
    # that explicit legacy form, but do not treat a known non-person class as
    # a person merely because it has an ID.
    return not _label(entity) and _entity_key(entity) is not None


def _is_medication_object(entity: dict[str, Any] | None) -> bool:
    return is_medication_entity(entity)


def _fact_confidence(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("fact confidence must be a finite non-Boolean number between 0 and 1")
    try:
        confidence = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("fact confidence must be a finite non-Boolean number between 0 and 1") from exc
    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        raise ValueError("fact confidence must be a finite non-Boolean number between 0 and 1")
    return confidence


def _confidence(facts: Iterable[PrimitiveFact]) -> float:
    """Use the weakest required fact as the confidence of the conjunction."""

    values = [_fact_confidence(fact.confidence) for fact in facts]
    return round(min(values), 3) if values else 0.0


def _continuity_segment(fact: PrimitiveFact) -> int | None:
    value = fact.metadata.get("continuity_segment", 0)
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
        return None
    return int(value)


def _same_continuity_segment(first: PrimitiveFact, second: PrimitiveFact) -> bool:
    first_segment = _continuity_segment(first)
    second_segment = _continuity_segment(second)
    return first_segment is not None and first_segment == second_segment


def _fact_source_signature(fact: PrimitiveFact) -> tuple[str, str | None]:
    """Return a conservative source provenance signature for a fact.

    Older fixtures may not carry provenance metadata, so a missing source is
    treated as unknown and remains compatible with a known source. An explicit
    malformed source is different: it cannot be used as evidence for a
    cross-fact inference.
    """

    metadata = fact.metadata
    if not isinstance(metadata, dict) or "source_id" not in metadata:
        return "missing", None
    value = metadata.get("source_id")
    if not isinstance(value, str) or not value.strip():
        return "invalid", None
    return "valid", value.strip()


def _same_fact_source(first: PrimitiveFact, second: PrimitiveFact) -> bool:
    """Allow only same-source evidence, while preserving legacy unknown facts."""

    first_state, first_source = _fact_source_signature(first)
    second_state, second_source = _fact_source_signature(second)
    if "invalid" in {first_state, second_state}:
        return False
    if first_state == "valid" and second_state == "valid":
        return first_source == second_source
    return True


def _fact_source_key(fact: PrimitiveFact) -> tuple[str, str | None]:
    """Make pending state keys source-aware without rejecting legacy facts."""

    state, source = _fact_source_signature(fact)
    if state == "invalid":
        # Keep malformed facts isolated from one another. They can still be
        # surfaced as single-fact candidates, but never paired as evidence.
        return state, str(id(fact))
    return state, source


def _validate_thresholds(*, duration: float, confidence: float, duration_name: str) -> None:
    if isinstance(duration, bool) or not isinstance(duration, Real):
        raise ValueError(f"{duration_name} must be a finite positive number")
    try:
        duration_value = float(duration)
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"{duration_name} must be a finite positive number") from exc
    if not math.isfinite(duration_value) or duration_value <= 0:
        raise ValueError(f"{duration_name} must be a finite positive number")
    try:
        timedelta(seconds=duration_value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{duration_name} exceeds the supported duration range") from exc
    if isinstance(confidence, bool) or not isinstance(confidence, Real):
        raise ValueError("min_confidence must be a finite number between 0 and 1")
    try:
        confidence_value = float(confidence)
    except (ValueError, OverflowError) as exc:
        raise ValueError("min_confidence must be a finite number between 0 and 1") from exc
    if not math.isfinite(confidence_value) or not 0.0 <= confidence_value <= 1.0:
        raise ValueError("min_confidence must be a finite number between 0 and 1")


def _ordered(facts: Iterable[PrimitiveFact]) -> list[PrimitiveFact]:
    ordered = list(facts)
    for fact in ordered:
        _fact_confidence(fact.confidence)
    return sorted(ordered, key=lambda fact: _utc(fact.timestamp))


def _candidate_scope(candidate: EventCandidate) -> tuple[str, str] | None:
    if candidate.event_type not in {"object_removed", "object_returned", "object_missing"}:
        return None
    for fact in reversed(candidate.evidence_facts):
        raw_zone_id = fact.metadata.get("zone_id")
        zone_id = str(raw_zone_id).strip() if raw_zone_id is not None else ""
        if zone_id:
            return ("zone_id", zone_id)
        location = (fact.location or "").strip().casefold()
        if location:
            return ("location", location)
    return None


def _deduplicate(candidates: list[EventCandidate]) -> list[EventCandidate]:
    seen: set[
        tuple[
            str,
            tuple[str, str] | None,
            tuple[str, str] | None,
            datetime,
            tuple[str, str] | None,
        ]
    ] = set()
    result: list[EventCandidate] = []
    for candidate in candidates:
        key = (
            candidate.event_type,
            _dedup_entity_key(candidate.subject),
            _dedup_entity_key(candidate.object),
            _utc(candidate.started_at),
            _candidate_scope(candidate),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(candidate)
    return result


class MedicationSequenceReasoner:
    """Recognise conservative medication-related cues.

    A complete candidate requires an explicitly medication-like object, a
    person/object interaction (pickup or confirmed proximity fact), then a
    matching hand-to-face fact from the same person and object. Put-down is
    optional supporting evidence. Partial pickup sequences are available via
    :meth:`infer_incomplete` and remain review-only cues.
    """

    _interaction_types = {"object_picked", "pickup_candidate", "near"}
    _incomplete_anchor_types = {"object_picked", "pickup_candidate"}
    _hand_types = {"hand_to_face", "hand_near_mouth", "object_to_face"}
    _put_down_types = {"object_put_down", "putdown_candidate"}

    def __init__(self, *, max_sequence_seconds: float = 45.0, min_confidence: float = 0.45) -> None:
        _validate_thresholds(
            duration=max_sequence_seconds,
            confidence=min_confidence,
            duration_name="max_sequence_seconds",
        )
        self.max_sequence = timedelta(seconds=float(max_sequence_seconds))
        self.min_confidence = float(min_confidence)

    def _person_and_object_interactions(
        self, ordered: list[PrimitiveFact], *, allowed_types: set[str]
    ) -> list[PrimitiveFact]:
        return [
            fact
            for fact in ordered
            if fact.fact_type in allowed_types
            and _is_medication_object(fact.object)
            and fact.subject is not None
            and _has_person_evidence(fact.subject)
        ]

    def _matching_hand(
        self,
        anchor: PrimitiveFact,
        ordered: list[PrimitiveFact],
        *,
        min_confidence: float | None = None,
    ) -> PrimitiveFact | None:
        anchor_time = _utc(anchor.timestamp)
        for fact in ordered:
            fact_time = _utc(fact.timestamp)
            if fact_time <= anchor_time:
                continue
            if fact_time - anchor_time > self.max_sequence:
                break
            if not _same_fact_source(anchor, fact):
                continue
            if not _same_continuity_segment(anchor, fact):
                continue
            if min_confidence is not None and fact.confidence < min_confidence:
                continue
            if (
                fact.fact_type in self._hand_types
                and _same_entity(anchor.subject, fact.subject)
                and _same_object(anchor.object, fact.object)
            ):
                return fact
        return None

    def infer(self, facts: Iterable[PrimitiveFact]) -> list[EventCandidate]:
        ordered = _ordered(facts)
        anchors = self._person_and_object_interactions(ordered, allowed_types=self._interaction_types)
        candidates: list[EventCandidate] = []
        used_hands: set[int] = set()

        for anchor in anchors:
            hand = self._matching_hand(anchor, ordered, min_confidence=self.min_confidence)
            if hand is None or id(hand) in used_hands:
                continue
            evidence = [anchor, hand]
            supporting = next(
                (
                    fact
                    for fact in ordered
                    if fact.fact_type in self._put_down_types
                    and fact.confidence >= self.min_confidence
                    and _utc(fact.timestamp) >= _utc(hand.timestamp)
                    and _utc(fact.timestamp) - _utc(anchor.timestamp) <= self.max_sequence
                    and _same_fact_source(anchor, fact)
                    and _same_fact_source(hand, fact)
                    and _same_continuity_segment(anchor, fact)
                    and _same_entity(anchor.subject, fact.subject)
                    and _same_object(anchor.object, fact.object)
                ),
                None,
            )
            if supporting is not None:
                evidence.append(supporting)
            confidence = _confidence(evidence)
            if confidence < self.min_confidence:
                continue
            used_hands.add(id(hand))
            evidence_tuple = tuple(evidence)
            candidates.append(
                EventCandidate(
                    event_type="suspected_medication",
                    started_at=_utc(anchor.timestamp),
                    ended_at=_utc(supporting.timestamp if supporting else hand.timestamp),
                    confidence=confidence,
                    subject=anchor.subject,
                    object=anchor.object,
                    evidence_fact_types=tuple(fact.fact_type for fact in evidence_tuple),
                    location=hand.location or anchor.location,
                    evidence_facts=evidence_tuple,
                    metadata={
                        "reasoner": "medication-sequence-v2",
                        "review_required": True,
                        "medical_diagnosis": False,
                        "sequence_complete": True,
                        "put_down_observed": supporting is not None,
                        "sequence_duration_seconds": round(
                            (_utc(hand.timestamp) - _utc(anchor.timestamp)).total_seconds(), 3
                        ),
                    },
                )
            )
        return _deduplicate(candidates)

    def infer_incomplete(self, facts: Iterable[PrimitiveFact]) -> list[EventCandidate]:
        """Return pickup cues with no matching hand-to-face fact in the window."""

        ordered = _ordered(facts)
        anchors = self._person_and_object_interactions(ordered, allowed_types=self._incomplete_anchor_types)
        candidates: list[EventCandidate] = []
        for anchor in anchors:
            if anchor.confidence < self.min_confidence or self._matching_hand(anchor, ordered) is not None:
                continue
            timestamp = _utc(anchor.timestamp)
            candidates.append(
                EventCandidate(
                    event_type="incomplete_medication_sequence",
                    started_at=timestamp,
                    ended_at=timestamp,
                    confidence=_confidence((anchor,)),
                    subject=anchor.subject,
                    object=anchor.object,
                    evidence_fact_types=(anchor.fact_type,),
                    location=anchor.location,
                    evidence_facts=(anchor,),
                    metadata={
                        "reasoner": "medication-sequence-v2",
                        "review_required": True,
                        "medical_diagnosis": False,
                        "sequence_complete": False,
                        "missing_step": "hand_to_face",
                    },
                )
            )
        return _deduplicate(candidates)


class WorkshopStateReasoner:
    """Infer object state changes from removal, return, and observed absence."""

    _removed_types = {"object_removed", "left_zone"}
    _returned_types = {"object_returned", "entered_zone"}
    _observation_types = {"scene_observed"}

    def __init__(self, *, missing_after_seconds: float = 120.0, min_confidence: float = 0.4) -> None:
        _validate_thresholds(
            duration=missing_after_seconds,
            confidence=min_confidence,
            duration_name="missing_after_seconds",
        )
        self.missing_after = timedelta(seconds=float(missing_after_seconds))
        self.min_confidence = float(min_confidence)

    def _make_candidate(
        self,
        event_type: str,
        evidence: tuple[PrimitiveFact, ...],
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EventCandidate:
        anchor = evidence[0]
        last = evidence[-1]
        anchor_object = anchor.object
        if anchor_object is None and anchor.fact_type in {"left_zone", "entered_zone"}:
            anchor_object = anchor.subject
        last_object = last.object
        if last_object is None and last.fact_type in {"left_zone", "entered_zone"}:
            last_object = last.subject
        anchor_subject = None if anchor.fact_type in {"left_zone", "entered_zone"} else anchor.subject
        last_subject = None if last.fact_type in {"left_zone", "entered_zone"} else last.subject
        return EventCandidate(
            event_type=event_type,
            started_at=_utc(start or anchor.timestamp),
            ended_at=_utc(end or last.timestamp),
            confidence=_confidence(evidence),
            subject=anchor_subject or last_subject,
            object=anchor_object or last_object,
            evidence_fact_types=tuple(fact.fact_type for fact in evidence),
            location=last.location if event_type == "object_returned" else anchor.location or last.location,
            evidence_facts=evidence,
            metadata={
                "reasoner": "workshop-state-v2",
                "review_required": event_type == "object_missing",
                **(metadata or {}),
            },
        )

    @staticmethod
    def _state_object_key(fact: PrimitiveFact) -> str | None:
        entity = fact.object
        if entity is None and fact.fact_type in {"left_zone", "entered_zone"}:
            entity = fact.subject
        if fact.fact_type in {"left_zone", "entered_zone"} and _is_person(entity):
            return None
        return _entity_key(entity)

    @staticmethod
    def _same_zone(previous: PrimitiveFact, current: PrimitiveFact) -> bool:
        previous_value = previous.metadata.get("zone_id")
        current_value = current.metadata.get("zone_id")
        previous_zone = str(previous_value).strip() if previous_value is not None else ""
        current_zone = str(current_value).strip() if current_value is not None else ""
        if previous_zone or current_zone:
            return bool(previous_zone) and previous_zone == current_zone
        previous_location = (previous.location or "").strip().casefold()
        current_location = (current.location or "").strip().casefold()
        return bool(previous_location and previous_location == current_location)

    @staticmethod
    def _zone_scope(fact: PrimitiveFact) -> tuple[str, str] | None:
        raw_zone_id = fact.metadata.get("zone_id")
        zone_id = str(raw_zone_id).strip() if raw_zone_id is not None else ""
        if zone_id:
            return ("zone_id", zone_id)
        location = (fact.location or "").strip().casefold()
        return ("location", location) if location else None

    @classmethod
    def _observation_matches_zone(
        cls,
        removed: PrimitiveFact,
        observation: PrimitiveFact,
    ) -> bool:
        removed_scope = cls._zone_scope(removed)
        observed_scope = cls._zone_scope(observation)
        if removed_scope is None or observed_scope is None:
            return True
        return cls._same_zone(removed, observation)

    @classmethod
    def _latest_pending_key(
        cls,
        last_removed: dict[tuple[str, tuple[str, str] | None, tuple[str, str | None]], PrimitiveFact],
        object_key: str,
        *,
        matching_zone: PrimitiveFact | None = None,
        matching_segment: PrimitiveFact | None = None,
        matching_source: PrimitiveFact | None = None,
        before_timestamp: datetime | None = None,
    ) -> tuple[str, tuple[str, str] | None, tuple[str, str | None]] | None:
        eligible = [
            state_key
            for state_key, removed in last_removed.items()
            if state_key[0] == object_key
            and (matching_zone is None or cls._same_zone(removed, matching_zone))
            and (matching_source is None or _same_fact_source(removed, matching_source))
            and (matching_segment is None or _same_continuity_segment(removed, matching_segment))
            and (
                before_timestamp is None
                or _utc(removed.timestamp) < _utc(before_timestamp)
            )
        ]
        return max(eligible, key=lambda key: _utc(last_removed[key].timestamp), default=None)

    def infer(self, facts: Iterable[PrimitiveFact]) -> list[EventCandidate]:
        ordered = _ordered(facts)
        candidates: list[EventCandidate] = []
        last_removed: dict[tuple[str, tuple[str, str] | None, tuple[str, str | None]], PrimitiveFact] = {}

        for fact in ordered:
            if fact.fact_type == "observation_gap":
                last_removed.clear()
                continue
            if fact.confidence < self.min_confidence:
                continue
            object_key = self._state_object_key(fact)
            if object_key is not None and fact.fact_type in self._removed_types:
                state_key = (object_key, self._zone_scope(fact), _fact_source_key(fact))
                last_removed[state_key] = fact
                candidates.append(self._make_candidate("object_removed", (fact,)))
            elif object_key is not None and fact.fact_type in self._returned_types:
                previous_key = self._latest_pending_key(
                    last_removed,
                    object_key,
                    matching_zone=fact if fact.fact_type == "entered_zone" else None,
                    matching_segment=fact,
                    matching_source=fact,
                    before_timestamp=fact.timestamp,
                )
                previous = last_removed.get(previous_key) if previous_key is not None else None
                if fact.fact_type == "entered_zone" and previous is None:
                    continue
                if previous_key is not None:
                    del last_removed[previous_key]
                evidence = (previous, fact) if previous is not None else (fact,)
                candidates.append(
                    self._make_candidate(
                        "object_returned",
                        evidence,
                        start=previous.timestamp if previous else fact.timestamp,
                    )
                )
            elif object_key is not None and fact.fact_type == "object_missing":
                missing_scope = fact if self._zone_scope(fact) is not None else None
                previous_key = self._latest_pending_key(
                    last_removed,
                    object_key,
                    matching_zone=missing_scope,
                    matching_segment=fact,
                    matching_source=fact,
                    before_timestamp=fact.timestamp,
                )
                previous = last_removed.pop(previous_key, None) if previous_key is not None else None
                evidence = (previous, fact) if previous is not None else (fact,)
                candidates.append(
                    self._make_candidate(
                        "object_missing",
                        evidence,
                        start=previous.timestamp if previous else fact.timestamp,
                        metadata={"missing_policy": "explicit_fact"},
                    )
                )

            if fact.fact_type not in self._observation_types:
                continue
            observed_at = _utc(fact.timestamp)
            for state_key, removed in list(last_removed.items()):
                if not _same_fact_source(removed, fact):
                    continue
                if not _same_continuity_segment(removed, fact):
                    continue
                if not self._observation_matches_zone(removed, fact):
                    continue
                if observed_at - _utc(removed.timestamp) < self.missing_after:
                    continue
                candidates.append(
                    self._make_candidate(
                        "object_missing",
                        (removed, fact),
                        start=removed.timestamp,
                        end=fact.timestamp,
                        metadata={
                            "missing_policy": "observed_timeout",
                            "missing_after_seconds": self.missing_after.total_seconds(),
                        },
                    )
                )
                del last_removed[state_key]

        return _deduplicate(candidates)
