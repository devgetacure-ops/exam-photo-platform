"""Reading an uploaded PDF: what it is, and what may safely be done to it.

The one question that matters before touching an existing PDF is whether its
pages are *pictures of a document* or *the document itself*. A scan of a
certificate is a photograph in a PDF wrapper, and re-encoding its image is the
normal way to make it smaller. A digitally issued certificate -- an Aadhaar
letter, a board mark sheet, an e-signed caste certificate -- holds real text and
vector marks, and converting that to a picture to save bytes destroys exactly
what makes it verifiable.

So the classification here is not a nicety. It decides whether the platform is
allowed to change how a page is stored.
"""

import io
from dataclasses import dataclass
from enum import Enum

from pypdf import PasswordType, PdfReader
from pypdf.errors import PdfReadError

from exam_photo.input.errors import ImageInspectionError, InputErrorCode


class PdfPageKind(str, Enum):
    """What a page is made of, and therefore what may be done to it."""

    #: A single large image covering the page: a scan or a photograph. Its
    #: pixels may be re-encoded.
    SCANNED = "scanned"
    #: Text and vector content, possibly with small images. Must not be
    #: rasterised; only its streams may be recompressed.
    DIGITAL = "digital"
    #: Neither could be established -- an unusual structure, or a page this
    #: reader could not walk. Treated as digital, because that is the treatment
    #: that changes least.
    UNKNOWN = "unknown"


class PdfPageLimitExceededError(ValueError):
    """A PDF exceeds the caller's page-processing budget."""


@dataclass(frozen=True)
class PdfInspection:
    """What an uploaded PDF is."""

    page_count: int
    page_kinds: list[PdfPageKind]
    #: Page sizes in points, in the order they appear.
    page_sizes: list[tuple[float, float]]
    is_encrypted: bool
    byte_size: int
    #: ``True`` when every page is a scan, which is the case where re-encoding
    #: the images is a safe way to reduce size.
    is_wholly_scanned: bool

    @property
    def has_digital_pages(self) -> bool:
        return any(kind is not PdfPageKind.SCANNED for kind in self.page_kinds)


#: Share of a page's area a single image must cover for the page to count as a
#: scan. A scanned page is one image edge to edge; a digital certificate may
#: carry a logo or a photograph, but those occupy a small part of the page.
#: 0.6 sits well above a letterhead or an inset portrait and below a scan, which
#: measures essentially 1.0.
_SCAN_AREA_SHARE = 0.6


def inspect_pdf(data: bytes, maximum_pages: int | None = None) -> PdfInspection:
    """Read an uploaded PDF's structure without altering it.

    Raises :class:`ImageInspectionError` when the file cannot be read at all,
    so a corrupt upload fails here with a clear code rather than deeper in as
    something less obvious.
    """
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        encrypted = reader.is_encrypted
        if encrypted:
            # An empty user password is common on "protected" documents and
            # costs nothing to try. A real password is the candidate's to
            # supply, and the platform does not attempt to get past one.
            #
            # pypdf reports a wrong password by returning NOT_DECRYPTED, not by
            # raising, so the result has to be read. Treating "no exception" as
            # "decrypted" sent every locked PDF on to read its pages, where it
            # failed as an undecodable upload instead of being named as locked.
            try:
                encrypted = reader.decrypt("") == PasswordType.NOT_DECRYPTED
            except Exception:
                encrypted = True
        page_count = len(reader.pages) if not encrypted else 0
    except PdfReadError as error:
        raise ImageInspectionError(
            InputErrorCode.INPUT_DECODE_FAILED,
            f"The PDF could not be read: {error}",
            "The file may be damaged. Try exporting or downloading it again.",
        ) from error
    except Exception as error:  # pragma: no cover - defensive
        raise ImageInspectionError(
            InputErrorCode.INPUT_DECODE_FAILED,
            f"The PDF could not be read: {error}",
            "The file may be damaged. Try exporting or downloading it again.",
        ) from error

    if maximum_pages is not None and page_count > maximum_pages:
        raise PdfPageLimitExceededError(
            f"A document may contain at most {maximum_pages} more pages; "
            f"this PDF contains {page_count}."
        )

    pages = list(reader.pages) if not encrypted else []
    kinds: list[PdfPageKind] = []
    sizes: list[tuple[float, float]] = []
    for page in pages:
        box = page.mediabox
        width = float(box.width) or 1.0
        height = float(box.height) or 1.0
        sizes.append((width, height))
        kinds.append(_classify(page, width * height))

    if encrypted:
        return PdfInspection(
            page_count=0,
            page_kinds=[],
            page_sizes=[],
            is_encrypted=True,
            byte_size=len(data),
            is_wholly_scanned=False,
        )

    return PdfInspection(
        page_count=len(pages),
        page_kinds=kinds,
        page_sizes=sizes,
        is_encrypted=False,
        byte_size=len(data),
        is_wholly_scanned=bool(kinds)
        and all(kind is PdfPageKind.SCANNED for kind in kinds),
    )


def _classify(page: object, page_area: float) -> PdfPageKind:
    """Decide whether a page is a scan or a real document.

    Measured by area rather than by image count, because "has an image" is true
    of most digitally issued certificates -- they carry a seal, a logo, a
    photograph of the holder. What distinguishes a scan is that one image *is*
    the page.
    """
    try:
        images = list(getattr(page, "images", []) or [])
    except Exception:  # pragma: no cover - malformed page
        return PdfPageKind.UNKNOWN
    if not images:
        return PdfPageKind.DIGITAL

    try:
        text = (page.extract_text() or "").strip()  # type: ignore[attr-defined]
    except Exception:
        text = ""

    # Real extractable text means real text objects, whatever else is present.
    # A scan has none: its words are pixels.
    if len(text) > 40:
        return PdfPageKind.DIGITAL

    for image in images:
        try:
            inner = image.image
            width, height = inner.size
        except Exception:  # pragma: no cover - undecodable embedded image
            continue
        # The embedded image's pixel dimensions are not page points, so compare
        # aspect-normalised coverage: a full-page scan matches the page's shape
        # and is the only image on it.
        if len(images) == 1 and width * height > 0:
            return PdfPageKind.SCANNED
        if page_area > 0 and (width * height) / page_area >= _SCAN_AREA_SHARE:
            return PdfPageKind.SCANNED
    return PdfPageKind.DIGITAL
