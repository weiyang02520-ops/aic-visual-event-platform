import pytest

from visual_event_ai.quality import QualityContractError, evaluate_channel_quality


def test_quality_gate_is_ungated_when_metadata_is_absent():
    decision = evaluate_channel_quality({"provider": "fixture"})

    assert decision.gated is False
    assert decision.allow_inference is True
    assert decision.degraded is False
    assert decision.summary()["channels"] == []


def test_quality_gate_allows_with_one_usable_channel_but_marks_degraded():
    decision = evaluate_channel_quality(
        {
            "channel_quality": {
                "RGB": {"available": True, "score": 0.92},
                "thermal-map": {"available": True, "score": 0.2, "reason": "occluded"},
            }
        }
    )

    assert decision.allow_inference is True
    assert decision.degraded is True
    summary = decision.summary()
    assert summary["channels"][0]["channel"] == "rgb"
    assert summary["channels"][1]["usable"] is False
    assert summary["channels"][1]["reason"] == "occluded"


def test_quality_gate_blocks_when_required_channel_is_unusable():
    decision = evaluate_channel_quality(
        {
            "channel_quality": {
                "rgb": {"available": True, "score": 0.9},
                "thermal": {"available": False, "score": 0.0, "reason": "missing"},
            },
            "quality_required_channels": ["thermal"],
        }
    )

    assert decision.allow_inference is False
    assert decision.blocked_reasons == ("required_channel_unusable:thermal",)


@pytest.mark.parametrize(
    "metadata",
    [
        {"channel_quality": {}},
        {"channel_quality": {"rgb": {"available": "yes", "score": 0.9}}},
        {"channel_quality": {"rgb": {"available": True, "score": "0.9"}}},
        {"channel_quality": {"rgb": {"available": True, "score": float("nan")}}},
        {
            "channel_quality": {"rgb": {"available": True, "score": 0.9}},
            "quality_required_channels": "rgb",
        },
        {
            "channel_quality": {"rgb": {"available": True, "score": 0.9}},
            "quality_required_channels": ["thermal"],
        },
    ],
)
def test_quality_gate_rejects_malformed_contract(metadata):
    with pytest.raises(QualityContractError):
        evaluate_channel_quality(metadata)

