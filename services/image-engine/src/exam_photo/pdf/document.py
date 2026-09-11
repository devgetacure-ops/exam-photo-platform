"""Assembling one PDF from several uploads, in an order the candidate chooses.

A certificate is rarely one page. A mark sheet has a front and a reverse, a
degree certificate comes with a consolidated statement, an experience letter
runs to three sheets. The candidate photographs them one at a time, in whatever
order they happened to pick them up, and sometimes uploads a PDF they already
had alongside photographs of the pages it is missing.

So this takes a list of uploads, flattens them into pages, and assembles them in
whatever order it is given -- with any page rotated, and any page left out.

Two properties are carried through from ``preparation``:

- A page that came from a **photograph** may be re-encoded and downscaled to
  reach a size limit, because it is a photograph.
- A page that came from a **document** is passed through as it arrived. Only
  where the uploaded PDF's own page is a scan may its image be re-encoded, and
  a page carrying real text is never touched.

Removing a page is available here and nowhere else, and the distinction is
deliberate. The automatic path never drops a page, because choosing which part
of somebody's certificate does not matter is not a decision software should
make. A candidate reordering their own document may of course remove one: it is
their certificate and their submission.
"""

import io
from dataclasses import dataclass, field
from enum import Enum

from PIL import Image
from pypdf import PasswordType, PdfReader, PdfWriter

from exam_photo.pdf.assembly import _DEFAULT_DPI, _QUALITY_LADDER, _SCALE_LADDER
from exam_photo.pdf.inspection import PdfPageKind, inspect_pdf
from exam_photo.pdf.preparation import _recompress_page_images


class PageOrigin(str, Enum):
    """Where a page came from, which decides what may be done to it."""

    #: An uploaded image: a photograph of a sheet of paper. Re-encodable.
    PHOTOGRAPH = "photograph"
    #: A page of an uploaded PDF that is itself a scan. Its image is
    #: re-encodable; its structure is not rebuilt.
    DOCUMENT_SCAN = "document_scan"
    #: A page of an uploaded PDF carrying real text. Passed through unchanged.
    DOCUMENT_TEXT = "document_text"


@dataclass(frozen=True)
class PageRef:
    """One page of one upload, identified stably enough to reorder by.

    ``source_index`` and ``page_index`` together are the identity. They survive
    reordering, because the order is expressed as a list of these rather than by
    moving anything.
    """

    source_index: int
    page_index: int
    origin: PageOrigin
    #: Clockwise rotation to apply, in degrees. PDF stores rotation as page
    #: metadata, so this costs nothing and loses nothing.
    rotation: int = 0

    @property
    def key(self) -> tuple[int, int]:
        return (self.source_index, self.page_index)


@dataclass(frozen=True)
class DocumentPlan:
    """Every page available across the uploads, in the order they arrived."""

    pages: list[PageRef]
    #: Uploads that could not be read at all, by index, with the reason.
    unreadable: dict[int, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentResult:
    content: bytes
    page_count: int
    byte_size: int
    exceeds_ceiling: bool
    findings: list[str]


def plan_document(sources: list[tuple[bytes, str]]) -> DocumentPlan:
    """Flatten uploads into the list of pages a candidate can reorder.

    An upload that cannot be read is recorded rather than raised: one damaged
    file among five should not stop the other four being assembled, and the
    candidate needs to be told which one to replace.
    """
    pages: list[PageRef] = []
    unreadable: dict[int, str] = {}

    for index, (data, name) in enumerate(sources):
        if data.startswith(b"%PDF-"):
            try:
                inspection = inspect_pdf(data)
            except Exception as error:
                unreadable[index] = f"{name}: {error}"
                continue
            if inspection.is_encrypted:
                unreadable[index] = (
                    f"{name}: the PDF is password-protected, so it can't be "
                    "opened. Upload a copy of the PDF without a password."
                )
                continue
            for page_index, kind in enumerate(inspection.page_kinds):
                pages.append(
                    PageRef(
                        source_index=index,
                        page_index=page_index,
                        origin=(
                            PageOrigin.DOCUMENT_SCAN
                            if kind is PdfPageKind.SCANNED
                            else PageOrigin.DOCUMENT_TEXT
                        ),
                    )
                )
            continue

        try:
            with Image.open(io.BytesIO(data)) as probe:
                probe.verify()
        except Exception as error:
            unreadable[index] = f"{name}: {error}"
            continue
        pages.append(
            PageRef(source_index=index, page_index=0, origin=PageOrigin.PHOTOGRAPH)
        )

    return DocumentPlan(pages=pages, unreadable=unreadable)


def _image_page(data: bytes, quality: int, scale: float, dpi: int) -> PdfReader:
    image = Image.open(io.BytesIO(data)).convert("RGB")
    if scale < 1.0:
        image = image.resize(
            (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
            resample=Image.Resampling.LANCZOS,
        )
    buffer = io.BytesIO()
    image.save(buffer, "PDF", resolution=float(dpi), quality=quality)
    return PdfReader(io.BytesIO(buffer.getvalue()))


def _build(
    sources: list[tuple[bytes, str]],
    order: list[PageRef],
    quality: int,
    scale: float,
    dpi: int,
) -> bytes:
    writer = PdfWriter()
    readers: dict[int, PdfReader] = {}

    for ref in order:
        data = sources[ref.source_index][0]
        if ref.origin is PageOrigin.PHOTOGRAPH:
            page = _image_page(data, quality, scale, dpi).pages[0]
            writer.add_page(page)
        else:
            reader = readers.get(ref.source_index)
            if reader is None:
                reader = PdfReader(io.BytesIO(data), strict=False)
                if reader.is_encrypted:
                    # A wrong password comes back as NOT_DECRYPTED, not an error.
                    try:
                        if reader.decrypt("") == PasswordType.NOT_DECRYPTED:
                            continue
                    except Exception:
                        continue
                readers[ref.source_index] = reader
            writer.add_page(reader.pages[ref.page_index])
            if ref.origin is PageOrigin.DOCUMENT_SCAN and scale < 1.0:
                # Only a scanned page's image is touched, and only once the
                # photographed pages have already given up what they can.
                _recompress_page_images(writer.pages[-1], quality, scale)

        if ref.rotation:
            writer.pages[-1].rotate(ref.rotation)

    writer.metadata = None
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def assemble_document(
    sources: list[tuple[bytes, str]],
    order: list[PageRef] | None = None,
    maximum_bytes: int | None = None,
    dpi: int = _DEFAULT_DPI,
) -> DocumentResult:
    """Combine uploads into one PDF, in ``order``, under ``maximum_bytes``.

    ``order`` is the candidate's arrangement: a list of the pages to include, in
    the sequence they should appear. Omitting a page leaves it out; repeating
    one is allowed and simply duplicates it, which is occasionally what a
    candidate wants when a portal asks for the same page twice.
    """
    plan = plan_document(sources)
    findings = [reason for reason in plan.unreadable.values()]

    available = {ref.key: ref for ref in plan.pages}
    if order is None:
        chosen = list(plan.pages)
    else:
        chosen = []
        for ref in order:
            known = available.get(ref.key)
            if known is None:
                findings.append(
                    f"Page {ref.page_index + 1} of upload "
                    f"{ref.source_index + 1} was requested but is not "
                    "available; it has been skipped."
                )
                continue
            # The order carries the rotation; the plan carries the origin.
            chosen.append(
                PageRef(
                    source_index=known.source_index,
                    page_index=known.page_index,
                    origin=known.origin,
                    rotation=ref.rotation,
                )
            )

    if not chosen:
        raise ValueError("No readable pages were supplied.")

    dropped = len(plan.pages) - len({ref.key for ref in chosen})
    if dropped > 0:
        findings.append(
            f"{dropped} uploaded page(s) were left out of the document at the "
            "candidate's direction."
        )

    best = _build(sources, chosen, _QUALITY_LADDER[0], 1.0, dpi)
    if maximum_bytes is None or len(best) <= maximum_bytes:
        return DocumentResult(
            content=best,
            page_count=len(chosen),
            byte_size=len(best),
            exceeds_ceiling=False,
            findings=findings,
        )

    for scale in _SCALE_LADDER:
        for quality in _QUALITY_LADDER:
            candidate = _build(sources, chosen, quality, scale, dpi)
            best = candidate
            if len(candidate) <= maximum_bytes:
                if scale < 1.0:
                    findings.append(
                        f"Pages were reduced to {int(scale * 100)}% of their "
                        "captured size to fit the published file-size limit."
                    )
                return DocumentResult(
                    content=candidate,
                    page_count=len(chosen),
                    byte_size=len(candidate),
                    exceeds_ceiling=False,
                    findings=findings,
                )

    text_pages = sum(1 for ref in chosen if ref.origin is PageOrigin.DOCUMENT_TEXT)
    if text_pages:
        findings.append(
            f"{text_pages} of the pages come from a document whose text is "
            "real text. Those are never converted to images, so the size "
            "cannot be reduced further without destroying what makes them "
            "readable and verifiable."
        )
    findings.append(
        f"The document is {len(best)} bytes at the lowest quality and smallest "
        f"size this will produce, against a limit of {maximum_bytes}. It is "
        "delivered anyway."
    )
    return DocumentResult(
        content=best,
        page_count=len(chosen),
        byte_size=len(best),
        exceeds_ceiling=True,
        findings=findings,
    )
