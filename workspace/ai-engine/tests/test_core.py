import json
from datetime import datetime, timezone
from threading import Event, Thread
from time import sleep

from visual_event_ai.fact_pipeline import FrameFactExtractor
from visual_event_ai.frame_pipeline import Frame, FramePipeline
from visual_event_ai.models import PrimitiveFact, ReviewStatus, UnifiedEvent
from visual_event_ai.plugins import PluginManager, mock_facts
from visual_event_ai.service import AnalysisService
from visual_event_ai.storage import SQLiteStore
from visual_event_ai.sources import SourceResolver


def test_plugin_discovery_and_parallel_evaluation(tmp_path):
    manager = PluginManager("plugins")
    views = manager.scan()
    assert {view.plugin_id for view in views} == {"elderly_care", "workshop"}
    events = manager.evaluate(mock_facts("mock://elderly-medication"), "camera-01")
    assert [event.event_type for event in events] == ["suspected_medication"]


def test_sqlite_event_review_roundtrip(tmp_path):
    manager = PluginManager("plugins")
    manager.scan()
    store = SQLiteStore(tmp_path / "events.db")
    service = AnalysisService(store, manager)
    job = service.create_job("mock://workshop-tool", None, {})
    completed = service.run_job(job.job_id)
    assert completed.status == "completed"
    event = store.list_events()[0]
    reviewed = store.review_event(event.event_id, ReviewStatus.CONFIRMED, "fixture review")
    assert reviewed is not None
    assert reviewed.review_status == ReviewStatus.CONFIRMED
    assert reviewed.metadata["review_note"] == "fixture review"


def test_sqlite_event_and_job_metadata_redact_pixel_arrays(tmp_path):
    store = SQLiteStore(tmp_path / "privacy.db")
    event = UnifiedEvent(
        plugin_id="workshop",
        plugin_version="0.1.0",
        event_type="object_removed",
        title="物品离开登记区域",
        description="fixture",
        source_id="fixture://privacy",
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ended_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
        confidence=0.8,
        facts=[
            PrimitiveFact(
                fact_type="object_removed",
                timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
                metadata={"rawPixels": [[1, 2]]},
            )
        ],
        metadata={"thermal_map": [[3, 4]]},
    )

    store.save_event(event)
    job = AnalysisService(store, PluginManager("plugins")).create_job(
        "fixture://privacy",
        None,
        {"rawPixels": [[5, 6]]},
    )

    stored = store.get_event(event.event_id)
    assert stored is not None
    assert stored.metadata["thermal_map"] == {
        "encoding": "redacted-thermal",
        "shape": [1, 2],
    }
    assert stored.facts[0].metadata["rawPixels"] == {
        "encoding": "redacted-pixels",
        "shape": [1, 2],
    }
    assert job.metadata["rawPixels"] == {
        "encoding": "redacted-pixels",
        "shape": [1, 2],
    }


def test_local_frame_job_uses_frame_fact_extractor(tmp_path):
    fixture = tmp_path / "objects.jsonl"
    fixture.write_text('{"payload":{"objects":[{"label":"电钻","confidence":0.9,"bbox":[1,1,4,4]}]}}\n', encoding="utf-8")
    manager = PluginManager("plugins")
    manager.scan()
    service = AnalysisService(SQLiteStore(tmp_path / "local.db"), manager)
    job = service.create_job(str(fixture), None, {})
    completed = service.run_job(job.job_id)
    assert completed.status == "completed"
    assert completed.metadata["fact_count"] == 1


def test_local_frame_job_emits_only_incomplete_medication_cue_without_action_model(tmp_path):
    fixture = tmp_path / "person_and_medicine.jsonl"
    records = [
        {
            "timestamp": f"2026-01-01T00:00:0{index}Z",
            "payload": {
                "objects": [
                    {"label": "家属", "confidence": 0.9, "bbox": [0, 0, 6, 6]},
                    {"label": "medicine bottle", "confidence": 0.85, "bbox": [10, 0, 6, 6]},
                ]
            },
        }
        for index in range(2)
    ]
    fixture.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )
    manager = PluginManager("plugins")
    manager.scan()
    store = SQLiteStore(tmp_path / "temporal.jsonl.db")
    service = AnalysisService(store, manager)
    job = service.run_job(service.create_job(str(fixture), None, {}).job_id)

    assert job.status == "completed"
    events = store.list_events()
    assert [event.event_type for event in events] == ["incomplete_medication_sequence"]
    assert events[0].metadata["sequence_complete"] is False
    assert events[0].metadata["needs_review"] is True


def test_local_keypoint_fixture_runs_complete_medication_reasoning_path(tmp_path):
    fixture = tmp_path / "keypoint_medicine.jsonl"
    records = [
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "payload": {
                "objects": [
                    {
                        "label": "家属",
                        "confidence": 0.95,
                        "bbox": [0, 0, 40, 100],
                        "keypoints": {
                            "nose": [20, 20, 0.95],
                            "left_wrist": [70, 80, 0.95],
                            "right_wrist": [35, 75, 0.9],
                        },
                    },
                    {"label": "medicine bottle", "confidence": 0.85, "bbox": [18, 20, 8, 10]},
                ]
            },
        },
        {
            "timestamp": "2026-01-01T00:00:01Z",
            "payload": {
                "objects": [
                    {
                        "label": "家属",
                        "confidence": 0.95,
                        "bbox": [0, 0, 40, 100],
                        "keypoints": {
                            "nose": [20, 20, 0.95],
                            "left_wrist": [20, 25, 0.9],
                            "right_wrist": [35, 75, 0.9],
                        },
                    },
                    {"label": "medicine bottle", "confidence": 0.85, "bbox": [18, 20, 8, 10]},
                ]
            },
        },
        {
            "timestamp": "2026-01-01T00:00:02Z",
            "payload": {
                "objects": [
                    {
                        "label": "家属",
                        "confidence": 0.95,
                        "bbox": [0, 0, 40, 100],
                        "keypoints": {
                            "nose": [20, 20, 0.95],
                            "left_wrist": [70, 80, 0.95],
                            "right_wrist": [35, 75, 0.9],
                        },
                    },
                    {"label": "medicine bottle", "confidence": 0.85, "bbox": [18, 20, 8, 10]},
                ]
            },
        },
        {
            "timestamp": "2026-01-01T00:00:03Z",
            "payload": {
                "objects": [
                    {
                        "label": "家属",
                        "confidence": 0.95,
                        "bbox": [0, 0, 40, 100],
                        "keypoints": {
                            "nose": [20, 20, 0.95],
                            "left_wrist": [20, 25, 0.9],
                            "right_wrist": [35, 75, 0.9],
                        },
                    },
                    {"label": "medicine bottle", "confidence": 0.85, "bbox": [18, 20, 8, 10]},
                ]
            },
        },
    ]
    fixture.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

    manager = PluginManager("plugins")
    manager.scan()
    store = SQLiteStore(tmp_path / "keypoint-analysis.db")
    service = AnalysisService(store, manager)
    job = service.run_job(service.create_job(str(fixture), None, {}).job_id)

    assert job.status == "completed"
    events = store.list_events()
    assert [event.event_type for event in events] == ["suspected_medication"]
    event = events[0]
    assert event.review_status == ReviewStatus.PENDING
    assert event.metadata["needs_review"] is True
    assert event.metadata["medical_diagnosis"] is False
    action = next(item for item in event.facts if item.fact_type == "hand_to_face")
    assert action.metadata["action_extractor"] == "keypoint-distance-v1"
    assert sum(item.fact_type == "hand_to_face" for item in event.facts) == 1
    assert events[0].confidence <= 0.85


def test_stopped_job_does_not_run_plugins_or_save_events(tmp_path):
    manager = PluginManager("plugins")
    manager.scan()
    store = SQLiteStore(tmp_path / "stopped.db")
    service = AnalysisService(store, manager)
    job = service.create_job("mock://elderly-medication", None, {})
    stopped = service.stop_job(job.job_id)
    assert stopped is not None and stopped.status == "stopped"
    after_run = service.run_job(job.job_id)
    assert after_run.status == "stopped"
    assert store.list_events() == []


def test_completed_job_rerun_does_not_duplicate_events(tmp_path):
    manager = PluginManager("plugins")
    manager.scan()
    store = SQLiteStore(tmp_path / "completed-idempotency.db")
    service = AnalysisService(store, manager)
    job = service.create_job("mock://elderly-medication", None, {})

    completed = service.run_job(job.job_id)
    first_event_ids = [event.event_id for event in store.list_events()]
    rerun = service.run_job(job.job_id)

    assert completed.status == "completed"
    assert rerun.status == "completed"
    assert rerun.event_ids == completed.event_ids
    assert [event.event_id for event in store.list_events()] == first_event_ids


def test_stop_racing_with_atomic_completion_returns_completed(tmp_path):
    class BlockingCompletionStore(SQLiteStore):
        def __init__(self, path):
            super().__init__(path)
            self.completion_started = Event()
            self.allow_completion = Event()

        def complete_job(self, job, events):
            self.completion_started.set()
            if not self.allow_completion.wait(timeout=3):
                raise TimeoutError("test did not release completion transaction")
            return super().complete_job(job, events)

    manager = PluginManager("plugins")
    manager.scan()
    store = BlockingCompletionStore(tmp_path / "stop-completion-race.db")
    service = AnalysisService(store, manager)
    job = service.create_job("mock://elderly-medication", None, {})
    run_results = []
    run_thread = Thread(target=lambda: run_results.append(service.run_job(job.job_id)), daemon=True)
    run_thread.start()
    assert store.completion_started.wait(timeout=2)

    stop_started = Event()
    stop_results = []

    def request_stop():
        stop_started.set()
        stop_results.append(service.stop_job(job.job_id))

    stop_thread = Thread(target=request_stop, daemon=True)
    stop_thread.start()
    assert stop_started.wait(timeout=2)
    try:
        # The atomic event/job completion has acquired the commit guard first.
        assert stop_results == []
    finally:
        store.allow_completion.set()
        run_thread.join(timeout=2)
        stop_thread.join(timeout=2)

    assert not run_thread.is_alive()
    assert not stop_thread.is_alive()
    assert run_results[0].status == "completed"
    assert stop_results[0] is not None and stop_results[0].status == "completed"
    assert store.list_events()


def test_stopping_running_frame_job_cancels_provider_and_finishes_as_stopped(tmp_path):
    class WaitingFrameProvider:
        def __init__(self):
            self.waiting_after_first_frame = Event()

        def iter_frames(self, source, *, interval, max_frames, token, recover):
            yield Frame(
                source,
                0,
                datetime(2026, 1, 1, tzinfo=timezone.utc),
                {"gray": [[0, 0], [0, 0]]},
                {"provider": "stop-test"},
            )
            self.waiting_after_first_frame.set()
            while not token.cancelled:
                sleep(0.001)
            token.raise_if_cancelled()

    manager = PluginManager("plugins")
    manager.scan()
    store = SQLiteStore(tmp_path / "running-stop.db")
    service = AnalysisService(store, manager)
    frame_provider = WaitingFrameProvider()
    service.frame_facts = FrameFactExtractor(
        pipeline=FramePipeline(providers={"file": frame_provider})
    )
    job = service.create_job("camera-stop-test", None, {})
    results = []
    worker = Thread(target=lambda: results.append(service.run_job(job.job_id)), daemon=True)
    worker.start()

    try:
        assert frame_provider.waiting_after_first_frame.wait(timeout=2)
        stopped = service.stop_job(job.job_id)
        assert stopped is not None and stopped.status == "stopped"
        worker.join(timeout=2)
        assert not worker.is_alive()
    finally:
        if worker.is_alive():
            service.stop_job(job.job_id)
            worker.join(timeout=2)

    final_job = store.get_job(job.job_id)
    assert results and results[0].status == "stopped"
    assert final_job is not None and final_job.status == "stopped"
    assert store.list_events() == []


def test_source_resolver_routes_without_decoding():
    resolver = SourceResolver()
    assert resolver.inspect("mock://elderly-medication").provider == "mock-provider"
    stream = resolver.inspect("rtmp://127.0.0.1/live/demo")
    assert stream.kind == "stream"
    assert stream.status == "configured"
    assert stream.provider == "opencv-stream-provider"
    assert "realtime-frames" in stream.capabilities
    assert resolver.inspect("C:/does-not-exist.mp4").status == "unavailable"
