"""Several uploads becoming one document, in the candidate's own order.

A mark sheet has a front and a reverse; a degree comes with a consolidated
statement; an experience letter runs to three sheets. The candidate photographs
them in whatever order they picked them up, sometimes alongside a PDF they
already had. This is the part that lets them fix the order afterwards.

The rule from ``preparation`` carries through and is asserted here: a page that
came from a photograph may be re-encoded to reach a size limit, and a page whose
text is real text never is.
"""

import io

import numpy as np
import pytest
from PIL import Image
from pypdf import PdfReader

from exam_photo.pdf import (
    PageOrigin,
    PageRef,
    assemble_document,
    inspect_pdf,
    plan_document,
)
from tests.pdf.test_pdf import _digital_pdf, _scanned_pdf


def _photo_bytes(width: int = 1300, height: int = 1800, seed: int = 1) -> bytes:
    rng = np.random.default_rng(seed)
    pixels = np.full((height, width, 3), 244.0, dtype=np.float32)
    for index in range(18):
        y = 90 + index * 92
        pixels[y : y + 8, 100 : width - 120, :] = 46.0
    pixels += rng.normal(0.0, 6.0, size=pixels.shape).astype(np.float32)
    buffer = io.BytesIO()
    Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8)).save(
        buffer, "JPEG", quality=92
    )
    return buffer.getvalue()


def _sources() -> list[tuple[bytes, str]]:
    return [
        (_photo_bytes(seed=1), "front.jpg"),
        (_photo_bytes(seed=2), "reverse.jpg"),
        (_scanned_pdf(pages=2), "old-scan.pdf"),
    ]


# --- Planning ---------------------------------------------------------------


def test_uploads_flatten_into_pages() -> None:
    plan = plan_document(_sources())
    assert [page.origin for page in plan.pages] == [
        PageOrigin.PHOTOGRAPH,
        PageOrigin.PHOTOGRAPH,
        PageOrigin.DOCUMENT_SCAN,
        PageOrigin.DOCUMENT_SCAN,
    ]
    assert [page.key for page in plan.pages] == [(0, 0), (1, 0), (2, 0), (2, 1)]


def test_a_damaged_upload_does_not_stop_the_others() -> None:
    """One bad file among five should not cost the candidate the other four."""
    sources = [
        (_photo_bytes(), "good.jpg"),
        (b"not an image at all", "broken.jpg"),
        (_photo_bytes(seed=3), "also-good.jpg"),
    ]
    plan = plan_document(sources)
    assert len(plan.pages) == 2
    assert 1 in plan.unreadable
    assert "broken.jpg" in plan.unreadable[1]


def test_a_text_document_is_planned_as_text() -> None:
    plan = plan_document([(_digital_pdf(), "certificate.pdf")])
    assert [page.origin for page in plan.pages] == [PageOrigin.DOCUMENT_TEXT]


# --- Assembling -------------------------------------------------------------


def test_every_page_arrives_in_one_document() -> None:
    result = assemble_document(_sources())
    assert result.page_count == 4
    assert inspect_pdf(result.content).page_count == 4


def test_pages_appear_in_the_order_given() -> None:
    """The point of the feature: the candidate fixes the order afterwards."""
    sources = _sources()
    plan = plan_document(sources)
    reversed_order = list(reversed(plan.pages))

    result = assemble_document(sources, order=reversed_order)
    assert result.page_count == 4

    # The two photographed sheets differ in content, so page identity is
    # checkable by size: the reversed document must not match the natural one.
    natural = assemble_document(sources)
    assert result.content != natural.content


def test_a_page_can_be_left_out() -> None:
    sources = _sources()
    plan = plan_document(sources)
    keep = [page for page in plan.pages if page.key != (1, 0)]

    result = assemble_document(sources, order=keep)
    assert result.page_count == 3
    assert inspect_pdf(result.content).page_count == 3
    assert any("left out" in finding for finding in result.findings)


def test_a_page_can_be_added_to_an_existing_document() -> None:
    """The common case: a PDF the candidate has, plus the page it is missing."""
    sources = [
        (_scanned_pdf(pages=1), "certificate.pdf"),
        (_photo_bytes(seed=9), "reverse-side.jpg"),
    ]
    plan = plan_document(sources)
    assert len(plan.pages) == 2

    result = assemble_document(sources, order=plan.pages)
    assert inspect_pdf(result.content).page_count == 2


def test_a_page_can_be_rotated() -> None:
    sources = [(_photo_bytes(), "sideways.jpg")]
    plan = plan_document(sources)
    rotated = [
        PageRef(
            source_index=page.source_index,
            page_index=page.page_index,
            origin=page.origin,
            rotation=90,
        )
        for page in plan.pages
    ]

    result = assemble_document(sources, order=rotated)
    page = PdfReader(io.BytesIO(result.content)).pages[0]
    assert int(page.get("/Rotate", 0)) % 360 == 90


def test_a_page_may_be_repeated() -> None:
    """Some portals ask for the same page twice; that is the candidate's call."""
    sources = [(_photo_bytes(), "page.jpg")]
    plan = plan_document(sources)
    result = assemble_document(sources, order=plan.pages + plan.pages)
    assert result.page_count == 2


def test_an_unknown_page_is_reported_and_skipped() -> None:
    sources = _sources()
    plan = plan_document(sources)
    order = plan.pages + [
        PageRef(source_index=9, page_index=0, origin=PageOrigin.PHOTOGRAPH)
    ]
    result = assemble_document(sources, order=order)
    assert result.page_count == 4
    assert any(
        "not" in finding and "available" in finding for finding in result.findings
    )


def test_nothing_readable_is_an_error_not_an_empty_pdf() -> None:
    with pytest.raises(ValueError):
        assemble_document([(b"garbage", "broken.jpg")])


# --- Size, and what may be given up to reach it -----------------------------


def test_the_assembled_document_meets_a_ceiling() -> None:
    result = assemble_document(_sources(), maximum_bytes=250_000)
    assert result.byte_size <= 250_000
    assert not result.exceeds_ceiling


def test_text_pages_are_never_re_encoded_to_meet_a_ceiling() -> None:
    """The rule carried through from single-document preparation.

    A page whose words are text objects has to still have them afterwards, even
    when the ceiling is impossible.
    """
    sources = [
        (_digital_pdf(), "certificate.pdf"),
        (_photo_bytes(seed=4), "extra-page.jpg"),
    ]
    result = assemble_document(sources, maximum_bytes=900)

    assert result.exceeds_ceiling
    inspection = inspect_pdf(result.content)
    assert inspection.has_digital_pages, "the text page must still be a text page"
    assert any("real text" in finding for finding in result.findings)


def test_an_impossible_ceiling_still_returns_the_document() -> None:
    result = assemble_document(_sources(), maximum_bytes=800)
    assert result.exceeds_ceiling
    assert result.content.startswith(b"%PDF-")
    assert inspect_pdf(result.content).page_count == 4


def test_the_assembled_document_carries_no_metadata() -> None:
    result = assemble_document(_sources())
    metadata = PdfReader(io.BytesIO(result.content)).metadata or {}
    assert not (metadata.get("/Producer") or "").strip()
    assert not (metadata.get("/Author") or "").strip()
