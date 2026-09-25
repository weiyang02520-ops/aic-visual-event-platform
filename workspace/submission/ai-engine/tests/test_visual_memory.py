import json
from datetime import datetime, timezone

from visual_event_ai.fact_pipeline import FrameFactExtractor
from visual_event_ai.models import PrimitiveFact
from visual_event_ai.relations import Zone
from visual_event_ai.visual_memory import VisualMemory


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _fact(fact_type, *, source="camera-a", segment=0, track=1, label="box", timestamp=BASE, **kwargs):
    metadata = {"source_id": source, "continuity_segment": segment}
    subject = {"id": f"track-{track}", "label": label}
    return PrimitiveFact(
        fact_type=fact_type,
        timestamp=timestamp,
        confidence=kwargs.pop("confidence", 0.9),
        subject=kwargs.pop("subject", subject),
        object=kwargs.pop("object", None),
        location=kwargs.pop("location", None),
        metadata={**metadata, **kwargs.pop("metadata", {})},
    )


def _observed(track=1, *, source="camera-a", segment=0, label="box", timestamp=BASE, bbox=(1, 2, 8, 9), metadata=None):
    return _fact(
        "object_detected",
        source=source,
        segment=segment,
        track=track,
        label=label,
        timestamp=timestamp,
        object={"bbox": bbox},
        metadata=metadata or {},
    )


def _in_zone(track=1, zone_id="zone-a", location="区域 A", *, source="camera-a", segment=0, label="box", timestamp=BASE):
    return _fact(
        "object_in_zone",
        source=source,
        segment=segment,
        track=track,
        label=label,
        timestamp=timestamp,
        location=location,
        object={"zone_id": zone_id, "label": location},
        metadata={"zone_id": zone_id, "bbox": [1, 2, 8, 9]},
    )


def test_memory_updates_last_seen_zone_and_bbox():
    memory = VisualMemory()
    memory.ingest([_observed(), _in_zone(zone_id="zone-a", location="区域 A")])

    record = memory.get("camera-a", 0, 1)
    assert record is not None
    assert record.current_zone_id == "zone-a"
    assert record.current_location == "区域 A"
    assert record.last_observed_location == "区域 A"
    assert record.last_bbox == (1.0, 2.0, 8.0, 9.0)
    assert record.provenance == "direct_observation"


def test_memory_moves_one_identity_between_zones():
    memory = VisualMemory()
    memory.ingest([_observed(), _in_zone(zone_id="zone-a", location="区域 A"), _in_zone(zone_id="zone-b", location="区域 B", timestamp=BASE.replace(second=1))])

    record = memory.get("camera-a", 0, 1)
    assert record is not None
    assert record.current_zone_id == "zone-b"
    assert record.current_location == "区域 B"
    assert record.last_observed_zone_id == "zone-b"


def test_same_label_tracks_remain_independent():
    memory = VisualMemory()
    memory.ingest([_observed(1), _observed(2), _in_zone(1, "zone-a", "区域 A"), _in_zone(2, "zone-b", "区域 B")])

    records = memory.last_seen_candidates("box")
    assert {record.identity_key for record in records} == {("camera-a", 0, "track-1"), ("camera-a", 0, "track-2")}
    assert {record.current_location for record in records} == {"区域 A", "区域 B"}


def test_same_track_across_sources_does_not_merge():
    memory = VisualMemory()
    memory.ingest([_observed(source="camera-a"), _observed(source="camera-b")])

    assert len(memory.records()) == 2
    assert memory.get("camera-a", 0, 1) is not None
    assert memory.get("camera-b", 0, 1) is not None


def test_same_track_after_continuity_gap_does_not_merge():
    memory = VisualMemory()
    memory.ingest([
        _observed(segment=0),
        _fact("observation_gap", segment=1, timestamp=BASE.replace(second=1)),
        _observed(segment=1, timestamp=BASE.replace(second=2)),
    ])

    assert len(memory.records()) == 2
    assert memory.get("camera-a", 0, 1) is not None
    assert memory.get("camera-a", 1, 1) is not None


def test_left_zone_removes_current_certainty_without_inventing_destination():
    memory = VisualMemory()
    memory.ingest([
        _observed(),
        _in_zone(zone_id="zone-a", location="区域 A"),
        _fact(
            "left_zone",
            location="区域 A",
            object={"zone_id": "zone-a", "label": "区域 A"},
            metadata={"zone_id": "zone-a"},
            timestamp=BASE.replace(second=1),
        ),
    ])

    record = memory.get("camera-a", 0, 1)
    assert record is not None
    assert record.current_zone_id is None
    assert record.current_location is None
    assert record.last_observed_location == "区域 A"
    assert record.state == "last_known"


def test_person_detections_are_excluded():
    memory = VisualMemory()
    memory.ingest([_observed(label="person")])

    assert memory.records() == []


def test_memory_record_has_explainable_provenance_and_no_pixels():
    memory = VisualMemory()
    memory.ingest([_observed(metadata={"image": [[1, 2]], "rgb": [[3, 4]]})])

    record = memory.records()[0]
    assert record.source_id == "camera-a"
    assert record.continuity_segment == 0
    assert record.last_seen_at.tzinfo is not None
    assert record.last_bbox == (1.0, 2.0, 8.0, 9.0)
    assert not hasattr(record, "image")
    assert not hasattr(record, "pixels")


def test_frame_fact_extractor_emits_generic_object_zone_fact_and_memory(tmp_path):
    fixture = tmp_path / "object-zone.jsonl"
    records = [
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "payload": {"objects": [{"label": "box", "confidence": 0.9, "bbox": [2, 2, 6, 6]}]},
        },
        {
            "timestamp": "2026-01-01T00:00:01Z",
            "payload": {"objects": [{"label": "box", "confidence": 0.9, "bbox": [22, 2, 6, 6]}]},
        },
    ]
    fixture.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

    facts = FrameFactExtractor(zones=[Zone("a", "区域 A", 0, 0, 15, 15), Zone("b", "区域 B", 20, 0, 15, 15)]).extract(str(fixture))
    location_facts = [fact for fact in facts if fact.fact_type == "object_in_zone"]
    assert [(fact.object["zone_id"], fact.location) for fact in location_facts] == [("a", "区域 A"), ("b", "区域 B")]

    memory = VisualMemory()
    memory.ingest(facts)
    record = memory.get(str(fixture), 0, 1)
    assert record is not None
    assert record.current_zone_id == "b"
    assert record.current_location == "区域 B"
    assert record.last_seen_at.tzinfo is not None
