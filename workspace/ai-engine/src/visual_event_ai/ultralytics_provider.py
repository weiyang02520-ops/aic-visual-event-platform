"""Optional Ultralytics-compatible person/pose provider.

The adapter is intentionally thin: it converts a model result into the
existing :class:`Detection` contract and leaves tracking, relations, keypoint
actions and scene reasoning unchanged. The ``ultralytics`` dependency and
model weights remain optional; deterministic tests inject a fake model.
"""

from __future__ import annotations

import importlib.util
import os
from collections.abc import Callable, Mapping
from math import isfinite
from pathlib import Path
from typing import Any

from .entity_labels import is_person_label
from .frame_pipeline import Frame
from .providers import Detection


COCO_KEYPOINT_INDICES = {
    "nose": 0,
    "left_wrist": 9,
    "right_wrist": 10,
}


def _attribute(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _to_python(value: Any) -> Any:
    """Detach torch/numpy-like values without importing either package."""

    current = value
    for name in ("detach", "cpu", "numpy"):
        method = getattr(current, name, None)
        if callable(method):
            current = method()
    tolist = getattr(current, "tolist", None)
    if callable(tolist):
        current = tolist()
    return current


def _rows(value: Any) -> list[Any]:
    value = _to_python(value)
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError("Ultralytics output must be a list-like tensor")
    values = list(value)
    if values and not isinstance(values[0], (list, tuple)):
        return [values]
    return values


def _vector(value: Any, field: str) -> list[Any]:
    value = _to_python(value)
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"Ultralytics {field} must be a list-like tensor")
    return list(value)


def _row_value(rows: list[Any], index: int, field: str) -> Any:
    if index >= len(rows):
        raise ValueError(f"Ultralytics output is missing {field} row {index}")
    row = rows[index]
    if isinstance(row, (list, tuple)) and len(row) == 1:
        return row[0]
    return row


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"Ultralytics {field} must be finite numeric data")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"Ultralytics {field} must be finite numeric data") from exc
    if not isfinite(number):
        raise ValueError(f"Ultralytics {field} must be finite numeric data")
    return number


def _confidence(value: Any, field: str) -> float:
    number = _finite_number(value, field)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"Ultralytics {field} must be between 0 and 1")
    return number


def _class_id(value: Any) -> int:
    number = _finite_number(value, "class id")
    if number != int(number):
        raise ValueError("Ultralytics class id must be an integer")
    return int(number)


class UltralyticsProvider:
    """Optional Ultralytics YOLO/pose adapter with a truthful availability gate."""

    provider_id = "ultralytics"
    version = "0.1.0"

    def __init__(
        self,
        model_path: str | None = None,
        *,
        model: Any | None = None,
        model_loader: Callable[[str], Any] | None = None,
        person_class_ids: tuple[int, ...] = (0,),
        keypoint_indices: Mapping[str, int] | None = None,
    ) -> None:
        self.model_path = Path(model_path) if model_path else None
        self._model = model
        self._model_loader = model_loader
        self._load_error: str | None = None
        if any(isinstance(item, bool) or not isinstance(item, int) for item in person_class_ids):
            raise ValueError("person_class_ids must contain integers")
        self.person_class_ids = frozenset(person_class_ids)
        indices = dict(keypoint_indices or COCO_KEYPOINT_INDICES)
        if any(
            not isinstance(name, str)
            or not name.strip()
            or isinstance(index, bool)
            or not isinstance(index, int)
            or index < 0
            for name, index in indices.items()
        ):
            raise ValueError("keypoint_indices must map non-empty names to non-negative integers")
        self.keypoint_indices = {name.strip(): index for name, index in indices.items()}

    def new_session(self) -> UltralyticsProvider:
        """Return a stateless provider view; model weights are not reloaded per job."""

        return self

    def available(self) -> bool:
        if self._model is not None:
            return True
        if self._load_error is not None:
            return False
        return bool(
            self.model_path
            and self.model_path.is_file()
            and importlib.util.find_spec("ultralytics") is not None
        )

    def reason(self) -> str | None:
        if self._model is not None:
            return None
        if self._load_error is not None:
            return self._load_error
        if self.model_path is None:
            return "AI_ULTRALYTICS_MODEL_PATH is not configured"
        if not self.model_path.is_file():
            return f"model file does not exist: {self.model_path}"
        if importlib.util.find_spec("ultralytics") is None:
            return "ultralytics is not installed; install the optional pose extra"
        return "Ultralytics provider is available but has not loaded the model yet"

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        if not self.available():
            raise RuntimeError(self.reason() or "Ultralytics provider unavailable")
        try:
            if self._model_loader is not None:
                model = self._model_loader(str(self.model_path))
            else:
                from ultralytics import YOLO  # type: ignore[import-not-found]

                model = YOLO(str(self.model_path))
            if model is None:
                raise RuntimeError("model loader returned None")
            self._model = model
            return model
        except Exception as exc:
            self._load_error = f"Ultralytics model load failed: {exc}"
            raise RuntimeError(self._load_error) from exc

    @staticmethod
    def _frame_source(frame: Frame) -> Any:
        payload = frame.payload
        if isinstance(payload, Mapping):
            for key in ("image", "frame", "bgr", "rgb"):
                if payload.get(key) is not None:
                    return payload[key]
            return None
        return payload

    @staticmethod
    def _class_name(names: Any, class_id: int) -> str:
        names = _to_python(names)
        if isinstance(names, Mapping):
            value = names.get(class_id, names.get(str(class_id)))
            return str(value).strip() if value is not None else ("person" if class_id == 0 else "")
        if isinstance(names, (list, tuple)) and 0 <= class_id < len(names):
            return str(names[class_id]).strip()
        return "person" if class_id == 0 else ""

    def _keypoints(self, result: Any, row_index: int) -> dict[str, list[float]]:
        keypoints = _attribute(result, "keypoints")
        if keypoints is None:
            return {}
        xy_rows = _rows(_attribute(keypoints, "xy"))
        if row_index >= len(xy_rows):
            raise ValueError(f"Ultralytics keypoints are missing detection row {row_index}")
        points = _to_python(xy_rows[row_index])
        if not isinstance(points, (list, tuple)):
            raise ValueError("Ultralytics keypoint row must be list-like")
        confidence_rows = _rows(_attribute(keypoints, "conf")) if _attribute(keypoints, "conf") is not None else []
        confidence_row = _to_python(confidence_rows[row_index]) if row_index < len(confidence_rows) else []
        if confidence_row and not isinstance(confidence_row, (list, tuple)):
            confidence_row = [confidence_row]
        normalized: dict[str, list[float]] = {}
        for name, index in self.keypoint_indices.items():
            if index >= len(points):
                continue
            point = _to_python(points[index])
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                raise ValueError(f"Ultralytics keypoint {name} has malformed coordinates")
            confidence = 1.0
            if confidence_row and index < len(confidence_row):
                confidence_value = confidence_row[index]
                if isinstance(confidence_value, (list, tuple)) and len(confidence_value) == 1:
                    confidence_value = confidence_value[0]
                confidence = _confidence(confidence_value, f"keypoint {name} confidence")
            normalized[name] = [
                _finite_number(point[0], f"keypoint {name} x"),
                _finite_number(point[1], f"keypoint {name} y"),
                confidence,
            ]
        return normalized

    def _normalize_results(self, results: Any) -> list[Detection]:
        result_list = results if isinstance(results, (list, tuple)) else [results]
        detections: list[Detection] = []
        for result in result_list:
            boxes = _attribute(result, "boxes")
            if boxes is None:
                raise ValueError("Ultralytics result is missing boxes")
            xy_rows = _rows(_attribute(boxes, "xyxy"))
            confidence_rows = _vector(_attribute(boxes, "conf"), "confidence")
            class_rows = _vector(_attribute(boxes, "cls"), "class")
            names = _attribute(result, "names", {})
            for row_index, coordinates in enumerate(xy_rows):
                if not isinstance(coordinates, (list, tuple)) or len(coordinates) < 4:
                    raise ValueError(f"Ultralytics bbox row {row_index} is malformed")
                class_id = _class_id(_row_value(class_rows, row_index, "class"))
                if class_id not in self.person_class_ids:
                    continue
                label = self._class_name(names, class_id)
                if not is_person_label(label):
                    continue
                x1 = _finite_number(coordinates[0], "bbox x1")
                y1 = _finite_number(coordinates[1], "bbox y1")
                x2 = _finite_number(coordinates[2], "bbox x2")
                y2 = _finite_number(coordinates[3], "bbox y2")
                if x2 <= x1 or y2 <= y1:
                    raise ValueError(f"Ultralytics bbox row {row_index} has non-positive extent")
                confidence = _confidence(_row_value(confidence_rows, row_index, "confidence"), "detection confidence")
                metadata: dict[str, Any] = {
                    "provider": self.provider_id,
                    "provider_version": self.version,
                    "class_id": class_id,
                    "keypoint_schema": "coco17",
                }
                keypoints = self._keypoints(result, row_index)
                if keypoints:
                    metadata["keypoints"] = keypoints
                detections.append(
                    Detection(
                        label="person",
                        confidence=confidence,
                        bbox=(x1, y1, x2 - x1, y2 - y1),
                        metadata=metadata,
                    )
                )
        return detections

    def detect(self, frame: Frame) -> list[Detection]:
        model = self._load_model()
        source = self._frame_source(frame)
        if source is None:
            raise ValueError("Ultralytics provider requires frame payload image/frame data")
        try:
            results = model.predict(source=source, verbose=False)
        except Exception as exc:
            raise RuntimeError(f"Ultralytics inference failed: {exc}") from exc
        return self._normalize_results(results)
