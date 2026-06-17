import pytest
from tests.helpers.synthetic_images import create_solid_image, save_image_to_bytes

from exam_photo.input.errors import ImageInspectionError, InputErrorCode
from exam_photo.input.limits import InputLimits
from exam_photo.input.normalization import normalize_image_input
from exam_photo.input.signatures import detect_signature_format


def test_signature_detection() -> None:
    png_data = save_image_to_bytes(create_solid_image("RGB"), "PNG")
    jpeg_data = save_image_to_bytes(create_solid_image("RGB"), "JPEG")

    assert detect_signature_format(png_data) == "png"
    assert detect_signature_format(jpeg_data) == "jpeg"
    assert detect_signature_format(b"not-an-image") is None


def test_signature_extension_mismatch() -> None:
    jpeg_data = save_image_to_bytes(create_solid_image("RGB"), "JPEG")
    limits_warn = InputLimits(extension_mismatch_policy="warn")

    # jpg file with png extension
    result = normalize_image_input(jpeg_data, "photo.png", limits_warn)
    assert result.metadata.extension_mismatch is True

    # png data with jpg extension and strict policy
    limits_strict = InputLimits(extension_mismatch_policy="reject")
    with pytest.raises(ImageInspectionError) as exc_info:
        normalize_image_input(jpeg_data, "photo.png", limits_strict)
    assert exc_info.value.code == InputErrorCode.INPUT_SIGNATURE_CONFLICT
