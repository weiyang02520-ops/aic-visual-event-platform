from datetime import datetime, timezone

import pytest

from visual_event_ai.fact_pipeline import FrameFactExtractor
from visual_event_ai.frame_pipeline import Frame, FramePipeline
from visual_event_ai.ultralytics_provider import UltralyticsProvider


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _pose_points():
    points = [[0.0, 0.0] for _ in range(17)]
    points[0] = [20.0, 20.0]
    points[9] = [20.0, 25.0]
    points[10] = [35.0, 75.0]
    return points


class FakeBoxes:
    xyxy = [[0.0, 0.0, 40.0, 100.0], [50.0, 50.0, 60.0, 60.0]]
    conf = [0.95, 0.8]
    cls = [0, 1]


class FakeKeypoints:
    xy = [_pose_points(), _pose_points()]
    conf = [[0.9 for _ in range(17)], [0.9 for _ in range(17)]]


class FakeResult:
    boxes = FakeBoxes()
    keypoints = FakeKeypoints()
    names = {0: "person", 1: "medicine bottle"}


class FakeModel:
    def __init__(self, results=None):
        self.results = [FakeResult()] if results is None else results
        self.calls = []

    def predict(self, *, source, verbose):
        self.calls.append((source, verbose))
        return self.results


def test_ultralytics_provider_normalizes_person_detection_and_pose_keypoints():
    model = FakeModel()
    provider = UltralyticsProvider(model=model)

    detections = provider.detect(Frame("camera://one", 0, BASE, {"image": object()}))

    assert provider.available() is True
    assert len(detections) == 1
    detection = detections[0]
    assert detection.label == "person"
    assert detection.confidence == 0.95
    assert detection.bbox == (0.0, 0.0, 40.0, 100.0)
    assert detection.metadata["provider"] == "ultralytics"
    assert detection.metadata["keypoints"]["nose"] == [20.0, 20.0, 0.9]
    assert detection.metadata["keypoints"]["left_wrist"] == [20.0, 25.0, 0.9]
    assert detection.metadata["keypoints"]["right_wrist"] == [35.0, 75.0, 0.9]
    assert model.calls and model.calls[0][1] is False


def test_ultralytics_provider_requires_image_payload():
    provider = UltralyticsProvider(model=FakeModel())

    with pytest.raises(ValueError, match="requires frame payload"):
        provider.detect(Frame("camera://one", 0, BASE, {"gray": [[0]]}))


def test_ultralytics_provider_fails_closed_on_malformed_model_output():
    class BadBoxes:
        xyxy = [[0.0, 0.0, 40.0]]
        conf = [0.95]
        cls = [0]

    class BadResult:
        boxes = BadBoxes()
        names = {0: "person"}

    with pytest.raises(ValueError, match="bbox row 0"):
        UltralyticsProvider(model=FakeModel([BadResult()])).detect(
            Frame("camera://one", 0, BASE, {"image": object()})
        )


def test_ultralytics_provider_reports_missing_optional_runtime_or_model(monkeypatch, tmp_path):
    model_path = tmp_path / "pose.pt"
    model_path.write_bytes(b"placeholder")
    monkeypatch.setattr("visual_event_ai.ultralytics_provider.importlib.util.find_spec", lambda name: None)

    provider = UltralyticsProvider(str(model_path))

    assert provider.available() is False
    assert "ultralytics is not installed" in (provider.reason() or "")


def test_ultralytics_provider_reaches_normalized_fact_pipeline():
    provider = UltralyticsProvider(model=FakeModel())

    class OneFrame:
        def iter_frames(self, source, *, interval, max_frames, token, recover):
            yield Frame(source, 0, BASE, {"image": object()}, {"provider": "ultralytics-test"})

    class Registry:
        def session_for_source(self, _source):
            return provider

    facts = FrameFactExtractor(
        pipeline=FramePipeline(providers={"mock": OneFrame()}),
        detectors=Registry(),
    ).extract("mock://pose")

    person = next(fact for fact in facts if fact.fact_type == "object_detected")
    assert person.subject == {"track_id": 1, "label": "person"}
    assert person.metadata["source_id"] == "mock://pose"
    assert person.metadata["keypoints"]["nose"] == [20.0, 20.0, 0.9]

