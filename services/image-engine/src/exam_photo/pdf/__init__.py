"""PDF deliverables: building them from pages, and preparing existing ones.

Certificates, mark sheets and identity documents are the deliverables that most
often have to be PDFs, and candidates arrive holding one of two things: a
photograph of a piece of paper, or a PDF somebody else made.

The two need opposite treatment and the distinction runs through this package.

A **photograph** the platform is free to work on. It came from the candidate's
camera, it is already being cleaned and framed by ``exam_photo.ink``, and
wrapping it into a PDF is the last step of a process that owns the pixels.

An **existing PDF** is somebody else's document. It may be a scan, or it may be
a digitally issued certificate whose text is real text -- an Aadhaar letter, a
board mark sheet. Rasterising that to hit a byte ceiling would turn crisp text
into a blurry picture of text, and would be exactly the silent alteration of a
document that the integrity rule forbids. So an existing PDF is only ever
restructured, never re-rendered: metadata stripped, streams recompressed, pages
selected or rotated. If it is still too large after that, the honest answer is
to say so.
"""

from exam_photo.pdf.assembly import PdfAssemblyResult, build_pdf_from_images
from exam_photo.pdf.inspection import PdfInspection, PdfPageKind, inspect_pdf
from exam_photo.pdf.preparation import PdfPreparationResult, prepare_existing_pdf

__all__ = [
    "PdfAssemblyResult",
    "PdfInspection",
    "PdfPageKind",
    "PdfPreparationResult",
    "build_pdf_from_images",
    "inspect_pdf",
    "prepare_existing_pdf",
]
