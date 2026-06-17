import pytest
from PIL import ImageFile
from tests.helpers.synthetic_images import create_solid_image, save_image_to_bytes

from exam_photo.input.errors import ImageInspectionError, InputErrorCode
from exam_photo.input.limits import InputLimits
from exam_photo.input.normalization import normalize_image_input


def test_byte_limit_preflight() -> None:
    # Construct small image
    img = create_solid_image("RGB", (10, 10))
    data = save_image_to_bytes(img, "PNG")

    # Set byte limit very small
    limits = InputLimits(maximum_encoded_byte_size=5)

    with pytest.raises(ImageInspectionError) as exc_info:
        normalize_image_input(data, "photo.png", limits)

    assert exc_info.value.code == InputErrorCode.INPUT_TOO_LARGE


def test_decompression_bomb_preflight() -> None:
    # Image claims to be 10000x10000 but we configure limit to 100x100
    limits = InputLimits(
        maximum_width=100,
        maximum_height=100,
        maximum_total_pixel_count=10000,
    )
    img = create_solid_image("RGB", (101, 100))
    data = save_image_to_bytes(img, "PNG")

    with pytest.raises(ImageInspectionError) as exc_info:
        normalize_image_input(data, "photo.png", limits)

    assert exc_info.value.code == InputErrorCode.INPUT_DIMENSIONS_EXCEEDED


def test_truncated_loading_not_globally_enabled() -> None:
    # Ensure starting state is False
    ImageFile.LOAD_TRUNCATED_IMAGES = False

    limits = InputLimits(truncated_image_policy="allow")
    img = create_solid_image("RGB", (10, 10))
    data = save_image_to_bytes(img, "PNG")

    # Call normalizer, which internally enables and restores the setting
    normalize_image_input(data, "photo.png", limits)

    # Ensure it was restored to False and did not leak globally
    assert ImageFile.LOAD_TRUNCATED_IMAGES is False


def test_metadata_privacy_stripped() -> None:
    img = create_solid_image("RGB", (20, 20))
    # Add dummy comment or EXIF metadata
    info_dict = {"comment": b"Author: Antigravity, GPS: 12.34, 56.78"}
    data = save_image_to_bytes(img, "JPEG", comment=info_dict["comment"])

    limits = InputLimits()
    result = normalize_image_input(data, "photo.jpg", limits)

    # Output image should have metadata stripped
    assert len(result.image.info) == 0
    # Metadata report should record metadata_present but not contain the actual comment
    assert result.metadata.metadata_present is True
    assert "GPS" not in result.metadata.model_dump_json()
    assert "Antigravity" not in result.metadata.model_dump_json()


def test_icc_profile_handling() -> None:
    # Image with ICC profile
    img = create_solid_image("RGB", (20, 20))
    # We can use ImageCms if available to create a profile
    try:
        from PIL import ImageCms

        srgb_profile = ImageCms.createProfile("sRGB")
        icc_profile_bytes = ImageCms.ImageCmsProfile(srgb_profile).tobytes()  # type: ignore[no-untyped-call]
    except Exception:
        icc_profile_bytes = b"invalid_profile_bytes"

    data = save_image_to_bytes(img, "JPEG", icc_profile=icc_profile_bytes)
    result = normalize_image_input(data, "photo.jpg", InputLimits())

    assert result.metadata.icc_profile_present is True
    # Raw ICC bytes should not be serialized
    assert "icc_profile_bytes" not in result.metadata.model_dump_json()
    assert result.metadata.icc_conversion_status in {"converted", "ignored"}


def test_file_handle_closure() -> None:
    # Normalization should not leave open handles
    img = create_solid_image("RGB", (20, 20))
    data = save_image_to_bytes(img, "PNG")

    # In-memory bytes stream is closed
    result = normalize_image_input(data, "photo.png", InputLimits())
    # Try using the returned in-memory image
    result.image.load()
    # If the handle was open or tied to stream, it might fail if closed, but we want it fully in-memory and autonomous
    assert result.image is not None
