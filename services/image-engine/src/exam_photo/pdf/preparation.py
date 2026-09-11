"""Preparing a PDF the candidate already has.

Everything here is restructuring. Nothing re-renders a page, and the reason is
the integrity rule: a digitally issued certificate's value is that its text is
text, and turning it into a picture of text to save bytes destroys that while
looking, at a glance, like it worked.

What is available without re-rendering, in the order it is tried:

1. **Strip metadata.** Author, producer, creation software, sometimes a
   filesystem path. Free to remove, and it should not be travelling to an
   examination body regardless of size.
2. **Recompress the content streams.** Lossless. Typically a few per cent.
3. **Re-encode the page images** -- but only on pages that *are* an image. A
   scan can be re-encoded because a scan is already a photograph; a digital
   page cannot, because its images are seals and portraits sitting alongside
   real text.

If the ceiling is still not met, that is reported. The alternative -- rasterise
the whole document and compress the pictures -- would meet the number and quietly
downgrade the evidence.
"""

import io
from dataclasses import dataclass

from PIL import Image
from pypdf import PasswordType, PdfReader, PdfWriter

from exam_photo.pdf.inspection import PdfInspection, inspect_pdf

#: Quality ladder for re-encoding the images inside scanned pages.
_IMAGE_QUALITY_LADDER = (85, 75, 65, 55, 45, 35)

#: Downscale factors for those same images, tried only after quality is spent.
#:
#: Quality alone does not reach a tight ceiling on a modern scan. Measured on a
#: real board mark sheet: the page holds one 2768x3952 image, 10.9 megapixels,
#: and re-encoding it at quality 35 still leaves the document at 867 KB against
#: a 400 KB limit. Halving the resolution takes it under while leaving roughly
#: 170 DPI on an A4 page, which is comfortably readable.
#:
#: Reducing a scan's resolution is legitimate in a way that rasterising a text
#: PDF is not: a scan is already a photograph of a document, so this is the same
#: operation the photograph pipeline performs, not a conversion of one kind of
#: content into another.
_IMAGE_SCALE_LADDER = (1.0, 0.8, 0.65, 0.5, 0.4, 0.3)


@dataclass(frozen=True)
class PdfPreparationResult:
    """The prepared document and what was done to it."""

    content: bytes
    page_count: int
    byte_size: int
    original_byte_size: int
    metadata_stripped: bool
    #: ``True`` when page images were re-encoded. Only ever true for pages the
    #: inspection classified as scans.
    images_recompressed: bool
    exceeds_ceiling: bool
    inspection: PdfInspection
    findings: list[str]


def prepare_existing_pdf(
    data: bytes,
    maximum_bytes: int | None = None,
    maximum_pages: int | None = None,
) -> PdfPreparationResult:
    """Restructure an uploaded PDF toward the examination's specification."""
    inspection = inspect_pdf(data)
    findings: list[str] = []

    if inspection.is_encrypted:
        findings.append(
            "The PDF is password-protected, so it can't be opened or prepared. "
            "Upload a copy of the PDF without a password."
        )
        return PdfPreparationResult(
            content=data,
            page_count=0,
            byte_size=len(data),
            original_byte_size=len(data),
            metadata_stripped=False,
            images_recompressed=False,
            exceeds_ceiling=maximum_bytes is not None and len(data) > maximum_bytes,
            inspection=inspection,
            findings=findings,
        )

    if maximum_pages is not None and inspection.page_count > maximum_pages:
        findings.append(
            f"The document has {inspection.page_count} pages and the "
            f"examination allows {maximum_pages}. Every page is kept -- "
            "dropping one would be deciding which part of the candidate's "
            "certificate does not matter."
        )

    content = _rewrite(data, recompress_images=False, quality=None)
    if maximum_bytes is None or len(content) <= maximum_bytes:
        return PdfPreparationResult(
            content=content,
            page_count=inspection.page_count,
            byte_size=len(content),
            original_byte_size=len(data),
            metadata_stripped=True,
            images_recompressed=False,
            exceeds_ceiling=False,
            inspection=inspection,
            findings=findings,
        )

    if not inspection.is_wholly_scanned:
        findings.append(
            f"The document is {len(content)} bytes against a limit of "
            f"{maximum_bytes}. It carries real text rather than page scans, so "
            "it has only been losslessly compressed: converting the text to "
            "images would meet the limit by making the certificate a picture "
            "of itself."
        )
        return PdfPreparationResult(
            content=content,
            page_count=inspection.page_count,
            byte_size=len(content),
            original_byte_size=len(data),
            metadata_stripped=True,
            images_recompressed=False,
            exceeds_ceiling=True,
            inspection=inspection,
            findings=findings,
        )

    best = content
    for scale in _IMAGE_SCALE_LADDER:
        for quality in _IMAGE_QUALITY_LADDER:
            candidate = _rewrite(
                data, recompress_images=True, quality=quality, scale=scale
            )
            best = candidate
            if len(candidate) <= maximum_bytes:
                if scale < 1.0:
                    findings.append(
                        f"The scanned pages were re-encoded and reduced to "
                        f"{int(scale * 100)}% of their scanned resolution to fit "
                        "the published file-size limit."
                    )
                else:
                    findings.append(
                        "The scanned pages were re-encoded to fit the published "
                        "file-size limit."
                    )
                return PdfPreparationResult(
                    content=candidate,
                    page_count=inspection.page_count,
                    byte_size=len(candidate),
                    original_byte_size=len(data),
                    metadata_stripped=True,
                    images_recompressed=True,
                    exceeds_ceiling=False,
                    inspection=inspection,
                    findings=findings,
                )

    findings.append(
        f"The document is {len(best)} bytes at the lowest quality and smallest "
        f"resolution this will produce, against a limit of {maximum_bytes}. It "
        "is delivered anyway; reducing it further would stop the pages being "
        "readable, which defeats the purpose of submitting them."
    )
    return PdfPreparationResult(
        content=best,
        page_count=inspection.page_count,
        byte_size=len(best),
        original_byte_size=len(data),
        metadata_stripped=True,
        images_recompressed=True,
        exceeds_ceiling=True,
        inspection=inspection,
        findings=findings,
    )


def _rewrite(
    data: bytes,
    recompress_images: bool,
    quality: int | None,
    scale: float = 1.0,
) -> bytes:
    """Write the document out again, stripped and optionally re-encoded."""
    reader = PdfReader(io.BytesIO(data), strict=False)
    if reader.is_encrypted:
        # A wrong password comes back as NOT_DECRYPTED rather than an error.
        try:
            if reader.decrypt("") == PasswordType.NOT_DECRYPTED:
                return data
        except Exception:
            return data

    writer = PdfWriter()
    for index, page in enumerate(reader.pages):
        writer.add_page(page)
        written = writer.pages[index]
        try:
            written.compress_content_streams()
        except Exception:
            # Lossless and optional: a stream this version cannot recompress is
            # left exactly as it was.
            pass
        if recompress_images and quality is not None:
            _recompress_page_images(written, quality, scale)

    # No producer, no author, no creation software, no source path. Setting the
    # whole dictionary to None rather than writing an empty one: pypdf stamps
    # itself as /Producer when asked to add empty metadata, and "made by pypdf"
    # is still a fact about the candidate's toolchain travelling to an
    # examination body.
    writer.metadata = None
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _recompress_page_images(page: object, quality: int, scale: float = 1.0) -> None:
    """Re-encode, and optionally shrink, the images on one scanned page."""
    try:
        images = list(getattr(page, "images", []) or [])
    except Exception:  # pragma: no cover - malformed page
        return
    for item in images:
        try:
            source: Image.Image = item.image
            if scale < 1.0:
                source = source.resize(
                    (
                        max(1, int(source.width * scale)),
                        max(1, int(source.height * scale)),
                    ),
                    resample=Image.Resampling.LANCZOS,
                )
            buffer = io.BytesIO()
            source.convert("RGB").save(buffer, "JPEG", quality=quality, optimize=True)
            item.replace(Image.open(io.BytesIO(buffer.getvalue())), quality=quality)
        except Exception:
            # An image that cannot be re-encoded keeps its original bytes. The
            # size search simply gains less from that page.
            continue
