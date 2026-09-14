"""A photograph under its examination's minimum size is delivered, not refused.

Found on SBI Junior Associates (200 x 230 px, 20-50 KB): a 17.7 KB result was
recorded as not produced. Over the ceiling still fails, because a portal
refuses that file outright; under the floor is reported with both figures.
"""

from __future__ import annotations

import io

from PIL import Image

from exam_photo.api.service import size_floor_finding
from exam_photo.orchestration.final_validation import (
    BELOW_MINIMUM_CODE,
    validate_final_candidate,
)
from exam_photo.providers.output_compression import OutputCompressionConfig


def _jpeg(width: int, height: int) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), "white").save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def test_under_the_floor_is_valid_with_its_own_code() -> None:
    data = _jpeg(200, 230)
    report = validate_final_candidate(
        data,
        expected_width=200,
        expected_height=230,
        config=OutputCompressionConfig(
            maximum_bytes=50_000, minimum_bytes=len(data) + 5_000
        ),
    )
    assert report.is_valid is True
    assert report.issue_codes == [BELOW_MINIMUM_CODE]


def test_over_the_ceiling_still_fails() -> None:
    data = _jpeg(600, 800)
    report = validate_final_candidate(
        data,
        expected_width=600,
        expected_height=800,
        config=OutputCompressionConfig(maximum_bytes=1_000, minimum_bytes=500),
    )
    assert report.is_valid is False
    assert "PIPELINE_FINAL_BYTE_SIZE_INVALID" in report.issue_codes
    assert BELOW_MINIMUM_CODE not in report.issue_codes


def test_under_the_floor_with_another_defect_still_fails() -> None:
    data = _jpeg(200, 230)
    report = validate_final_candidate(
        data,
        expected_width=300,
        expected_height=230,
        config=OutputCompressionConfig(
            maximum_bytes=50_000, minimum_bytes=len(data) + 5_000
        ),
    )
    assert report.is_valid is False


SBI = {
    "exam": {"exam_name": "SBI Junior Associates 2025"},
    "image_requirements": {
        "file_size": {
            "minimum_bytes": 20_000,
            "maximum_bytes": 50_000,
            "published_minimum": 20,
            "size_unit_as_published": "KB",
        }
    },
}


def test_the_finding_names_both_figures_in_the_notice_unit() -> None:
    assert (
        size_floor_finding(SBI, 17_700)
        == "This photo is 17.7 KB; SBI Junior Associates 2025 asks for at least 20 KB."
    )


def test_no_finding_when_the_floor_is_met_or_absent() -> None:
    assert size_floor_finding(SBI, 20_000) is None
    assert size_floor_finding(SBI, None) is None
    assert size_floor_finding({"image_requirements": {"file_size": {}}}, 1) is None
