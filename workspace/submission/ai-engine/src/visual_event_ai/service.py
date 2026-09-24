from __future__ import annotations

import logging
from collections.abc import Iterable
from threading import Lock

from .models import AnalysisJobView, UnifiedEvent, utc_now
from .fact_pipeline import FrameFactExtractor
from .frame_pipeline import CancellationToken
from .plugins import PluginManager, mock_facts
from .privacy import sanitize_sensitive_payload
from .relations import Zone
from .storage import SQLiteStore

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, store: SQLiteStore, plugins: PluginManager, *, zones: Iterable[Zone] = ()):
        self.store = store
        self.plugins = plugins
        self.frame_facts = FrameFactExtractor(registry_provider=self.store.registry_embeddings, zones=zones)
        self._locks: dict[str, Lock] = {}
        self._completion_locks: dict[str, Lock] = {}
        self._cancel_tokens: dict[str, CancellationToken] = {}

    def create_job(self, source: str, plugin_ids: list[str] | None, metadata: dict) -> AnalysisJobView:
        safe_metadata = sanitize_sensitive_payload({**metadata, "plugin_ids": plugin_ids or []})
        job = self.store.create_job(
            source,
            safe_metadata if isinstance(safe_metadata, dict) else {"plugin_ids": plugin_ids or []},
        )
        self._locks[job.job_id] = Lock()
        self._completion_locks[job.job_id] = Lock()
        self._cancel_tokens[job.job_id] = CancellationToken()
        logger.info("analysis job created job_id=%s source=%s plugins=%s", job.job_id, source, plugin_ids or "all")
        return job

    def _stop_requested(self, job: AnalysisJobView) -> bool:
        cancel = self._cancel_tokens.setdefault(job.job_id, CancellationToken())
        if not cancel.cancelled:
            return False
        job.status = "stopped"
        job.updated_at = utc_now()
        self.store.update_job(job)
        logger.info("analysis job stopped job_id=%s", job.job_id)
        return True

    def run_job(self, job_id: str) -> AnalysisJobView:
        job = self.store.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        lock = self._locks.setdefault(job_id, Lock())
        completion_lock = self._completion_locks.setdefault(job_id, Lock())
        cancellation = self._cancel_tokens.setdefault(job_id, CancellationToken())
        if not lock.acquire(blocking=False):
            logger.warning("analysis job already running job_id=%s", job_id)
            return job
        try:
            with completion_lock:
                latest = self.store.get_job(job_id)
                if latest is None:
                    raise KeyError(job_id)
                job = latest
                if job.status in {"completed", "stopped"} or self._stop_requested(job):
                    return job
                logger.info("analysis job started job_id=%s source=%s", job_id, job.source)
                job.status = "running"
                job.progress = 0.1
                job.event_ids = []
                job.error = None
                job.updated_at = utc_now()
                self.store.update_job(job)

            facts = (
                mock_facts(job.source)
                if job.source.startswith("mock://")
                else self.frame_facts.extract(job.source, token=cancellation)
            )
            if self._stop_requested(job):
                return job
            job.metadata["fact_count"] = len(facts)
            job.progress = 0.45
            job.updated_at = utc_now()
            self.store.update_job(job)

            selected = job.metadata.get("plugin_ids") or None
            events = self.plugins.evaluate(facts, job.source, selected)
            if self._stop_requested(job):
                return job
            with completion_lock:
                if self._stop_requested(job):
                    return job
                job.event_ids = [event.event_id for event in events]
                job.status = "completed"
                job.progress = 1.0
                job.updated_at = utc_now()
                self.store.complete_job(job, events)
            logger.info("analysis job completed job_id=%s events=%d facts=%d", job_id, len(events), len(facts))
            return job
        except Exception as exc:
            with completion_lock:
                latest = self.store.get_job(job_id)
                if latest is not None and latest.status == "stopped":
                    return latest
                if self._stop_requested(job):
                    return job
                job.event_ids = []
                job.status = "failed"
                job.error = str(exc)
                job.updated_at = utc_now()
                self.store.update_job(job)
                logger.exception("analysis job failed job_id=%s", job_id)
                return job
        finally:
            lock.release()

    def stop_job(self, job_id: str) -> AnalysisJobView | None:
        completion_lock = self._completion_locks.setdefault(job_id, Lock())
        with completion_lock:
            job = self.store.get_job(job_id)
            if job is None:
                return None
            if job.status in {"queued", "running"}:
                self._cancel_tokens.setdefault(job_id, CancellationToken()).cancel()
                job.status = "stopped"
                job.updated_at = utc_now()
                self.store.update_job(job)
                logger.info("analysis stop requested job_id=%s", job_id)
            return job
