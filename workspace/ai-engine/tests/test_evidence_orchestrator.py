from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

from visual_event_ai.evidence_capture import EvidenceUploadResult
from visual_event_ai.evidence_capture import HttpEvidenceClipUploader
from visual_event_ai.evidence_orchestrator import (
    CAPTURE_AVAILABLE,
    CAPTURE_DISABLED,
    CAPTURE_UNAVAILABLE,
    EvidenceCaptureOrchestrator,
)
from visual_event_ai.evidence_recorder import RollingEvidenceRecorder
from visual_event_ai.frame_pipeline import FramePipeline


BASE = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class _Event:
    event_id: str
    source_id: str
    started_at: datetime
    ended_at: datetime


class _Image:
    shape = (4, 6, 3)


class _FakeWriter:
    def __init__(self, path: Path):
        self.path = path
        self.frames: list[object] = []
        self.released = False

    def isOpened(self):
        return True

    def write(self, frame):
        self.frames.append(frame)

    def release(self):
        self.released = True
        self.path.write_bytes(b"encoded-mp4")


class _WriterFactory:
    def __init__(self):
        self.writers: list[_FakeWriter] = []

    def __call__(self, path: Path, _fps: float, _size: tuple[int, int], _codec: str):
        writer = _FakeWriter(path)
        self.writers.append(writer)
        return writer


class _Uploader:
    def __init__(self):
        self.windows = []
        self.clips: list[Path] = []

    async def upload(self, window, clip):
        assert isinstance(clip, Path)
        assert clip.is_file()
        self.windows.append(window)
        self.clips.append(clip)
        return EvidenceUploadResult("available", f"https://makerverse/evidence/{len(self.windows)}")


class _TrackingClient:
    def __init__(self, urls: list[str]):
        self.urls = urls
        self.closed = False

    async def post(self, url, **_kwargs):
        self.urls.append(str(url))
        request = httpx.Request("POST", str(url))
        return httpx.Response(200, json={"status": "available", "uri": f"{url}/clip"}, request=request)

    async def aclose(self):
        self.closed = True


def _event(event_id: str, source_id: str = "camera-01", offset: int = 0) -> _Event:
    timestamp = BASE + timedelta(seconds=offset)
    return _Event(event_id, source_id, timestamp, timestamp)


def test_disabled_hook_does_not_observe_or_upload(tmp_path):
    factory = _WriterFactory()
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, writer_factory=factory)
    uploader = _Uploader()
    hook = EvidenceCaptureOrchestrator(recorder, uploader, enabled=False, pre_seconds=0, post_seconds=0)

    assert hook.observe_frame(type("Frame", (), {"timestamp": BASE, "payload": _Image(), "source_id": "camera-01"})()) is None
    assert recorder.buffered_frames == 0
    result = asyncio.run(hook.capture_event(_event("event-disabled")))

    assert result.status == CAPTURE_DISABLED
    assert result.uri is None
    assert uploader.windows == []
    hook.close()


def test_enabled_hook_without_recorder_is_explicitly_unavailable():
    hook = EvidenceCaptureOrchestrator(enabled=True)
    result = asyncio.run(hook.capture_events([_event("event-no-recorder")]))

    assert len(result) == 1
    assert result[0].status == CAPTURE_UNAVAILABLE
    assert "recorder" in (result[0].reason or "")


def test_source_mismatch_fails_closed_without_uploader_call(tmp_path):
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, writer_factory=_WriterFactory())
    uploader = _Uploader()
    hook = EvidenceCaptureOrchestrator(recorder, uploader, enabled=True, pre_seconds=0, post_seconds=0)
    hook.observe_frame(type("Frame", (), {"timestamp": BASE, "payload": _Image(), "source_id": "camera-01"})())

    result = asyncio.run(hook.capture_event(_event("event-other-source", source_id="camera-02")))

    assert result.status == CAPTURE_UNAVAILABLE
    assert "does not match" in (result.reason or "")
    assert uploader.windows == []
    hook.close()


def test_fixture_payload_without_opencv_is_unavailable_and_creates_no_media(tmp_path):
    fixture = tmp_path / "frames.jsonl"
    fixture.write_text(
        '{"timestamp":"2026-01-01T08:00:00Z","payload":{"fixture":"cpu-only"}}\n',
        encoding="utf-8",
    )
    source = str(fixture)
    recorder = RollingEvidenceRecorder(source, output_dir=tmp_path / "evidence")
    hook = EvidenceCaptureOrchestrator(recorder, enabled=True, pre_seconds=0, post_seconds=0)

    for frame in FramePipeline().iter_frames(source, interval_ms=0, max_frames=1):
        hook.observe_frame(frame)

    result = asyncio.run(hook.capture_event(_event("event-fixture", source_id=source)))

    assert result.status == CAPTURE_UNAVAILABLE
    assert "usable OpenCV image" in (result.reason or "")
    assert not (tmp_path / "evidence").exists()
    hook.close()


def test_capture_events_uploads_in_order_and_cleans_generated_clips(tmp_path):
    factory = _WriterFactory()
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, writer_factory=factory)
    uploader = _Uploader()
    hook = EvidenceCaptureOrchestrator(recorder, uploader, enabled=True, pre_seconds=0, post_seconds=0)
    for offset in (0, 30):
        hook.append_frame(BASE + timedelta(seconds=offset), _Image(), source_id="camera-01")

    results = asyncio.run(hook.capture_events([_event("event-1"), _event("event-2", offset=30)]))

    assert [item.status for item in results] == [CAPTURE_AVAILABLE, CAPTURE_AVAILABLE]
    assert [item.event_id for item in results] == ["event-1", "event-2"]
    assert [window.started_at for window in uploader.windows] == [BASE, BASE + timedelta(seconds=30)]
    assert all(writer.released for writer in factory.writers)
    assert all(not clip.exists() for clip in uploader.clips)
    assert list(tmp_path.iterdir()) == []
    hook.close()


def test_close_cleans_owned_clip_when_capture_is_not_uploaded(tmp_path):
    factory = _WriterFactory()
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, writer_factory=factory)
    hook = EvidenceCaptureOrchestrator(recorder, enabled=True, pre_seconds=0, post_seconds=0)
    hook.append_frame(BASE, _Image(), source_id="camera-01")
    exported = recorder.export_event(BASE, BASE, pre_seconds=0, post_seconds=0)
    assert exported.clip is not None and exported.clip.exists()

    hook.close()

    assert not exported.clip.exists()
    assert recorder.closed is True


def test_per_event_http_uploader_factory_binds_distinct_event_urls_and_closes_clients(tmp_path):
    factory = _WriterFactory()
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, writer_factory=factory)
    urls: list[str] = []
    clients: list[_TrackingClient] = []

    def uploader_factory(event_id: str):
        client = _TrackingClient(urls)
        clients.append(client)
        uploader = HttpEvidenceClipUploader(
            base_url="http://makerverse",
            event_id=event_id,
            client=client,
        )
        # The factory owns one client per event and asks the uploader to close
        # it after that event.  The production constructor still defaults to
        # ownership=False for injected clients.
        uploader._owns_client = True
        return uploader

    hook = EvidenceCaptureOrchestrator(
        recorder,
        enabled=True,
        pre_seconds=0,
        post_seconds=0,
        uploader_factory=uploader_factory,
    )
    hook.append_frame(BASE, _Image(), source_id="camera-01")
    hook.append_frame(BASE + timedelta(seconds=30), _Image(), source_id="camera-01")

    results = asyncio.run(hook.capture_events([_event("event-1"), _event("event-2", offset=30)]))

    assert [result.status for result in results] == [CAPTURE_AVAILABLE, CAPTURE_AVAILABLE]
    assert [result.uri for result in results] == [url + "/clip" for url in urls]
    assert urls == [
        "http://makerverse/api/v1/events/event-1/evidence",
        "http://makerverse/api/v1/events/event-2/evidence",
    ]
    assert all(client.closed for client in clients)
    assert all(not clip.exists() for clip in factory.writers[0].path.parent.glob("*.mp4"))
    hook.close()


def test_fixed_event_uploader_mismatch_fails_closed_without_second_http_post(tmp_path):
    factory = _WriterFactory()
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, writer_factory=factory)
    urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        urls.append(str(request.url))
        return httpx.Response(200, json={"status": "available", "uri": "http://makerverse/evidence/1"}, request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    uploader = HttpEvidenceClipUploader(
        base_url="http://makerverse",
        event_id="event-1",
        client=client,
    )
    hook = EvidenceCaptureOrchestrator(recorder, uploader, enabled=True, pre_seconds=0, post_seconds=0)
    hook.append_frame(BASE, _Image(), source_id="camera-01")
    hook.append_frame(BASE + timedelta(seconds=30), _Image(), source_id="camera-01")

    results = asyncio.run(hook.capture_events([_event("event-1"), _event("event-2", offset=30)]))

    assert results[0].status == CAPTURE_AVAILABLE
    assert results[1].status == CAPTURE_UNAVAILABLE
    assert "bound to event_id" in (results[1].reason or "")
    assert urls == ["http://makerverse/api/v1/events/event-1/evidence"]
    asyncio.run(hook.aclose())


def test_available_without_uri_is_not_a_success(tmp_path):
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, writer_factory=_WriterFactory())

    class MissingUriUploader:
        async def upload(self, _window, _clip):
            return EvidenceUploadResult("available", None)

    hook = EvidenceCaptureOrchestrator(
        recorder,
        MissingUriUploader(),
        enabled=True,
        pre_seconds=0,
        post_seconds=0,
    )
    hook.append_frame(BASE, _Image(), source_id="camera-01")

    result = asyncio.run(hook.capture_event(_event("event-no-uri")))

    assert result.status == "error"
    assert result.available is False
    assert "without a usable URI" in (result.reason or "")
    hook.close()


def test_per_event_upload_failure_closes_uploader_and_removes_generated_clip(tmp_path):
    recorder = RollingEvidenceRecorder("camera-01", output_dir=tmp_path, writer_factory=_WriterFactory())
    created: list[object] = []

    class FailingUploader:
        def __init__(self):
            self.closed = False

        async def upload(self, _window, clip):
            assert isinstance(clip, Path)
            assert clip.exists()
            raise OSError("remote evidence endpoint failed")

        async def aclose(self):
            self.closed = True

    def uploader_factory(_event_id: str):
        uploader = FailingUploader()
        created.append(uploader)
        return uploader

    hook = EvidenceCaptureOrchestrator(
        recorder,
        enabled=True,
        pre_seconds=0,
        post_seconds=0,
        uploader_factory=uploader_factory,
    )
    hook.append_frame(BASE, _Image(), source_id="camera-01")

    result = asyncio.run(hook.capture_event(_event("event-failure")))

    assert result.status == "error"
    assert "remote evidence endpoint failed" in (result.reason or "")
    assert created and created[0].closed is True
    assert list(tmp_path.iterdir()) == []
    hook.close()
