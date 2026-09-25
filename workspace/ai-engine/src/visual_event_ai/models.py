from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from math import isfinite
from numbers import Real
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_numeric_list(value: Any, field_name: str, *, nested: bool = False) -> Any:
    if value is None or not isinstance(value, (list, tuple)):
        return value
    values = (
        [item for row in value if isinstance(row, (list, tuple)) for item in row]
        if nested
        else value
    )
    if any(isinstance(item, bool) or not isinstance(item, Real) for item in values):
        raise ValueError(f"{field_name} values must be numeric non-Boolean values")
    return value


def _validate_real_number(value: Any, field_name: str) -> Any:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field_name} must be a real number")
    return value


def _validate_confidence(value: Any, field_name: str = "confidence") -> Any:
    value = _validate_real_number(value, field_name)
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field_name} must be finite and between 0 and 1") from exc
    if not isfinite(numeric) or not 0.0 <= numeric <= 1.0:
        raise ValueError(f"{field_name} must be finite and between 0 and 1")
    return value


class ReviewStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    started_at: datetime
    ended_at: datetime
    resolver: str = "unavailable"
    uri: str | None = None
    status: str = "designed"


class PrimitiveFact(BaseModel):
    model_config = ConfigDict(extra="allow")

    fact_type: str
    timestamp: datetime = Field(default_factory=utc_now)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    subject: dict[str, Any] | None = None
    object: dict[str, Any] | None = None
    location: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("confidence", mode="before")
    @classmethod
    def validate_confidence_type_and_range(cls, value: Any) -> Any:
        return _validate_confidence(value)


class UnifiedEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: str = "1.0"
    plugin_id: str
    plugin_version: str
    event_type: str
    title: str
    description: str
    source_id: str
    started_at: datetime
    ended_at: datetime
    confidence: float = Field(ge=0.0, le=1.0)
    severity: Severity = Severity.INFO
    review_status: ReviewStatus = ReviewStatus.PENDING
    subject: dict[str, Any] | None = None
    object: dict[str, Any] | None = None
    location: str | None = None
    evidence: list[EvidenceRef] = Field(default_factory=list)
    facts: list[PrimitiveFact] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class PluginManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plugin_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,63}$")
    name: str
    version: str
    description: str
    entrypoint: str = "plugin.py"
    enabled_by_default: bool = True


class PluginView(PluginManifest):
    enabled: bool
    state: str
    error: str | None = None


class AnalysisJobCreate(BaseModel):
    source: str = Field(min_length=1)
    plugin_ids: list[str] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceInspection(BaseModel):
    source_id: str
    kind: str
    provider: str
    status: str
    uri: str
    capabilities: list[str]
    reason: str | None = None


class FrameView(BaseModel):
    source_id: str
    frame_index: int
    timestamp: datetime
    payload: Any
    metadata: dict[str, Any] = Field(default_factory=dict)


class ObservationView(BaseModel):
    source_id: str
    timestamp: datetime
    fact_type: str
    confidence: float
    subject: dict[str, Any] | None = None
    object: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceResolution(BaseModel):
    source_id: str
    started_at: datetime
    ended_at: datetime
    resolver: str
    status: str
    uri: str | None = None
    reason: str | None = None


class DetectorProviderView(BaseModel):
    provider_id: str
    version: str
    available: bool
    selected: bool
    reason: str | None = None
    model_path: str | None = None
    object_model_path: str | None = None
    component: str | None = None
    pose_available: bool | None = None
    object_available: bool | None = None
    object_reason: str | None = None


class AnalysisJobView(BaseModel):
    job_id: str
    source: str
    status: str
    progress: float = Field(ge=0.0, le=1.0)
    event_ids: list[str] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewRequest(BaseModel):
    status: ReviewStatus
    note: str | None = None


class RegisteredObjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    reference_uris: list[str] = Field(default_factory=list)
    embedding: list[float] | None = None

    @field_validator("embedding", mode="before")
    @classmethod
    def validate_embedding_values(cls, value: Any) -> Any:
        return _validate_numeric_list(value, "embedding")


class RegisteredObject(RegisteredObjectCreate):
    object_id: str
    status: str = "active"
    created_at: datetime


class RegisteredPersonCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    role: str = "unknown"
    reference_uris: list[str] = Field(default_factory=list)
    embedding: list[float] | None = None

    @field_validator("embedding", mode="before")
    @classmethod
    def validate_embedding_values(cls, value: Any) -> Any:
        return _validate_numeric_list(value, "embedding")


class RegisteredPerson(RegisteredPersonCreate):
    person_id: str
    status: str = "active"
    created_at: datetime


class RegistryMatchRequest(BaseModel):
    kind: str = Field(pattern="^(object|person|all)$")
    embedding: list[float] | None = None
    gray: list[list[float]] | None = None
    threshold: float = Field(default=0.8, ge=0.0, le=1.0)

    @field_validator("embedding", mode="before")
    @classmethod
    def validate_embedding_values(cls, value: Any) -> Any:
        return _validate_numeric_list(value, "embedding")

    @field_validator("gray", mode="before")
    @classmethod
    def validate_gray_values(cls, value: Any) -> Any:
        return _validate_numeric_list(value, "gray", nested=True)

    @field_validator("threshold", mode="before")
    @classmethod
    def validate_threshold_type(cls, value: Any) -> Any:
        return _validate_real_number(value, "threshold")


class RegistryMatchView(BaseModel):
    registry_id: str
    label: str
    kind: str
    similarity: float
    accepted: bool
