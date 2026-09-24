from __future__ import annotations

from pathlib import Path
from collections.abc import Callable, Iterable

from .embeddings import match_embeddings
from .frame_pipeline import CancellationToken, FramePipeline
from .keypoint_actions import KeypointActionExtractor
from .models import PrimitiveFact
from .model_providers import DetectorProviderRegistry
from .privacy import sanitize_sensitive_payload
from .providers import CentroidTracker, normalize_observations
from .quality import evaluate_channel_quality
from .relations import Entity, RelationEngine, Zone


class FrameFactExtractor:
    """Connects frame providers, detector/tracker and relation facts."""

    def __init__(
        self,
        pipeline: FramePipeline | None = None,
        detectors: DetectorProviderRegistry | None = None,
        registry_provider: Callable[[], Iterable[tuple[str, str, str, list[float]]]] | None = None,
        zones: Iterable[Zone] = (),
    ) -> None:
        self.pipeline = pipeline or FramePipeline()
        self.detectors = detectors or DetectorProviderRegistry()
        self.registry_provider = registry_provider
        self.zones = tuple(zones)

    def extract(
        self,
        source: str,
        *,
        max_frames: int = 64,
        token: CancellationToken | None = None,
    ) -> list[PrimitiveFact]:
        suffix = Path(source.split("?", 1)[0]).suffix.lower()
        session_factory = getattr(self.detectors, "session_for_source", None)

        def detector_session():
            if callable(session_factory):
                return session_factory(source)
            provider = self.detectors.for_source(source)
            new_session = getattr(provider, "new_session", None)
            return new_session() if callable(new_session) else provider

        detector = detector_session()
        cancellation = token or CancellationToken()
        tracker = CentroidTracker()
        relations = RelationEngine(cooldown_seconds=0)
        keypoint_actions = KeypointActionExtractor()
        continuity_segment = 0
        facts: list[PrimitiveFact] = []
        for frame in self.pipeline.iter_frames(source, max_frames=max_frames, token=cancellation):
            cancellation.raise_if_cancelled()
            frame_metadata = frame.metadata if isinstance(frame.metadata, dict) else {}
            discontinuity_before = frame_metadata.get("discontinuity_before") is True
            if discontinuity_before:
                continuity_segment += 1
                previous_detector = detector
                detector = detector_session()
                if detector is previous_detector:
                    reset = getattr(detector, "reset", None)
                    if callable(reset):
                        reset()
                tracker = CentroidTracker()
                relations.reset_after_discontinuity()
                keypoint_actions = KeypointActionExtractor()
                gap_metadata = {
                    "continuity_segment": continuity_segment,
                    "reason": frame_metadata.get("discontinuity_reason", "provider_discontinuity"),
                    "source_provider": frame_metadata.get("provider"),
                    "source_id": frame.source_id,
                }
                if "skipped_line" in frame_metadata:
                    gap_metadata["skipped_line"] = frame_metadata["skipped_line"]
                facts.append(
                    PrimitiveFact(
                        fact_type="observation_gap",
                        timestamp=frame.timestamp,
                        metadata=gap_metadata,
                    )
                )
            quality = evaluate_channel_quality(frame_metadata)
            quality_summary = quality.summary() if quality.gated else None
            if not quality.allow_inference:
                continuity_segment += 1
                previous_detector = detector
                detector = detector_session()
                if detector is previous_detector:
                    reset = getattr(detector, "reset", None)
                    if callable(reset):
                        reset()
                tracker = CentroidTracker()
                relations.reset_after_discontinuity()
                keypoint_actions = KeypointActionExtractor()
                facts.append(
                    PrimitiveFact(
                        fact_type="observation_gap",
                        timestamp=frame.timestamp,
                        metadata={
                            "continuity_segment": continuity_segment,
                            "reason": "quality_gate",
                            "source_provider": frame_metadata.get("provider"),
                            "source_id": frame.source_id,
                            "quality_gate": quality_summary,
                        },
                    )
                )
                continue
            detections = detector.detect(frame)
            tracks = tracker.update(detections)
            observations = normalize_observations(frame, detections, tracks)
            for observation in observations:
                sanitized_metadata = sanitize_sensitive_payload(observation.metadata)
                metadata = dict(sanitized_metadata) if isinstance(sanitized_metadata, dict) else {}
                metadata["continuity_segment"] = continuity_segment
                metadata["source_id"] = frame.source_id
                if quality_summary is not None:
                    metadata["quality_gate"] = quality_summary
                if discontinuity_before:
                    metadata["frame_discontinuity_before"] = True
                    if "skipped_line" in frame_metadata:
                        metadata["skipped_frame_line"] = frame_metadata["skipped_line"]
                embedding = metadata.get("embedding")
                if self.registry_provider and isinstance(embedding, list):
                    matches = match_embeddings(embedding, self.registry_provider(), threshold=0.8)
                    if matches:
                        metadata["registry_matches"] = [
                            {
                                "registry_id": match.registry_id,
                                "label": match.label,
                                "kind": match.kind,
                                "similarity": match.similarity,
                                "accepted": match.accepted,
                            }
                            for match in matches[:5]
                        ]
                facts.append(
                    PrimitiveFact(
                        fact_type=observation.fact_type,
                        timestamp=observation.timestamp,
                        confidence=observation.confidence,
                        subject=observation.subject,
                        object=observation.object,
                        metadata=metadata,
                    )
                )
            entities = [
                Entity(
                    entity_id=f"track-{track.track_id}",
                    label=track.label,
                    bbox=track.bbox,
                    confidence=track.confidence,
                )
                for track in tracks
                if track.missed == 0
            ]
            frame_relation_facts: list[PrimitiveFact] = []
            for relation in relations.evaluate(entities, list(self.zones), frame.timestamp):
                relation_metadata = sanitize_sensitive_payload(
                    {
                        **relation.metadata,
                        "source_provider": frame_metadata.get("provider"),
                        "source_id": frame.source_id,
                        "continuity_segment": continuity_segment,
                        **({"quality_gate": quality_summary} if quality_summary is not None else {}),
                        **({"frame_discontinuity_before": True} if discontinuity_before else {}),
                    }
                )
                primitive = PrimitiveFact(
                    fact_type=relation.fact_type,
                    timestamp=relation.timestamp,
                    confidence=relation.confidence,
                    subject=relation.subject,
                    object=relation.object,
                    metadata=relation_metadata if isinstance(relation_metadata, dict) else {},
                )
                facts.append(primitive)
                frame_relation_facts.append(primitive)
            action_facts = keypoint_actions.extract(
                observations,
                frame_relation_facts,
                frame_index=frame.frame_index,
            )
            for action in action_facts:
                action.metadata["continuity_segment"] = continuity_segment
                action.metadata["source_id"] = frame.source_id
                if quality_summary is not None:
                    action.metadata["quality_gate"] = quality_summary
                if discontinuity_before:
                    action.metadata["frame_discontinuity_before"] = True
            facts.extend(action_facts)
        return facts
