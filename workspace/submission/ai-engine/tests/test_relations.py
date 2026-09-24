from datetime import datetime, timedelta, timezone

import pytest

from visual_event_ai.relations import Entity, RelationEngine, Zone


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def person(x=0, y=0):
    return Entity("person-1", "person", (x, y, 4, 4), 0.9)


def box(x=60, y=0):
    return Entity("box-1", "medicine_box", (x, y, 4, 4), 0.8)


def test_relations_emit_near_pickup_putdown_and_distance():
    engine = RelationEngine(near_distance=20, cooldown_seconds=0)
    assert {fact.fact_type for fact in engine.evaluate([person(), box()], [], BASE)} == {"person_object_distance"}
    near_types = {fact.fact_type for fact in engine.evaluate([person(), box(10)], [], BASE + timedelta(seconds=1))}
    assert {"person_object_distance", "near", "pickup_candidate"} <= near_types
    far_types = {fact.fact_type for fact in engine.evaluate([person(), box(60)], [], BASE + timedelta(seconds=2))}
    assert "putdown_candidate" in far_types


def test_zone_entry_exit_motion_and_cooldown():
    engine = RelationEngine(motion_distance=3, cooldown_seconds=10)
    zone = Zone("table", "药盒区域", 0, 0, 20, 20)
    engine.evaluate([person(50, 50)], [zone], BASE)
    entered = engine.evaluate([person(5, 5)], [zone], BASE + timedelta(seconds=1))
    assert "entered_zone" in {fact.fact_type for fact in entered}
    moved = engine.evaluate([person(12, 5)], [zone], BASE + timedelta(seconds=2))
    assert "motion" not in {fact.fact_type for fact in moved}  # cooldown suppresses repeated same entity motion
    left = engine.evaluate([person(50, 50)], [zone], BASE + timedelta(seconds=12))
    assert "left_zone" in {fact.fact_type for fact in left}


def test_relation_engine_does_not_infer_pair_transition_across_missing_detection():
    engine = RelationEngine(near_distance=20, motion_distance=3, cooldown_seconds=0)
    close = engine.evaluate([person(), box(10)], [], BASE)
    assert "pickup_candidate" in {fact.fact_type for fact in close}

    engine.evaluate([person()], [], BASE + timedelta(seconds=1))
    far_after_gap = engine.evaluate([person(), box(100)], [], BASE + timedelta(seconds=2))
    assert "putdown_candidate" not in {fact.fact_type for fact in far_after_gap}
    assert "motion" not in {fact.fact_type for fact in far_after_gap}

    close_after_gap = engine.evaluate([person(), box(10)], [], BASE + timedelta(seconds=3))
    assert "pickup_candidate" in {fact.fact_type for fact in close_after_gap}


def test_relation_engine_resets_pair_cooldown_after_detection_gap():
    engine = RelationEngine(near_distance=20, cooldown_seconds=1.5)
    close = [person(), box(10)]
    assert "pickup_candidate" in {fact.fact_type for fact in engine.evaluate(close, [], BASE)}

    engine.evaluate([person()], [], BASE + timedelta(seconds=0.5))
    restored = engine.evaluate(close, [], BASE + timedelta(seconds=1))

    assert {"near", "pickup_candidate"} <= {fact.fact_type for fact in restored}


def test_relation_engine_resets_motion_cooldown_after_entity_gap():
    engine = RelationEngine(motion_distance=3, cooldown_seconds=10)
    engine.evaluate([person(0)], [], BASE)
    assert "motion" in {
        fact.fact_type
        for fact in engine.evaluate([person(10)], [], BASE + timedelta(seconds=0.1))
    }

    engine.evaluate([], [], BASE + timedelta(seconds=0.2))
    engine.evaluate([person(100)], [], BASE + timedelta(seconds=0.3))
    resumed_motion = engine.evaluate([person(110)], [], BASE + timedelta(seconds=0.4))

    assert "motion" in {fact.fact_type for fact in resumed_motion}


def test_relation_engine_resets_zone_cooldown_after_entity_gap():
    engine = RelationEngine(cooldown_seconds=10)
    zone = Zone("table", "工作台", 0, 0, 20, 20)
    engine.evaluate([box(40)], [zone], BASE)
    first_entry = engine.evaluate([box(5)], [zone], BASE + timedelta(seconds=1))
    assert "entered_zone" in {fact.fact_type for fact in first_entry}

    engine.evaluate([], [zone], BASE + timedelta(seconds=1.1))
    engine.evaluate([box(40)], [zone], BASE + timedelta(seconds=1.2))
    resumed_entry = engine.evaluate([box(5)], [zone], BASE + timedelta(seconds=1.3))

    assert "entered_zone" in {fact.fact_type for fact in resumed_entry}


def test_relation_engine_omits_pair_facts_when_finite_coordinates_overflow_distance():
    engine = RelationEngine(cooldown_seconds=0)
    far_person = Entity("far-person", "person", (1e308, 0, 1, 1))
    far_item = Entity("far-item", "medicine_box", (-1e308, 0, 1, 1))

    facts = engine.evaluate([far_person, far_item], [], BASE)

    assert facts == []


def test_relation_engine_omits_motion_when_finite_coordinates_overflow_displacement():
    engine = RelationEngine(cooldown_seconds=0)
    engine.evaluate([Entity("moving", "tool", (-1e308, 0, 1, 1))], [], BASE)

    facts = engine.evaluate(
        [Entity("moving", "tool", (1e308, 0, 1, 1))],
        [],
        BASE + timedelta(seconds=1),
    )

    assert "motion" not in {fact.fact_type for fact in facts}


def test_relation_engine_does_not_infer_zone_exit_or_motion_across_missing_detection():
    engine = RelationEngine(motion_distance=3, cooldown_seconds=0)
    zone = Zone("table", "工作台", 0, 0, 20, 20)
    engine.evaluate([box(5, 5)], [zone], BASE)
    engine.evaluate([], [zone], BASE + timedelta(seconds=1))

    after_gap = engine.evaluate([box(100, 5)], [zone], BASE + timedelta(seconds=2))
    after_gap_types = {fact.fact_type for fact in after_gap}
    assert "left_zone" not in after_gap_types
    assert "motion" not in after_gap_types

    observed_entry = engine.evaluate([box(5, 5)], [zone], BASE + timedelta(seconds=3))
    assert "entered_zone" in {fact.fact_type for fact in observed_entry}


def test_relation_cooldowns_do_not_collide_for_colon_delimited_entity_ids():
    engine = RelationEngine(near_distance=20, cooldown_seconds=10)
    engine.evaluate(
        [
            Entity("p:a", "person", (0, 0, 4, 4)),
            Entity("b:c", "tool", (10, 0, 4, 4)),
        ],
        [],
        BASE,
    )

    facts = engine.evaluate(
        [
            Entity("p", "person", (0, 0, 4, 4)),
            Entity("a:b:c", "tool", (10, 0, 4, 4)),
        ],
        [],
        BASE + timedelta(seconds=1),
    )

    assert {"near", "pickup_candidate"} <= {fact.fact_type for fact in facts}


def test_zone_cooldowns_do_not_collide_for_colon_delimited_ids():
    engine = RelationEngine(cooldown_seconds=10)
    zones = [Zone("b", "区域 A", 0, 0, 10, 10), Zone("a:b", "区域 B", 20, 0, 10, 10)]
    engine.evaluate(
        [Entity("e:a", "tool", (50, 0, 4, 4)), Entity("e", "tool", (50, 0, 4, 4))],
        zones,
        BASE,
    )
    first_entry = engine.evaluate(
        [Entity("e:a", "tool", (0, 0, 4, 4)), Entity("e", "tool", (50, 0, 4, 4))],
        zones,
        BASE + timedelta(seconds=1),
    )
    second_entry = engine.evaluate(
        [Entity("e:a", "tool", (0, 0, 4, 4)), Entity("e", "tool", (20, 0, 4, 4))],
        zones,
        BASE + timedelta(seconds=2),
    )

    assert [(fact.fact_type, fact.location) for fact in first_entry if fact.fact_type == "entered_zone"] == [("entered_zone", "区域 A")]
    assert [(fact.fact_type, fact.location) for fact in second_entry if fact.fact_type == "entered_zone"] == [("entered_zone", "区域 B")]


def test_relation_engine_rejects_time_regression_without_corrupting_state():
    engine = RelationEngine(cooldown_seconds=0)
    engine.evaluate([person()], [], BASE + timedelta(seconds=2))
    with pytest.raises(ValueError, match="non-decreasing"):
        engine.evaluate([person(20, 0)], [], BASE + timedelta(seconds=1))

    facts = engine.evaluate([person(2, 0), box(40, 0)], [], BASE + timedelta(seconds=3))
    assert facts
    assert all(fact.timestamp.tzinfo == timezone.utc for fact in facts)


def test_relation_engine_discontinuity_reset_preserves_timestamp_regression_guard():
    engine = RelationEngine()
    engine.evaluate([], [], BASE + timedelta(seconds=2))

    engine.reset_after_discontinuity()

    with pytest.raises(ValueError, match="non-decreasing"):
        engine.evaluate([], [], BASE + timedelta(seconds=1))


def test_relation_engine_interprets_naive_timestamps_as_utc():
    engine = RelationEngine(cooldown_seconds=0)
    engine.evaluate([], [], BASE.replace(tzinfo=None))
    facts = engine.evaluate([person(), box()], [], BASE + timedelta(seconds=1))
    assert facts[0].timestamp.tzinfo == timezone.utc


@pytest.mark.parametrize("person_label", ["家属", "Person"])
def test_relation_engine_recognizes_person_aliases_consistently(person_label):
    actor = Entity("person-1", person_label, (0, 0, 4, 4), 0.9)
    engine = RelationEngine(near_distance=20, cooldown_seconds=0)
    facts = engine.evaluate([actor, box(10, 0)], [], BASE)
    assert {"near", "pickup_candidate"} <= {fact.fact_type for fact in facts}


@pytest.mark.parametrize("bbox", [(0, 0, 0, 4), (0, 0, 4, -1), (0, 0, float("nan"), 4), (1e308, 0, 1e308, 4)])
def test_entity_rejects_invalid_geometry(bbox):
    with pytest.raises(ValueError, match="bbox"):
        Entity("bad", "tool", bbox)


@pytest.mark.parametrize("confidence", [-0.1, 1.1, float("inf")])
def test_entity_rejects_invalid_confidence(confidence):
    with pytest.raises(ValueError, match="confidence"):
        Entity("bad", "tool", (0, 0, 4, 4), confidence)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"near_distance": 0},
        {"near_distance": float("inf")},
        {"near_distance": 10**1000},
        {"motion_distance": -1},
        {"cooldown_seconds": -1},
        {"cooldown_seconds": float("nan")},
        {"near_distance": True},
        {"motion_distance": "8"},
        {"cooldown_seconds": False},
    ],
)
def test_relation_engine_rejects_invalid_thresholds(kwargs):
    with pytest.raises(ValueError):
        RelationEngine(**kwargs)


@pytest.mark.parametrize("width,height", [(0, 10), (10, -1), (float("inf"), 10)])
def test_zone_rejects_invalid_dimensions(width, height):
    with pytest.raises(ValueError, match="zone"):
        Zone("bad", "bad", 0, 0, width, height)


def test_zone_rejects_finite_values_with_overflowing_extent():
    with pytest.raises(ValueError, match="extents"):
        Zone("bad", "bad", 1e308, 0, 1e308, 10)

@pytest.mark.parametrize("zone_id", ["", "   ", None, 7])
def test_zone_rejects_empty_or_non_string_ids(zone_id):
    with pytest.raises(ValueError, match="zone_id"):
        Zone(zone_id, "工具架", 0, 0, 20, 20)


@pytest.mark.parametrize("label", ["", "   ", None, 7])
def test_zone_rejects_empty_or_non_string_labels(label):
    with pytest.raises(ValueError, match="label"):
        Zone("shelf-a", label, 0, 0, 20, 20)


@pytest.mark.parametrize(
    "coordinates",
    [
        (True, 0, 10, 10),
        (0, "1", 10, 10),
        (0, 0, "10", 10),
        (0, 0, 10, False),
        (10**1000, 0, 10, 10),
    ],
)
def test_zone_rejects_non_numeric_or_boolean_geometry(coordinates):
    with pytest.raises(ValueError, match="zone"):
        Zone("shelf-a", "工具架", *coordinates)


def test_zone_normalizes_non_empty_id_and_label():
    zone = Zone(" shelf-a ", " 工具架 A ", 0, 0, 20, 20)
    assert zone.zone_id == "shelf-a"
    assert zone.label == "工具架 A"


def test_relation_engine_rejects_duplicate_zone_ids_without_advancing_time():
    engine = RelationEngine()
    zones = [
        Zone("shared", "工具架", 0, 0, 20, 20),
        Zone("shared", "工作台", 20, 0, 20, 20),
    ]
    with pytest.raises(ValueError, match="unique"):
        engine.evaluate([], zones, BASE)

    assert engine.evaluate([], [], BASE) == []

@pytest.mark.parametrize("entity_id", ["", "   ", None, 7])
def test_entity_rejects_empty_or_non_string_ids(entity_id):
    with pytest.raises(ValueError, match="entity_id"):
        Entity(entity_id, "tool", (0, 0, 4, 4))


@pytest.mark.parametrize("label", ["", "   ", None, 7])
def test_entity_rejects_empty_or_non_string_labels(label):
    with pytest.raises(ValueError, match="label"):
        Entity("tool-1", label, (0, 0, 4, 4))


@pytest.mark.parametrize(
    "bbox",
    [
        (True, 0, 4, 4),
        (0, "1", 4, 4),
        (0, 0, "4", 4),
        (0, 0, 4, False),
    ],
)
def test_entity_rejects_non_numeric_or_boolean_bbox_values(bbox):
    with pytest.raises(ValueError, match="bbox"):
        Entity("tool-1", "tool", bbox)


@pytest.mark.parametrize("confidence", [True, "0.9", None, 10**1000])
def test_entity_rejects_non_numeric_or_boolean_confidence(confidence):
    with pytest.raises(ValueError, match="confidence"):
        Entity("tool-1", "tool", (0, 0, 4, 4), confidence)


def test_entity_rejects_unrepresentable_integer_bbox_with_value_error():
    with pytest.raises(ValueError):
        Entity("tool-1", "tool", (10**1000, 0, 1, 1))


def test_entity_normalizes_identity_and_numeric_bbox():
    entity = Entity(" tool-1 ", " 电钻 ", (0, 0.5, 4, 4), 0.9)
    assert entity.entity_id == "tool-1"
    assert entity.label == "电钻"
    assert entity.bbox == (0.0, 0.5, 4.0, 4.0)


def test_relation_engine_rejects_duplicate_entity_ids_without_advancing_time():
    engine = RelationEngine()
    duplicate_id_entities = [
        Entity("same-id", "person", (0, 0, 4, 4)),
        Entity("same-id", "tool", (20, 0, 4, 4)),
    ]
    with pytest.raises(ValueError, match="unique"):
        engine.evaluate(duplicate_id_entities, [], BASE + timedelta(seconds=2))

    assert engine.evaluate([person()], [], BASE + timedelta(seconds=1)) == []
