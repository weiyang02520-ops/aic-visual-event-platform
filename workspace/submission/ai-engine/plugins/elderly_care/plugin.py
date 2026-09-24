from datetime import timedelta

from visual_event_ai.algorithm_reasoner import EventCandidate, MedicationSequenceReasoner
from visual_event_ai.models import EvidenceRef, PluginManifest, PrimitiveFact, Severity, UnifiedEvent


class ElderlyCarePlugin:
    def __init__(self, manifest: PluginManifest):
        self.manifest = manifest
        self.reasoner = MedicationSequenceReasoner()

    def evaluate(self, facts: list[PrimitiveFact], source_id: str) -> list[UnifiedEvent]:
        candidates = self.reasoner.infer(facts)
        candidates.extend(self.reasoner.infer_incomplete(facts))
        candidates.sort(key=lambda candidate: candidate.started_at)
        return [self._event(candidate, source_id) for candidate in candidates]

    def _event(self, candidate: EventCandidate, source_id: str) -> UnifiedEvent:
        complete = candidate.event_type == "suspected_medication"
        start = candidate.started_at
        end = candidate.ended_at
        return UnifiedEvent(
            plugin_id=self.manifest.plugin_id,
            plugin_version=self.manifest.version,
            event_type=candidate.event_type,
            title="疑似发生服药相关行为" if complete else "服药相关序列不完整",
            description=(
                "同一人物与药品对象出现拿取/接近后手部接近面部的时序事实；仅作为辅助判断，需人工复核。"
                if complete
                else "检测到同一人物与药品对象的拿取线索，但缺少匹配的后续手部接近面部事实；仅作为待复核线索。"
            ),
            source_id=source_id,
            started_at=start,
            ended_at=end,
            confidence=candidate.confidence,
            severity=Severity.MEDIUM if complete else Severity.LOW,
            subject=candidate.subject,
            object=candidate.object,
            location=candidate.location,
            evidence=[
                EvidenceRef(
                    source_id=source_id,
                    started_at=start - timedelta(seconds=3),
                    ended_at=end + timedelta(seconds=3),
                    status="designed",
                )
            ],
            facts=list(candidate.evidence_facts),
            metadata={
                **candidate.metadata,
                "interpretation": "辅助判断，不是医学诊断",
                "needs_review": True,
                "sequence_complete": complete,
            },
        )


def build_plugin(manifest: PluginManifest) -> ElderlyCarePlugin:
    return ElderlyCarePlugin(manifest)
