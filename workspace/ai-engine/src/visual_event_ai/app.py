from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    AnalysisJobCreate,
    AnalysisJobView,
    PluginView,
    RegisteredObject,
    RegisteredObjectCreate,
    RegisteredPerson,
    RegisteredPersonCreate,
    ReviewRequest,
    FrameView,
    ObservationView,
    EvidenceResolution,
    DetectorProviderView,
    SourceInspection,
    UnifiedEvent,
    RegistryMatchRequest,
    RegistryMatchView,
)
from .makerverse_client import MakerverseClient
from .plugins import PluginManager
from .service import AnalysisService
from .sources import SourceResolver
from .zone_config import parse_zones_json
from .frame_pipeline import FramePipeline, FramePipelineError
from .providers import CentroidTracker, FixtureDetector, MotionDetector, normalize_observations
from .evidence import EvidenceResolver
from .model_providers import DetectorProviderRegistry
from .storage import SQLiteStore
from .embeddings import EmbeddingError, gray_embedding, match_embeddings
from .privacy import sanitize_sensitive_payload


def _frame_payload_for_api(payload: object) -> object:
    """Return frame metadata without exposing nested raw image/pixel arrays."""

    return sanitize_sensitive_payload(payload)


def create_app() -> FastAPI:
    root = Path(__file__).resolve().parents[2]
    db_path = Path(os.getenv("AI_DB_PATH", root / "runtime" / "events.db"))
    plugin_dir = Path(os.getenv("PLUGIN_DIR", root / "plugins"))
    plugins = PluginManager(plugin_dir)
    plugins.scan()
    zones = parse_zones_json(os.getenv("AI_ZONES_JSON"))
    store = SQLiteStore(db_path)
    service = AnalysisService(store, plugins, zones=zones)
    sources = SourceResolver()
    frame_pipeline = FramePipeline()
    evidence = EvidenceResolver()
    detectors = DetectorProviderRegistry()

    # Makerverse client (optional, for pushing events)
    makerverse_url = os.getenv("MAKERVERSE_URL")
    if makerverse_url:
        makerverse = MakerverseClient(
            makerverse_url,
            live_id=os.getenv("MAKERVERSE_LIVE_ID"),
            retries=int(os.getenv("MAKERVERSE_RETRIES", "2")),
        )
        # Pass makerverse client to store for event pushing
        store.makerverse = makerverse

    app = FastAPI(title="Visual Event AI", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.analysis = service

    @app.on_event("shutdown")
    async def shutdown_makerverse() -> None:
        # Drain loop-owned pushes and the sync worker before closing the app.
        await store.shutdown()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "visual-event-ai", "version": "0.1.0"}

    @app.get("/ready")
    def ready() -> dict[str, object]:
        detector_states = detectors.statuses()
        detector_ready = any(item.selected and item.available for item in detector_states)
        return {
            "ready": bool(db_path.parent.exists() and detector_ready),
            "status": "ready" if detector_ready else "degraded",
            "database": "ok" if db_path.parent.exists() else "unavailable",
            "plugin_manager": "ok" if plugins.records else "degraded",
            "detector": "ok" if detector_ready else "degraded",
            "tracker": "ok",
            "plugins": len(plugins.records),
        }

    @app.get("/api/v1/sources/inspect", response_model=SourceInspection)
    def inspect_source(source: str = Query(min_length=1)) -> SourceInspection:
        descriptor = sources.inspect(source)
        return SourceInspection(
            source_id=descriptor.source_id,
            kind=descriptor.kind,
            provider=descriptor.provider,
            status=descriptor.status,
            uri=descriptor.uri,
            capabilities=list(descriptor.capabilities),
            reason=descriptor.reason,
        )

    @app.get("/api/v1/sources/frames", response_model=list[FrameView])
    def preview_frames(
        source: str = Query(min_length=1),
        max_frames: int = Query(default=8, ge=1, le=64),
        interval_ms: int = Query(default=1000, ge=0, le=60000),
    ) -> list[FrameView]:
        try:
            return [
                FrameView(
                    source_id=frame.source_id,
                    frame_index=frame.frame_index,
                    timestamp=frame.timestamp,
                    payload=_frame_payload_for_api(frame.payload),
                    metadata=frame.metadata,
                )
                for frame in frame_pipeline.iter_frames(source, interval_ms=interval_ms, max_frames=max_frames)
            ]
        except (FramePipelineError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/vision/preview", response_model=list[ObservationView])
    def preview_vision(
        source: str = Query(min_length=1),
        detector: str = Query(default="fixture", pattern="^(fixture|motion)$"),
        max_frames: int = Query(default=8, ge=1, le=64),
    ) -> list[ObservationView]:
        selected_detector = FixtureDetector() if detector == "fixture" else MotionDetector()
        tracker = CentroidTracker()
        try:
            observations = []
            for frame in frame_pipeline.iter_frames(source, max_frames=max_frames):
                detections = selected_detector.detect(frame)
                observations.extend(normalize_observations(frame, detections, tracker.update(detections)))
            return [
                ObservationView.model_validate(
                    {
                        **observation.__dict__,
                        "metadata": sanitize_sensitive_payload(observation.metadata),
                    }
                )
                for observation in observations
            ]
        except (FramePipelineError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/evidence/resolve", response_model=EvidenceResolution)
    def resolve_evidence(
        source_id: str = Query(min_length=1),
        started_at: datetime = Query(),
        ended_at: datetime = Query(),
        uri: str | None = Query(default=None),
    ) -> EvidenceResolution:
        try:
            result = evidence.resolve(source_id, started_at, ended_at, uri)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return EvidenceResolution(
            source_id=result.source_id,
            started_at=result.started_at,
            ended_at=result.ended_at,
            resolver=result.resolver,
            status=result.status,
            uri=result.uri,
            reason=result.reason,
        )

    @app.get("/api/v1/providers/detectors", response_model=list[DetectorProviderView])
    def list_detector_providers(source: str | None = Query(default=None)) -> list[DetectorProviderView]:
        return [DetectorProviderView(**status.__dict__) for status in detectors.statuses(source)]

    @app.get("/api/v1/plugins", response_model=list[PluginView])
    def list_plugins() -> list[PluginView]:
        return plugins.list()

    @app.post("/api/v1/plugins/{plugin_id}/enable", response_model=PluginView)
    def enable_plugin(plugin_id: str) -> PluginView:
        try:
            return plugins.set_enabled(plugin_id, True)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"plugin not found: {plugin_id}") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/v1/plugins/{plugin_id}/disable", response_model=PluginView)
    def disable_plugin(plugin_id: str) -> PluginView:
        try:
            return plugins.set_enabled(plugin_id, False)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"plugin not found: {plugin_id}") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/v1/analysis/jobs", response_model=AnalysisJobView, status_code=202)
    def create_job(request: AnalysisJobCreate, tasks: BackgroundTasks) -> AnalysisJobView:
        unknown = [p for p in (request.plugin_ids or []) if p not in plugins.records]
        if unknown:
            raise HTTPException(status_code=400, detail=f"unknown plugins: {unknown}")
        job = service.create_job(request.source, request.plugin_ids, request.metadata)
        tasks.add_task(service.run_job, job.job_id)
        return job

    @app.get("/api/v1/analysis/jobs", response_model=list[AnalysisJobView])
    def list_jobs() -> list[AnalysisJobView]:
        return service.store.list_jobs()

    @app.get("/api/v1/analysis/jobs/{job_id}", response_model=AnalysisJobView)
    def get_job(job_id: str) -> AnalysisJobView:
        job = service.store.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return job

    @app.post("/api/v1/analysis/jobs/{job_id}/stop", response_model=AnalysisJobView)
    def stop_job(job_id: str) -> AnalysisJobView:
        job = service.stop_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return job

    @app.get("/api/v1/events", response_model=list[UnifiedEvent])
    def list_events(
        plugin_id: str | None = None,
        review_status: str | None = None,
        limit: int = Query(default=100, ge=1, le=500),
    ) -> list[UnifiedEvent]:
        return service.store.list_events(plugin_id, review_status)[:limit]

    @app.get("/api/v1/events/{event_id}", response_model=UnifiedEvent)
    def get_event(event_id: str) -> UnifiedEvent:
        event = service.store.get_event(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="event not found")
        return event

    @app.post("/api/v1/events/{event_id}/review", response_model=UnifiedEvent)
    @app.patch("/api/v1/events/{event_id}/review", response_model=UnifiedEvent)
    def review_event(event_id: str, request: ReviewRequest) -> UnifiedEvent:
        event = service.store.review_event(event_id, request.status, request.note)
        if event is None:
            raise HTTPException(status_code=404, detail="event not found")
        return event

    @app.get("/api/v1/objects", response_model=list[RegisteredObject])
    def list_objects() -> list[RegisteredObject]:
        """List registered objects. Proxy to Makerverse if available, else local SQLite."""
        if makerverse_url and os.getenv("MAKERVERSE_PROXY_REGISTRY") == "1":
            try:
                import httpx
                response = httpx.get(f"{makerverse_url}/api/v1/objects", timeout=5.0)
                response.raise_for_status()
                return response.json()
            except Exception:
                pass  # Fallback to local
        return service.store.list_objects()

    @app.post("/api/v1/objects", response_model=RegisteredObject, status_code=201)
    def create_object(request: RegisteredObjectCreate) -> RegisteredObject:
        """Register a new object. Proxy to Makerverse if available, else local SQLite."""
        if makerverse_url and os.getenv("MAKERVERSE_PROXY_REGISTRY") == "1":
            try:
                import httpx
                response = httpx.post(f"{makerverse_url}/api/v1/objects", json=request.model_dump(), timeout=5.0)
                response.raise_for_status()
                return response.json()
            except Exception:
                pass  # Fallback to local
        try:
            return service.store.save_object(request)
        except EmbeddingError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/v1/objects/{object_id}", status_code=204, response_class=Response)
    def delete_object(object_id: str) -> Response:
        if not service.store.delete_object(object_id):
            raise HTTPException(status_code=404, detail="object not found")
        return Response(status_code=204)

    @app.get("/api/v1/persons", response_model=list[RegisteredPerson])
    def list_persons() -> list[RegisteredPerson]:
        """List registered persons. Proxy to Makerverse if available, else local SQLite."""
        if makerverse_url and os.getenv("MAKERVERSE_PROXY_REGISTRY") == "1":
            try:
                import httpx
                response = httpx.get(f"{makerverse_url}/api/v1/persons", timeout=5.0)
                response.raise_for_status()
                return response.json()
            except Exception:
                pass  # Fallback to local
        return service.store.list_persons()

    @app.post("/api/v1/persons", response_model=RegisteredPerson, status_code=201)
    def create_person(request: RegisteredPersonCreate) -> RegisteredPerson:
        """Register a new person. Proxy to Makerverse if available, else local SQLite."""
        if makerverse_url and os.getenv("MAKERVERSE_PROXY_REGISTRY") == "1":
            try:
                import httpx
                response = httpx.post(f"{makerverse_url}/api/v1/persons", json=request.model_dump(), timeout=5.0)
                response.raise_for_status()
                return response.json()
            except Exception:
                pass  # Fallback to local
        try:
            return service.store.save_person(request)
        except EmbeddingError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/v1/persons/{person_id}", status_code=204, response_class=Response)
    def delete_person(person_id: str) -> Response:
        if not service.store.delete_person(person_id):
            raise HTTPException(status_code=404, detail="person not found")
        return Response(status_code=204)

    @app.post("/api/v1/registry/match", response_model=list[RegistryMatchView])
    def match_registry(request: RegistryMatchRequest) -> list[RegistryMatchView]:
        if request.embedding is None and request.gray is None:
            raise HTTPException(status_code=400, detail="provide embedding or gray matrix")
        try:
            query = request.embedding if request.embedding is not None else gray_embedding(request.gray or [])
            candidates: list[tuple[str, str, str, list[float]]] = []
            if request.kind in {"object", "all"}:
                candidates.extend(
                    (item.object_id, item.name, "object", item.embedding)
                    for item in service.store.list_objects()
                    if item.embedding
                )
            if request.kind in {"person", "all"}:
                candidates.extend(
                    (item.person_id, item.display_name, "person", item.embedding)
                    for item in service.store.list_persons()
                    if item.embedding
                )
            matches = match_embeddings(query, candidates, threshold=request.threshold)
        except (EmbeddingError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return [RegistryMatchView(**match.__dict__) for match in matches]

    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run("visual_event_ai.app:app", host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8010")), reload=False)


if __name__ == "__main__":
    run()
