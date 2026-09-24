from datetime import datetime, timedelta, timezone

from visual_event_ai.models import PluginManifest, PrimitiveFact
from visual_event_ai.plugins import PluginManager, mock_facts


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def fact(kind, seconds=0, **kwargs):
    return PrimitiveFact(fact_type=kind, timestamp=BASE + timedelta(seconds=seconds), **kwargs)


def test_elderly_plugin_marks_incomplete_sequence_for_review():
    manager = PluginManager("plugins")
    manager.scan()
    plugin = manager.records["elderly_care"].implementation
    event = plugin.evaluate(
        [
            fact(
                "object_picked",
                subject={"id": "p1", "label": "老人"},
                object={"id": "box", "label": "药盒"},
                confidence=0.8,
            )
        ],
        "cam-01",
    )[0]
    assert event.event_type == "incomplete_medication_sequence"
    assert event.metadata["needs_review"] is True
    assert event.metadata["sequence_complete"] is False


def test_elderly_plugin_uses_temporal_reasoner_and_preserves_fact_evidence():
    manager = PluginManager("plugins")
    manager.scan()
    events = manager.evaluate(mock_facts("mock://elderly-medication"), "mock://elderly-medication")
    event = next(item for item in events if item.plugin_id == "elderly_care")
    assert event.event_type == "suspected_medication"
    assert event.metadata["reasoner"] == "medication-sequence-v2"
    assert event.metadata["sequence_complete"] is True
    assert [item.fact_type for item in event.facts] == [
        "object_picked",
        "hand_to_face",
        "object_put_down",
    ]
    assert event.started_at < event.ended_at


def test_elderly_plugin_preserves_distinct_label_only_medication_events():
    manager = PluginManager("plugins")
    manager.scan()
    plugin = manager.records["elderly_care"].implementation
    facts = []
    for label in ("药盒 A", "药盒 B"):
        facts.extend(
            [
                fact(
                    "pickup_candidate",
                    1,
                    subject={"id": "p1", "label": "老人"},
                    object={"label": label},
                    confidence=0.9,
                ),
                fact(
                    "hand_to_face",
                    5,
                    subject={"id": "p1", "label": "老人"},
                    object={"label": label},
                    confidence=0.9,
                ),
            ]
        )

    events = plugin.evaluate(facts, "cam-01")

    assert len(events) == 2
    assert {event.event_type for event in events} == {"suspected_medication"}
    assert {event.object["label"] for event in events} == {"药盒 A", "药盒 B"}


def test_elderly_plugin_does_not_pair_different_people_or_objects():
    manager = PluginManager("plugins")
    manager.scan()
    plugin = manager.records["elderly_care"].implementation
    facts = [
        fact(
            "object_picked",
            1,
            subject={"id": "p1", "label": "老人"},
            object={"id": "m1", "label": "药盒"},
        ),
        fact(
            "hand_to_face",
            2,
            subject={"id": "p2", "label": "老人"},
            object={"id": "m1", "label": "药盒"},
        ),
    ]
    events = plugin.evaluate(facts, "cam-01")
    assert events
    assert all(event.event_type == "incomplete_medication_sequence" for event in events)
    assert all(event.metadata["sequence_complete"] is False for event in events)


def test_elderly_plugin_rejects_explicit_non_person_subject_even_with_id():
    manager = PluginManager("plugins")
    manager.scan()
    plugin = manager.records["elderly_care"].implementation
    facts = [
        fact(
            "pickup_candidate",
            1,
            subject={"id": "entity-7", "label": "自动发药柜"},
            object={"id": "m1", "label": "药盒"},
        ),
        fact(
            "hand_to_face",
            5,
            subject={"id": "entity-7", "label": "自动发药柜"},
            object={"id": "m1", "label": "药盒"},
        ),
    ]

    assert plugin.evaluate(facts, "cam-01") == []


def test_workshop_plugin_tracks_taken_returned_and_missing():
    manager = PluginManager("plugins")
    manager.scan()
    plugin = manager.records["workshop"].implementation
    for kind, expected, state in (("object_removed", "object_removed", "taken"), ("object_returned", "object_returned", "returned"), ("object_missing", "object_missing", "missing")):
        event = plugin.evaluate([fact(kind, object={"id": "drill"}, location="工具架 A")], "cam-02")[0]
        assert event.event_type == expected
        assert event.metadata["object_state"] == state


def test_workshop_plugin_uses_observed_timeout_and_keeps_both_source_facts():
    manager = PluginManager("plugins")
    manager.scan()
    plugin = manager.records["workshop"].implementation
    events = plugin.evaluate(
        [
            fact("object_removed", 0, object={"id": "drill", "label": "电钻"}, confidence=0.9),
            fact("scene_observed", 121, location="工具架 A", confidence=0.8),
        ],
        "cam-02",
    )
    missing = next(event for event in events if event.event_type == "object_missing")
    assert missing.metadata["reasoner"] == "workshop-state-v2"
    assert missing.metadata["missing_policy"] == "observed_timeout"
    assert [item.fact_type for item in missing.facts] == ["object_removed", "scene_observed"]
    assert missing.confidence == 0.8
