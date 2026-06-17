import pytest
from tests.helpers.synthetic_images import create_solid_image, save_image_to_bytes

from exam_photo.input.errors import ImageInspectionError, InputErrorCode
from exam_photo.input.limits import InputLimits
from exam_photo.input.normalization import normalize_image_input


def test_empty_input_rejected() -> None:
    with pytest.raises(ImageInspectionError) as exc_info:
        normalize_image_input(b"", "photo.jpg", InputLimits())
    assert exc_info.value.code == InputErrorCode.INPUT_EMPTY


def test_byte_limit_enforced() -> None:
    png_data = save_image_to_bytes(create_solid_image("RGB"), "PNG")
    limits = InputLimits(maximum_encoded_byte_size=len(png_data) - 1)

    with pytest.raises(ImageInspectionError) as exc_info:
        normalize_image_input(png_data, "photo.png", limits)
    assert exc_info.value.code == InputErrorCode.INPUT_TOO_LARGE


def test_dimension_limits_enforced() -> None:
    png_data = save_image_to_bytes(create_solid_image("RGB", (100, 100)), "PNG")
    limits_width = InputLimits(maximum_width=90)

    with pytest.raises(ImageInspectionError) as exc_info:
        normalize_image_input(png_data, "photo.png", limits_width)
    assert exc_info.value.code == InputErrorCode.INPUT_DIMENSIONS_EXCEEDED
