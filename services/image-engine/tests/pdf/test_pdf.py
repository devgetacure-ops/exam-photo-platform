"""PDF deliverables: assembling them, and preparing ones the candidate has.

The line these tests defend is the one between a *scan* and a *document*. A
scan is a photograph in a PDF wrapper and may be re-encoded and reduced like
any photograph. A digitally issued certificate holds real text, and turning
that into a picture to hit a byte ceiling destroys what makes it verifiable
while looking, from the file size alone, like a success.

Every fixture is synthesised. Real certificates are personal documents and are
never committed.
"""

import io
from typing import Any

import numpy as np
import pytest
from PIL import Image, ImageDraw
from pypdf import PdfReader, PdfWriter

from exam_photo.input.errors import ImageInspectionError
from exam_photo.pdf import (
    PdfPageKind,
    build_pdf_from_images,
    inspect_pdf,
    prepare_existing_pdf,
)


def _scan_page(width: int = 1700, height: int = 2340) -> Image.Image:
    """A photograph of a printed page: detail everywhere, no text objects."""
    rng = np.random.default_rng(7)
    pixels = np.full((height, width, 3), 246.0, dtype=np.float32)
    for index in range(28):
        y = 120 + index * 76
        pixels[y : y + 9, 130 : width - 160, :] = 44.0
    # Paper grain, which is what makes a scan expensive to store.
    pixels += rng.normal(0.0, 7.0, size=pixels.shape).astype(np.float32)
    return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))


def _scanned_pdf(pages: int = 1, size: tuple[int, int] = (1700, 2340)) -> bytes:
    images = [_scan_page(*size) for _ in range(pages)]
    buffer = io.BytesIO()
    images[0].save(
        buffer, "PDF", save_all=True, append_images=images[1:], resolution=200.0
    )
    return buffer.getvalue()


def _digital_pdf(with_seal: bool = True) -> bytes:
    """A PDF whose words are text objects, not pixels.

    This is what a digitally issued certificate looks like structurally: real
    text drawn from a font, plus a small inset image for the seal. The
    classifier has to call it a document despite the image being there, because
    "contains an image" is true of nearly every generated certificate.
    """
    from pypdf.generic import (
        ArrayObject,
        DecodedStreamObject,
        DictionaryObject,
        NameObject,
        NumberObject,
    )

    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    page = writer.pages[0]

    lines = [
        "BOARD OF SECONDARY EDUCATION",
        "This is to certify that the candidate named below has passed",
        "the examination held in the year two thousand and twenty six",
        "with the subjects and marks recorded on this statement.",
    ]
    body = ["BT", "/F1 13 Tf"]
    for index, line in enumerate(lines):
        body.append(f"1 0 0 1 48 {780 - index * 26} Tm ({line}) Tj")
    body.append("ET")

    stream = DecodedStreamObject()
    stream.set_data("\n".join(body).encode("latin-1"))
    page[NameObject("/Contents")] = writer._add_object(stream)

    font = DictionaryObject()
    font[NameObject("/Type")] = NameObject("/Font")
    font[NameObject("/Subtype")] = NameObject("/Type1")
    font[NameObject("/BaseFont")] = NameObject("/Helvetica")
    fonts = DictionaryObject()
    fonts[NameObject("/F1")] = writer._add_object(font)
    resources = DictionaryObject()
    resources[NameObject("/Font")] = fonts
    page[NameObject("/Resources")] = resources
    page[NameObject("/MediaBox")] = ArrayObject(
        [NumberObject(0), NumberObject(0), NumberObject(595), NumberObject(842)]
    )

    if with_seal:
        # Merged last, so pypdf concatenates the content streams itself rather
        # than the fixture hand-building a contents array.
        seal = Image.new("RGB", (80, 80), "white")
        ImageDraw.Draw(seal).ellipse((5, 5, 75, 75), outline="black", width=4)
        buffer = io.BytesIO()
        seal.save(buffer, "PDF", resolution=72.0)
        page.merge_page(PdfReader(io.BytesIO(buffer.getvalue())).pages[0])

    final = io.BytesIO()
    writer.write(final)
    return final.getvalue()


# --- Building a PDF from pages the platform prepared ------------------------


def test_pages_become_a_pdf() -> None:
    result = build_pdf_from_images([_scan_page(800, 1100)])
    assert result.content.startswith(b"%PDF-")
    assert result.page_count == 1
    assert inspect_pdf(result.content).page_count == 1


def test_several_pages_become_one_document() -> None:
    pages = [_scan_page(800, 1100) for _ in range(3)]
    result = build_pdf_from_images(pages)
    assert result.page_count == 3
    assert inspect_pdf(result.content).page_count == 3


def test_assembly_lands_under_the_ceiling() -> None:
    result = build_pdf_from_images([_scan_page()], maximum_bytes=150_000)
    assert result.byte_size <= 150_000
    assert not result.exceeds_ceiling


def test_assembly_gives_up_quality_before_resolution() -> None:
    """A soft full-size page stays readable; a sharp shrunken one may not."""
    result = build_pdf_from_images([_scan_page()], maximum_bytes=260_000)
    assert not result.exceeds_ceiling
    assert result.scale == 1.0, "resolution should not be spent while quality remains"
    assert result.quality < 95


def test_an_impossible_ceiling_still_returns_a_document() -> None:
    """A file slightly too large is something a candidate can act on."""
    result = build_pdf_from_images([_scan_page()], maximum_bytes=1200)
    assert result.exceeds_ceiling
    assert result.content.startswith(b"%PDF-")
    assert any("delivered anyway" in finding for finding in result.findings)


def test_assembly_writes_no_producer_metadata() -> None:
    result = build_pdf_from_images([_scan_page(600, 800)])
    reader = PdfReader(io.BytesIO(result.content))
    metadata = reader.metadata or {}
    assert not (metadata.get("/Producer") or "").strip()
    assert not (metadata.get("/Creator") or "").strip()


# --- Reading what the candidate uploaded ------------------------------------


def test_a_scan_is_recognised_as_a_scan() -> None:
    inspection = inspect_pdf(_scanned_pdf())
    assert inspection.page_kinds == [PdfPageKind.SCANNED]
    assert inspection.is_wholly_scanned


def test_a_text_document_is_not_treated_as_a_scan() -> None:
    """The classification that protects a digitally issued certificate."""
    inspection = inspect_pdf(_digital_pdf())
    assert not inspection.is_wholly_scanned
    assert inspection.has_digital_pages


def test_page_count_and_sizes_are_reported() -> None:
    inspection = inspect_pdf(_scanned_pdf(pages=3))
    assert inspection.page_count == 3
    assert len(inspection.page_sizes) == 3
    assert all(width > 0 and height > 0 for width, height in inspection.page_sizes)


def test_a_damaged_file_fails_clearly() -> None:
    with pytest.raises(ImageInspectionError):
        inspect_pdf(b"%PDF-1.4 this is not really a pdf")


# --- Preparing what the candidate uploaded ----------------------------------


def test_metadata_is_stripped() -> None:
    source = _scanned_pdf()
    writer = PdfWriter(clone_from=io.BytesIO(source))
    writer.add_metadata({"/Author": "Somebody", "/Producer": "SomeScannerApp 4.2"})
    stamped = io.BytesIO()
    writer.write(stamped)

    result = prepare_existing_pdf(stamped.getvalue())
    metadata = PdfReader(io.BytesIO(result.content)).metadata or {}
    assert not (metadata.get("/Author") or "").strip()
    assert not (metadata.get("/Producer") or "").strip()
    assert result.metadata_stripped


def test_a_scan_is_reduced_to_meet_the_ceiling() -> None:
    source = _scanned_pdf()
    result = prepare_existing_pdf(source, maximum_bytes=120_000)
    assert result.byte_size <= 120_000
    assert not result.exceeds_ceiling
    assert result.images_recompressed


def test_a_text_document_is_never_rasterised_to_meet_a_ceiling() -> None:
    """The rule this package exists to keep.

    A digitally issued certificate that will not fit is reported as not
    fitting. It is not converted into pictures of its own pages, which would
    satisfy the byte count and destroy the thing being submitted.
    """
    source = _digital_pdf()
    result = prepare_existing_pdf(source, maximum_bytes=200)

    assert not result.images_recompressed, "a text document must not be re-encoded"
    assert result.exceeds_ceiling
    assert any("real text" in finding for finding in result.findings)

    prepared = inspect_pdf(result.content)
    assert prepared.has_digital_pages, "the pages must still be a document"


def test_a_comfortable_ceiling_leaves_the_pages_alone() -> None:
    result = prepare_existing_pdf(_scanned_pdf(), maximum_bytes=50_000_000)
    assert not result.images_recompressed
    assert not result.exceeds_ceiling


def test_a_page_limit_is_reported_and_no_page_is_dropped() -> None:
    """Dropping a page would be deciding which part of a certificate matters."""
    result = prepare_existing_pdf(_scanned_pdf(pages=4), maximum_pages=2)
    assert result.page_count == 4
    assert inspect_pdf(result.content).page_count == 4
    assert any("pages" in finding for finding in result.findings)


def test_the_prepared_document_still_opens() -> None:
    result = prepare_existing_pdf(_scanned_pdf(pages=2), maximum_bytes=100_000)
    reopened = inspect_pdf(result.content)
    assert reopened.page_count == 2
    assert result.content.startswith(b"%PDF-")


def _unused(_: Any) -> None:  # pragma: no cover - keeps Any imported meaningfully
    return None
