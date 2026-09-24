import json

import pytest

from visual_event_ai.relations import Zone
from visual_event_ai.zone_config import parse_zones_json


def test_zone_config_defaults_to_no_regions_and_parses_pixel_rectangles():
    assert parse_zones_json(None) == ()
    assert parse_zones_json("[]") == ()

    zones = parse_zones_json(
        json.dumps(
            [
                {
                    "zone_id": "shelf-a",
                    "label": "工具架 A",
                    "x": 0,
                    "y": 0,
                    "width": 20,
                    "height": 20,
                }
            ],
            ensure_ascii=False,
        )
    )
    assert zones == (Zone("shelf-a", "工具架 A", 0.0, 0.0, 20.0, 20.0),)


@pytest.mark.parametrize(
    "value",
    [
        "not-json",
        '{"zone_id":"shelf-a"}',
        '[{"zone_id":"shelf-a","label":"shelf","x":0,"y":0,"width":0,"height":10}]',
        '[{"zone_id":"shelf-a","label":"shelf","x":0,"y":0,"width":10,"height":10,"widht":2}]',
        '[{"zone_id":"shelf-a","label":"shelf","x":0,"y":0,"width":10,"height":10},{"zone_id":" shelf-a ","label":"other","x":0,"y":0,"width":10,"height":10}]',
        '[{"zone_id":"shelf-a","label":"shelf","x":NaN,"y":0,"width":10,"height":10}]',
        '[{"zone_id":"overflow","label":"shelf","x":1e308,"y":0,"width":1e308,"height":10}]',
    ],
)
def test_zone_config_rejects_malformed_or_ambiguous_regions(value):
    with pytest.raises(ValueError):
        parse_zones_json(value)


def test_zone_config_rejects_unrepresentable_integer_coordinates():
    encoded = json.dumps(
        [
            {
                "zone_id": "shelf-a",
                "label": "工具架 A",
                "x": 10**1000,
                "y": 0,
                "width": 10,
                "height": 10,
            }
        ]
    )

    with pytest.raises(ValueError):
        parse_zones_json(encoded)
