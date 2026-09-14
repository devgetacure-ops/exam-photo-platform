"""The watermarked preview, and the properties it has to keep (DEC-063, amended).

A purchase gate depends on two things: the preview is not the finished file,
and it is not claimed to be watermarked when it is not. Since the owner's
testing note B it must also be sharp, and its mark must say what the file is.
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
from exam_photo.preview.watermark import (
    PREVIEW_LONG_EDGE,
    _preview_size,
    watermark_line,
)


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
# Never the file's own size, and sharp
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("width", "height"),
    [(413, 531), (1200, 1600), (900, 400), (200, 230), (140, 60), (800, 600)],
)
def test_the_preview_is_never_the_files_own_pixel_size(width, height):
    """The point of the fixed size: a preview cannot meet a pixel specification."""
    preview = render_watermarked_preview(_photo(width, height))

    assert (preview.width, preview.height) != (width, height)
    assert preview.is_reduced


def test_a_small_file_is_shown_at_a_size_a_phone_screen_keeps_sharp():
    preview = render_watermarked_preview(_photo(200, 230))
    assert max(preview.width, preview.height) == PREVIEW_LONG_EDGE


def test_a_large_file_is_not_shown_at_full_size():
    preview = render_watermarked_preview(_photo(1200, 1600))
    assert max(preview.width, preview.height) == PREVIEW_LONG_EDGE


def test_the_aspect_ratio_survives():
    """Never distort. A stretched preview misrepresents the file being sold."""
    preview = render_watermarked_preview(_photo(413, 531))

    assert preview.width / preview.height == pytest.approx(413 / 531, abs=0.01)


def test_a_file_already_at_the_display_size_still_gets_a_different_size():
    assert max(_preview_size(800, 600)) != 800


# ----------------------------------------------------------------------
# The mark is in the pixels, and it names the file
# ----------------------------------------------------------------------


def test_the_mark_names_the_file_in_ascii():
    line = watermark_line(
        "PREVIEW ONLY - NOT FOR SUBMISSION",
        ["NEET (UG) 2026", "200×230 px", "21 KB", "JPEG", "neet-ug_photo.jpg", ""],
    )
    assert line == (
        "PREVIEW ONLY - NOT FOR SUBMISSION - NEET (UG) 2026 - 200x230 px - "
        "21 KB - JPEG - neet-ug_photo.jpg"
    )
    assert line.isascii()


def test_the_mark_is_burned_into_the_pixels():
    """Not a layer, not an overlay: the pixels themselves differ."""
    source = _photo(600, 800, shade=200)
    preview = render_watermarked_preview(source, details=["Exam", "600x800 px"])

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
    for row in range(3):
        for column in range(3):
            region = pixels[
                row * height // 3 : (row + 1) * height // 3,
                column * width // 3 : (column + 1) * width // 3,
            ]
            spread = int(region.max()) - int(region.min())
            assert spread > 30, f"region ({row}, {column}) carries no mark"


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
# PDFs, and refusals
# ----------------------------------------------------------------------


def _pdf() -> bytes:
    page = Image.new("RGB", (620, 877), (255, 255, 255))
    buffer = io.BytesIO()
    page.save(buffer, "PDF", resolution=72)
    return buffer.getvalue()


def test_a_pdf_gets_a_watermarked_preview_of_its_first_page():
    preview = render_watermarked_preview(
        _pdf(), media_type="application/pdf", details=["certificate.pdf"]
    )
    assert preview.media_type == PREVIEW_MEDIA_TYPE
    assert max(preview.width, preview.height) == PREVIEW_LONG_EDGE
    pixels = _pixels(preview.content)
    assert int(pixels.max()) - int(pixels.min()) > 30, "the page carries no mark"


def test_a_broken_pdf_gets_no_preview_rather_than_a_pretend_one():
    with pytest.raises(PreviewUnavailableError):
        render_watermarked_preview(b"%PDF-1.7\n", media_type="application/pdf")


def test_an_undecodable_file_is_refused():
    with pytest.raises(PreviewUnavailableError):
        render_watermarked_preview(b"this is not an image at all")
