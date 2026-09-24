"""Strict parsing for optional pixel-coordinate scene zones."""

from __future__ import annotations

import json
from math import isfinite
from numbers import Real

from .relations import Zone


_ZONE_FIELDS = {"zone_id", "label", "x", "y", "width", "height"}


def parse_zones_json(value: str | None) -> tuple[Zone, ...]:
    """Parse ``AI_ZONES_JSON`` without silently accepting misspelled fields."""

    if value is None or not value.strip():
        return ()
    try:
        items = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError("AI_ZONES_JSON must be valid JSON") from exc
    if not isinstance(items, list):
        raise ValueError("AI_ZONES_JSON must be a JSON array")

    zones: list[Zone] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"AI_ZONES_JSON[{index}] must be an object")
        missing = _ZONE_FIELDS - set(item)
        unknown = set(item) - _ZONE_FIELDS
        if missing or unknown:
            details = []
            if missing:
                details.append(f"missing fields: {sorted(missing)}")
            if unknown:
                details.append(f"unknown fields: {sorted(unknown)}")
            raise ValueError(f"AI_ZONES_JSON[{index}] " + "; ".join(details))

        raw_zone_id = item["zone_id"]
        raw_label = item["label"]
        if not isinstance(raw_zone_id, str) or not raw_zone_id.strip():
            raise ValueError(f"AI_ZONES_JSON[{index}].zone_id must be a non-empty string")
        if not isinstance(raw_label, str) or not raw_label.strip():
            raise ValueError(f"AI_ZONES_JSON[{index}].label must be a non-empty string")
        zone_id = raw_zone_id.strip()
        label = raw_label.strip()
        if zone_id in seen_ids:
            raise ValueError(f"AI_ZONES_JSON contains duplicate zone_id: {zone_id}")

        coordinates: dict[str, float] = {}
        for field in ("x", "y", "width", "height"):
            raw = item[field]
            if isinstance(raw, bool) or not isinstance(raw, Real):
                raise ValueError(f"AI_ZONES_JSON[{index}].{field} must be a finite number")
            try:
                coordinate = float(raw)
            except (ValueError, OverflowError) as exc:
                raise ValueError(f"AI_ZONES_JSON[{index}].{field} must be a finite number") from exc
            if not isfinite(coordinate):
                raise ValueError(f"AI_ZONES_JSON[{index}].{field} must be a finite number")
            coordinates[field] = coordinate
        if coordinates["width"] <= 0 or coordinates["height"] <= 0:
            raise ValueError(f"AI_ZONES_JSON[{index}] width and height must be positive")

        zones.append(
            Zone(
                zone_id=zone_id.strip(),
                label=label,
                x=coordinates["x"],
                y=coordinates["y"],
                width=coordinates["width"],
                height=coordinates["height"],
            )
        )
        seen_ids.add(zone_id)
    return tuple(zones)
