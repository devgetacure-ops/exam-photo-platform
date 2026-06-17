from tests.helpers.synthetic_images import create_solid_image, save_image_to_bytes

from exam_photo.input.limits import InputLimits
from exam_photo.input.normalization import normalize_image_input


def test_rgb_converted_to_rgba() -> None:
    rgb_data = save_image_to_bytes(create_solid_image("RGB"), "PNG")
    result = normalize_image_input(rgb_data, "photo.png", InputLimits())

    assert result.metadata.original_mode == "RGB"
    assert result.metadata.normalized_mode == "RGBA"
    assert result.metadata.alpha_present is False


def test_rgba_preserves_alpha() -> None:
    rgba_data = save_image_to_bytes(create_solid_image("RGBA"), "PNG")
    result = normalize_image_input(rgba_data, "photo.png", InputLimits())

    assert result.metadata.original_mode == "RGBA"
    assert result.metadata.normalized_mode == "RGBA"
    assert result.metadata.alpha_present is True


def test_grayscale_converted_safely() -> None:
    gray_data = save_image_to_bytes(create_solid_image("L"), "PNG")
    result = normalize_image_input(gray_data, "photo.png", InputLimits())

    assert result.metadata.original_mode == "L"
    assert result.metadata.normalized_mode == "RGBA"
