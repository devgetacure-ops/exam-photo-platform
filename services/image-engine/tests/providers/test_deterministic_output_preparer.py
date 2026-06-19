import pytest
from PIL import Image

from exam_photo.providers.output_preparation import (
    EnhancementMode,
    OutputPreparationConfig,
    OutputPreparationIssueCode,
    ResizeMode,
)
from exam_photo.providers.output_preparers.deterministic_output_preparer import (
    DeterministicOutputPreparer,
)

pytestmark = pytest.mark.mandatory_output_preparation


def test_exact_resize_success():
    img = Image.new("RGB", (600, 800), color="blue")
    config = OutputPreparationConfig(
        resize_mode=ResizeMode.EXACT,
        target_width=300,
        target_height=400,
    )
    preparer = DeterministicOutputPreparer()
    result = preparer.prepare_output(img, config)

    assert result.validation.is_valid
    assert result.output_width == 300
    assert result.output_height == 400
    assert result.output_image is not None
    assert result.output_image.size == (300, 400)
    assert "output_image" not in result.model_dump()
    assert "output_image" not in result.model_dump_json()


def test_exact_aspect_mismatch():
    img = Image.new("RGB", (600, 800), color="blue")  # aspect = 0.75
    config = OutputPreparationConfig(
        resize_mode=ResizeMode.EXACT,
        target_width=300,
        target_height=300,  # aspect = 1.0
    )
    preparer = DeterministicOutputPreparer()
    result = preparer.prepare_output(img, config)

    assert not result.validation.is_valid
    assert (
        OutputPreparationIssueCode.OUTPUT_ASPECT_MISMATCH
        in result.validation.issue_codes
    )


def test_upscale_warning_thresholds():
    preparer = DeterministicOutputPreparer()

    # 1. scale <= 1.5 (normal)
    img_normal = Image.new("RGB", (200, 200), color="blue")
    res_normal = preparer.prepare_output(
        img_normal,
        OutputPreparationConfig(
            resize_mode=ResizeMode.EXACT, target_width=300, target_height=300
        ),
    )
    assert res_normal.validation.is_valid
    assert len(res_normal.validation.issue_codes) == 0

    # 2. 1.5 < scale <= 2.0 (upscale warning)
    img_warning = Image.new("RGB", (200, 200), color="blue")
    res_warning = preparer.prepare_output(
        img_warning,
        OutputPreparationConfig(
            resize_mode=ResizeMode.EXACT, target_width=360, target_height=360
        ),
    )
    assert res_warning.validation.is_valid
    assert (
        OutputPreparationIssueCode.OUTPUT_UPSCALE_WARNING
        in res_warning.validation.issue_codes
    )

    # 3. 2.0 < scale <= 3.0 (strong warning)
    img_strong = Image.new("RGB", (200, 200), color="blue")
    res_strong = preparer.prepare_output(
        img_strong,
        OutputPreparationConfig(
            resize_mode=ResizeMode.EXACT, target_width=500, target_height=500
        ),
    )
    assert res_strong.validation.is_valid
    assert (
        OutputPreparationIssueCode.OUTPUT_UPSCALE_STRONG_WARNING
        in res_strong.validation.issue_codes
    )

    # 4. scale > 3.0 (limit exceeded / error)
    img_error = Image.new("RGB", (200, 200), color="blue")
    res_error = preparer.prepare_output(
        img_error,
        OutputPreparationConfig(
            resize_mode=ResizeMode.EXACT, target_width=700, target_height=700
        ),
    )
    assert not res_error.validation.is_valid
    assert (
        OutputPreparationIssueCode.OUTPUT_UPSCALE_LIMIT_EXCEEDED
        in res_error.validation.issue_codes
    )


def test_downscale_warning_thresholds():
    preparer = DeterministicOutputPreparer()

    # 1. scale >= 0.20 (normal)
    img_normal = Image.new("RGB", (1000, 1000), color="blue")
    res_normal = preparer.prepare_output(
        img_normal,
        OutputPreparationConfig(
            resize_mode=ResizeMode.EXACT, target_width=250, target_height=250
        ),
    )
    assert res_normal.validation.is_valid
    assert len(res_normal.validation.issue_codes) == 0

    # 2. 0.10 <= scale < 0.20 (downscale warning)
    img_warning = Image.new("RGB", (1000, 1000), color="blue")
    res_warning = preparer.prepare_output(
        img_warning,
        OutputPreparationConfig(
            resize_mode=ResizeMode.EXACT, target_width=150, target_height=150
        ),
    )
    assert res_warning.validation.is_valid
    assert (
        OutputPreparationIssueCode.OUTPUT_DOWNSCALE_WARNING
        in res_warning.validation.issue_codes
    )

    # 3. 0.05 <= scale < 0.10 (severe warning)
    img_severe = Image.new("RGB", (1000, 1000), color="blue")
    res_severe = preparer.prepare_output(
        img_severe,
        OutputPreparationConfig(
            resize_mode=ResizeMode.EXACT, target_width=80, target_height=80
        ),
    )
    assert res_severe.validation.is_valid
    assert (
        OutputPreparationIssueCode.OUTPUT_DOWNSCALE_SEVERE_WARNING
        in res_severe.validation.issue_codes
    )

    # 4. scale < 0.05 (too severe / error)
    img_error = Image.new("RGB", (1000, 1000), color="blue")
    res_error = preparer.prepare_output(
        img_error,
        OutputPreparationConfig(
            resize_mode=ResizeMode.EXACT, target_width=40, target_height=40
        ),
    )
    assert not res_error.validation.is_valid
    assert (
        OutputPreparationIssueCode.OUTPUT_DOWNSCALE_TOO_SEVERE
        in res_error.validation.issue_codes
    )


def test_range_select_priority_1():
    # Preferred width/height supplied and aspect ratio matches source aspect ratio exactly
    img = Image.new("RGB", (600, 800), color="blue")  # aspect = 0.75
    config = OutputPreparationConfig(
        resize_mode=ResizeMode.RANGE_SELECT,
        min_width=200,
        max_width=400,
        min_height=200,
        max_height=600,
        preferred_width=300,
        preferred_height=400,  # matches 0.75
    )
    preparer = DeterministicOutputPreparer()
    result = preparer.prepare_output(img, config)

    assert result.validation.is_valid
    assert result.output_width == 300
    assert result.output_height == 400


def test_range_select_priority_2():
    # Preferred width/height supplied but aspect mismatch, choose largest aspect-preserving
    img = Image.new("RGB", (600, 800), color="blue")  # aspect = 0.75
    config = OutputPreparationConfig(
        resize_mode=ResizeMode.RANGE_SELECT,
        min_width=200,
        max_width=400,
        min_height=200,
        max_height=600,
        preferred_width=300,
        preferred_height=300,  # aspect = 1.0 (mismatch)
    )
    preparer = DeterministicOutputPreparer()
    result = preparer.prepare_output(img, config)

    assert result.validation.is_valid
    # Largest aspect-preserving size inside range:
    # If w=400, h = 400 / 0.75 = 533 (valid because 533 is in [200, 600])
    # If h=600, w = 600 * 0.75 = 450 (invalid because 450 > 400)
    # So we should choose (400, 533)
    assert result.output_width == 400
    assert result.output_height == 533


def test_range_select_priority_3():
    # Aspect ratio cannot be preserved in range, fallback to clamped closest valid and fail
    img = Image.new("RGB", (100, 800), color="blue")  # aspect = 0.125 (very tall)
    config = OutputPreparationConfig(
        resize_mode=ResizeMode.RANGE_SELECT,
        min_width=300,
        max_width=400,
        min_height=300,
        max_height=400,
        preferred_width=350,
        preferred_height=350,
    )
    preparer = DeterministicOutputPreparer()
    result = preparer.prepare_output(img, config)

    assert not result.validation.is_valid
    assert (
        OutputPreparationIssueCode.OUTPUT_ASPECT_MISMATCH
        in result.validation.issue_codes
    )
    assert result.output_width == 350
    assert result.output_height == 350


def test_enhancement_safety():
    img = Image.new("RGB", (300, 400), color="blue")

    # Mode is NONE, but adjustments are not 1.0
    config_none_invalid = OutputPreparationConfig(
        resize_mode=ResizeMode.EXACT,
        target_width=300,
        target_height=400,
        enhancement_mode=EnhancementMode.NONE,
        brightness_adjustment=1.05,
    )
    preparer = DeterministicOutputPreparer()
    res_none_invalid = preparer.prepare_output(img, config_none_invalid)
    assert not res_none_invalid.validation.is_valid
    assert (
        OutputPreparationIssueCode.OUTPUT_ENHANCEMENT_UNSAFE
        in res_none_invalid.validation.issue_codes
    )

    # Mode is CONSERVATIVE, within limits
    config_cons_valid = OutputPreparationConfig(
        resize_mode=ResizeMode.EXACT,
        target_width=300,
        target_height=400,
        enhancement_mode=EnhancementMode.CONSERVATIVE,
        brightness_adjustment=1.05,
        contrast_adjustment=0.95,
        sharpness_adjustment=1.1,
    )
    res_cons_valid = preparer.prepare_output(img, config_cons_valid)
    assert res_cons_valid.validation.is_valid
    assert res_cons_valid.brightness_adjustment == 1.05

    # Mode is CONSERVATIVE, outside limits
    config_cons_invalid = OutputPreparationConfig(
        resize_mode=ResizeMode.EXACT,
        target_width=300,
        target_height=400,
        enhancement_mode=EnhancementMode.CONSERVATIVE,
        brightness_adjustment=1.15,  # limit is 1.12
    )
    res_cons_invalid = preparer.prepare_output(img, config_cons_invalid)
    assert not res_cons_invalid.validation.is_valid
    assert (
        OutputPreparationIssueCode.OUTPUT_ENHANCEMENT_UNSAFE
        in res_cons_invalid.validation.issue_codes
    )


def test_strip_metadata():
    img = Image.new("RGB", (600, 800), color="blue")
    img.info["test"] = "data"

    config = OutputPreparationConfig(
        resize_mode=ResizeMode.EXACT,
        target_width=300,
        target_height=400,
        strip_metadata=True,
    )
    preparer = DeterministicOutputPreparer()
    result = preparer.prepare_output(img, config)

    assert result.validation.is_valid
    assert result.metadata_stripped is True
    assert "test" not in result.output_image.info


def test_colour_mode_conversion():
    img = Image.new("RGBA", (600, 800), color="blue")
    config = OutputPreparationConfig(
        resize_mode=ResizeMode.EXACT,
        target_width=300,
        target_height=400,
        output_colour_mode="RGB",
    )
    preparer = DeterministicOutputPreparer()
    result = preparer.prepare_output(img, config)

    assert result.validation.is_valid
    assert result.output_colour_mode == "RGB"
    assert result.output_image.mode == "RGB"
