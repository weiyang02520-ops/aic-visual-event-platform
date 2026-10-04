from __future__ import annotations

import asyncio
import inspect
import json
import logging
import queue
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from threading import Lock, Thread, current_thread
from typing import Any

from .models import (
    AnalysisJobView,
    RegisteredObject,
    RegisteredObjectCreate,
    RegisteredPerson,
    RegisteredPersonCreate,
    ReviewStatus,
    UnifiedEvent,
    utc_now,
)
from .embeddings import normalize_vector
from .privacy import sanitize_sensitive_payload


def _safe_json(value: Any) -> str:
    return json.dumps(sanitize_sensitive_payload(value), ensure_ascii=False)


def _event_payload(event: UnifiedEvent) -> str:
    return _safe_json(event.model_dump(mode="json"))


class _MakerverseSyncWorker:
    """Single owning loop for Makerverse pushes made by sync callers.

    FastAPI executes ``BackgroundTasks`` that wrap ``AnalysisService.run_job``
    in a worker thread.  That thread has no running asyncio loop, so a direct
    ``get_running_loop`` lookup would silently drop the event.  This worker
    keeps a bounded queue and one persistent loop, which also gives each
    ``MakerverseClient`` a stable owner for its AsyncClient.
    """

    _STOP = object()

    def __init__(self, push, *, maxsize: int = 128):
        self._push = push
        self._queue: queue.Queue[object] = queue.Queue(maxsize=maxsize)
        self._state_lock = Lock()
        self._thread: Thread | None = None
        self._closing = False
        self._stop_enqueued = False

    def _ensure_started(self) -> None:
        if self._thread is not None:
            return
        self._thread = Thread(
            target=self._run,
            name="makerverse-sync",
            daemon=True,
        )
        self._thread.start()

    def submit(self, event: UnifiedEvent, client: Any) -> bool:
        with self._state_lock:
            if self._closing:
                return False
            self._ensure_started()
            try:
                self._queue.put_nowait((event, client))
            except queue.Full:
                return False
            return True

    def _run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        clients: set[int] = set()
        client_refs: dict[int, Any] = {}
        try:
            while True:
                item = self._queue.get()
                try:
                    if item is self._STOP:
                        return
                    event, client = item  # type: ignore[misc]
                    clients.add(id(client))
                    client_refs[id(client)] = client
                    loop.run_until_complete(self._push(event, client))
                except Exception:
                    # ``_push`` records individual failures.  Keep the worker
                    # alive if a custom client raises outside that guard.
                    logging.getLogger(__name__).exception("Makerverse sync worker item failed")
                finally:
                    self._queue.task_done()
        finally:
            for client in client_refs.values():
                close = getattr(client, "close", None)
                if not callable(close):
                    continue
                try:
                    result = close()
                    if inspect.isawaitable(result):
                        loop.run_until_complete(result)
                except Exception:
                    logging.getLogger(__name__).warning(
                        "Makerverse client close failed", exc_info=True
                    )
            loop.close()
            asyncio.set_event_loop(None)

    def shutdown(self, *, wait: bool = True) -> None:
        with self._state_lock:
            self._closing = True
            thread = self._thread
            if thread is None or self._stop_enqueued:
                stop_needed = False
            else:
                self._stop_enqueued = True
                stop_needed = True
        if stop_needed:
            # A full queue is drained by the worker before this sentinel is
            # accepted, preserving already completed job events.
            self._queue.put(self._STOP)
        if wait and thread is not None and thread is not current_thread():
            thread.join()


class SQLiteStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        self.makerverse = None  # Will be set by app.py if MAKERVERSE_URL is configured
        self._makerverse_worker = _MakerverseSyncWorker(self._push_to_makerverse)
        self._makerverse_lock = Lock()
        self._makerverse_pending: set[str] = set()
        self._makerverse_synced: set[str] = set()
        self._makerverse_tasks: set[asyncio.Task[Any]] = set()
        self._makerverse_closed = False

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    plugin_id TEXT NOT NULL,
                    review_status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_source ON events(source_id);
                CREATE INDEX IF NOT EXISTS idx_events_review ON events(review_status);
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL,
                    event_ids TEXT NOT NULL,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS objects (
                    object_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS persons (
                    person_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                """
            )

    def save_event(self, event: UnifiedEvent, makerverse_client=None) -> None:
        """Save event to SQLite (fallback) and optionally push to Makerverse."""
        payload = _event_payload(event)

        # Always save to SQLite as fallback
        with self._connect() as db:
            db.execute(
                """INSERT OR REPLACE INTO events
                   (event_id, source_id, plugin_id, review_status, started_at, payload)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    event.event_id,
                    event.source_id,
                    event.plugin_id,
                    event.review_status.value,
                    event.started_at.isoformat(),
                    payload,
                ),
            )

        self._schedule_makerverse(event, makerverse_client or self.makerverse)

    def _schedule_makerverse(self, event: UnifiedEvent, client: Any) -> None:
        if client is None:
            return
        event_id = event.event_id
        with self._makerverse_lock:
            if (
                self._makerverse_closed
                or event_id in self._makerverse_pending
                or event_id in self._makerverse_synced
            ):
                return
            self._makerverse_pending.add(event_id)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            if not self._makerverse_worker.submit(event, client):
                self._makerverse_sync_failed(event_id)
            return
        try:
            task = loop.create_task(self._push_to_makerverse(event, client))
        except RuntimeError:
            if not self._makerverse_worker.submit(event, client):
                self._makerverse_sync_failed(event_id)
            return
        with self._makerverse_lock:
            self._makerverse_tasks.add(task)
        task.add_done_callback(lambda done: self._makerverse_task_done(event_id, done))

    def _makerverse_task_done(self, event_id: str, task: asyncio.Task[Any]) -> None:
        with self._makerverse_lock:
            self._makerverse_tasks.discard(task)
        if task.cancelled():
            self._makerverse_sync_failed(event_id)
            return
        try:
            exc = task.exception()
        except Exception:
            self._makerverse_sync_failed(event_id)
        else:
            if exc is not None:
                self._makerverse_sync_failed(event_id)

    def _makerverse_synced_event(self, event_id: str) -> None:
        with self._makerverse_lock:
            self._makerverse_pending.discard(event_id)
            self._makerverse_synced.add(event_id)

    def _makerverse_sync_failed(self, event_id: str) -> None:
        with self._makerverse_lock:
            self._makerverse_pending.discard(event_id)

    @staticmethod
    def _is_idempotent_receipt(exc: Exception) -> bool:
        """Treat a backend duplicate response as an idempotent success."""

        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
        if status_code not in {400, 409}:
            return False
        try:
            detail = response.text.lower()
        except Exception:
            detail = ""
        return any(token in detail for token in ("duplicate", "already exists", "event_id", "unique"))

    async def _push_to_makerverse(self, event: UnifiedEvent, client) -> None:
        """Push event to Makerverse backend."""
        event_dict = event.model_dump(mode="json")
        event_dict["source_id"] = event.source_id
        try:
            await client.push_event(event_dict)
        except Exception as exc:
            if self._is_idempotent_receipt(exc):
                self._makerverse_synced_event(event.event_id)
                logging.getLogger(__name__).info(
                    "Makerverse already contains event %s; treating duplicate as success",
                    event.event_id,
                )
            else:
                self._makerverse_sync_failed(event.event_id)
                logging.getLogger(__name__).warning("Makerverse sync unavailable for event %s: %s", event.event_id, exc)
        else:
            self._makerverse_synced_event(event.event_id)

    def close(self) -> None:
        """Stop the sync worker and reject any later schedules."""

        with self._makerverse_lock:
            self._makerverse_closed = True
        self._makerverse_worker.shutdown(wait=True)

    async def shutdown(self) -> None:
        """Await loop-owned tasks, then stop the sync worker."""

        with self._makerverse_lock:
            self._makerverse_closed = True
            tasks = tuple(self._makerverse_tasks)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.to_thread(self._makerverse_worker.shutdown, wait=True)

    def list_events(self, plugin_id: str | None = None, review_status: str | None = None) -> list[UnifiedEvent]:
        clauses: list[str] = []
        values: list[str] = []
        if plugin_id:
            clauses.append("plugin_id = ?")
            values.append(plugin_id)
        if review_status:
            clauses.append("review_status = ?")
            values.append(review_status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as db:
            rows = db.execute(
                f"SELECT payload FROM events {where} ORDER BY started_at DESC",
                values,
            ).fetchall()
        return [UnifiedEvent.model_validate_json(row["payload"]) for row in rows]

    def get_event(self, event_id: str) -> UnifiedEvent | None:
        with self._connect() as db:
            row = db.execute("SELECT payload FROM events WHERE event_id = ?", (event_id,)).fetchone()
        return UnifiedEvent.model_validate_json(row["payload"]) if row else None

    def review_event(self, event_id: str, status: ReviewStatus, note: str | None) -> UnifiedEvent | None:
        event = self.get_event(event_id)
        if event is None:
            return None
        event.review_status = status
        if note:
            event.metadata["review_note"] = note
        self.save_event(event, makerverse_client=self.makerverse)
        return event

    def create_job(self, source: str, metadata: dict[str, Any]) -> AnalysisJobView:
        from uuid import uuid4

        now = utc_now()
        job = AnalysisJobView(
            job_id=f"job_{uuid4()}",
            source=source,
            status="queued",
            progress=0.0,
            created_at=now,
            updated_at=now,
            metadata=metadata,
        )
        with self._connect() as db:
            db.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    job.job_id,
                    job.source,
                    job.status,
                    job.progress,
                    json.dumps(job.event_ids),
                    job.error,
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                    _safe_json(job.metadata),
                ),
            )
        return job

    def update_job(self, job: AnalysisJobView) -> None:
        with self._connect() as db:
            db.execute(
                """UPDATE jobs SET status=?, progress=?, event_ids=?, error=?, updated_at=?, metadata=?
                   WHERE job_id=?""",
                (
                    job.status,
                    job.progress,
                    json.dumps(job.event_ids),
                    job.error,
                    job.updated_at.isoformat(),
                    _safe_json(job.metadata),
                    job.job_id,
                ),
            )

    def complete_job(self, job: AnalysisJobView, events: Iterable[UnifiedEvent]) -> None:
        """Persist all job events and the completed job row atomically."""

        event_rows = [
            (
                event,
                _event_payload(event),
            )
            for event in events
        ]
        with self._connect() as db:
            for event, payload in event_rows:
                db.execute(
                    """INSERT OR REPLACE INTO events
                       (event_id, source_id, plugin_id, review_status, started_at, payload)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        event.event_id,
                        event.source_id,
                        event.plugin_id,
                        event.review_status.value,
                        event.started_at.isoformat(),
                        payload,
                    ),
                )
            cursor = db.execute(
                """UPDATE jobs SET status=?, progress=?, event_ids=?, error=?, updated_at=?, metadata=?
                   WHERE job_id=?""",
                (
                    job.status,
                    job.progress,
                    json.dumps(job.event_ids),
                    job.error,
                    job.updated_at.isoformat(),
                    _safe_json(job.metadata),
                    job.job_id,
                ),
            )
            if cursor.rowcount != 1:
                raise KeyError(job.job_id)
        for event, _ in event_rows:
            self._schedule_makerverse(event, self.makerverse)

    def get_job(self, job_id: str) -> AnalysisJobView | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        return self._job_from_row(row) if row else None

    def list_jobs(self) -> list[AnalysisJobView]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        return [self._job_from_row(row) for row in rows]

    @staticmethod
    def _job_from_row(row: sqlite3.Row) -> AnalysisJobView:
        return AnalysisJobView(
            job_id=row["job_id"],
            source=row["source"],
            status=row["status"],
            progress=row["progress"],
            event_ids=json.loads(row["event_ids"]),
            error=row["error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=json.loads(row["metadata"]),
        )

    def save_object(self, item: RegisteredObjectCreate) -> RegisteredObject:
        from uuid import uuid4

        payload = item.model_dump()
        if payload.get("embedding") is not None:
            payload["embedding"] = normalize_vector(payload["embedding"])
        result = RegisteredObject(object_id=str(uuid4()), created_at=utc_now(), **payload)
        with self._connect() as db:
            db.execute("INSERT INTO objects VALUES (?, ?)", (result.object_id, result.model_dump_json()))
        return result

    def list_objects(self) -> list[RegisteredObject]:
        with self._connect() as db:
            rows = db.execute("SELECT payload FROM objects ORDER BY rowid DESC").fetchall()
        return [RegisteredObject.model_validate_json(row["payload"]) for row in rows]

    def delete_object(self, object_id: str) -> bool:
        with self._connect() as db:
            cursor = db.execute("DELETE FROM objects WHERE object_id = ?", (object_id,))
        return cursor.rowcount > 0

    def save_person(self, item: RegisteredPersonCreate) -> RegisteredPerson:
        from uuid import uuid4

        payload = item.model_dump()
        if payload.get("embedding") is not None:
            payload["embedding"] = normalize_vector(payload["embedding"])
        result = RegisteredPerson(person_id=str(uuid4()), created_at=utc_now(), **payload)
        with self._connect() as db:
            db.execute("INSERT INTO persons VALUES (?, ?)", (result.person_id, result.model_dump_json()))
        return result

    def list_persons(self) -> list[RegisteredPerson]:
        with self._connect() as db:
            rows = db.execute("SELECT payload FROM persons ORDER BY rowid DESC").fetchall()
        return [RegisteredPerson.model_validate_json(row["payload"]) for row in rows]

    def delete_person(self, person_id: str) -> bool:
        with self._connect() as db:
            cursor = db.execute("DELETE FROM persons WHERE person_id = ?", (person_id,))
        return cursor.rowcount > 0

    def registry_embeddings(self) -> list[tuple[str, str, str, list[float]]]:
        """Return only registered records with a usable embedding.

        The tuple shape is shared with ``embeddings.match_embeddings`` so the
        frame pipeline can enrich facts without depending on SQLite details.
        """

        candidates: list[tuple[str, str, str, list[float]]] = []
        for item in self.list_objects():
            if item.embedding:
                candidates.append((item.object_id, item.name, "object", item.embedding))
        for item in self.list_persons():
            if item.embedding:
                candidates.append((item.person_id, item.display_name, "person", item.embedding))
        return candidates
