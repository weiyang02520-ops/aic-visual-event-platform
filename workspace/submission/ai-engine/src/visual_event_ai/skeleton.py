"""Canonical, pixel-free pose skeleton contracts.

The contract keeps named semantic keypoints separate from image pixels. It is
used by real pose providers and fixtures alike, so upper-layer action rules do
not need to know which camera or model produced the skeleton.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from numbers import Real
from typing import Any


COCO17_KEYPOINT_NAMES: tuple[str, ...] = (
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
)
COCO17_KEYPOINT_INDICES: dict[str, int] = {
    name: index for index, name in enumerate(COCO17_KEYPOINT_NAMES)
}
COCO17_SCHEMA = "coco17"
COCO17_SCHEMA_VERSION = "1.0"


def _finite(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"skeleton {field} must be finite numeric data")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"skeleton {field} must be finite numeric data") from exc
    if not isfinite(number):
        raise ValueError(f"skeleton {field} must be finite numeric data")
    return number


def _confidence(value: Any) -> float:
    confidence = _finite(value, "confidence")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("skeleton confidence must be between 0 and 1")
    return confidence


def _utc_timestamp(value: Any) -> datetime:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("skeleton timestamp must be an ISO-8601 datetime") from exc
    if not isinstance(value, datetime):
        raise ValueError("skeleton timestamp must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class SkeletonKeypoint:
    """One validated named keypoint; absent points are represented by omission."""

    name: str
    x: float
    y: float
    confidence: float

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("skeleton keypoint name must be a non-empty string")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "x", _finite(self.x, f"{self.name} x"))
        object.__setattr__(self, "y", _finite(self.y, f"{self.name} y"))
        object.__setattr__(self, "confidence", _confidence(self.confidence))

    @classmethod
    def from_value(
        cls,
        name: str,
        value: Any,
        *,
        strict: bool = True,
        default_confidence: float = 1.0,
    ) -> SkeletonKeypoint | None:
        if value is None and not strict:
            return None
        if not isinstance(value, (list, tuple)) or len(value) < 2:
            if strict:
                raise ValueError(f"skeleton keypoint {name} must contain x and y")
            return None
        try:
            confidence = value[2] if len(value) >= 3 else default_confidence
            return cls(name, value[0], value[1], confidence)
        except ValueError:
            if strict:
                raise
            return None

    def as_list(self) -> list[float]:
        return [self.x, self.y, self.confidence]


def normalize_keypoints(
    values: Mapping[str, Any] | None,
    *,
    strict: bool = True,
) -> dict[str, list[float]]:
    """Normalize available named points while omitting missing/occluded points."""

    if values is None:
        return {}
    if not isinstance(values, Mapping):
        raise ValueError("skeleton keypoints must be a mapping")
    normalized: dict[str, list[float]] = {}
    for name, value in values.items():
        if not isinstance(name, str) or not name.strip():
            if strict:
                raise ValueError("skeleton keypoint names must be non-empty strings")
            continue
        point = SkeletonKeypoint.from_value(name, value, strict=strict)
        if point is not None:
            normalized[point.name] = point.as_list()
    return normalized


@dataclass(frozen=True)
class SkeletonObservation:
    """A validated semantic skeleton with optional provenance."""

    schema: str
    version: str
    keypoints: dict[str, list[float]]
    source_id: str | None = None
    timestamp: datetime | None = None
    track_id: str | int | None = None
    continuity_segment: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.schema, str) or not self.schema.strip():
            raise ValueError("skeleton schema must be a non-empty string")
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError("skeleton schema version must be a non-empty string")
        object.__setattr__(self, "schema", self.schema.strip())
        object.__setattr__(self, "version", self.version.strip())
        object.__setattr__(self, "keypoints", normalize_keypoints(self.keypoints, strict=True))
        if self.source_id is not None:
            if not isinstance(self.source_id, str) or not self.source_id.strip():
                raise ValueError("skeleton source_id must be a non-empty string")
            object.__setattr__(self, "source_id", self.source_id.strip())
        if self.timestamp is not None:
            object.__setattr__(self, "timestamp", _utc_timestamp(self.timestamp))
        if self.track_id is not None:
            if isinstance(self.track_id, bool) or not isinstance(self.track_id, (str, int)):
                raise ValueError("skeleton track_id must be a string or integer")
            if isinstance(self.track_id, str) and not self.track_id.strip():
                raise ValueError("skeleton track_id must be non-empty")
        if self.continuity_segment is not None:
            if isinstance(self.continuity_segment, bool) or not isinstance(self.continuity_segment, int) or self.continuity_segment < 0:
                raise ValueError("skeleton continuity_segment must be a non-negative integer")

    @classmethod
    def from_keypoints(
        cls,
        keypoints: Mapping[str, Any] | None,
        *,
        schema: str = COCO17_SCHEMA,
        version: str = COCO17_SCHEMA_VERSION,
        source_id: str | None = None,
        timestamp: datetime | None = None,
        track_id: str | int | None = None,
        continuity_segment: int | None = None,
        strict: bool = True,
    ) -> SkeletonObservation:
        normalized = normalize_keypoints(keypoints, strict=strict)
        return cls(schema, version, normalized, source_id, timestamp, track_id, continuity_segment)

    @classmethod
    def from_metadata(
        cls,
        metadata: Mapping[str, Any] | None,
        *,
        source_id: str | None = None,
        timestamp: datetime | None = None,
        track_id: str | int | None = None,
        continuity_segment: int | None = None,
        strict: bool = False,
    ) -> SkeletonObservation | None:
        if not isinstance(metadata, Mapping):
            return None
        raw_skeleton = metadata.get("skeleton")
        source = raw_skeleton if isinstance(raw_skeleton, Mapping) else metadata
        raw_keypoints = source.get("keypoints")
        if not isinstance(raw_keypoints, Mapping):
            return None
        schema = source.get("schema", metadata.get("keypoint_schema", COCO17_SCHEMA))
        version = source.get("version", metadata.get("keypoint_schema_version", COCO17_SCHEMA_VERSION))
        if not isinstance(schema, str) or not isinstance(version, str):
            if strict:
                raise ValueError("skeleton schema metadata must be strings")
            return None
        try:
            return cls.from_keypoints(
                raw_keypoints,
                schema=schema,
                version=version,
                source_id=source_id or source.get("source_id"),
                timestamp=timestamp or source.get("timestamp"),
                track_id=track_id if track_id is not None else source.get("track_id"),
                continuity_segment=(
                    continuity_segment
                    if continuity_segment is not None
                    else source.get("continuity_segment")
                ),
                strict=strict,
            )
        except (TypeError, ValueError):
            if strict:
                raise
            return None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema": self.schema,
            "version": self.version,
            "keypoints": {name: list(point) for name, point in self.keypoints.items()},
        }
        if self.source_id is not None:
            result["source_id"] = self.source_id
        if self.timestamp is not None:
            result["timestamp"] = self.timestamp.isoformat()
        if self.track_id is not None:
            result["track_id"] = self.track_id
        if self.continuity_segment is not None:
            result["continuity_segment"] = self.continuity_segment
        return result
