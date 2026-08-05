"""Building a PDF from pages the platform prepared itself.

The input is one or more images that have already been through
``exam_photo.ink`` -- cleaned, framed, levelled. This wraps them into a PDF at a
real physical page size and lands the file under the examination's byte ceiling.

Two things make this easier than the general case and both come from owning the
pixels. The page content is known, so quality can be traded for size by
re-encoding the images rather than by touching PDF structure. And the ceiling
can be hit by search, the same way the photograph pipeline hits it: encode,
measure, adjust, repeat. There is no need to guess a quality that will fit.
"""

import io
from dataclasses import dataclass
from typing import Sequence

from PIL import Image

#: Points per inch. PDF measures pages in points, so a page's physical size is
#: the pixel size divided by its DPI, times 72.
_POINTS_PER_INCH = 72.0

#: DPI a scanned page is written at when the caller does not say. 200 is the
#: usual floor for a document scan to stay readable in print, and it keeps an
#: A4 page near its true physical size rather than making it enormous or
#: postage-stamp small when a portal opens it.
_DEFAULT_DPI = 200

#: Quality ladder for the size search, highest first. Coarse on purpose: JPEG
#: size responds steeply to quality, so a handful of steps spans the useful
#: range, and every extra step is a full re-encode of every page.
_QUALITY_LADDER = (95, 88, 80, 72, 64, 55, 45, 35)

#: Downscale factors tried once the quality ladder is exhausted. Resolution is
#: given up only after quality, because a soft page of text at full size stays
#: readable and a sharp page at half size may not.
_SCALE_LADDER = (1.0, 0.85, 0.7, 0.55, 0.45)


@dataclass(frozen=True)
class PdfAssemblyResult:
    """The assembled document and the compromises it required."""

    content: bytes
    page_count: int
    byte_size: int
    quality: int
    scale: float
    #: ``True`` when even the last rung of both ladders could not reach the
    #: ceiling. The file is still returned -- a document that is slightly too
    #: large is something a candidate can act on, an exception is not.
    exceeds_ceiling: bool
    findings: list[str]


def _encode(
    pages: Sequence[Image.Image], quality: int, scale: float, dpi: int
) -> bytes:
    prepared: list[Image.Image] = []
    for page in pages:
        image = page.convert("RGB")
        if scale < 1.0:
            image = image.resize(
                (
                    max(1, int(image.width * scale)),
                    max(1, int(image.height * scale)),
                ),
                resample=Image.Resampling.LANCZOS,
            )
        prepared.append(image)

    buffer = io.BytesIO()
    prepared[0].save(
        buffer,
        "PDF",
        save_all=True,
        append_images=prepared[1:],
        resolution=float(dpi),
        quality=quality,
        # Nothing about the candidate's camera, software or filesystem belongs
        # in a file they hand to an examination body.
        producer="",
        creator="",
    )
    return buffer.getvalue()


def build_pdf_from_images(
    pages: Sequence[Image.Image],
    maximum_bytes: int | None = None,
    dpi: int = _DEFAULT_DPI,
) -> PdfAssemblyResult:
    """Wrap prepared pages into a PDF, under ``maximum_bytes`` where possible.

    The search gives up quality before resolution, and both before it gives up
    on the ceiling. A page that is soft but full size stays readable; a page
    that is sharp but shrunk may not have legible text at all, which for a
    certificate is the whole point of the document.
    """
    if not pages:
        raise ValueError("A PDF needs at least one page.")

    findings: list[str] = []
    best = _encode(pages, _QUALITY_LADDER[0], 1.0, dpi)
    if maximum_bytes is None or len(best) <= maximum_bytes:
        return PdfAssemblyResult(
            content=best,
            page_count=len(pages),
            byte_size=len(best),
            quality=_QUALITY_LADDER[0],
            scale=1.0,
            exceeds_ceiling=False,
            findings=findings,
        )

    for scale in _SCALE_LADDER:
        for quality in _QUALITY_LADDER:
            candidate = _encode(pages, quality, scale, dpi)
            if len(candidate) <= maximum_bytes:
                if scale < 1.0:
                    findings.append(
                        f"Pages were reduced to {int(scale * 100)}% of their "
                        "captured size to fit the published file-size limit."
                    )
                return PdfAssemblyResult(
                    content=candidate,
                    page_count=len(pages),
                    byte_size=len(candidate),
                    quality=quality,
                    scale=scale,
                    exceeds_ceiling=False,
                    findings=findings,
                )
            best = candidate

    findings.append(
        f"The document is {len(best)} bytes at the lowest quality and smallest "
        f"size this will produce, against a limit of {maximum_bytes}. It is "
        "delivered anyway; reducing it further would stop the pages being "
        "readable, which defeats the purpose of submitting them."
    )
    return PdfAssemblyResult(
        content=best,
        page_count=len(pages),
        byte_size=len(best),
        quality=_QUALITY_LADDER[-1],
        scale=_SCALE_LADDER[-1],
        exceeds_ceiling=True,
        findings=findings,
    )


def page_size_points(
    image: Image.Image, dpi: int = _DEFAULT_DPI
) -> tuple[float, float]:
    """The physical page size an image becomes, in PDF points."""
    return (
        image.width / dpi * _POINTS_PER_INCH,
        image.height / dpi * _POINTS_PER_INCH,
    )
