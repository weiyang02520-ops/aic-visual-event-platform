"""Software-only quality contract for optional multimodal channels.

Providers may attach a small ``channel_quality`` map to frame metadata. The
gate validates that metadata, exposes a safe summary for facts, and tells the
frame pipeline whether inference may proceed. It does not inspect pixels or
claim that any physical sensor is present.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from numbers import Real
from typing import Any


class QualityContractError(ValueError):
    """Raised when an optional channel-quality record is malformed."""


def _finite_score(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise QualityContractError("channel quality score must be a finite number between 0 and 1")
    try:
        score = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise QualityContractError("channel quality score must be a finite number between 0 and 1") from exc
    if not isfinite(score) or not 0.0 <= score <= 1.0:
        raise QualityContractError("channel quality score must be a finite number between 0 and 1")
    return score


def _channel_name(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise QualityContractError("channel quality names must be non-empty strings")
    return value.strip().casefold()


@dataclass(frozen=True)
class ChannelQuality:
    channel: str
    available: bool
    score: float
    usable: bool
    reason: str | None = None


@dataclass(frozen=True)
class QualityDecision:
    gated: bool
    allow_inference: bool
    degraded: bool
    min_score: float
    required_channels: tuple[str, ...]
    channels: tuple[ChannelQuality, ...]
    blocked_reasons: tuple[str, ...] = ()

    def summary(self) -> dict[str, Any]:
        return {
            "gated": self.gated,
            "allow_inference": self.allow_inference,
            "degraded": self.degraded,
            "min_score": self.min_score,
            "required_channels": list(self.required_channels),
            "channels": [
                {
                    "channel": item.channel,
                    "available": item.available,
                    "score": item.score,
                    "usable": item.usable,
                    **({"reason": item.reason} if item.reason is not None else {}),
                }
                for item in self.channels
            ],
            "blocked_reasons": list(self.blocked_reasons),
        }


def evaluate_channel_quality(
    metadata: Mapping[str, Any] | None,
    *,
    min_score: float = 0.5,
) -> QualityDecision:
    """Validate optional channel quality and return a fail-closed decision.

    Without ``channel_quality`` the decision is ungated and preserves the
    existing CPU/fixture path. When present, at least one usable channel is
    required unless ``quality_required_channels`` names a stricter set.
    """

    threshold = _finite_score(min_score)
    if metadata is None or not isinstance(metadata, Mapping) or "channel_quality" not in metadata:
        return QualityDecision(False, True, False, threshold, (), ())

    raw_channels = metadata.get("channel_quality")
    if not isinstance(raw_channels, Mapping) or not raw_channels:
        raise QualityContractError("channel_quality must be a non-empty mapping")

    channels: list[ChannelQuality] = []
    seen: set[str] = set()
    for raw_name, raw_spec in raw_channels.items():
        channel = _channel_name(raw_name)
        if channel in seen:
            raise QualityContractError(f"duplicate channel quality name: {channel}")
        seen.add(channel)
        if not isinstance(raw_spec, Mapping):
            raise QualityContractError(f"channel quality entry must be a mapping: {channel}")
        available = raw_spec.get("available")
        if not isinstance(available, bool):
            raise QualityContractError(f"channel availability must be boolean: {channel}")
        reason = raw_spec.get("reason")
        if reason is not None and not isinstance(reason, str):
            raise QualityContractError(f"channel quality reason must be a string: {channel}")
        score = _finite_score(raw_spec.get("score"))
        channels.append(ChannelQuality(channel, available, score, available and score >= threshold, reason))

    raw_required = metadata.get("quality_required_channels", ())
    if not isinstance(raw_required, (list, tuple)):
        raise QualityContractError("quality_required_channels must be a list")
    required: list[str] = []
    for value in raw_required:
        channel = _channel_name(value)
        if channel not in required:
            required.append(channel)
    unknown_required = [channel for channel in required if channel not in seen]
    if unknown_required:
        raise QualityContractError(f"required channel is missing from channel_quality: {unknown_required[0]}")

    usable = {item.channel for item in channels if item.usable}
    if required:
        blocked = [channel for channel in required if channel not in usable]
        allow = not blocked
        reasons = tuple(f"required_channel_unusable:{channel}" for channel in blocked)
    else:
        allow = bool(usable)
        reasons = () if allow else ("no_usable_channel",)
    degraded = allow and len(usable) < len(channels)
    return QualityDecision(
        True,
        allow,
        degraded,
        threshold,
        tuple(required),
        tuple(channels),
        reasons,
    )
