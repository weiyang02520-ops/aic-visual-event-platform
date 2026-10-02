"""HTTP client for pushing AI analysis results to Makerverse backend."""

from __future__ import annotations

import logging
import asyncio
from typing import Any

import httpx

logger = logging.getLogger(__name__)


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
        allowed = {
            "event_id", "live_id", "plugin_id", "plugin_version", "event_type", "title",
            "description", "started_at", "ended_at", "confidence", "severity", "location",
            "subject", "object", "review_status", "metadata", "created_at",
        }
        payload = {key: value for key, value in event.items() if key in allowed and value is not None}
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
