"""Shared privacy boundary for pixel-bearing AI metadata.

The algorithm engine may receive detector metadata from optional providers. A
provider can attach raw image-like arrays even when the current detector only
needs boxes or keypoints. This module keeps those arrays out of API previews,
facts, jobs, and persisted event payloads while preserving a small shape and
encoding summary for debugging.
"""

from __future__ import annotations

import re
from collections.abc import Mapping


_PIXEL_ENCODINGS = {
    "image": "server-side-image",
    "image_data": "redacted-image",
    "image_pixels": "redacted-image",
    "raw_image": "redacted-image",
    "frame_data": "redacted-frame",
    "raw_frame": "redacted-frame",
    "gray": "redacted-grayscale",
    "grayscale": "redacted-grayscale",
    "pixels": "redacted-pixels",
    "raw_pixels": "redacted-pixels",
    "pixel_data": "redacted-pixels",
    "pixel_values": "redacted-pixels",
    "rgb": "redacted-rgb",
    "bgr": "redacted-bgr",
    "depth": "redacted-depth",
    "depth_map": "redacted-depth",
    "thermal": "redacted-thermal",
    "thermal_map": "redacted-thermal",
    "infrared": "redacted-infrared",
}


def _normalized_key(key: object) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(key).strip())
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").casefold()


def _shape_for_payload(value: object, fallback: object = None) -> list[int]:
    shape = getattr(value, "shape", None)
    if shape is None and isinstance(value, (list, tuple)):
        shape = [len(value)]
        if value and isinstance(value[0], (list, tuple)):
            shape.extend(_shape_for_payload(value[0]))
    if shape is None and isinstance(value, Mapping):
        shape = value.get("shape")
    if shape is None:
        shape = fallback
    if not isinstance(shape, (list, tuple)):
        return []
    try:
        return [int(dimension) for dimension in shape]
    except (TypeError, ValueError, OverflowError):
        return []


def sanitize_sensitive_payload(payload: object) -> object:
    """Recursively replace recognized raw pixel arrays with safe summaries."""

    if isinstance(payload, Mapping):
        result: dict[object, object] = {}
        fallback_shape = payload.get("shape")
        for key, value in payload.items():
            encoding = _PIXEL_ENCODINGS.get(_normalized_key(key))
            if encoding is not None:
                result[key] = {
                    "encoding": encoding,
                    "shape": _shape_for_payload(value, fallback_shape),
                }
            else:
                result[key] = sanitize_sensitive_payload(value)
        return result
    if isinstance(payload, (list, tuple)):
        return [sanitize_sensitive_payload(value) for value in payload]
    return payload

