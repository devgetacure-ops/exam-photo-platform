from tests.helpers.synthetic_images import create_rotated_exif_jpeg

from exam_photo.input.limits import InputLimits
from exam_photo.input.normalization import normalize_image_input


def test_orientation_normalization() -> None:
    # Orientation 6: Rotated 90 degrees CW.
    # Exif transpose will rotate 90 CCW to correct.
    jpeg_data = create_rotated_exif_jpeg(6, (200, 100))
    result = normalize_image_input(jpeg_data, "photo.jpg", InputLimits())

    assert result.metadata.orientation_tag_present is True
    assert result.metadata.orientation_applied is True
    assert result.metadata.orientation_operation == "transpose_6"
    assert result.metadata.normalized_width == 100
    assert result.metadata.normalized_height == 200


def test_orientation_180_degrees() -> None:
    # Orientation 3: 180 degrees.
    jpeg_data = create_rotated_exif_jpeg(3, (200, 100))
    result = normalize_image_input(jpeg_data, "photo.jpg", InputLimits())
    assert result.metadata.orientation_tag_present is True
    assert result.metadata.orientation_applied is True
    assert result.metadata.orientation_operation == "transpose_3"
    assert result.metadata.normalized_width == 200
    assert result.metadata.normalized_height == 100


def test_orientation_270_degrees() -> None:
    # Orientation 8: 270 degrees.
    jpeg_data = create_rotated_exif_jpeg(8, (200, 100))
    result = normalize_image_input(jpeg_data, "photo.jpg", InputLimits())
    assert result.metadata.orientation_tag_present is True
    assert result.metadata.orientation_applied is True
    assert result.metadata.orientation_operation == "transpose_8"
    assert result.metadata.normalized_width == 100
    assert result.metadata.normalized_height == 200


def test_orientation_horizontal_flip() -> None:
    # Orientation 2: Horizontal flip.
    jpeg_data = create_rotated_exif_jpeg(2, (200, 100))
    result = normalize_image_input(jpeg_data, "photo.jpg", InputLimits())
    assert result.metadata.orientation_tag_present is True
    assert result.metadata.orientation_applied is True
    assert result.metadata.orientation_operation == "transpose_2"


def test_orientation_normal() -> None:
    # Orientation 1: Normal.
    jpeg_data = create_rotated_exif_jpeg(1, (200, 100))
    result = normalize_image_input(jpeg_data, "photo.jpg", InputLimits())
    assert result.metadata.orientation_tag_present is True
    assert result.metadata.orientation_applied is False
    assert result.metadata.orientation_operation is None


def test_orientation_invalid_tag() -> None:
    # Orientation 999: Invalid.
    jpeg_data = create_rotated_exif_jpeg(999, (200, 100))
    result = normalize_image_input(jpeg_data, "photo.jpg", InputLimits())
    assert result.metadata.orientation_tag_present is True
    assert result.metadata.orientation_applied is False
    assert result.metadata.orientation_operation is None
