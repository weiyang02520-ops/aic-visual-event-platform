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
from .providers import BBox, Detection
from .skeleton import (
    COCO17_KEYPOINT_INDICES,
    COCO17_SCHEMA,
    COCO17_SCHEMA_VERSION,
    SkeletonKeypoint,
)


# Backward-compatible alias for callers that imported the old provider map.
COCO_KEYPOINT_INDICES = COCO17_KEYPOINT_INDICES


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
        # The legacy variable remains a pose-model alias.  Semantic objects
        # have their own provider/configuration below so an object model can
        # be added without replacing a working pose path.
        configured_path = model_path or os.getenv("AI_ULTRALYTICS_POSE_MODEL_PATH") or os.getenv("AI_ULTRALYTICS_MODEL_PATH")
        self.model_path = Path(configured_path) if configured_path else None
        self._model = model
        self._model_loader = model_loader
        self._load_error: str | None = None
        if any(isinstance(item, bool) or not isinstance(item, int) for item in person_class_ids):
            raise ValueError("person_class_ids must contain integers")
        self.person_class_ids = frozenset(person_class_ids)
        indices = dict(keypoint_indices or COCO17_KEYPOINT_INDICES)
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
        self.keypoint_schema = (
            COCO17_SCHEMA
            if all(
                name in COCO17_KEYPOINT_INDICES and COCO17_KEYPOINT_INDICES[name] == index
                for name, index in self.keypoint_indices.items()
            )
            else "custom"
        )

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
            return "AI_ULTRALYTICS_POSE_MODEL_PATH or AI_ULTRALYTICS_MODEL_PATH is not configured"
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
            if point is None:
                continue
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                raise ValueError(f"Ultralytics keypoint {name} has malformed coordinates")
            confidence = 1.0
            if confidence_row and index < len(confidence_row):
                confidence_value = confidence_row[index]
                if confidence_value is None:
                    continue
                if isinstance(confidence_value, (list, tuple)) and len(confidence_value) == 1:
                    confidence_value = confidence_value[0]
                confidence = _confidence(confidence_value, f"keypoint {name} confidence")
            normalized_point = SkeletonKeypoint(
                name,
                _finite_number(point[0], f"keypoint {name} x"),
                _finite_number(point[1], f"keypoint {name} y"),
                confidence,
            )
            normalized[name] = normalized_point.as_list()
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
                    "keypoint_schema": self.keypoint_schema,
                    "keypoint_schema_version": COCO17_SCHEMA_VERSION,
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


class UltralyticsObjectProvider:
    """Optional Ultralytics adapter for semantic non-person boxes.

    It intentionally has no pose/keypoint handling.  Any class named as a
    person is excluded so that a semantic model cannot create duplicate person
    rows beside the pose provider.  The model and weights remain optional;
    tests inject a small Ultralytics-compatible fake result.
    """

    provider_id = "ultralytics_objects"
    version = "0.1.0"

    def __init__(
        self,
        model_path: str | None = None,
        *,
        model: Any | None = None,
        model_loader: Callable[[str], Any] | None = None,
        person_class_ids: tuple[int, ...] = (0,),
    ) -> None:
        configured_path = model_path or os.getenv("AI_ULTRALYTICS_OBJECT_MODEL_PATH")
        self.model_path = Path(configured_path) if configured_path else None
        self._model = model
        self._model_loader = model_loader
        self._load_error: str | None = None
        if any(isinstance(item, bool) or not isinstance(item, int) for item in person_class_ids):
            raise ValueError("person_class_ids must contain integers")
        self.person_class_ids = frozenset(person_class_ids)

    def new_session(self) -> UltralyticsObjectProvider:
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
            return "AI_ULTRALYTICS_OBJECT_MODEL_PATH is not configured"
        if not self.model_path.is_file():
            return f"model file does not exist: {self.model_path}"
        if importlib.util.find_spec("ultralytics") is None:
            return "ultralytics is not installed; install the optional pose extra"
        return "Ultralytics object provider is available but has not loaded the model yet"

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        if not self.available():
            raise RuntimeError(self.reason() or "Ultralytics object provider unavailable")
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
            self._load_error = f"Ultralytics object model load failed: {exc}"
            raise RuntimeError(self._load_error) from exc

    @staticmethod
    def _frame_source(frame: Frame) -> Any:
        return UltralyticsProvider._frame_source(frame)

    def _normalize_results(self, results: Any) -> list[Detection]:
        result_list = results if isinstance(results, (list, tuple)) else [results]
        detections: list[Detection] = []
        for result in result_list:
            boxes = _attribute(result, "boxes")
            if boxes is None:
                raise ValueError("Ultralytics object result is missing boxes")
            xy_rows = _rows(_attribute(boxes, "xyxy"))
            confidence_rows = _vector(_attribute(boxes, "conf"), "object confidence")
            class_rows = _vector(_attribute(boxes, "cls"), "object class")
            names = _attribute(result, "names", {})
            for row_index, coordinates in enumerate(xy_rows):
                if not isinstance(coordinates, (list, tuple)) or len(coordinates) < 4:
                    raise ValueError(f"Ultralytics object bbox row {row_index} is malformed")
                class_id = _class_id(_row_value(class_rows, row_index, "object class"))
                label = UltralyticsProvider._class_name(names, class_id)
                if not label:
                    raise ValueError(f"Ultralytics object class label row {row_index} is empty")
                if class_id in self.person_class_ids or is_person_label(label):
                    continue
                x1 = _finite_number(coordinates[0], "object bbox x1")
                y1 = _finite_number(coordinates[1], "object bbox y1")
                x2 = _finite_number(coordinates[2], "object bbox x2")
                y2 = _finite_number(coordinates[3], "object bbox y2")
                if x2 <= x1 or y2 <= y1:
                    raise ValueError(f"Ultralytics object bbox row {row_index} has non-positive extent")
                confidence = _confidence(
                    _row_value(confidence_rows, row_index, "object confidence"),
                    "object detection confidence",
                )
                detections.append(
                    Detection(
                        label=label,
                        confidence=confidence,
                        bbox=(x1, y1, x2 - x1, y2 - y1),
                        metadata={
                            "provider": self.provider_id,
                            "provider_version": self.version,
                            "component": "semantic_object",
                            "class_id": class_id,
                        },
                    )
                )
        return detections

    def detect(self, frame: Frame) -> list[Detection]:
        model = self._load_model()
        source = self._frame_source(frame)
        if source is None:
            raise ValueError("Ultralytics object provider requires frame payload image/frame data")
        try:
            results = model.predict(source=source, verbose=False)
        except Exception as exc:
            raise RuntimeError(f"Ultralytics object inference failed: {exc}") from exc
        return self._normalize_results(results)


class CombinedUltralyticsProvider:
    """Compose pose and optional semantic-object inference for one frame."""

    provider_id = "ultralytics"
    version = "0.2.0"

    def __init__(
        self,
        pose_provider: UltralyticsProvider | None = None,
        object_provider: UltralyticsObjectProvider | None = None,
        *,
        pose_model_path: str | None = None,
        object_model_path: str | None = None,
    ) -> None:
        self.pose_provider = pose_provider or UltralyticsProvider(pose_model_path)
        self.object_provider = object_provider or UltralyticsObjectProvider(object_model_path)

    @property
    def model_path(self) -> Path | None:
        return self.pose_provider.model_path

    @property
    def object_model_path(self) -> Path | None:
        return self.object_provider.model_path

    def new_session(self) -> CombinedUltralyticsProvider:
        return self

    def available(self) -> bool:
        # Pose is the proven primary path.  Semantic objects are optional and
        # must not make a working pose provider unavailable.
        return self.pose_provider.available()

    def reason(self) -> str | None:
        pose_reason = self.pose_provider.reason()
        object_reason = self.object_provider.reason()
        if pose_reason:
            return pose_reason
        if object_reason:
            return f"pose available; semantic object component unavailable: {object_reason}"
        return None

    def component_status(self) -> dict[str, dict[str, Any]]:
        return {
            "pose": {
                "available": self.pose_provider.available(),
                "configured_path": str(self.pose_provider.model_path) if self.pose_provider.model_path else None,
                "reason": self.pose_provider.reason(),
            },
            "semantic_object": {
                "available": self.object_provider.available(),
                "configured_path": str(self.object_provider.model_path) if self.object_provider.model_path else None,
                "reason": self.object_provider.reason(),
            },
        }

    def detect(self, frame: Frame) -> list[Detection]:
        if not self.pose_provider.available():
            raise RuntimeError(self.pose_provider.reason() or "Ultralytics pose provider unavailable")
        detections = list(self.pose_provider.detect(frame))
        if self.object_provider.available():
            detections.extend(self.object_provider.detect(frame))
        # Keep a deterministic person-first order and never allow the object
        # model to create a second person row.
        unique_people: dict[BBox, Detection] = {}
        object_detections: list[Detection] = []
        for detection in detections:
            if is_person_label(detection.label):
                # A semantic detector must not duplicate a pose person row;
                # duplicate pose rows with the same geometry are also safely
                # collapsed before tracking.
                unique_people.setdefault(detection.bbox, detection)
            else:
                # Do not deduplicate non-person boxes: two same-label objects
                # may legitimately share a bbox in a fixture or occlusion.
                object_detections.append(detection)
        unique = [*unique_people.values(), *object_detections]
        return sorted(
            unique,
            key=lambda item: (
                0 if is_person_label(item.label) else 1,
                item.label.casefold(),
                item.bbox,
                -item.confidence,
            ),
        )


# Names used by callers/tests can describe the same explicit composition.
UltralyticsSemanticObjectProvider = UltralyticsObjectProvider
UltralyticsCombinedProvider = CombinedUltralyticsProvider
CombinedPerceptionProvider = CombinedUltralyticsProvider
