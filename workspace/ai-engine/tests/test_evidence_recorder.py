from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import pytest

from visual_event_ai.evidence_capture import (
    CLIP_AVAILABLE,
    CLIP_ERROR,
    CLIP_UNAVAILABLE,
    CLIP_UNSUPPORTED,
    EvidenceClipResult,
    EvidenceWindow,
    HttpEvidenceClipUploader,
    RollingEvidenceRecorder,
)


BASE = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)


class _Image:
    shape = (4, 6, 3)


class _FakeWriter:
    def __init__(self, path: Path, *, opened: bool = True, output: bytes = b"encoded-mp4"):
        self.path = path
        self.opened = opened
        self.output = output
        self.frames: list[object] = []
        self.released = False

    def isOpened(self):
        return self.opened

    def write(self, frame):
        self.frames.append(frame)

    def release(self):
        self.released = True
        if self.opened:
            self.path.write_bytes(self.output)


class _WriterFactory:
    def __init__(self, *, opened: bool = True, output: bytes = b"encoded-mp4"):
        self.opened = opened
        self.output = output
        self.writers: list[_FakeWriter] = []

    def __call__(self, path: Path, _fps: float, _size: tuple[int, int], _codec: str):
        writer = _FakeWriter(path, opened=self.opened, output=self.output)
        self.writers.append(writer)
        return writer


def _append_full_window(recorder: RollingEvidenceRecorder, *, event_start=BASE, event_end=BASE + timedelta(seconds=5)):
    for second in range(-10, 16):
        recorder.append_frame(event_start + timedelta(seconds=second), _Image())


def test_event_export_builds_default_and_configured_time_windows(tmp_path):
    factory = _WriterFactory()
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, writer_factory=factory)
    _append_full_window(recorder)

    result = recorder.export_event(BASE, BASE + timedelta(seconds=5))
    assert result.status == CLIP_AVAILABLE
    assert result.window is not None
    assert result.window.started_at == BASE - timedelta(seconds=10)
    assert result.window.ended_at == BASE + timedelta(seconds=15)
    assert result.frame_count == 26
    assert result.clip is not None and result.clip.is_file()
    assert len(factory.writers) == 1
    assert factory.writers[0].frames

    configured = recorder.window_for_event(BASE, BASE, pre_seconds=2, post_seconds=3)
    assert configured.started_at == BASE - timedelta(seconds=2)
    assert configured.ended_at == BASE + timedelta(seconds=3)
    recorder.close()


def test_export_filters_frames_to_window_and_rejects_mismatched_source(tmp_path):
    factory = _WriterFactory()
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, writer_factory=factory)
    for second in range(-2, 4):
        recorder.append_frame(BASE + timedelta(seconds=second), _Image())

    window = recorder.window_for_event(BASE, BASE + timedelta(seconds=1), pre_seconds=1, post_seconds=1)
    result = recorder.export(window)
    assert result.status == CLIP_AVAILABLE
    assert result.frame_count == 4  # -1, 0, 1, 2
    assert len(factory.writers[0].frames) == 4

    with pytest.raises(ValueError, match="does not match"):
        recorder.export(EvidenceWindow("camera-02", BASE - timedelta(seconds=1), BASE + timedelta(seconds=2)))
    recorder.close()


def test_event_export_is_unavailable_until_full_rolling_window_is_buffered(tmp_path):
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, writer_factory=_WriterFactory())
    recorder.append_frame(BASE, _Image())
    result = recorder.export_event(BASE, BASE + timedelta(seconds=1))
    assert result.status == CLIP_UNAVAILABLE
    assert result.clip is None
    assert "complete evidence window" in (result.reason or "")
    recorder.close()


def test_missing_opencv_dependency_is_explicitly_unavailable(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "cv2", None)
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path)
    _append_full_window(recorder)
    result = recorder.export_event(BASE, BASE + timedelta(seconds=5))
    assert result.status == CLIP_UNAVAILABLE
    assert result.uri is None
    assert result.clip is None
    assert "OpenCV/FFmpeg" in (result.reason or "")
    assert list(tmp_path.iterdir()) == []
    recorder.close()


def test_default_output_directory_is_project_owned_and_not_system_temp(monkeypatch):
    monkeypatch.delenv("AI_EVIDENCE_DIR", raising=False)
    recorder = RollingEvidenceRecorder("camera-01")
    expected = Path(__file__).resolve().parents[1] / "runtime" / "evidence"
    assert recorder.output_dir == expected
    assert recorder.output_dir != Path(__import__("tempfile").gettempdir())
    recorder.close()


def test_non_image_fixture_payload_is_unsupported_without_fabricating_media(tmp_path):
    recorder = RollingEvidenceRecorder("fixture-camera", output_dir=tmp_path, writer_factory=_WriterFactory())
    for second in range(-10, 16):
        recorder.append_frame(BASE + timedelta(seconds=second), {"fixture": second})
    result = recorder.export_event(BASE, BASE + timedelta(seconds=5))
    assert result.status == CLIP_UNSUPPORTED
    assert result.clip is None
    assert result.uri is None
    assert list(tmp_path.iterdir()) == []
    recorder.close()


def test_writer_failure_and_size_limit_release_resources_and_remove_temp_clip(tmp_path):
    closed_factory = _WriterFactory(opened=False)
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, writer_factory=closed_factory)
    _append_full_window(recorder)
    unavailable = recorder.export_event(BASE, BASE + timedelta(seconds=5))
    assert unavailable.status == CLIP_UNSUPPORTED
    assert closed_factory.writers[0].released is True
    assert list(tmp_path.iterdir()) == []
    recorder.close()

    oversized_factory = _WriterFactory(output=b"0123456789")
    limited = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, max_bytes=4, writer_factory=oversized_factory)
    _append_full_window(limited)
    oversized = limited.export_event(BASE, BASE + timedelta(seconds=5))
    assert oversized.status == CLIP_ERROR
    assert oversized.bytes_written == 10
    assert "max_bytes" in (oversized.reason or "")
    assert oversized_factory.writers[0].released is True
    assert list(tmp_path.iterdir()) == []
    limited.close()


def test_close_removes_owned_clips_and_rejects_new_frames(tmp_path):
    factory = _WriterFactory()
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, writer_factory=factory)
    _append_full_window(recorder)
    result = recorder.export_event(BASE, BASE + timedelta(seconds=5))
    assert result.clip is not None and result.clip.exists()
    recorder.close()
    assert not result.clip.exists()
    assert recorder.closed is True
    with pytest.raises(RuntimeError, match="closed"):
        recorder.append_frame(BASE, _Image())
    recorder.close()  # idempotent cleanup


def test_upload_event_passes_evidence_window_and_generated_clip_to_uploader(tmp_path):
    factory = _WriterFactory()
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, writer_factory=factory)
    _append_full_window(recorder)
    seen: dict[str, object] = {}

    class Uploader:
        async def upload(self, window, clip):
            seen["window"] = window
            seen["clip"] = clip
            assert isinstance(clip, Path)
            assert clip.is_file()
            return type("UploadResult", (), {"status": "available", "uri": "https://makerverse/evidence/1", "reason": None})()

    result = asyncio.run(recorder.upload_event(BASE, BASE + timedelta(seconds=5), Uploader()))
    assert result.status == "available"
    assert result.uri == "https://makerverse/evidence/1"
    assert seen["window"].started_at == BASE - timedelta(seconds=10)
    assert isinstance(seen["clip"], Path)
    assert not seen["clip"].exists()  # recorder cleans generated media after upload
    recorder.close()


def test_upload_event_accepts_bytes_and_fixture_path_without_changing_uploader_contract(tmp_path):
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, writer_factory=_WriterFactory())
    fixture = tmp_path / "fixture.mp4"
    fixture.write_bytes(b"fixture-bytes")
    seen: list[object] = []

    class Uploader:
        async def upload(self, window, clip):
            seen.append((window, clip))
            return type("UploadResult", (), {"status": "available", "uri": "https://makerverse/evidence/fixture", "reason": None})()

    result_bytes = asyncio.run(
        recorder.upload_event(BASE, BASE, Uploader(), pre_seconds=0, post_seconds=0, clip=b"clip-bytes")
    )
    result_path = asyncio.run(
        recorder.upload_event(BASE, BASE, Uploader(), pre_seconds=0, post_seconds=0, clip=fixture)
    )
    assert result_bytes.uri.endswith("fixture")
    assert result_path.uri.endswith("fixture")
    assert seen[0][1] == b"clip-bytes"
    assert seen[1][1] == fixture
    recorder.close()


def test_http_uploader_still_accepts_fixture_path(tmp_path):
    fixture = tmp_path / "clip.mp4"
    fixture.write_bytes(b"fixture-clip")
    uploader = HttpEvidenceClipUploader("http://makerverse/evidence")

    async def run():
        try:
            return await uploader.upload(
                recorder_window := RollingEvidenceRecorder("camera-01", writer_factory=_WriterFactory()).window_for_event(BASE, BASE),
                fixture,
            )
        finally:
            await uploader.aclose()

    # No network endpoint is expected in this unit test; an actual request is
    # not made because the uploader's client is replaced before invocation.
    # This verifies the path is accepted by the unchanged payload adapter.
    class Client:
        async def post(self, *_args, **_kwargs):
            return type("Response", (), {"raise_for_status": lambda self: None, "json": lambda self: {"uri": "http://makerverse/evidence/1"}})()

        async def aclose(self):
            return None

    uploader.client = Client()
    result = asyncio.run(run())
    assert result.uri == "http://makerverse/evidence/1"
