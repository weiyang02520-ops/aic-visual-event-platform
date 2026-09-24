from visual_event_ai.privacy import sanitize_sensitive_payload


def test_privacy_sanitizer_redacts_nested_pixel_channels_but_keeps_algorithm_metadata():
    payload = {
        "rawPixels": [[1, 2], [3, 4]],
        "sensor": {
            "Thermal-Map": [[5, 6]],
            "pose": {"keypoints": [[10, 20, 0.9]]},
            "label": "person",
        },
    }

    sanitized = sanitize_sensitive_payload(payload)

    assert sanitized["rawPixels"] == {
        "encoding": "redacted-pixels",
        "shape": [2, 2],
    }
    assert sanitized["sensor"]["Thermal-Map"] == {
        "encoding": "redacted-thermal",
        "shape": [1, 2],
    }
    assert sanitized["sensor"]["pose"]["keypoints"] == [[10, 20, 0.9]]
    assert sanitized["sensor"]["label"] == "person"

