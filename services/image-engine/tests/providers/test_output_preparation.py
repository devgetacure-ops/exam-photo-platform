import pytest
from pydantic import ValidationError

from exam_photo.providers.output_preparation import (
    OutputPreparationConfig,
    ResizeMode,
)

pytestmark = pytest.mark.mandatory_output_preparation


def test_valid_exact_config():
    config = OutputPreparationConfig(
        resize_mode=ResizeMode.EXACT,
        target_width=300,
        target_height=400,
    )
    assert config.resize_mode == ResizeMode.EXACT
    assert config.target_width == 300
    assert config.target_height == 400


def test_forbid_extra_fields():
    with pytest.raises(ValidationError):
        OutputPreparationConfig(
            resize_mode=ResizeMode.EXACT,
            target_width=300,
            target_height=400,
            unknown_field=123,
        )
