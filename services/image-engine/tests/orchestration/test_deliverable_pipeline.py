"""Producing one compliant deliverable file from one uploaded image.

The tests here are about the *file*, not the picture. Whether a signature looks
right is settled in ``tests/ink``; what matters here is that what comes out is
the size the examination asked for, under the byte ceiling it published, named
as it required -- and that where those cannot all be satisfied, the shortfall is
reported rather than papered over.
"""

import io
from typing import Any

import numpy as np
import pytest
from PIL import Image

from exam_photo.ink import InkTreatment
from exam_photo.models.exam_rule import DeliverableFileSpec, RequirementType
from exam_photo.orchestration.deliverable_pipeline import (
    prepare_deliverable,
    treatment_for,
)


def _photo_of(sheet: np.ndarray[Any, Any]) -> bytes:
    buffer = io.BytesIO()
    Image.fromarray(sheet.astype(np.uint8)).save(buffer, "JPEG", quality=94)
    return buffer.getvalue()


def _signature_sheet(width: int = 1600, height: int = 900) -> np.ndarray[Any, Any]:
    sheet = np.full((height, width, 3), 243.0, dtype=np.float32)
    xs = np.arange(int(width * 0.2), int(width * 0.8))
    for x in xs:
        y = int(height * 0.5 + height * 0.09 * np.sin(x / (width * 0.05)))
        sheet[y - 4 : y + 4, x, :] = np.array([34.0, 40.0, 128.0])
    # A warm, uneven capture, as a phone produces.
    sheet *= np.linspace(0.82, 1.0, width, dtype=np.float32)[None, :, None]
    sheet *= np.array([1.0, 0.96, 0.9])
    return sheet


def _page_sheet(width: int = 1200, height: int = 1700) -> np.ndarray[Any, Any]:
    sheet = np.full((height, width, 3), 244.0, dtype=np.float32)
    for index in range(8):
        y = int(height * 0.12) + index * int(height * 0.09)
        sheet[y : y + 7, int(width * 0.1) : int(width * 0.9), :] = np.array(
            [38.0, 42.0, 96.0]
        )
    frame = np.full((height + 260, width + 260, 3), 33.0, dtype=np.float32)
    frame[130 : 130 + height, 130 : 130 + width, :] = sheet
    return frame


def _spec(**blocks: Any) -> DeliverableFileSpec:
    return DeliverableFileSpec.model_validate(blocks)


# --- Treatment routing ------------------------------------------------------


@pytest.mark.parametrize(
    "requirement_type,expected",
    [
        (RequirementType.SIGNATURE, InkTreatment.MARK),
        (RequirementType.THUMB_IMPRESSION, InkTreatment.IMPRESSION),
        (RequirementType.HANDWRITTEN_DECLARATION, InkTreatment.PAGE),
        (RequirementType.CERTIFICATE_SCAN, InkTreatment.PAGE),
        (RequirementType.IDENTITY_DOCUMENT, InkTreatment.PAGE),
        (RequirementType.OTHER, InkTreatment.PAGE),
    ],
)
def test_each_requirement_type_gets_its_treatment(
    requirement_type: RequirementType, expected: InkTreatment
) -> None:
    assert treatment_for(requirement_type) is expected


def test_a_declaration_is_delivered_whole_not_cropped_to_its_writing() -> None:
    """The product owner's ruling: a declaration is the full page.

    Cropping it to the writing would take off the heading above and the date
    below, which are part of the statement being made.
    """
    data = _photo_of(_page_sheet())
    page = prepare_deliverable(
        data, "declaration.jpg", RequirementType.HANDWRITTEN_DECLARATION
    )
    mark = prepare_deliverable(data, "declaration.jpg", RequirementType.SIGNATURE)

    page_area = page.width * page.height
    mark_area = mark.width * mark.height
    assert page_area > mark_area * 1.3, (
        page.width,
        page.height,
        mark.width,
        mark.height,
    )


# --- The file the examination asked for -------------------------------------


def test_exact_dimensions_are_delivered() -> None:
    result = prepare_deliverable(
        _photo_of(_signature_sheet()),
        "sign.jpg",
        RequirementType.SIGNATURE,
        _spec(
            dimensions={"mode": "exact", "width_px": 140, "height_px": 60},
            file_size={"maximum_bytes": 20000},
            formats={"allowed_formats": ["jpg"], "preferred_format": "jpg"},
        ),
    )
    assert (result.width, result.height) == (140, 60)


def test_the_mark_is_padded_rather_than_stretched_to_fit() -> None:
    """A stretched signature is not the candidate's signature.

    The delivered frame is square while the mark is wide, so the difference has
    to go somewhere. It goes into paper, and the check is that the mark keeps
    its own proportions inside the frame.
    """
    result = prepare_deliverable(
        _photo_of(_signature_sheet()),
        "sign.jpg",
        RequirementType.SIGNATURE,
        _spec(
            dimensions={"mode": "exact", "width_px": 400, "height_px": 400},
            file_size={"maximum_bytes": 60000},
        ),
    )
    assert (result.width, result.height) == (400, 400)

    delivered = np.asarray(Image.open(io.BytesIO(result.content)).convert("L"))
    ink = delivered < 160
    rows = np.nonzero(ink.any(axis=1))[0]
    columns = np.nonzero(ink.any(axis=0))[0]
    # A wide mark squeezed into a square frame stays wide; stretched, it would
    # fill the height.
    assert (columns.max() - columns.min()) > (rows.max() - rows.min()) * 1.6


def test_the_file_lands_under_the_published_ceiling() -> None:
    result = prepare_deliverable(
        _photo_of(_page_sheet()),
        "declaration.jpg",
        RequirementType.HANDWRITTEN_DECLARATION,
        _spec(
            dimensions={"mode": "exact", "width_px": 800, "height_px": 400},
            file_size={"minimum_bytes": 50000, "maximum_bytes": 100000},
        ),
    )
    assert result.byte_size <= 100000, "the ceiling is the hard constraint"
    # The floor is a preference and may be unreachable; when it is missed, that
    # has to be said rather than silently delivered.
    if result.byte_size < 50000:
        assert any("asks for at least" in finding for finding in result.findings)


def test_the_published_filename_is_used() -> None:
    result = prepare_deliverable(
        _photo_of(_signature_sheet()),
        "whatever-the-candidate-called-it.jpg",
        RequirementType.SIGNATURE,
        _spec(
            file_size={"maximum_bytes": 40000},
            formats={"allowed_formats": ["jpg"], "preferred_format": "jpg"},
            filename={"mode": "exact", "exact_filename": "signature"},
        ),
    )
    assert result.filename == "signature.jpg"


def test_an_unpublished_ceiling_is_bounded_and_declared() -> None:
    """No published limit is not the same as no limit."""
    result = prepare_deliverable(
        _photo_of(_page_sheet()), "scan.jpg", RequirementType.CERTIFICATE_SCAN
    )
    assert result.ceiling_was_unpublished
    assert 0 < result.byte_size <= 500_000


# --- When the published values cannot all be met ----------------------------


def test_an_unreachable_minimum_is_reported_not_faked() -> None:
    """IBPS asks for a signature at 140x60 *and* 10-20 KB.

    A clean two-tone mark over 8,400 pixels does not contain 10 KB of JPEG.
    Measured on the reference signature: 3.0 KB at quality 95 and 7.1 KB at
    quality 100 with chroma subsampling off, which is as far as an honest
    encoder goes. The file is delivered at that size and the shortfall is
    stated -- padding it to clear the number would put bytes in the file that
    are not the signature.
    """
    result = prepare_deliverable(
        _photo_of(_signature_sheet()),
        "sign.jpg",
        RequirementType.SIGNATURE,
        _spec(
            dimensions={"mode": "exact", "width_px": 140, "height_px": 60},
            file_size={"minimum_bytes": 10000, "maximum_bytes": 20000},
        ),
    )
    assert result.byte_size < 10000
    assert result.byte_size <= 20000, "the ceiling still has to hold"
    assert any("asks for at least" in finding for finding in result.findings), (
        result.findings
    )


def test_the_minimum_push_never_breaks_the_ceiling() -> None:
    """The floor is a preference; the ceiling is a hard portal limit.

    A large page at maximum quality with full chroma is far bigger than this
    ceiling, so the push toward the floor has to decline its own result. A spec
    with the floor *above* the ceiling cannot be constructed at all -- the rule
    model rejects it -- so the case that matters is a floor near the ceiling
    where the push would overshoot.
    """
    result = prepare_deliverable(
        _photo_of(_page_sheet()),
        "declaration.jpg",
        RequirementType.HANDWRITTEN_DECLARATION,
        _spec(
            dimensions={"mode": "exact", "width_px": 900, "height_px": 1200},
            file_size={"minimum_bytes": 58000, "maximum_bytes": 60000},
        ),
    )
    assert result.byte_size <= 60000


def test_the_delivered_bytes_decode_to_the_declared_size() -> None:
    """A size reported but not actually encoded is worse than no report."""
    result = prepare_deliverable(
        _photo_of(_signature_sheet()),
        "sign.jpg",
        RequirementType.SIGNATURE,
        _spec(
            dimensions={"mode": "exact", "width_px": 200, "height_px": 90},
            file_size={"maximum_bytes": 30000},
        ),
    )
    decoded = Image.open(io.BytesIO(result.content))
    assert decoded.size == (result.width, result.height) == (200, 90)
    assert len(result.content) == result.byte_size


def test_a_preferred_size_is_delivered_padded_not_stretched() -> None:
    """DEC-093: "140 x 60 pixels (preferred)" is honoured without claiming a mandate."""
    result = prepare_deliverable(
        _photo_of(_signature_sheet()),
        "sign.jpg",
        RequirementType.SIGNATURE,
        _spec(
            dimensions={
                "mode": "unspecified",
                "preferred_width_px": 140,
                "preferred_height_px": 60,
                "fallback_reason": "preferred, not mandated",
            },
            file_size={"maximum_bytes": 40000},
            formats={"allowed_formats": ["jpg"], "preferred_format": "jpg"},
        ),
    )
    assert (result.width, result.height) == (140, 60)
    assert not any("could not be sized" in f for f in result.findings)


def test_a_tall_range_takes_a_wide_signature_by_padding() -> None:
    """BPSC: 150-220 px wide and 250-320 px tall; a wide signature is padded to fit."""
    result = prepare_deliverable(
        _photo_of(_signature_sheet()),
        "sign.jpg",
        RequirementType.SIGNATURE,
        _spec(
            dimensions={
                "mode": "range",
                "minimum_width_px": 150,
                "maximum_width_px": 220,
                "minimum_height_px": 250,
                "maximum_height_px": 320,
            },
            file_size={"maximum_bytes": 20000},
            formats={"allowed_formats": ["jpg"], "preferred_format": "jpg"},
        ),
    )
    assert 150 <= result.width <= 220
    assert 250 <= result.height <= 320
    assert not any("could not be sized" in f for f in result.findings)
