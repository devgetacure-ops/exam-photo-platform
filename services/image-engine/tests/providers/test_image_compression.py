import io

import pytest
from PIL import Image
from pydantic import ValidationError

from exam_photo.providers.compression.deterministic_image_compressor import (
    DeterministicJpegCompressor,
)
from exam_photo.providers.output_compression import (
    CompressionFormat,
    OutputCompressionConfig,
    OutputCompressionIssueCode,
)

pytestmark = pytest.mark.mandatory_output_compression


def test_config_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        OutputCompressionConfig(
            maximum_bytes=50000,
            unknown_field="hello",  # type: ignore[call-arg]
        )


def test_config_validation_rules() -> None:
    # maximum_bytes required and positive
    with pytest.raises(ValidationError):
        OutputCompressionConfig(maximum_bytes=0)

    with pytest.raises(ValidationError):
        OutputCompressionConfig(maximum_bytes=-100)

    # minimum_bytes must be non-negative
    with pytest.raises(ValidationError):
        OutputCompressionConfig(maximum_bytes=1000, minimum_bytes=-1)

    # minimum_bytes <= maximum_bytes
    with pytest.raises(ValidationError):
        OutputCompressionConfig(maximum_bytes=1000, minimum_bytes=1001)

    # target_ceiling_ratio range (0, 1]
    with pytest.raises(ValidationError):
        OutputCompressionConfig(maximum_bytes=1000, target_ceiling_ratio=0.0)

    with pytest.raises(ValidationError):
        OutputCompressionConfig(maximum_bytes=1000, target_ceiling_ratio=1.01)

    # safety_margin_bytes range [0, maximum_bytes)
    with pytest.raises(ValidationError):
        OutputCompressionConfig(maximum_bytes=1000, safety_margin_bytes=-1)

    with pytest.raises(ValidationError):
        OutputCompressionConfig(maximum_bytes=1000, safety_margin_bytes=1000)

    # quality ranges
    with pytest.raises(ValidationError):
        OutputCompressionConfig(maximum_bytes=1000, min_quality=100, max_quality=50)

    with pytest.raises(ValidationError):
        OutputCompressionConfig(maximum_bytes=1000, min_quality=0, max_quality=90)

    with pytest.raises(ValidationError):
        OutputCompressionConfig(maximum_bytes=1000, min_quality=30, max_quality=101)

    # initial_quality inside bounds
    with pytest.raises(ValidationError):
        OutputCompressionConfig(
            maximum_bytes=1000,
            min_quality=30,
            max_quality=80,
            initial_quality=90,
        )


def test_unsupported_format() -> None:
    img = Image.new("RGB", (300, 400), color="blue")
    preparer = DeterministicJpegCompressor()

    # Create config with unsupported format (using mock/forcing since type check prohibits it)
    class FakeConfig(OutputCompressionConfig):
        target_format: CompressionFormat = "png"  # type: ignore

    config = FakeConfig(maximum_bytes=50000)
    result = preparer.compress_output(img, config)

    assert not result.validation.is_valid
    assert (
        OutputCompressionIssueCode.COMPRESSION_FORMAT_UNSUPPORTED
        in result.validation.issue_codes
    )


def test_jpeg_compression_rgb_input() -> None:
    img = Image.new("RGB", (300, 400), color="blue")
    config = OutputCompressionConfig(
        maximum_bytes=50000,
        minimum_bytes=5000,
    )
    preparer = DeterministicJpegCompressor()
    result = preparer.compress_output(img, config)

    assert result.validation.is_valid
    assert result.target_format == CompressionFormat.JPEG
    assert result.encoded_bytes is not None
    assert len(result.encoded_bytes) == result.actual_bytes
    assert result.actual_bytes <= result.target_bytes
    assert result.final_quality is not None
    assert result.min_quality <= result.final_quality <= result.max_quality or (
        result.full_quality_encoding and result.final_quality == 100
    )


def test_jpeg_compression_rgba_input() -> None:
    # Create RGBA image with transparent pixels
    img = Image.new("RGBA", (300, 400), color=(0, 0, 255, 128))
    config = OutputCompressionConfig(maximum_bytes=50000)
    preparer = DeterministicJpegCompressor()
    result = preparer.compress_output(img, config)

    assert result.validation.is_valid
    # The output candidate must decode successfully and have RGB mode
    assert result.validation.decode_after_encode_valid
    assert result.encoded_bytes is not None
    decoded = Image.open(io.BytesIO(result.encoded_bytes))
    assert decoded.mode == "RGB"


def test_input_image_not_mutated() -> None:
    img = Image.new("RGBA", (300, 400), color="blue")
    original_mode = img.mode

    config = OutputCompressionConfig(maximum_bytes=50000)
    preparer = DeterministicJpegCompressor()
    preparer.compress_output(img, config)

    assert img.mode == original_mode


def test_metadata_stripped() -> None:
    img = Image.new("RGB", (300, 400), color="blue")
    img.info["exif"] = b"fake exif data data data"

    config = OutputCompressionConfig(maximum_bytes=50000, strip_metadata=True)
    preparer = DeterministicJpegCompressor()
    result = preparer.compress_output(img, config)

    assert result.validation.is_valid
    assert result.metadata_stripped is True

    # Decode and verify no exif
    assert result.encoded_bytes is not None
    decoded = Image.open(io.BytesIO(result.encoded_bytes))
    assert "exif" not in decoded.info


def test_jpeg_compression_writes_target_dpi_without_exif() -> None:
    img = Image.new("RGB", (300, 400), color="blue")
    config = OutputCompressionConfig(
        maximum_bytes=50000,
        strip_metadata=True,
        target_dpi=72,
    )
    preparer = DeterministicJpegCompressor()
    result = preparer.compress_output(img, config)

    assert result.validation.is_valid
    assert result.target_dpi == 72
    assert result.actual_dpi == 72
    assert result.validation.dpi_satisfied is True
    assert result.metadata_stripped is True

    assert result.encoded_bytes is not None
    decoded = Image.open(io.BytesIO(result.encoded_bytes))
    assert decoded.info.get("dpi") == (72, 72)
    assert "exif" not in decoded.info


def test_encoded_bytes_excluded_from_serialization() -> None:
    img = Image.new("RGB", (300, 400), color="blue")
    config = OutputCompressionConfig(maximum_bytes=50000)
    preparer = DeterministicJpegCompressor()
    result = preparer.compress_output(img, config)

    # Excluded from dict
    dump_dict = result.model_dump()
    assert "encoded_bytes" not in dump_dict
    actual_bytes = dump_dict.get("actual_bytes")
    assert actual_bytes is not None and actual_bytes > 0

    # Excluded from JSON
    dump_json = result.model_dump_json()
    assert "encoded_bytes" not in dump_json


def test_impossible_byte_ceiling_failure() -> None:
    img = Image.new("RGB", (300, 400), color="blue")
    # Set maximum bytes to an extremely small number (10 bytes)
    config = OutputCompressionConfig(
        maximum_bytes=10,
        safety_margin_bytes=0,
        min_quality=35,
        allow_oversize_output=False,
    )
    preparer = DeterministicJpegCompressor()
    result = preparer.compress_output(img, config)

    assert not result.validation.is_valid
    assert (
        OutputCompressionIssueCode.COMPRESSION_MAX_SIZE_EXCEEDED
        in result.validation.issue_codes
    )


def test_allow_quality_below_minimum() -> None:
    img = Image.new("RGB", (600, 800), color="blue")
    # Make a target size that's very tight, but can fit at quality 15 (below min_quality=35)
    config = OutputCompressionConfig(
        maximum_bytes=12000,
        min_quality=35,
        allow_quality_below_minimum=True,
    )
    preparer = DeterministicJpegCompressor()
    result = preparer.compress_output(img, config)

    # If it fits with quality < 35, it should succeed but flag warning for low quality
    if result.validation.is_valid:
        assert result.final_quality is not None
        if result.final_quality < 35:
            assert (
                OutputCompressionIssueCode.COMPRESSION_QUALITY_TOO_LOW
                in result.validation.issue_codes
            )


def _detailed(width: int, height: int) -> Image.Image:
    """A photograph-like frame: smooth gradients with fine texture, not a flat fill."""
    import random

    rng = random.Random(7)
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    assert pixels is not None
    for y in range(height):
        for x in range(width):
            pixels[x, y] = (
                (x * 255 // width + rng.randint(0, 40)) % 256,
                (y * 255 // height + rng.randint(0, 40)) % 256,
                ((x + y) * 128 // (width + height) + rng.randint(0, 40)) % 256,
            )
    return img


def _sampling(data: bytes) -> int:
    from PIL import JpegImagePlugin

    with Image.open(io.BytesIO(data)) as opened:
        return int(JpegImagePlugin.get_sampling(opened))


def test_full_quality_is_used_when_the_budget_holds_it() -> None:
    img = _detailed(200, 230)
    result = DeterministicJpegCompressor().compress_output(
        img, OutputCompressionConfig(maximum_bytes=200_000)
    )
    assert result.validation.is_valid
    assert result.full_quality_encoding is True
    assert result.final_quality == 100
    assert result.encoded_bytes is not None
    assert _sampling(result.encoded_bytes) == 0  # 4:4:4, no chroma subsampling
    assert result.actual_bytes <= result.target_bytes


def test_full_quality_is_skipped_when_it_would_break_the_ceiling() -> None:
    img = _detailed(200, 230)
    searched = DeterministicJpegCompressor().compress_output(
        img,
        OutputCompressionConfig(maximum_bytes=200_000, full_quality_when_it_fits=False),
    )
    ceiling = searched.actual_bytes + 2000  # room for the search, not for quality 100
    result = DeterministicJpegCompressor().compress_output(
        img, OutputCompressionConfig(maximum_bytes=ceiling)
    )
    assert result.validation.is_valid
    assert result.full_quality_encoding is False
    assert result.final_quality is not None and result.final_quality <= 98
    assert result.actual_bytes <= result.target_bytes


def test_full_quality_lifts_a_small_photo_over_its_floor() -> None:
    img = _detailed(200, 230)
    plain = DeterministicJpegCompressor().compress_output(
        img,
        OutputCompressionConfig(maximum_bytes=200_000, full_quality_when_it_fits=False),
    )
    lifted = DeterministicJpegCompressor().compress_output(
        img, OutputCompressionConfig(maximum_bytes=200_000)
    )
    floor = plain.actual_bytes + 1  # unreachable at the searched quality
    assert lifted.actual_bytes >= floor
