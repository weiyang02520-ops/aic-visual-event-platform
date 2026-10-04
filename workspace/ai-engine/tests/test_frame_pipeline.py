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


@pytest.mark.parametrize(
    "source",
    [
        "rtsp://127.0.0.1/live/demo",
        "rtmp://127.0.0.1/live/demo",
        "http://127.0.0.1/live/demo",
        "https://127.0.0.1/live/demo.m3u8",
        "hls://127.0.0.1/live/demo.m3u8",
    ],
)
def test_network_streams_route_to_optional_opencv_provider(source):
    assert type(FramePipeline().provider_for(source)).__name__ == "OpenCVFrameProvider"


@pytest.mark.parametrize("source", ["camera://0", "webcam://0"])
def test_camera_sources_route_to_optional_opencv_provider(source):
    assert type(FramePipeline().provider_for(source)).__name__ == "OpenCVFrameProvider"


@pytest.mark.parametrize("source", ["camera://", "camera://-1", "camera://abc", "webcam://1.5", "camera:0"])
def test_camera_source_requires_non_negative_integer_index(source):
    with pytest.raises(FramePipelineError, match="non-negative integer camera index"):
        list(FramePipeline().iter_frames(source, max_frames=1))


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


def test_opencv_provider_exposes_bgr_image_and_gray_helper_payload(tmp_path, monkeypatch):
    path = tmp_path / "payload-contract.avi"
    path.touch()

    class BgrImage:
        shape = (3, 4, 3)

    class GrayImage:
        shape = (3, 4)

        @staticmethod
        def tolist():
            return [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]

    bgr = BgrImage()

    class Capture:
        def __init__(self):
            self.read_count = 0

        def isOpened(self):
            return True

        def get(self, property_id):
            return 25.0 if property_id == 1 else 0.0

        def read(self):
            if self.read_count:
                return False, None
            self.read_count += 1
            return True, bgr

        def release(self):
            pass

    class CV2:
        CAP_PROP_FPS = 1
        CAP_PROP_POS_MSEC = 2
        COLOR_BGR2GRAY = 3

        def __init__(self):
            self.capture = Capture()

        def VideoCapture(self, _path):
            return self.capture

        @staticmethod
        def cvtColor(_image, _conversion):
            return GrayImage()

    monkeypatch.setitem(sys.modules, "cv2", CV2())

    frames = list(FramePipeline().iter_frames(str(path), interval_ms=0, max_frames=1))

    payload = frames[0].payload
    assert payload["image"] is bgr
    assert payload["gray"] == [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]
    assert payload["shape"] == [3, 4]
    assert payload["channels"] == 3


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


def test_opencv_provider_reads_network_stream_and_marks_transport(monkeypatch):
    source = "rtsp://127.0.0.1/live/demo"
    monkeypatch.setitem(sys.modules, "cv2", _FakeCV2(25.0, [0.0]))

    frames = list(FramePipeline().iter_frames(source, interval_ms=0, max_frames=1))

    assert len(frames) == 1
    assert frames[0].metadata["provider"] == "opencv"
    assert frames[0].metadata["source_kind"] == "stream"
    assert frames[0].metadata["stream_transport"] == "rtsp"


def test_opencv_provider_reports_unreachable_network_stream(monkeypatch):
    class ClosedCapture:
        def isOpened(self):
            return False

        def release(self):
            pass

    class ClosedCV2:
        def VideoCapture(self, _source):
            return ClosedCapture()

    monkeypatch.setitem(sys.modules, "cv2", ClosedCV2())

    with pytest.raises(FramePipelineError, match="could not open stream"):
        list(FramePipeline().iter_frames("rtmp://127.0.0.1/live/missing", max_frames=1))


def test_opencv_provider_reads_camera_index_and_marks_camera_metadata(monkeypatch):
    class CameraCapture(_FakeCapture):
        def __init__(self):
            super().__init__(25.0, [0.0])
            self.target = None
            self.release_count = 0

        def release(self):
            self.release_count += 1

    class CameraCV2(_FakeCV2):
        def __init__(self):
            super().__init__(25.0, [0.0])
            self.capture = CameraCapture()

        def VideoCapture(self, target):
            self.capture.target = target
            return self.capture

    fake_cv2 = CameraCV2()
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)

    frames = list(FramePipeline().iter_frames("camera://0", interval_ms=0, max_frames=1))

    assert len(frames) == 1
    assert fake_cv2.capture.target == 0
    assert fake_cv2.capture.release_count == 1
    assert frames[0].metadata["source_kind"] == "camera"
    assert frames[0].metadata["camera_index"] == 0
    assert frames[0].metadata["stream_transport"] == "webcam"


def test_opencv_provider_reports_unavailable_camera_without_mock_fallback(monkeypatch):
    class ClosedCapture:
        def __init__(self):
            self.release_count = 0

        def isOpened(self):
            return False

        def release(self):
            self.release_count += 1

    class ClosedCV2:
        def __init__(self):
            self.capture = ClosedCapture()

        def VideoCapture(self, target):
            assert target == 0
            return self.capture

    fake_cv2 = ClosedCV2()
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)

    with pytest.raises(FramePipelineError, match="could not open camera index 0"):
        list(FramePipeline().iter_frames("camera://0", max_frames=1))
    assert fake_cv2.capture.release_count == 1


def test_opencv_provider_releases_camera_when_cancelled(monkeypatch):
    class CameraCapture(_FakeCapture):
        def __init__(self):
            super().__init__(25.0, [0.0])
            self.release_count = 0

        def release(self):
            self.release_count += 1

    class CameraCV2(_FakeCV2):
        def __init__(self):
            super().__init__(25.0, [0.0])
            self.capture = CameraCapture()

        def VideoCapture(self, target):
            assert target == 0
            return self.capture

    fake_cv2 = CameraCV2()
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    token = CancellationToken()
    token.cancel()

    with pytest.raises(FramePipelineError, match="cancelled"):
        list(FramePipeline().iter_frames("webcam://0", token=token, max_frames=1))
    assert fake_cv2.capture.release_count == 1


def test_opencv_provider_reports_network_stream_without_frames(monkeypatch):
    class EmptyCapture:
        def isOpened(self):
            return True

        def get(self, _property_id):
            return 25.0

        def read(self):
            return False, None

        def release(self):
            pass

    class EmptyCV2:
        CAP_PROP_FPS = 1
        CAP_PROP_POS_MSEC = 2

        def VideoCapture(self, _source):
            return EmptyCapture()

    monkeypatch.setitem(sys.modules, "cv2", EmptyCV2())

    with pytest.raises(FramePipelineError, match="returned no frames"):
        list(FramePipeline().iter_frames("https://127.0.0.1/live/missing.m3u8", max_frames=1))


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
