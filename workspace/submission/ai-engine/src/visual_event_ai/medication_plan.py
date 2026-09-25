"""Schedule-aware, review-only medication-plan comparison.

This module compares explicit medication-associated visual evidence with a
user-configured plan.  It never infers swallowing, dose correctness, medical
treatment or diagnosis.  Outputs are deterministic review cues carrying the
source/time/continuity evidence that produced them.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from math import isfinite
from numbers import Real
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .algorithm_reasoner import MedicationSequenceReasoner
from .models import PrimitiveFact


def _strict_text(value: Any, field: str, *, allow_none: bool = False) -> str | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _strict_non_negative(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field} must be a finite non-negative number")
    result = float(value)
    if not isfinite(result) or result < 0:
        raise ValueError(f"{field} must be a finite non-negative number")
    return result


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, bool) or not isinstance(value, (datetime, str)):
        raise ValueError("scheduled_at must be a timezone-aware datetime or ISO string")
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("scheduled_at must be a valid ISO timestamp") from exc
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("scheduled_at must include an explicit timezone")
    return value.astimezone(timezone.utc)


def _parse_local_time(value: Any) -> time:
    if isinstance(value, time):
        if value.tzinfo is not None:
            raise ValueError("scheduled_local_time must not contain an inline timezone")
        return value.replace(tzinfo=None)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("scheduled_local_time must be HH:MM or HH:MM:SS")
    try:
        parsed = time.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError("scheduled_local_time must be HH:MM or HH:MM:SS") from exc
    if parsed.tzinfo is not None:
        raise ValueError("scheduled_local_time must not contain an inline timezone")
    return parsed.replace(tzinfo=None)


class MedicationPlanEntry(BaseModel):
    """One JSON-friendly schedule entry with explicit timing semantics."""

    model_config = ConfigDict(extra="forbid")

    entry_id: str = Field(min_length=1)
    medicine_label: str = Field(min_length=1)
    medicine_identity: str | None = None
    scheduled_at: datetime | None = None
    scheduled_local_time: str | None = None
    timezone: str = "UTC"
    early_tolerance_seconds: float = 0.0
    late_tolerance_seconds: float = 0.0
    note: str | None = None
    dose: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_and_validate(cls, value: Any) -> dict[str, Any]:
        if not isinstance(value, Mapping):
            raise ValueError("medication plan entry must be an object")
        data = dict(value)
        aliases = {
            "id": "entry_id",
            "plan_id": "entry_id",
            "medicine": "medicine_label",
            "label": "medicine_label",
            "medicine_id": "medicine_identity",
            "scheduled_time_local": "scheduled_local_time",
            "early_tolerance": "early_tolerance_seconds",
            "late_tolerance": "late_tolerance_seconds",
            "schedule_timezone": "timezone",
        }
        for alias, target in aliases.items():
            if target not in data and alias in data:
                data[target] = data[alias]
            data.pop(alias, None)
        data["entry_id"] = _strict_text(data.get("entry_id"), "entry_id")
        data["medicine_label"] = _strict_text(data.get("medicine_label"), "medicine_label")
        if "medicine_identity" in data and data["medicine_identity"] is not None:
            data["medicine_identity"] = _strict_text(data["medicine_identity"], "medicine_identity")
        if "scheduled_at" not in data and "scheduled_time" in data:
            scheduled_value = data["scheduled_time"]
            if isinstance(scheduled_value, datetime) or (isinstance(scheduled_value, str) and ("T" in scheduled_value or "-" in scheduled_value)):
                data["scheduled_at"] = scheduled_value
            else:
                data["scheduled_local_time"] = scheduled_value
        data.pop("scheduled_time", None)
        if "tolerance_seconds" in data:
            data.setdefault("early_tolerance_seconds", data["tolerance_seconds"])
            data.setdefault("late_tolerance_seconds", data["tolerance_seconds"])
        data.pop("tolerance_seconds", None)
        scheduled_at = data.get("scheduled_at")
        local_time = data.get("scheduled_local_time")
        if scheduled_at is None and local_time is None:
            raise ValueError("provide exactly one of scheduled_at or scheduled_local_time")
        if scheduled_at is not None and local_time is not None:
            raise ValueError("scheduled_at and scheduled_local_time are mutually exclusive")
        if scheduled_at is not None:
            data["scheduled_at"] = _parse_timestamp(scheduled_at)
        else:
            data["scheduled_local_time"] = _parse_local_time(local_time).isoformat()
        data["timezone"] = _strict_text(data.get("timezone", "UTC"), "timezone") or "UTC"
        try:
            ZoneInfo(data["timezone"])
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("timezone must be an installed IANA timezone") from exc
        data["early_tolerance_seconds"] = _strict_non_negative(
            data.get("early_tolerance_seconds", 0.0), "early_tolerance_seconds"
        )
        data["late_tolerance_seconds"] = _strict_non_negative(
            data.get("late_tolerance_seconds", 0.0), "late_tolerance_seconds"
        )
        for field in ("note", "dose"):
            if field in data and data[field] is not None and not isinstance(data[field], str):
                raise ValueError(f"{field} must be a string when provided")
        return data

    @property
    def scheduled_clock(self) -> time | None:
        if self.scheduled_local_time is None:
            return None
        return _parse_local_time(self.scheduled_local_time)

    def scheduled_for(self, observed_at: datetime) -> datetime:
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        observed_at = observed_at.astimezone(timezone.utc)
        if self.scheduled_at is not None:
            return _parse_timestamp(self.scheduled_at)
        local = observed_at.astimezone(ZoneInfo(self.timezone))
        clock = self.scheduled_clock or time(0, 0)
        return datetime.combine(local.date(), clock, tzinfo=ZoneInfo(self.timezone)).astimezone(timezone.utc)


class MedicationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entries: list[MedicationPlanEntry] = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def _accept_entry_list(cls, value: Any) -> Any:
        if isinstance(value, list):
            return {"entries": value}
        return value

    @model_validator(mode="after")
    def _unique_ids(self) -> MedicationPlan:
        ids = [entry.entry_id for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("medication plan entry_id values must be unique")
        return self

    @classmethod
    def from_json(cls, value: str) -> MedicationPlan:
        return cls.model_validate_json(value)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _safe_id(entity: Mapping[str, Any] | None) -> str | None:
    if not isinstance(entity, Mapping):
        return None
    value = entity.get("track_id")
    if value is None or (isinstance(value, str) and not value.strip()):
        value = entity.get("id")
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _source_scope(fact: PrimitiveFact) -> tuple[str | None, int | None] | None:
    metadata = fact.metadata if isinstance(fact.metadata, Mapping) else {}
    source = metadata.get("source_id")
    if source is not None and (not isinstance(source, str) or not source.strip()):
        return None
    segment = metadata.get("continuity_segment")
    if segment is not None and (isinstance(segment, bool) or not isinstance(segment, int) or segment < 0):
        return None
    return (source.strip() if isinstance(source, str) else None, segment)


def _medication_actions(facts: list[PrimitiveFact]) -> list[PrimitiveFact]:
    """Return unique medication-associated action evidence in one scope."""

    candidates: list[PrimitiveFact] = []
    for fact in facts:
        if fact.fact_type not in {"hand_to_face", "hand_near_mouth", "object_to_face"}:
            continue
        if _source_scope(fact) is None:
            continue
        obj = fact.object if isinstance(fact.object, Mapping) else None
        # The configured plan is the authority for the accepted medicine
        # vocabulary.  Do not discard an explicit object label merely because
        # the generic label helper does not know a newly configured medicine;
        # an incompatible label is reported as ``wrong_item_candidate``.
        if not isinstance(obj, Mapping) or (not _safe_id(obj) and not str(obj.get("label", "")).strip()):
            continue
        candidates.append(fact)
    candidates.sort(key=lambda item: _utc(item.timestamp))
    result: list[PrimitiveFact] = []
    seen: set[tuple[Any, ...]] = set()
    for fact in candidates:
        scope = _source_scope(fact)
        subject_id = _safe_id(fact.subject)
        object_id = _safe_id(fact.object)
        # Timestamp is part of the identity; exact repeated facts are
        # deduplicated without collapsing distinct same-label objects.
        key = (
            scope,
            subject_id,
            object_id,
            _utc(fact.timestamp),
            (fact.object or {}).get("label"),
            # Two label-only observations at the same instant remain
            # separate candidates so the evaluator can report ambiguity.
            id(fact) if object_id is None else None,
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(fact)
    return result


@dataclass(frozen=True)
class MedicationPlanReview:
    cue: str
    entry_id: str | None
    observed_at: datetime
    source_id: str | None
    continuity_segment: int | None
    confidence: float
    subject: dict[str, Any] | None
    object: dict[str, Any] | None
    evidence_facts: tuple[PrimitiveFact, ...] = field(default_factory=tuple, repr=False, compare=False)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return self.cue

    @property
    def status(self) -> str:
        return self.cue

    @property
    def evidence(self) -> tuple[PrimitiveFact, ...]:
        return self.evidence_facts

    @property
    def evidence_fact_types(self) -> tuple[str, ...]:
        return tuple(fact.fact_type for fact in self.evidence_facts)

    def as_dict(self) -> dict[str, Any]:
        return {
            "cue": self.cue,
            "event_type": self.event_type,
            "entry_id": self.entry_id,
            "observed_at": self.observed_at.isoformat(),
            "source_id": self.source_id,
            "continuity_segment": self.continuity_segment,
            "confidence": self.confidence,
            "subject": self.subject,
            "object": self.object,
            "evidence_fact_types": list(self.evidence_fact_types),
            "metadata": dict(self.metadata),
        }


class MedicationPlanEvaluator:
    """Compare medication action evidence against a validated plan."""

    def __init__(
        self,
        plan: MedicationPlan | Mapping[str, Any] | Iterable[MedicationPlanEntry],
        *,
        debounce_seconds: float = 2.0,
    ) -> None:
        if isinstance(plan, MedicationPlan):
            self.plan = plan
        elif isinstance(plan, Mapping):
            self.plan = MedicationPlan.model_validate(plan)
        else:
            self.plan = MedicationPlan(entries=list(plan))
        if isinstance(debounce_seconds, bool) or not isinstance(debounce_seconds, Real):
            raise ValueError("debounce_seconds must be a finite non-negative number")
        debounce = float(debounce_seconds)
        if not isfinite(debounce) or debounce < 0:
            raise ValueError("debounce_seconds must be a finite non-negative number")
        self.debounce = timedelta(seconds=debounce)

    @staticmethod
    def _compatible(entry: MedicationPlanEntry, fact: PrimitiveFact) -> bool:
        obj = fact.object if isinstance(fact.object, Mapping) else {}
        label = str(obj.get("label", "")).strip().casefold()
        identity = _safe_id(obj)
        if entry.medicine_identity is not None:
            if identity is not None:
                return identity == entry.medicine_identity
            # If the stream has not assigned an identity, a configured label
            # may still be compared, but never invent an identity match.
            return False
        expected = entry.medicine_label.casefold().strip()
        return bool(label and (label == expected or label in expected or expected in label))

    @staticmethod
    def _confidence(facts: tuple[PrimitiveFact, ...]) -> float:
        values: list[float] = []
        for fact in facts:
            if isinstance(fact.confidence, bool) or not isinstance(fact.confidence, Real):
                raise ValueError("medication plan fact confidence must be numeric")
            value = float(fact.confidence)
            if not isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError("medication plan fact confidence must be finite and between 0 and 1")
            values.append(value)
        return round(min(values), 3) if values else 0.0

    def _review_for(
        self,
        cue: str,
        entry: MedicationPlanEntry | None,
        evidence: tuple[PrimitiveFact, ...],
        observed_at: datetime,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> MedicationPlanReview:
        scope = _source_scope(evidence[0]) if evidence else (None, None)
        first = evidence[0] if evidence else None
        details: dict[str, Any] = {
            "review_required": True,
            "medical_diagnosis": False,
            "evidence_level": "review_candidate",
        }
        if entry is not None:
            details["entry_id"] = entry.entry_id
            details["medicine_label"] = entry.medicine_label
            # User metadata is echoed verbatim as configuration only; it is
            # never presented as a visual inference.
            if entry.note is not None:
                details["plan_note"] = entry.note
            if entry.dose is not None:
                details["plan_dose"] = entry.dose
        details.update(dict(metadata or {}))
        return MedicationPlanReview(
            cue=cue,
            entry_id=entry.entry_id if entry else None,
            observed_at=_utc(observed_at),
            source_id=scope[0],
            continuity_segment=scope[1],
            confidence=self._confidence(evidence),
            subject=dict(first.subject) if isinstance(first and first.subject, Mapping) else None,
            object=dict(first.object) if isinstance(first and first.object, Mapping) else None,
            evidence_facts=evidence,
            metadata=details,
        )

    def evaluate(
        self,
        facts: Iterable[PrimitiveFact],
        *,
        observed_at: datetime | None = None,
    ) -> list[MedicationPlanReview]:
        ordered = sorted(list(facts), key=lambda item: _utc(item.timestamp))
        actions = _medication_actions(ordered)
        # MedicationSequenceReasoner supplies the stronger same-person/object
        # and source/continuity pairing when pickup evidence exists.  Direct
        # medication action facts remain valid review evidence for streams that
        # begin after the pickup frame.
        complete = MedicationSequenceReasoner().infer(ordered)
        evidence_events: list[tuple[PrimitiveFact, ...]] = []
        for event in complete:
            evidence_events.append(tuple(event.evidence_facts))
        for action in actions:
            if not any(action in evidence for evidence in evidence_events):
                evidence_events.append((action,))

        # Debounce repeated action facts from one scope/episode while retaining
        # distinct object IDs and continuity segments.
        debounced: list[tuple[PrimitiveFact, ...]] = []
        last_by_scope: dict[tuple[Any, ...], datetime] = {}
        for evidence in evidence_events:
            anchor = evidence[-1]
            scope = _source_scope(anchor)
            key = (scope, _safe_id(anchor.subject), _safe_id(anchor.object), (anchor.object or {}).get("label"))
            timestamp = _utc(anchor.timestamp)
            previous = last_by_scope.get(key)
            if previous is not None and timestamp - previous <= self.debounce:
                continue
            last_by_scope[key] = timestamp
            debounced.append(evidence)

        reviews: list[MedicationPlanReview] = []
        used_entries: set[str] = set()
        ambiguous_episode_keys: set[tuple[Any, ...]] = set()
        episode_objects: dict[tuple[Any, ...], set[str | None]] = {}
        episode_counts: dict[tuple[Any, ...], int] = {}
        blocked_actions: set[int] = set()
        interactions = {"object_picked", "pickup_candidate", "near"}
        for action in actions:
            action_scope = _source_scope(action)
            action_subject = _safe_id(action.subject)
            action_object = _safe_id(action.object)
            for earlier in ordered:
                if earlier is action or _utc(earlier.timestamp) > _utc(action.timestamp):
                    continue
                if earlier.fact_type not in interactions:
                    continue
                if _safe_id(earlier.subject) != action_subject or _safe_id(earlier.object) != action_object:
                    continue
                if _source_scope(earlier) != action_scope:
                    blocked_actions.add(id(action))
                    break
        for evidence in debounced:
            anchor = evidence[-1]
            episode_key = (
                _source_scope(anchor),
                _safe_id(anchor.subject),
                _utc(anchor.timestamp),
                str((anchor.object or {}).get("label", "")).casefold(),
            )
            episode_objects.setdefault(episode_key, set()).add(_safe_id(anchor.object))
            episode_counts[episode_key] = episode_counts.get(episode_key, 0) + 1
        for episode_key, object_ids in episode_objects.items():
            if len(object_ids) > 1 or (len(object_ids) == 1 and None in object_ids and episode_counts[episode_key] > 1):
                ambiguous_episode_keys.add(episode_key)
        for evidence in debounced:
            anchor = evidence[-1]
            at = _utc(observed_at or anchor.timestamp)
            episode_key = (
                _source_scope(anchor),
                _safe_id(anchor.subject),
                _utc(anchor.timestamp),
                str((anchor.object or {}).get("label", "")).casefold(),
            )
            if episode_key in ambiguous_episode_keys:
                reviews.append(
                    self._review_for(
                        "unresolved_candidate",
                        None,
                        evidence,
                        at,
                        metadata={"reason": "ambiguous_parallel_object_identity"},
                    )
                )
                continue
            if id(anchor) in blocked_actions:
                reviews.append(
                    self._review_for(
                        "unresolved_candidate",
                        None,
                        evidence,
                        at,
                        metadata={"reason": "cross_source_or_continuity_context"},
                    )
                )
                continue
            compatible = [entry for entry in self.plan.entries if entry.entry_id not in used_entries and self._compatible(entry, anchor)]
            if len(compatible) > 1:
                reviews.append(self._review_for("unresolved_candidate", None, evidence, at, metadata={"reason": "ambiguous_plan_entries"}))
                continue
            if not compatible:
                matching_labels = [entry for entry in self.plan.entries if self._compatible(entry, anchor)]
                cue = "wrong_item_candidate" if matching_labels == [] else "unresolved_candidate"
                reviews.append(self._review_for(cue, None, evidence, at, metadata={"reason": "incompatible_or_already_used_item"}))
                continue
            entry = compatible[0]
            scheduled = entry.scheduled_for(at)
            delta = (at - scheduled).total_seconds()
            if delta < -entry.early_tolerance_seconds:
                cue = "early_candidate"
            elif delta > entry.late_tolerance_seconds:
                cue = "late_candidate"
            else:
                cue = "plan_match_candidate"
            used_entries.add(entry.entry_id)
            reviews.append(
                self._review_for(
                    cue,
                    entry,
                    evidence,
                    at,
                    metadata={
                        "scheduled_at": scheduled.isoformat(),
                        "time_delta_seconds": round(delta, 3),
                    },
                )
            )
        if not reviews:
            default_time = observed_at or datetime(1970, 1, 1, tzinfo=timezone.utc)
            reviews.append(self._review_for("unresolved_candidate", None, (), _utc(default_time), metadata={"reason": "insufficient_evidence"}))
        return reviews

    def review(self, facts: Iterable[PrimitiveFact], *, observed_at: datetime | None = None) -> list[MedicationPlanReview]:
        return self.evaluate(facts, observed_at=observed_at)


MedicationPlanReviewEvaluator = MedicationPlanEvaluator
MedicationScheduleEvaluator = MedicationPlanEvaluator
MedicationPlanReviewer = MedicationPlanEvaluator
MedicationSchedule = MedicationPlan
MedicationPlanConfig = MedicationPlan
MedicationScheduleEntry = MedicationPlanEntry


def evaluate_medication_plan(
    plan: MedicationPlan | Mapping[str, Any] | Iterable[MedicationPlanEntry],
    facts: Iterable[PrimitiveFact],
    *,
    observed_at: datetime | None = None,
) -> list[MedicationPlanReview]:
    return MedicationPlanEvaluator(plan).evaluate(facts, observed_at=observed_at)
