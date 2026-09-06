"""The watermarked preview, and the properties it has to keep (DEC-063).

These assert the two things a purchase gate depends on: the preview is not the
finished file, and it is not silently claimed to be watermarked when it is not.
Everything else about it is presentation.
"""

import io

import numpy as np
import pytest
from PIL import Image

from exam_photo.preview import (
    PREVIEW_MEDIA_TYPE,
    PreviewUnavailableError,
    render_watermarked_preview,
)
from exam_photo.preview.watermark import _MIN_PREVIEW_LONG_EDGE, _preview_size


def _photo(width: int, height: int, shade: int = 200, mode: str = "RGB") -> bytes:
    """A plain synthetic file of a given size."""
    image = Image.new(mode, (width, height), (shade, shade, shade))
    buffer = io.BytesIO()
    image.save(buffer, "PNG" if mode == "RGBA" else "JPEG", quality=95)
    return buffer.getvalue()


def _pixels(content: bytes) -> np.ndarray:
    with Image.open(io.BytesIO(content)) as opened:
        return np.asarray(opened.convert("RGB"), dtype=np.int16)


# ----------------------------------------------------------------------
# Reduced resolution
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("width", "height"),
    [(413, 531), (1200, 1600), (900, 400), (200, 230)],
)
def test_the_preview_cannot_meet_the_exams_pixel_specification(width, height):
    """The point of the downscale: a preview is not submittable."""
    preview = render_watermarked_preview(_photo(width, height))

    assert (preview.width, preview.height) != (width, height)
    assert max(preview.width, preview.height) < max(width, height)
    assert preview.is_reduced


def test_the_aspect_ratio_survives_the_downscale():
    """Never distort. A stretched preview misrepresents the file being sold."""
    preview = render_watermarked_preview(_photo(413, 531))

    assert preview.width / preview.height == pytest.approx(413 / 531, abs=0.01)


def test_a_photograph_already_smaller_than_the_floor_is_not_shrunk_further():
    """DEC-063: below the floor the mark is the whole of the gate.

    A candidate cannot judge their own face at a hundred pixels, so the few
    examinations specifying a photograph this small get the preview at the
    finished file's own size and the watermark alone carries it.
    """
    preview = render_watermarked_preview(_photo(150, 190))

    assert (preview.width, preview.height) == (150, 190)
    assert preview.is_reduced is False


def test_the_floor_is_honoured_rather_than_halving_blindly():
    assert _preview_size(200, 230) == (174, _MIN_PREVIEW_LONG_EDGE)
    assert _preview_size(1000, 500) == (500, 250)


# ----------------------------------------------------------------------
# The mark is in the pixels
# ----------------------------------------------------------------------


def test_the_mark_is_burned_into_the_pixels():
    """Not a layer, not an overlay: the pixels themselves differ."""
    source = _photo(600, 800, shade=200)
    preview = render_watermarked_preview(source)

    with Image.open(io.BytesIO(source)) as opened:
        plain = opened.convert("RGB").resize(
            (preview.width, preview.height), Image.LANCZOS
        )

    difference = np.abs(_pixels(preview.content) - np.asarray(plain, dtype=np.int16))
    marked_fraction = float((difference.max(axis=2) > 12).mean())
    assert marked_fraction > 0.05, "the mark barely touched the image"


def test_the_mark_reaches_every_region_of_the_frame():
    """Tiled rather than placed: a corner crop must not remove it."""
    preview = render_watermarked_preview(_photo(600, 800, shade=200))
    pixels = _pixels(preview.content)

    height, width, _ = pixels.shape
    for row in range(2):
        for column in range(2):
            quadrant = pixels[
                row * height // 2 : (row + 1) * height // 2,
                column * width // 2 : (column + 1) * width // 2,
            ]
            spread = int(quadrant.max()) - int(quadrant.min())
            assert spread > 30, f"quadrant ({row}, {column}) carries no mark"


def test_the_preview_carries_no_metadata_from_the_source():
    """A preview leaves the service as pixels only."""
    source_image = Image.new("RGB", (600, 800), (180, 180, 180))
    buffer = io.BytesIO()
    source_image.save(buffer, "JPEG", quality=95, comment=b"candidate name")

    preview = render_watermarked_preview(buffer.getvalue())

    with Image.open(io.BytesIO(preview.content)) as opened:
        assert not opened.getexif()
        assert b"candidate name" not in preview.content


def test_transparency_is_flattened_onto_white_not_left_to_the_browser():
    preview = render_watermarked_preview(_photo(600, 800, mode="RGBA"))

    assert preview.media_type == PREVIEW_MEDIA_TYPE
    with Image.open(io.BytesIO(preview.content)) as opened:
        assert opened.mode == "RGB"


# ----------------------------------------------------------------------
# Refusal, rather than a preview that is not one
# ----------------------------------------------------------------------


def test_a_pdf_gets_no_preview_rather_than_a_pretend_one():
    """The rasteriser this repository deliberately does not carry."""
    with pytest.raises(PreviewUnavailableError):
        render_watermarked_preview(b"%PDF-1.7\n", media_type="application/pdf")


def test_an_undecodable_file_is_refused():
    with pytest.raises(PreviewUnavailableError):
        render_watermarked_preview(b"this is not an image at all")
