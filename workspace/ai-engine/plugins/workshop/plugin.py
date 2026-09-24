from datetime import timedelta

from visual_event_ai.algorithm_reasoner import EventCandidate, WorkshopStateReasoner
from visual_event_ai.models import EvidenceRef, PluginManifest, PrimitiveFact, Severity, UnifiedEvent


class WorkshopPlugin:
    def __init__(self, manifest: PluginManifest):
        self.manifest = manifest
        self.reasoner = WorkshopStateReasoner()

    def evaluate(self, facts: list[PrimitiveFact], source_id: str) -> list[UnifiedEvent]:
        candidates = self.reasoner.infer(facts)
        return [self._event(candidate, source_id) for candidate in candidates]

    def _event(self, candidate: EventCandidate, source_id: str) -> UnifiedEvent:
        event_type = candidate.event_type
        title = {
            "object_removed": "物品离开登记区域",
            "object_returned": "物品已回到登记区域",
            "object_missing": "物品疑似缺失",
        }[event_type]
        description = {
            "object_removed": "检测到关注物品离开登记区域，位置和时间可回看确认。",
            "object_returned": "检测到关注物品回到登记区域，已形成归还记录。",
            "object_missing": "在明确的场景观察事实中，物品超过等待时间仍未重新出现；建议人工核对最后位置。",
        }[event_type]
        return UnifiedEvent(
            plugin_id=self.manifest.plugin_id,
            plugin_version=self.manifest.version,
            event_type=event_type,
            title=title,
            description=description,
            source_id=source_id,
            started_at=candidate.started_at,
            ended_at=candidate.ended_at,
            confidence=candidate.confidence,
            severity=Severity.HIGH if event_type == "object_missing" else Severity.LOW,
            subject=candidate.subject,
            object=candidate.object,
            location=candidate.location,
            evidence=[
                EvidenceRef(
                    source_id=source_id,
                    started_at=candidate.started_at - timedelta(seconds=3),
                    ended_at=candidate.ended_at + timedelta(seconds=3),
                    status="designed",
                )
            ],
            facts=list(candidate.evidence_facts),
            metadata={
                **candidate.metadata,
                "object_state": {
                    "object_removed": "taken",
                    "object_returned": "returned",
                    "object_missing": "missing",
                }[event_type],
                "last_seen_policy": "等待后续归还事实或有时间戳的场景观察",
                "needs_review": event_type == "object_missing",
            },
        )


def build_plugin(manifest: PluginManifest) -> WorkshopPlugin:
    return WorkshopPlugin(manifest)
