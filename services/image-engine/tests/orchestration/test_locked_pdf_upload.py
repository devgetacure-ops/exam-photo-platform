"""A PDF that needs a password is refused, never handed back as prepared.

A locked PDF cannot be restructured, so the only file the pipeline could return
is the candidate's own, unchanged and still unusable -- which the kit would then
list, and price, as a prepared deliverable. The product never asks for the
password (DEC-052 amendment): the candidate is told to upload a copy without
one. A PDF locked only against printing or copying opens with no password and
is prepared as usual.

These run against real encrypted PDFs rather than a stubbed reader, because
the defect they guard against lived in how pypdf's answer was read: a wrong
password comes back as ``NOT_DECRYPTED``, not as an exception.

Both fixtures are synthesised blank pages.
"""

import io

import pytest
from pypdf import PdfReader, PdfWriter

from exam_photo.models.exam_rule import RequirementType
from exam_photo.orchestration.deliverable_pipeline import (
    PasswordProtectedPdfError,
    prepare_deliverable,
)
from exam_photo.pdf import inspect_pdf, plan_document


def _encrypted_pdf(user_password: str) -> bytes:
    """A one-page PDF. An empty user password opens without asking for one."""
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    # RC4 rather than AES: AES needs the optional `cryptography` package, and
    # what is under test is the lock, not the cipher.
    writer.encrypt(
        user_password=user_password,
        owner_password="owner-only",
        algorithm="RC4-128",
    )
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


# --- Inspection ---------------------------------------------------------------


def test_inspection_names_a_locked_pdf_instead_of_failing_to_read_it() -> None:
    inspection = inspect_pdf(_encrypted_pdf("ABCD1999"))

    assert inspection.is_encrypted
    assert inspection.page_count == 0


def test_inspection_opens_a_pdf_locked_only_against_printing() -> None:
    inspection = inspect_pdf(_encrypted_pdf(""))

    assert not inspection.is_encrypted
    assert inspection.page_count == 1


# --- Single-file preparation --------------------------------------------------


@pytest.mark.parametrize(
    "requirement_type",
    [RequirementType.CERTIFICATE_SCAN, RequirementType.IDENTITY_DOCUMENT],
)
def test_a_pdf_that_needs_a_password_is_refused(
    requirement_type: RequirementType,
) -> None:
    with pytest.raises(PasswordProtectedPdfError):
        prepare_deliverable(_encrypted_pdf("ABCD1999"), "aadhaar.pdf", requirement_type)


def test_a_pdf_locked_only_against_printing_is_still_prepared() -> None:
    result = prepare_deliverable(
        _encrypted_pdf(""), "marks.pdf", RequirementType.CERTIFICATE_SCAN
    )

    assert result.content.startswith(b"%PDF-")
    assert result.filename.endswith(".pdf")
    assert not any("password" in finding.lower() for finding in result.findings)
    # What the candidate receives is never locked, whatever they uploaded.
    assert not PdfReader(io.BytesIO(result.content)).is_encrypted


# --- The arranger ---------------------------------------------------------------


def test_the_arranger_names_a_locked_pdf_and_keeps_the_rest() -> None:
    plan = plan_document(
        [
            (_encrypted_pdf("ABCD1999"), "aadhaar.pdf"),
            (_encrypted_pdf(""), "marks.pdf"),
        ]
    )

    assert plan.unreadable == {
        0: "aadhaar.pdf: the PDF is password-protected, so it can't be opened. "
        "Upload a copy of the PDF without a password."
    }
    assert [page.source_index for page in plan.pages] == [1]
