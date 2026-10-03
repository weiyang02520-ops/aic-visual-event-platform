"""HTTP client for pushing AI analysis results to Makerverse backend."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Mapping
from datetime import date, datetime, time
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# ``LiveService.Models.AiEvent`` stores these three values as nullable
# ``string`` properties whose contents are JSON.  Keep the conversion at the
# adapter boundary so the UnifiedEvent contract and the AI reasoning pipeline
# remain unchanged.
_JSON_FIELDS = {"subject", "object"}
_EVENT_FIELDS = {
    "event_id",
    "live_id",
    "plugin_id",
    "plugin_version",
    "event_type",
    "title",
    "description",
    "started_at",
    "ended_at",
    "confidence",
    "severity",
    "location",
    "subject",
    "object",
    "review_status",
    "metadata",
    "created_at",
}
_RELATED_FIELDS = ("facts", "evidence")


def _json_compatible(value: Any) -> Any:
    """Convert common UnifiedEvent values into JSON-compatible primitives.

    ``storage.SQLiteStore`` normally calls ``model_dump(mode="json")`` before
    reaching this client, but the client is also used directly in tests and by
    integrations.  Handling dates, enums, Pydantic-like models, and tuples at
    this boundary keeps the HTTP payload deterministic for both call paths.
    ``None`` is intentionally retained inside JSON fields; top-level optional
    fields are filtered by :meth:`MakerverseClient.push_event`.
    """

    if value is None:
        return None
    if isinstance(value, Enum):
        return _json_compatible(value.value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    # Avoid importing Pydantic into this small transport adapter.  Evidence
    # and fact values may be supplied as BaseModel instances by callers.
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        try:
            return _json_compatible(model_dump(mode="python"))
        except TypeError:
            return _json_compatible(model_dump())

    if isinstance(value, Mapping):
        return {str(key): _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_compatible(item) for item in value]
    return value


def _json_string(value: Any) -> str:
    """Return a JSON document string, accepting already-encoded JSON input."""

    if isinstance(value, str):
        try:
            # Callers may already have a C#-compatible JSON string.  Parse and
            # re-encode it to avoid double encoding while still normalising
            # nested dates/enums when the input is valid JSON.
            value = json.loads(value)
        except json.JSONDecodeError:
            # A plain string is still represented as a valid JSON string.
            pass
    return json.dumps(
        _json_compatible(value),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _metadata_root(value: Any) -> dict[str, Any]:
    """Normalise metadata to an object so facts/evidence can be retained."""

    if value is None:
        return {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {"legacy_metadata": value}

    value = _json_compatible(value)
    if isinstance(value, dict):
        return value
    # AiEvent.Metadata is a JSON string, and an object root makes the related
    # fields addressable without changing the backend model.
    return {"metadata": value}


def _metadata_json(event: Mapping[str, Any]) -> str | None:
    """Build AiEvent.Metadata while preserving UnifiedEvent-only fields."""

    metadata_present = "metadata" in event and event.get("metadata") is not None
    related_present = any(
        key in event and event.get(key) is not None for key in _RELATED_FIELDS
    )
    if not metadata_present and not related_present:
        return None

    root = _metadata_root(event.get("metadata"))
    for key in _RELATED_FIELDS:
        if key in event and event.get(key) is not None:
            root[key] = _json_compatible(event[key])
    return _json_string(root)


class MakerverseClient:
    """Client for communicating with Makerverse LiveService API."""

    def __init__(self, base_url: str, *, live_id: str | None = None, timeout: float = 10.0, retries: int = 2):
        self.base_url = base_url.rstrip("/")
        self.live_id = live_id.strip() if live_id and live_id.strip() else None
        self.retries = max(0, int(retries))
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        await self.client.aclose()

    async def push_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Push a completed AI event to Makerverse.

        The event dict must include all required fields from AiEvent model:
        live_id, plugin_id, plugin_version, event_type, title, started_at, ended_at, review_status.
        """
        live_id = event.get("live_id") or self.live_id
        if not isinstance(live_id, str) or not live_id.strip():
            raise ValueError("Makerverse live_id is not configured; set MAKERVERSE_LIVE_ID")
        payload: dict[str, Any] = {}
        for key, value in event.items():
            if key not in _EVENT_FIELDS or value is None:
                continue
            if key in _JSON_FIELDS:
                # Subject/Object are nullable JSON strings in AiEvent.  This
                # also accepts an already-encoded JSON string without nesting
                # it a second time.
                payload[key] = _json_string(value)
            elif key == "metadata":
                # Facts/evidence are UnifiedEvent fields and have no scalar
                # slots on AiEvent.  Store them in its JSON metadata instead.
                continue
            else:
                payload[key] = _json_compatible(value)

        metadata = _metadata_json(event)
        if metadata is not None:
            payload["metadata"] = metadata
        payload["live_id"] = live_id.strip()
        url = f"{self.base_url}/api/v1/events"
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = await self.client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                logger.info("Pushed event %s to Makerverse", payload.get("event_id"))
                return result
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt < self.retries:
                    await asyncio.sleep(0.2 * (attempt + 1))
        assert last_error is not None
        logger.error("Failed to push event %s to Makerverse after %s attempts: %s", payload.get("event_id"), self.retries + 1, last_error)
        raise last_error

    async def get_objects(self) -> list[dict[str, Any]]:
        """Fetch registered objects from Makerverse."""
        url = f"{self.base_url}/api/v1/objects"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.error(f"Failed to fetch objects from Makerverse: {exc}")
            return []

    async def get_persons(self) -> list[dict[str, Any]]:
        """Fetch registered persons from Makerverse."""
        url = f"{self.base_url}/api/v1/persons"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.error(f"Failed to fetch persons from Makerverse: {exc}")
            return []

    async def get_medication_plans(self) -> list[dict[str, Any]]:
        """Fetch medication plans from Makerverse."""
        url = f"{self.base_url}/api/v1/medication/plans"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.error(f"Failed to fetch medication plans from Makerverse: {exc}")
            return []
