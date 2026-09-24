from __future__ import annotations

import importlib.util
import json
import logging
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Protocol

from .models import PluginManifest, PluginView, PrimitiveFact, UnifiedEvent, utc_now

logger = logging.getLogger(__name__)


class ScenePlugin(Protocol):
    def evaluate(self, facts: list[PrimitiveFact], source_id: str) -> list[UnifiedEvent]: ...


@dataclass
class PluginRecord:
    manifest: PluginManifest
    implementation: ScenePlugin
    enabled: bool
    state: str = "enabled"
    error: str | None = None


class PluginManager:
    def __init__(self, plugin_dir: str | Path):
        self.plugin_dir = Path(plugin_dir)
        self.records: dict[str, PluginRecord] = {}

    def scan(self) -> list[PluginView]:
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        for manifest_path in sorted(self.plugin_dir.glob("*/manifest.json")):
            try:
                manifest = PluginManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
                module_path = manifest_path.parent / manifest.entrypoint
                spec = importlib.util.spec_from_file_location(
                    f"visual_event_plugin_{manifest.plugin_id}", module_path
                )
                if spec is None or spec.loader is None:
                    raise RuntimeError(f"cannot load entrypoint: {module_path}")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                implementation = module.build_plugin(manifest)
                self.records[manifest.plugin_id] = PluginRecord(
                    manifest=manifest,
                    implementation=implementation,
                    enabled=manifest.enabled_by_default,
                )
                logger.info("plugin loaded plugin_id=%s version=%s", manifest.plugin_id, manifest.version)
            except Exception as exc:  # a broken plugin must not kill the service
                plugin_id = manifest_path.parent.name
                fallback = PluginManifest(
                    plugin_id=plugin_id,
                    name=plugin_id,
                    version="unknown",
                    description="Plugin failed to load",
                )
                self.records[plugin_id] = PluginRecord(
                    manifest=fallback,
                    implementation=_BrokenPlugin(),
                    enabled=False,
                    state="error",
                    error=str(exc),
                )
                logger.exception("plugin load failed plugin_id=%s", plugin_id)
        return self.list()

    def list(self) -> list[PluginView]:
        return [
            PluginView(
                **record.manifest.model_dump(),
                enabled=record.enabled,
                state=record.state,
                error=record.error,
            )
            for record in self.records.values()
        ]

    def set_enabled(self, plugin_id: str, enabled: bool) -> PluginView:
        record = self.records.get(plugin_id)
        if record is None:
            raise KeyError(plugin_id)
        if record.state == "error":
            raise RuntimeError(record.error or "plugin is not loadable")
        record.enabled = enabled
        record.state = "enabled" if enabled else "disabled"
        logger.info("plugin toggled plugin_id=%s enabled=%s", plugin_id, enabled)
        return self.list()[list(self.records).index(plugin_id)]

    def evaluate(self, facts: list[PrimitiveFact], source_id: str, selected: list[str] | None = None) -> list[UnifiedEvent]:
        events: list[UnifiedEvent] = []
        for plugin_id, record in self.records.items():
            if not record.enabled or (selected and plugin_id not in selected):
                continue
            try:
                events.extend(record.implementation.evaluate(facts, source_id))
            except Exception as exc:
                record.state = "degraded"
                record.error = str(exc)
                logger.exception("plugin evaluation failed plugin_id=%s source=%s", plugin_id, source_id)
        return events


class _BrokenPlugin:
    def evaluate(self, facts: list[PrimitiveFact], source_id: str) -> list[UnifiedEvent]:
        return []


def mock_facts(source: str) -> list[PrimitiveFact]:
    """Generate deterministic facts used by the offline demo and tests."""
    base = utc_now()
    if source.startswith("mock://elderly-medication"):
        return [
            PrimitiveFact(fact_type="person_present", timestamp=base, subject={"id": "person_01", "label": "家属"}),
            PrimitiveFact(
                fact_type="object_picked",
                timestamp=base + timedelta(seconds=2),
                subject={"id": "person_01"},
                object={"id": "medicine_box_01", "label": "药盒"},
                location="药箱区域",
                confidence=0.91,
            ),
            PrimitiveFact(
                fact_type="hand_to_face",
                timestamp=base + timedelta(seconds=6),
                subject={"id": "person_01"},
                object={"id": "medicine_box_01", "label": "药盒"},
                location="客厅桌面",
                confidence=0.74,
            ),
            PrimitiveFact(
                fact_type="object_put_down",
                timestamp=base + timedelta(seconds=9),
                subject={"id": "person_01"},
                object={"id": "medicine_box_01", "label": "药盒"},
                location="客厅桌面",
                confidence=0.86,
            ),
        ]
    if source.startswith("mock://workshop-tool"):
        return [
            PrimitiveFact(fact_type="person_present", timestamp=base, subject={"id": "person_02", "label": "工作人员"}),
            PrimitiveFact(
                fact_type="object_removed",
                timestamp=base + timedelta(seconds=3),
                subject={"id": "person_02"},
                object={"id": "drill_01", "label": "电钻"},
                location="工具架 A",
                confidence=0.88,
            ),
        ]
    return [
        PrimitiveFact(fact_type="person_present", timestamp=base, subject={"id": "unknown"}),
        PrimitiveFact(fact_type="scene_observed", timestamp=base, location="未标注区域"),
    ]
