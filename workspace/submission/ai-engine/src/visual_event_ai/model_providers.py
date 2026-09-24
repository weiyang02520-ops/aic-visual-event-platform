from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .frame_pipeline import Frame
from .providers import Detection, FixtureDetector, MotionDetector


class DetectorProvider(Protocol):
    provider_id: str
    version: str

    def available(self) -> bool: ...

    def reason(self) -> str | None: ...

    def detect(self, frame: Frame) -> list[Detection]: ...


@dataclass(frozen=True)
class DetectorProviderStatus:
    provider_id: str
    version: str
    available: bool
    selected: bool
    reason: str | None = None
    model_path: str | None = None


class MotionCPUProvider:
    provider_id = "motion_cpu"
    version = "0.1.0"

    def __init__(self) -> None:
        self.detector = MotionDetector()

    def new_session(self) -> MotionCPUProvider:
        """Give each analysis job an independent frame-difference history."""

        return MotionCPUProvider()

    def reset(self) -> None:
        self.detector.reset()

    def available(self) -> bool:
        return True

    def reason(self) -> str | None:
        return "explainable frame-difference baseline; not a trained object model"

    def detect(self, frame: Frame) -> list[Detection]:
        return self.detector.detect(frame)


class FixtureProvider:
    provider_id = "fixture"
    version = "0.1.0"

    def __init__(self) -> None:
        self.detector = FixtureDetector()

    def available(self) -> bool:
        return True

    def reason(self) -> str | None:
        return "normalizes precomputed fixture objects; not a model accuracy result"

    def detect(self, frame: Frame) -> list[Detection]:
        return self.detector.detect(frame)


class OnnxProvider:
    provider_id = "onnx"
    version = "0.1.0"

    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = Path(model_path or os.getenv("AI_ONNX_MODEL_PATH", ""))

    def available(self) -> bool:
        # A model file and runtime alone are not enough. This project still
        # lacks a verified model-specific input/output adapter, so never mark
        # ONNX selectable until that adapter is implemented and tested.
        return False

    def reason(self) -> str | None:
        if not self.model_path:
            return "AI_ONNX_MODEL_PATH is not configured"
        if not self.model_path.is_file():
            return f"model file does not exist: {self.model_path}"
        if not importlib.util.find_spec("onnxruntime"):
            return "onnxruntime is not installed; install the model extra"
        return "model runtime is present, but no verified input/output adapter is installed for this model"

    def detect(self, frame: Frame) -> list[Detection]:
        if not self.available():
            raise RuntimeError(self.reason() or "ONNX provider unavailable")
        raise RuntimeError("ONNX model adapter is intentionally not inferred without a verified model contract")


class DetectorProviderRegistry:
    def __init__(self, requested: str | None = None) -> None:
        self.requested = requested or os.getenv("AI_DETECTOR_PROVIDER", "motion_cpu")
        self.providers: dict[str, DetectorProvider] = {
            "motion_cpu": MotionCPUProvider(),
            "fixture": FixtureProvider(),
            "onnx": OnnxProvider(),
        }

    def for_source(self, source: str) -> DetectorProvider:
        if source.split("?", 1)[0].lower().endswith((".jsonl", ".ndjson")):
            return self.providers["fixture"]
        selected = self.providers.get(self.requested)
        if selected is not None and selected.available():
            return selected
        return self.providers["motion_cpu"]

    def session_for_source(self, source: str) -> DetectorProvider:
        """Return a source provider with job-local state when needed."""

        provider = self.for_source(source)
        new_session = getattr(provider, "new_session", None)
        return new_session() if callable(new_session) else provider

    def statuses(self, source: str | None = None) -> list[DetectorProviderStatus]:
        active = self.for_source(source) if source else self.providers.get(self.requested, self.providers["motion_cpu"])
        if not active.available():
            active = self.providers["motion_cpu"]
        return [
            DetectorProviderStatus(
                provider_id=provider_id,
                version=provider.version,
                available=provider.available(),
                selected=provider is active,
                reason=provider.reason(),
                model_path=str(getattr(provider, "model_path", "")) or None,
            )
            for provider_id, provider in self.providers.items()
        ]
