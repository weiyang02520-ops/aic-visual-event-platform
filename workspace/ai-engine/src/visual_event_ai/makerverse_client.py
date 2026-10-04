"""HTTP client for pushing AI analysis results to Makerverse backend."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
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
    """Build AiEvent.Metadata while preserving UnifiedEvent-only fields.

    ``source_id`` belongs to the unified event contract, but Makerverse's
    ``AiEvent`` model has no top-level property for it.  Prefer the explicit
    event value when present and keep a metadata value as the fallback for
    callers that already supplied provenance there.
    """

    metadata_present = "metadata" in event and event.get("metadata") is not None
    related_present = any(
        key in event and event.get(key) is not None for key in _RELATED_FIELDS
    )
    source_id_present = "source_id" in event and event.get("source_id") is not None
    if not metadata_present and not related_present and not source_id_present:
        return None

    root = _metadata_root(event.get("metadata"))
    if source_id_present:
        root["source_id"] = _json_compatible(event["source_id"])
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
        self._timeout = timeout
        # AsyncClient instances are owned by the event loop that created them.
        # A store may use one persistent loop in its sync worker and FastAPI
        # may use a different loop for request-time calls, so never share one
        # instance between loops.
        self._loop_clients: dict[asyncio.AbstractEventLoop, httpx.AsyncClient] = {}
        self._client_lock = threading.RLock()
        self._injected_client: httpx.AsyncClient | None = None
        self._injected_owner: asyncio.AbstractEventLoop | None = None
        self._injected_transport: httpx.AsyncBaseTransport | None = None
        self._compat_client: httpx.AsyncClient | None = None
        self._pushed_event_ids: set[str] = set()
        self._pushed_ids_lock = threading.Lock()

    @property
    def client(self) -> httpx.AsyncClient:
        """Return the client for the current loop.

        The property remains available for test/integration transport
        injection.  Production requests use :meth:`_client_for_loop`, which
        creates the AsyncClient lazily in the owning loop.
        """

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # Backwards-compatible access from synchronous test setup.  This
            # object is never used for a request until it is assigned as an
            # injected client or claimed by an owning loop.
            with self._client_lock:
                if self._injected_client is not None:
                    return self._injected_client
                if self._compat_client is None or self._compat_client.is_closed:
                    self._compat_client = httpx.AsyncClient(timeout=self._timeout)
                return self._compat_client
        return self._client_for_loop()

    @client.setter
    def client(self, value: httpx.AsyncClient) -> None:
        # Existing integrations assign a MockTransport-backed AsyncClient to
        # this attribute.  Claim it lazily from the first loop that sends a
        # request; a different loop will get its own client instead.
        with self._client_lock:
            self._injected_client = value
            self._injected_owner = None
            transport = getattr(value, "_transport", None)
            self._injected_transport = (
                transport if isinstance(transport, httpx.MockTransport) else None
            )

    def _client_for_loop(self) -> httpx.AsyncClient:
        loop = asyncio.get_running_loop()
        with self._client_lock:
            existing = self._loop_clients.get(loop)
            if existing is not None and not existing.is_closed:
                return existing
            if self._injected_client is not None and self._injected_owner is None:
                client = self._injected_client
                self._injected_owner = loop
            elif self._injected_transport is not None:
                # MockTransport is loop-neutral and is commonly injected by
                # tests.  Clone only the AsyncClient so a second asyncio.run
                # never reuses the first loop's client.
                client = httpx.AsyncClient(transport=self._injected_transport)
            else:
                client = httpx.AsyncClient(timeout=self._timeout)
            self._loop_clients[loop] = client
            return client

    async def close(self):
        """Close only the AsyncClient owned by the current event loop."""

        loop = asyncio.get_running_loop()
        with self._client_lock:
            client = self._loop_clients.pop(loop, None)
            if client is None and self._injected_owner is loop:
                client = self._injected_client
                self._injected_owner = None
            if client is None and self._compat_client is not None:
                client = self._compat_client
                self._compat_client = None
        if client is not None and not client.is_closed:
            await client.aclose()

    async def push_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Push a completed AI event to Makerverse.

        The event dict must include all required fields from AiEvent model:
        live_id, plugin_id, plugin_version, event_type, title, started_at, ended_at, review_status.
        """
        live_id = event.get("live_id") or self.live_id
        if not isinstance(live_id, str) or not live_id.strip():
            raise ValueError("Makerverse live_id is not configured; set MAKERVERSE_LIVE_ID")
        event_id = event.get("event_id")
        if isinstance(event_id, str):
            with self._pushed_ids_lock:
                if event_id in self._pushed_event_ids:
                    # The backend treats event_id as unique.  Returning a
                    # local idempotent receipt avoids a second POST when the
                    # same event is reviewed more than once.
                    return {"event_id": event_id, "idempotent": True}
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
        client = self._client_for_loop()
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                if isinstance(event_id, str):
                    with self._pushed_ids_lock:
                        self._pushed_event_ids.add(event_id)
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
            response = await self._client_for_loop().get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.error(f"Failed to fetch objects from Makerverse: {exc}")
            return []

    async def get_persons(self) -> list[dict[str, Any]]:
        """Fetch registered persons from Makerverse."""
        url = f"{self.base_url}/api/v1/persons"
        try:
            response = await self._client_for_loop().get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.error(f"Failed to fetch persons from Makerverse: {exc}")
            return []

    async def get_medication_plans(self) -> list[dict[str, Any]]:
        """Fetch medication plans from Makerverse."""
        url = f"{self.base_url}/api/v1/medication/plans"
        try:
            response = await self._client_for_loop().get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.error(f"Failed to fetch medication plans from Makerverse: {exc}")
            return []
