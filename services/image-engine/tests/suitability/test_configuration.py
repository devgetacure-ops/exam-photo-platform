import pytest
from pydantic import ValidationError

from exam_photo.suitability.configuration import SuitabilityThresholds


def test_valid_default_configuration() -> None:
    config = SuitabilityThresholds()
    assert config.minimum_source_width == 300
    assert config.minimum_source_height == 300


def test_invalid_negative_thresholds() -> None:
    with pytest.raises(ValidationError):
        SuitabilityThresholds(minimum_source_width=-10)

    with pytest.raises(ValidationError):
        SuitabilityThresholds(blur_warning_threshold=-1.0)


def test_invalid_order_thresholds() -> None:
    with pytest.raises(
        ValidationError, match="blur_blocking_threshold cannot be higher"
    ):
        SuitabilityThresholds(
            blur_warning_threshold=5.0,
            blur_blocking_threshold=10.0,  # blocking softer/higher than warning
        )

    with pytest.raises(
        ValidationError,
        match="mean_luminance_blocking_low must be less than or equal to warning_low",
    ):
        SuitabilityThresholds(
            mean_luminance_warning_low=50.0,
            mean_luminance_blocking_low=60.0,
        )


def test_invalid_pose_thresholds() -> None:
    with pytest.raises(ValidationError, match="pose_blocking_yaw must be >= warning"):
        SuitabilityThresholds(
            pose_warning_yaw=20.0,
            pose_blocking_yaw=10.0,
        )


def test_serialization() -> None:
    config = SuitabilityThresholds()
    dump = config.model_dump()
    assert dump["minimum_source_width"] == 300
    restored = SuitabilityThresholds(**dump)
    assert restored.minimum_source_width == 300
