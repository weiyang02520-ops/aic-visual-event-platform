from datetime import datetime, timedelta, timezone

import pytest

from visual_event_ai.algorithm_reasoner import MedicationSequenceReasoner, WorkshopStateReasoner
from visual_event_ai.models import PrimitiveFact


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def fact(kind, seconds, *, subject=None, object=None, confidence=0.9, location=None, naive=False, metadata=None):
    timestamp = BASE + timedelta(seconds=seconds)
    if naive:
        timestamp = timestamp.replace(tzinfo=None)
    return PrimitiveFact(
        fact_type=kind,
        timestamp=timestamp,
        confidence=confidence,
        subject=subject,
        object=object,
        location=location,
        metadata=metadata or {},
    )


def medication_sequence(*, person_id="p1", object_id="m1", hand_seconds=5, hand_person_id=None, hand_object_id=None):
    return [
        fact(
            "pickup_candidate",
            1,
            subject={"id": person_id, "label": "老人"},
            object={"id": object_id, "label": "药盒"},
            confidence=0.91,
        ),
        fact(
            "hand_to_face",
            hand_seconds,
            subject={"id": hand_person_id or person_id, "label": "老人"},
            object={"id": hand_object_id or object_id, "label": "药盒"},
            confidence=0.74,
        ),
    ]


def test_medication_reasoner_requires_same_person_object_and_ordered_window():
    reasoner = MedicationSequenceReasoner(max_sequence_seconds=20)
    facts = medication_sequence(hand_person_id="p2")
    assert reasoner.infer(facts) == []

    facts = medication_sequence(hand_object_id="m2")
    assert reasoner.infer(facts) == []

    facts = medication_sequence(hand_seconds=22)
    assert reasoner.infer(facts) == []

    facts = list(reversed(medication_sequence()))
    events = reasoner.infer(facts)
    assert len(events) == 1
    assert events[0].event_type == "suspected_medication"
    assert events[0].confidence == 0.74
    assert events[0].metadata["review_required"] is True
    assert events[0].metadata["medical_diagnosis"] is False
    assert events[0].evidence_fact_types == ("pickup_candidate", "hand_to_face")


def test_medication_reasoner_does_not_pair_explicit_facts_across_sources():
    facts = medication_sequence()
    facts[0].metadata["source_id"] = "camera://a"
    facts[1].metadata["source_id"] = "camera://b"

    reasoner = MedicationSequenceReasoner()

    assert reasoner.infer(facts) == []
    incomplete = reasoner.infer_incomplete(facts)
    assert len(incomplete) == 1
    assert incomplete[0].evidence_facts[0] is facts[0]


def test_medication_reasoner_rejects_malformed_source_provenance_for_pairing():
    facts = medication_sequence()
    facts[0].metadata["source_id"] = "camera://a"
    facts[1].metadata["source_id"] = " "

    assert MedicationSequenceReasoner().infer(facts) == []


@pytest.mark.parametrize(
    "confidence",
    [True, False, "0.9", float("nan"), float("inf"), -0.1, 1.1],
)
def test_primitive_fact_rejects_coerced_or_invalid_confidence(confidence):
    with pytest.raises(ValueError):
        fact("pickup_candidate", 1, confidence=confidence)



@pytest.mark.parametrize(
    "confidence",
    [True, "0.9", 10**1000, float("nan"), 1.1],
)
def test_reasoner_rejects_confidence_mutated_after_fact_creation(confidence):
    anchor = fact(
        "object_picked",
        0,
        subject={"id": "p1", "label": "家属"},
        object={"id": "m1", "label": "药盒"},
    )
    action = fact(
        "hand_to_face",
        1,
        subject={"id": "p1", "label": "家属"},
        object={"id": "m1", "label": "药盒"},
    )
    anchor.confidence = confidence

    with pytest.raises(ValueError, match="fact confidence"):
        MedicationSequenceReasoner().infer([anchor, action])


def test_medication_reasoner_does_not_treat_blank_person_ids_as_same_identity():
    reasoner = MedicationSequenceReasoner()
    facts = medication_sequence(person_id="   ")
    assert reasoner.infer(facts) == []


def test_medication_reasoner_does_not_pair_actions_across_observation_gap():
    anchor = fact(
        "object_picked",
        0,
        subject={"id": "p1", "label": "家属"},
        object={"id": "m1", "label": "药盒"},
        metadata={"continuity_segment": 0},
    )
    gap = fact("observation_gap", 1, metadata={"continuity_segment": 1})
    action = fact(
        "hand_to_face",
        2,
        subject={"id": "p1", "label": "家属"},
        object={"id": "m1", "label": "药盒"},
        metadata={"continuity_segment": 1},
    )
    reasoner = MedicationSequenceReasoner()

    assert reasoner.infer([anchor, gap, action]) == []
    incomplete = reasoner.infer_incomplete([anchor, gap, action])
    assert len(incomplete) == 1
    assert incomplete[0].event_type == "incomplete_medication_sequence"


def test_medication_reasoner_does_not_match_different_objects_by_blank_ids():
    facts = medication_sequence(object_id=" ")
    facts[0].object["label"] = "药盒 A"
    facts[1].object["label"] = "药盒 B"

    assert MedicationSequenceReasoner().infer(facts) == []


def test_medication_reasoner_keeps_label_fallback_when_both_object_ids_are_blank():
    facts = medication_sequence(object_id=" ")
    events = MedicationSequenceReasoner().infer(facts)

    assert len(events) == 1
    assert events[0].event_type == "suspected_medication"


def test_medication_reasoner_deduplicates_same_unidentified_object_by_label():
    facts = medication_sequence(object_id=" ")
    duplicate = medication_sequence(object_id=" ")

    events = MedicationSequenceReasoner().infer(facts + duplicate)

    assert len(events) == 1
    assert events[0].object["label"] == "药盒"


def test_medication_reasoner_preserves_distinct_unidentified_objects_in_deduplication():
    first = medication_sequence(object_id=" ")
    second = medication_sequence(object_id=" ")
    for item in first:
        item.object["label"] = "药盒 A"
    for item in second:
        item.object["label"] = "药盒 B"

    events = MedicationSequenceReasoner().infer(first + second)

    assert len(events) == 2
    assert {event.object["label"] for event in events} == {"药盒 A", "药盒 B"}


def test_medication_reasoner_uses_valid_id_when_track_id_is_blank():
    facts = medication_sequence()
    facts[0].subject = {"track_id": " ", "id": "p1", "label": "老人"}
    facts[1].subject = {"id": "p1", "label": "老人"}

    events = MedicationSequenceReasoner().infer(facts)

    assert len(events) == 1
    assert events[0].event_type == "suspected_medication"


def test_medication_reasoner_rejects_explicit_non_person_subject_even_with_id():
    facts = medication_sequence()
    for item in facts:
        item.subject["label"] = "自动发药柜"

    reasoner = MedicationSequenceReasoner()

    assert reasoner.infer(facts) == []
    assert reasoner.infer_incomplete(facts) == []


@pytest.mark.parametrize("invalid_id", [True, 1.0, ["p1"]])
def test_medication_reasoner_rejects_malformed_person_identity_values(invalid_id):
    facts = medication_sequence(person_id=invalid_id)

    assert MedicationSequenceReasoner().infer(facts) == []


@pytest.mark.parametrize("invalid_id", [True, 1.0, ["m1"]])
def test_medication_reasoner_does_not_fallback_to_labels_for_malformed_object_ids(invalid_id):
    facts = medication_sequence(object_id=invalid_id)

    assert MedicationSequenceReasoner().infer(facts) == []

def test_medication_reasoner_rejects_generic_box_and_unassociated_object_labels():
    reasoner = MedicationSequenceReasoner()
    generic_box = [
        fact("object_picked", 0, subject={"id": "p1"}, object={"id": "box1", "label": "工具盒"}),
        fact("hand_to_face", 2, subject={"id": "p1"}, object={"id": "box1", "label": "工具盒"}),
    ]
    assert reasoner.infer(generic_box) == []

    # Labels cannot override conflicting object IDs.
    conflicting_ids = medication_sequence(hand_object_id="different-medicine")
    assert reasoner.infer(conflicting_ids) == []


@pytest.mark.parametrize(
    "storage_label",
    ["药柜", "药品柜", "药架", "药房", "medicine cabinet", "medicine shelf", "pharmacy"],
)
def test_medication_reasoner_rejects_medication_storage_as_the_medicine_object(storage_label):
    facts = medication_sequence()
    for item in facts:
        item.object["label"] = storage_label

    reasoner = MedicationSequenceReasoner()

    assert reasoner.infer(facts) == []
    assert reasoner.infer_incomplete(facts) == []


@pytest.mark.parametrize(
    "document_label",
    [
        "药品说明书",
        "药物说明书",
        "用药说明",
        "药品清单",
        "药品目录",
        "用药记录",
        "处方单",
        "处方笺",
        "medication list",
        "medicine instructions",
        "package insert",
        "prescription form",
    ],
)
def test_medication_reasoner_rejects_medication_documents_as_the_medicine_object(document_label):
    facts = medication_sequence()
    for item in facts:
        item.object["label"] = document_label

    reasoner = MedicationSequenceReasoner()

    assert reasoner.infer(facts) == []
    assert reasoner.infer_incomplete(facts) == []


def test_explicit_medication_category_overrides_storage_like_display_label():
    facts = medication_sequence()
    for item in facts:
        item.object["label"] = "药柜"
        item.object["category"] = "medicine"

    events = MedicationSequenceReasoner().infer(facts)

    assert len(events) == 1
    assert events[0].event_type == "suspected_medication"


def test_explicit_medication_category_overrides_document_like_display_label():
    facts = medication_sequence()
    for item in facts:
        item.object["label"] = "药品说明书"
        item.object["category"] = "medicine"

    events = MedicationSequenceReasoner().infer(facts)

    assert len(events) == 1
    assert events[0].event_type == "suspected_medication"


def test_medication_reasoner_adds_only_same_object_putdown_as_support():
    reasoner = MedicationSequenceReasoner()
    facts = medication_sequence()
    facts.extend(
        [
            fact(
                "object_put_down",
                7,
                subject={"id": "p1"},
                object={"id": "other", "label": "药盒"},
                confidence=0.99,
            ),
            fact(
                "putdown_candidate",
                8,
                subject={"id": "p1"},
                object={"id": "m1", "label": "药盒"},
                confidence=0.68,
            ),
        ]
    )
    event = reasoner.infer(facts)[0]
    assert event.evidence_fact_types == ("pickup_candidate", "hand_to_face", "putdown_candidate")
    assert event.confidence == 0.68
    assert event.metadata["put_down_observed"] is True


def test_medication_reasoner_skips_weak_hand_for_later_qualified_action():
    facts = [
        fact(
            "pickup_candidate",
            1,
            subject={"id": "p1", "label": "老人"},
            object={"id": "m1", "label": "药盒"},
            confidence=0.91,
        ),
        fact(
            "hand_to_face",
            2,
            subject={"id": "p1", "label": "老人"},
            object={"id": "m1", "label": "药盒"},
            confidence=0.1,
        ),
        fact(
            "hand_to_face",
            5,
            subject={"id": "p1", "label": "老人"},
            object={"id": "m1", "label": "药盒"},
            confidence=0.74,
        ),
    ]

    events = MedicationSequenceReasoner().infer(facts)

    assert len(events) == 1
    assert events[0].event_type == "suspected_medication"
    assert events[0].evidence_fact_types == ("pickup_candidate", "hand_to_face")
    assert events[0].ended_at == BASE + timedelta(seconds=5)


def test_medication_reasoner_ignores_low_confidence_optional_putdown():
    facts = medication_sequence()
    facts.append(
        fact(
            "putdown_candidate",
            7,
            subject={"id": "p1", "label": "老人"},
            object={"id": "m1", "label": "药盒"},
            confidence=0.1,
        )
    )

    events = MedicationSequenceReasoner().infer(facts)

    assert len(events) == 1
    assert events[0].event_type == "suspected_medication"
    assert events[0].evidence_fact_types == ("pickup_candidate", "hand_to_face")
    assert events[0].metadata["put_down_observed"] is False


def test_medication_reasoner_produces_only_reviewable_partial_pickup_cue():
    reasoner = MedicationSequenceReasoner()
    facts = [
        fact(
            "object_picked",
            0,
            subject={"id": "p1", "label": "person"},
            object={"id": "m1", "label": "medicine bottle"},
        )
    ]
    event = reasoner.infer_incomplete(facts)[0]
    assert event.event_type == "incomplete_medication_sequence"
    assert event.metadata["sequence_complete"] is False
    assert event.metadata["missing_step"] == "hand_to_face"

    # A matching hand fact, even below the output confidence threshold, means
    # the sequence is present and should not be mislabeled as incomplete.
    facts.append(
        fact(
            "hand_to_face",
            2,
            subject={"id": "p1"},
            object={"id": "m1", "label": "medicine bottle"},
            confidence=0.1,
        )
    )
    assert reasoner.infer_incomplete(facts) == []


def test_reasoners_normalize_legacy_naive_timestamps_as_utc():
    reasoner = MedicationSequenceReasoner()
    facts = [
        fact("object_picked", 0, subject={"id": "p1"}, object={"id": "m1", "label": "药品"}, naive=True),
        fact("hand_to_face", 2, subject={"id": "p1"}, object={"id": "m1", "label": "药品"}),
    ]
    event = reasoner.infer(facts)[0]
    assert event.started_at.tzinfo == timezone.utc
    assert event.ended_at.tzinfo == timezone.utc


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_sequence_seconds": 0},
        {"max_sequence_seconds": -1},
        {"max_sequence_seconds": float("inf")},
        {"max_sequence_seconds": 1e20},
        {"max_sequence_seconds": 10**1000},
        {"max_sequence_seconds": True},
        {"max_sequence_seconds": "45"},
        {"min_confidence": True},
        {"min_confidence": "0.45"},
        {"min_confidence": -0.1},
        {"min_confidence": 1.1},
        {"min_confidence": 10**1000},
    ],
)
def test_medication_reasoner_rejects_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        MedicationSequenceReasoner(**kwargs)


def test_workshop_reasoner_emits_removed_return_and_observed_timeout_missing():
    reasoner = WorkshopStateReasoner(missing_after_seconds=10)
    removed = fact(
        "object_removed",
        0,
        subject={"id": "p1", "label": "工作人员"},
        object={"id": "tool1", "label": "电钻"},
        location="工具架 A",
    )
    returned = fact(
        "object_returned",
        4,
        subject={"id": "p1", "label": "工作人员"},
        object={"id": "tool1", "label": "电钻"},
        location="工具架 B",
    )
    events = reasoner.infer([returned, removed])
    assert [event.event_type for event in events] == ["object_removed", "object_returned"]
    assert events[-1].started_at == BASE
    assert events[-1].location == "工具架 B"
    assert events[-1].evidence_fact_types == ("object_removed", "object_returned")

    timed_out = reasoner.infer(
        [removed, fact("scene_observed", 10, confidence=0.8, location="工具架 A")]
    )
    assert [event.event_type for event in timed_out] == ["object_removed", "object_missing"]
    assert timed_out[-1].ended_at == BASE + timedelta(seconds=10)
    assert timed_out[-1].confidence == 0.8
    assert timed_out[-1].metadata["review_required"] is True
    assert timed_out[-1].metadata["missing_policy"] == "observed_timeout"



def test_workshop_reasoner_does_not_pair_explicit_transitions_across_sources():
    tool = {"id": "tool1", "label": "电钻"}
    removed = fact(
        "object_removed",
        0,
        object=tool,
        metadata={"source_id": "camera://a"},
    )
    returned = fact(
        "object_returned",
        4,
        object=tool,
        metadata={"source_id": "camera://b"},
    )

    events = WorkshopStateReasoner().infer([removed, returned])

    assert [event.event_type for event in events] == ["object_removed", "object_returned"]
    assert events[-1].evidence_fact_types == ("object_returned",)


def test_workshop_reasoner_does_not_use_observation_from_another_source_for_missing():
    removed = fact(
        "object_removed",
        0,
        object={"id": "tool1", "label": "电钻"},
        metadata={"source_id": "camera://a"},
    )
    observed = fact(
        "scene_observed",
        10,
        location="工具架 A",
        metadata={"source_id": "camera://b"},
    )

    events = WorkshopStateReasoner(missing_after_seconds=10).infer([removed, observed])

    assert [event.event_type for event in events] == ["object_removed"]


def test_workshop_reasoner_requires_timeout_observation_from_removed_zone():
    reasoner = WorkshopStateReasoner(missing_after_seconds=10)
    tool = {"id": "tool1", "label": "电钻"}
    removed = fact(
        "left_zone",
        0,
        subject=tool,
        location="工具架 A",
        metadata={"zone_id": "shelf-a"},
    )
    wrong_zone_observation = fact(
        "scene_observed",
        10,
        location="工作台",
        metadata={"zone_id": "bench"},
    )
    matching_observation = fact(
        "scene_observed",
        11,
        location="工具架 A",
        metadata={"zone_id": "shelf-a"},
    )

    wrong_zone_events = reasoner.infer([removed, wrong_zone_observation])
    assert [event.event_type for event in wrong_zone_events] == ["object_removed"]

    events = reasoner.infer([removed, wrong_zone_observation, matching_observation])
    assert [event.event_type for event in events] == ["object_removed", "object_missing"]
    missing = events[-1]
    assert missing.ended_at == BASE + timedelta(seconds=11)
    assert missing.evidence_fact_types == ("left_zone", "scene_observed")
    assert missing.location == "工具架 A"

def test_workshop_reasoner_requires_explicit_scene_observation_for_timeout():
    reasoner = WorkshopStateReasoner(missing_after_seconds=10)
    removed = fact("object_removed", 0, object={"id": "tool1"})
    unrelated = fact("person_object_distance", 30, subject={"id": "p1"}, object={"id": "other"})
    events = reasoner.infer([removed, unrelated])
    assert [event.event_type for event in events] == ["object_removed"]


def test_workshop_reasoner_does_not_infer_missing_across_observation_gap():
    reasoner = WorkshopStateReasoner(missing_after_seconds=10)
    removed = fact(
        "object_removed",
        0,
        object={"id": "tool1", "label": "电钻"},
        metadata={"continuity_segment": 0},
    )
    gap = fact("observation_gap", 1, metadata={"continuity_segment": 1})
    observed = fact(
        "scene_observed",
        20,
        location="工具架 A",
        metadata={"continuity_segment": 1},
    )

    events = reasoner.infer([removed, gap, observed])

    assert [event.event_type for event in events] == ["object_removed"]


def test_workshop_reasoner_does_not_pair_explicit_transitions_across_segments():
    reasoner = WorkshopStateReasoner()
    removed = fact(
        "left_zone",
        0,
        subject={"id": "tool1", "label": "电钻"},
        location="工具架 A",
        metadata={"zone_id": "shelf-a", "continuity_segment": 0},
    )
    returned = fact(
        "object_returned",
        2,
        object={"id": "tool1", "label": "电钻"},
        location="工具架 A",
        metadata={"continuity_segment": 1},
    )
    missing = fact(
        "object_missing",
        3,
        object={"id": "tool1", "label": "电钻"},
        location="工具架 A",
        metadata={"continuity_segment": 1},
    )

    events = reasoner.infer([removed, returned, missing])

    assert [event.event_type for event in events] == [
        "object_removed",
        "object_returned",
        "object_missing",
    ]
    assert events[1].evidence_fact_types == ("object_returned",)
    assert events[2].evidence_fact_types == ("object_missing",)


def test_workshop_reasoner_does_not_use_scene_observation_from_another_segment():
    reasoner = WorkshopStateReasoner(missing_after_seconds=10)
    removed = fact(
        "object_removed",
        0,
        object={"id": "tool1", "label": "电钻"},
        metadata={"continuity_segment": 0},
    )
    observed = fact(
        "scene_observed",
        20,
        location="工具架 A",
        metadata={"continuity_segment": 1},
    )

    events = reasoner.infer([removed, observed])

    assert [event.event_type for event in events] == ["object_removed"]


def test_workshop_reasoner_does_not_treat_person_object_separation_as_return():
    reasoner = WorkshopStateReasoner()
    removed = fact("object_removed", 0, object={"id": "tool1", "label": "电钻"})
    putdown_candidate = fact(
        "putdown_candidate",
        3,
        subject={"id": "p1", "label": "工作人员"},
        object={"id": "tool1", "label": "电钻"},
    )
    events = reasoner.infer([removed, putdown_candidate])
    assert [event.event_type for event in events] == ["object_removed"]


def test_workshop_reasoner_matches_zone_transitions_by_tracked_subject_and_zone_id():
    reasoner = WorkshopStateReasoner()
    left = fact(
        "left_zone",
        0,
        subject={"id": "tool1", "label": "电钻"},
        location="工具架 A",
        metadata={"zone_id": "shelf-a"},
    )
    entered_wrong_zone = fact(
        "entered_zone",
        2,
        subject={"id": "tool1", "label": "电钻"},
        location="工作台",
        metadata={"zone_id": "bench"},
    )
    entered_origin = fact(
        "entered_zone",
        4,
        subject={"id": "tool1", "label": "电钻"},
        location="工具架 A",
        metadata={"zone_id": "shelf-a"},
    )
    events = reasoner.infer([left, entered_wrong_zone, entered_origin])
    assert [event.event_type for event in events] == ["object_removed", "object_returned"]
    assert events[-1].object == {"id": "tool1", "label": "电钻"}
    assert events[-1].location == "工具架 A"
    assert events[-1].evidence_fact_types == ("left_zone", "entered_zone")




@pytest.mark.parametrize("reverse", [False, True])
def test_workshop_reasoner_does_not_infer_return_from_equal_timestamp_zone_facts(reverse):
    reasoner = WorkshopStateReasoner()
    tool = {"id": "tool1", "label": "电钻"}
    facts = [
        fact("left_zone", 0, subject=tool, location="工具架 A", metadata={"zone_id": "shelf-a"}),
        fact("entered_zone", 0, subject=tool, location="工具架 A", metadata={"zone_id": "shelf-a"}),
    ]
    if reverse:
        facts.reverse()

    events = reasoner.infer(facts)

    assert [event.event_type for event in events] == ["object_removed"]


@pytest.mark.parametrize("reverse", [False, True])
def test_workshop_reasoner_does_not_attach_equal_timestamp_removal_to_explicit_transitions(reverse):
    reasoner = WorkshopStateReasoner()
    tool = {"id": "tool1", "label": "电钻"}
    removed = fact("object_removed", 0, object=tool, location="工具架 A")
    transitions = (
        fact("object_returned", 0, object=tool, location="工具架 A"),
        fact("object_missing", 0, object=tool, location="工具架 A"),
    )

    for transition in transitions:
        facts = [removed, transition]
        if reverse:
            facts.reverse()
        events = reasoner.infer(facts)
        by_type = {event.event_type: event for event in events}
        assert "object_removed" in by_type
        assert transition.fact_type in by_type
        assert by_type[transition.fact_type].evidence_fact_types == (transition.fact_type,)


def test_workshop_reasoner_deduplicates_only_within_the_same_zone():
    reasoner = WorkshopStateReasoner(missing_after_seconds=10)
    tool = {"id": "tool1", "label": "电钻"}
    events = reasoner.infer(
        [
            fact("left_zone", 0, subject=tool, location="工具架 A", metadata={"zone_id": "shelf-a"}),
            fact("left_zone", 0, subject=tool, location="工作台", metadata={"zone_id": "bench"}),
            fact("scene_observed", 10),
        ]
    )

    assert [event.event_type for event in events] == [
        "object_removed",
        "object_removed",
        "object_missing",
        "object_missing",
    ]
    assert [event.evidence_facts[0].metadata["zone_id"] for event in events] == [
        "shelf-a",
        "bench",
        "shelf-a",
        "bench",
    ]

def test_workshop_reasoner_preserves_pending_removal_for_each_zone():
    reasoner = WorkshopStateReasoner()
    tool = {"id": "tool1", "label": "电钻"}
    events = reasoner.infer(
        [
            fact("left_zone", 0, subject=tool, location="工具架 A", metadata={"zone_id": "shelf-a"}),
            fact("entered_zone", 1, subject=tool, location="工作台", metadata={"zone_id": "bench"}),
            fact("left_zone", 2, subject=tool, location="工作台", metadata={"zone_id": "bench"}),
            fact("entered_zone", 3, subject=tool, location="工具架 A", metadata={"zone_id": "shelf-a"}),
            fact("entered_zone", 4, subject=tool, location="工作台", metadata={"zone_id": "bench"}),
        ]
    )

    assert [event.event_type for event in events] == [
        "object_removed",
        "object_removed",
        "object_returned",
        "object_returned",
    ]
    returned_shelf, returned_bench = events[2:]
    assert returned_shelf.started_at == BASE
    assert returned_shelf.ended_at == BASE + timedelta(seconds=3)
    assert returned_shelf.evidence_fact_types == ("left_zone", "entered_zone")
    assert returned_shelf.location == "工具架 A"
    assert returned_bench.started_at == BASE + timedelta(seconds=2)
    assert returned_bench.ended_at == BASE + timedelta(seconds=4)
    assert returned_bench.evidence_fact_types == ("left_zone", "entered_zone")
    assert returned_bench.location == "工作台"



def test_workshop_reasoner_does_not_match_blank_zone_ids_across_locations():
    reasoner = WorkshopStateReasoner()
    tool = {"id": "tool1", "label": "电钻"}
    events = reasoner.infer(
        [
            fact("left_zone", 0, subject=tool, location="工具架 A", metadata={"zone_id": " "}),
            fact("entered_zone", 1, subject=tool, location="工作台", metadata={"zone_id": " "}),
        ]
    )

    assert [event.event_type for event in events] == ["object_removed"]

def test_workshop_reasoner_scoped_explicit_missing_uses_same_zone_removal():
    reasoner = WorkshopStateReasoner()
    tool = {"id": "tool1", "label": "电钻"}
    events = reasoner.infer(
        [
            fact("left_zone", 0, subject=tool, location="工具架 A", metadata={"zone_id": "shelf-a"}),
            fact("left_zone", 1, subject=tool, location="工作台", metadata={"zone_id": "bench"}),
            fact(
                "object_missing",
                2,
                object=tool,
                location="工具架 A",
                metadata={"zone_id": "shelf-a"},
            ),
        ]
    )

    assert [event.event_type for event in events] == [
        "object_removed",
        "object_removed",
        "object_missing",
    ]
    missing = events[-1]
    assert missing.started_at == BASE
    assert missing.ended_at == BASE + timedelta(seconds=2)
    assert missing.evidence_fact_types == ("left_zone", "object_missing")
    assert missing.evidence_facts[0].metadata["zone_id"] == "shelf-a"
    assert missing.location == "工具架 A"

def test_workshop_reasoner_handles_explicit_missing_and_does_not_duplicate_timeout():
    reasoner = WorkshopStateReasoner(missing_after_seconds=10)
    removed = fact("object_removed", 0, object={"id": "tool1"})
    missing = fact("object_missing", 5, object={"id": "tool1"})
    events = reasoner.infer([removed, missing, fact("scene_observed", 20)])
    assert [event.event_type for event in events] == ["object_removed", "object_missing"]
    assert events[-1].metadata["missing_policy"] == "explicit_fact"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"missing_after_seconds": 0},
        {"missing_after_seconds": float("nan")},
        {"missing_after_seconds": 1e20},
        {"missing_after_seconds": 10**1000},
        {"missing_after_seconds": True},
        {"missing_after_seconds": "120"},
        {"min_confidence": True},
        {"min_confidence": "0.4"},
        {"min_confidence": 1.5},
    ],
)
def test_workshop_reasoner_rejects_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        WorkshopStateReasoner(**kwargs)
