import json
import sys

import pytest

from visual_event_ai.frame_pipeline import CancellationToken, FramePipeline, FramePipelineError


def test_mock_frames_preserve_source_and_timestamp_spacing():
    frames = list(FramePipeline().iter_frames("mock://elderly-medication?frames=3", interval_ms=250))
    assert len(frames) == 3
    assert {frame.source_id for frame in frames} == {"mock://elderly-medication?frames=3"}
    assert [frame.frame_index for frame in frames] == [0, 1, 2]
    assert (frames[1].timestamp - frames[0].timestamp).total_seconds() == pytest.approx(0.25)


@pytest.mark.parametrize("interval_ms", [True, 1.5, "250", -1, 10**1000])
def test_frame_pipeline_rejects_invalid_interval_types_and_ranges(interval_ms):
    with pytest.raises(ValueError, match="interval_ms"):
        list(FramePipeline().iter_frames("mock://test?frames=2", interval_ms=interval_ms))


@pytest.mark.parametrize("max_frames", [True, 1.5, "2", -1])
def test_frame_pipeline_rejects_invalid_frame_limits(max_frames):
    with pytest.raises(ValueError, match="max_frames"):
        list(FramePipeline().iter_frames("mock://test?frames=2", max_frames=max_frames))


def test_frame_pipeline_allows_zero_frame_limit():
    assert list(FramePipeline().iter_frames("mock://test?frames=2", max_frames=0)) == []


def test_jsonl_fixture_skips_bad_lines_and_supports_cancel(tmp_path):
    fixture = tmp_path / "frames.jsonl"
    fixture.write_text(
        json.dumps({"payload": {"objects": ["box"]}}) + "\nnot-json\n" + json.dumps({"payload": {"objects": ["person"]}}) + "\n",
        encoding="utf-8",
    )
    pipeline = FramePipeline()
    frames = list(pipeline.iter_frames(str(fixture), recover=True))
    assert len(frames) == 2
    assert frames[0].metadata.get("discontinuity_before") is None
    assert frames[1].metadata["discontinuity_before"] is True
    assert frames[1].metadata["skipped_line"] == 2
    assert frames[1].metadata["discontinuity_reason"] == "malformed_jsonl_record"
    token = CancellationToken()
    token.cancel()
    with pytest.raises(FramePipelineError, match="cancelled"):
        next(pipeline.iter_frames(str(fixture), token=token))


def test_unknown_stream_requires_explicit_adapter():
    with pytest.raises(FramePipelineError, match="no frame provider"):
        list(FramePipeline().iter_frames("rtmp://127.0.0.1/live/demo"))


def test_video_extension_routes_to_optional_opencv_provider(tmp_path):
    path = tmp_path / "clip.mp4"
    path.write_bytes(b"fixture placeholder")
    assert type(FramePipeline().provider_for(str(path))).__name__ == "OpenCVFrameProvider"


def test_opencv_provider_reads_real_local_video_when_available(tmp_path):
    cv2 = pytest.importorskip("cv2")
    path = tmp_path / "tiny.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 5.0, (16, 12))
    if not writer.isOpened():
        pytest.skip("OpenCV video writer codec unavailable")
    import numpy as np

    writer.write(np.zeros((12, 16, 3), dtype=np.uint8))
    writer.write(np.full((12, 16, 3), 80, dtype=np.uint8))
    writer.release()
    frames = list(FramePipeline().iter_frames(str(path), interval_ms=0, max_frames=2))
    assert len(frames) == 2
    assert frames[0].metadata["provider"] == "opencv"
    assert frames[0].payload["shape"] == [12, 16]


class _FakeCapture:
    def __init__(self, fps, positions):
        self.fps = fps
        self.positions = positions
        self.read_count = 0

    def isOpened(self):
        return True

    def get(self, property_id):
        if property_id == 1:
            return self.fps
        return self.positions[min(max(self.read_count - 1, 0), len(self.positions) - 1)]

    def read(self):
        if self.read_count >= len(self.positions):
            return False, None
        self.read_count += 1
        return True, object()

    def release(self):
        pass


class _FakeCV2:
    CAP_PROP_FPS = 1
    CAP_PROP_POS_MSEC = 2
    COLOR_BGR2GRAY = 3

    def __init__(self, fps, positions):
        self.capture = _FakeCapture(fps, positions)

    def VideoCapture(self, _path):
        return self.capture

    @staticmethod
    def cvtColor(_image, _conversion):
        return type("GrayImage", (), {"shape": (2, 2)})()


@pytest.mark.parametrize("fps", [None, float("nan"), float("inf"), -1.0, 10**1000])
def test_opencv_provider_falls_back_when_fps_metadata_is_invalid(tmp_path, monkeypatch, fps):
    path = tmp_path / "invalid_fps.avi"
    path.touch()
    fake_cv2 = _FakeCV2(fps, [0.0])
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)

    frames = list(FramePipeline().iter_frames(str(path), max_frames=1))

    assert len(frames) == 1
    assert frames[0].metadata["fps"] == 25.0


@pytest.mark.parametrize("position_ms", [float("nan"), float("inf"), 1e308])
def test_opencv_provider_falls_back_when_position_metadata_is_invalid(tmp_path, monkeypatch, position_ms):
    path = tmp_path / "invalid_position.avi"
    path.touch()
    fake_cv2 = _FakeCV2(25.0, [position_ms, position_ms])
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)

    frames = list(FramePipeline().iter_frames(str(path), interval_ms=0, max_frames=2))

    assert len(frames) == 2
    assert (frames[1].timestamp - frames[0].timestamp).total_seconds() == pytest.approx(1 / 25)
