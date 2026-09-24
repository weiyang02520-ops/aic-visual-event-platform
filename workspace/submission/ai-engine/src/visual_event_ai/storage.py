from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
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


class SQLiteStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

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

    def save_event(self, event: UnifiedEvent) -> None:
        payload = _event_payload(event)
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
        self.save_event(event)
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
