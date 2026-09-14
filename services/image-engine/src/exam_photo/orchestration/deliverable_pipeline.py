"""Turning an uploaded file into one compliant application deliverable.

This is the non-photograph counterpart to ``rule_pipeline``. A candidate uploads
a photograph of their signature, their thumb impression, their handwritten
declaration or a certificate; an examination's requirement says what the file
has to be; this produces that file.

The stages are the generic half of the photograph pipeline plus one
deliverable-specific step:

1. **Normalise the input** -- the same decoding, signature check, EXIF strip and
   orientation fix a photograph gets. Shared deliberately: the security
   properties of "accept an arbitrary uploaded file" do not depend on what the
   file is a picture of.
2. **Prepare the content** -- ``exam_photo.ink``, with the treatment chosen by
   what the requirement is for. A signature is cropped to its strokes, an
   impression is left whole, a page is framed by its sheet.
3. **Resize** to the published dimensions, where the body publishes any.
4. **Compress** to the published byte ceiling, landing just underneath it.
5. **Name** the file as the body requires.

Steps 1, 3, 4 and 5 are the existing providers, unchanged. That is the point:
the photograph pipeline had already solved "make this file satisfy a
specification", and the only thing missing for the other deliverables was
something to put in front of it.

What this does *not* do is decide whether the platform should be preparing the
requirement at all. A requirement whose submission method is an official live
capture, or whose platform support says otherwise, must be filtered out by the
caller -- and the rule model refuses to record such a requirement as supported
in the first place.
"""

import io
from dataclasses import dataclass, field
from typing import Any, Optional

from PIL import Image

from exam_photo.ink import InkPreparation, InkTreatment, prepare_ink_document
from exam_photo.input.limits import InputLimits
from exam_photo.input.normalization import normalize_image_input
from exam_photo.models.exam_rule import (
    DeliverableFileSpec,
    DimensionMode,
    RequirementType,
)
from exam_photo.orchestration.filename_generation import (
    FilenameGenerationConfig,
    generate_safe_filename,
)
from exam_photo.pdf import (
    build_pdf_from_images,
    prepare_existing_pdf,
)
from exam_photo.providers.compression.deterministic_image_compressor import (
    DeterministicJpegCompressor,
)
from exam_photo.providers.output_compression import (
    CompressionFormat,
    OutputCompressionConfig,
)
from exam_photo.providers.output_preparation import (
    EnhancementMode,
    OutputPreparationConfig,
    ResizeMode,
)
from exam_photo.providers.output_preparers.deterministic_output_preparer import (
    DeterministicOutputPreparer,
)

#: Which treatment each requirement type gets.
#:
#: The mapping is the product decision, not a technical one, and it is short
#: enough to read as the statement it is: a signature is its strokes, an
#: impression is its ridge pattern, everything else is a sheet of paper.
_TREATMENT_BY_TYPE = {
    RequirementType.SIGNATURE: InkTreatment.MARK,
    RequirementType.THUMB_IMPRESSION: InkTreatment.IMPRESSION,
    RequirementType.HANDWRITTEN_DECLARATION: InkTreatment.PAGE,
    RequirementType.CERTIFICATE_SCAN: InkTreatment.PAGE,
    RequirementType.IDENTITY_DOCUMENT: InkTreatment.PAGE,
}

#: Ceiling applied when a body publishes no byte limit at all.
#:
#: Not a guess at what the portal wants -- there is nothing to guess from -- but
#: a bound on what this pipeline will emit, so an unbounded requirement cannot
#: produce a 12 MB file from a modern phone camera. Recorded in the result so a
#: caller can tell a published ceiling from this one.
_UNSPECIFIED_BYTE_CEILING = 500_000


@dataclass(frozen=True)
class DeliverableResult:
    """One prepared file, and what is true about it."""

    content: bytes
    filename: str
    width: int
    height: int
    byte_size: int
    #: ``True`` when the byte ceiling came from the fallback above rather than
    #: from the examination.
    ceiling_was_unpublished: bool
    #: ``True`` when the page appeared to carry no mark at all. Reported, never
    #: refused, on the same reasoning as DEC-041: the candidate still receives
    #: their file and can see for themselves that it is blank.
    is_blank: bool
    #: ``None`` when the upload was already a PDF: nothing was prepared from
    #: pixels, because a PDF is restructured rather than re-rendered.
    preparation: Optional[InkPreparation]
    #: Things worth a candidate's attention before they submit.
    findings: list[str]
    #: Routine normalisation done to the upload -- metadata removed, colour
    #: mode converted -- as codes. Not findings: nothing is wrong, and a
    #: caveat that fires on every ordinary JPEG trains people to ignore the
    #: caveats that matter (DEC-056).
    changes: list[str] = field(default_factory=list)


def treatment_for(requirement_type: RequirementType) -> InkTreatment:
    """The treatment a requirement type gets. Unknown types are pages.

    Falling back to ``PAGE`` is the conservative default: it is the treatment
    that crops least and clips least, so a requirement type added to the schema
    before this mapping is updated gets handled cautiously rather than having
    its content cropped away by a rule written for signatures.
    """
    return _TREATMENT_BY_TYPE.get(requirement_type, InkTreatment.PAGE)


def _resize_config(
    spec: Optional[DeliverableFileSpec],
) -> Optional[OutputPreparationConfig]:
    """Build a resize configuration, or ``None`` when the body published none.

    A deliverable with no published dimensions is delivered at the size its own
    content produced. That mirrors what the photograph pipeline does for the
    fifteen examinations that publish a file size and no pixel dimensions
    (DEC-045): inventing a size would be asserting something the body did not.
    """
    dimensions = spec.dimensions if spec else None
    if dimensions is None:
        return None
    if dimensions.mode == DimensionMode.EXACT:
        return OutputPreparationConfig(
            resize_mode=ResizeMode.EXACT,
            target_width=dimensions.width_px,
            target_height=dimensions.height_px,
            # Padding rather than distortion, on the same rule the photograph
            # pipeline follows: the delivered aspect follows the content, and a
            # mismatch is filled with paper rather than stretched out of shape.
            # A stretched signature is not the candidate's signature.
            allow_padding=True,
            enhancement_mode=EnhancementMode.NONE,
        )
    if dimensions.mode == DimensionMode.RANGE:
        return OutputPreparationConfig(
            resize_mode=ResizeMode.RANGE_SELECT,
            min_width=dimensions.minimum_width_px,
            max_width=dimensions.maximum_width_px,
            min_height=dimensions.minimum_height_px,
            max_height=dimensions.maximum_height_px,
            preferred_width=dimensions.preferred_width_px,
            preferred_height=dimensions.preferred_height_px,
            enhancement_mode=EnhancementMode.NONE,
        )
    return None


def _pad_to_aspect(image: Image.Image, target_aspect: float) -> Image.Image:
    """Extend the frame with paper until it matches the required aspect.

    Done here rather than by the resizer, and the reason is worth stating. The
    shared output preparer rejects an aspect mismatch beyond an *absolute* 0.01,
    which is a sensible bound at a photograph's 0.75 aspect -- about 1.3%
    relative -- and a very tight one at a signature's 2.33, where it is 0.43%.
    A signature cropped to its own strokes will essentially never land within
    0.43% of a published 140x60, so every signature was being refused.

    Padding rather than loosening the shared bound: the photograph pipeline
    depends on that bound and a face has no spare margin to add, whereas the
    white space around a signature is arbitrary by nature. Adding more of it
    changes nothing about the mark, and it is what a person would do by hand.
    """
    width, height = image.size
    current = width / height if height else target_aspect
    if abs(current - target_aspect) < 1e-6:
        return image
    if current < target_aspect:
        new_width, new_height = int(round(height * target_aspect)), height
    else:
        new_width, new_height = width, int(round(width / target_aspect))
    new_width = max(new_width, width)
    new_height = max(new_height, height)

    canvas = Image.new("RGB", (new_width, new_height), (255, 255, 255))
    canvas.paste(
        image.convert("RGB"),
        ((new_width - width) // 2, (new_height - height) // 2),
    )
    return canvas


def _largest_encoding(
    image: Image.Image, ceiling: int, current_size: int, current: bytes
) -> tuple[bytes, bool]:
    """Re-encode as large as JPEG honestly goes, for a published *minimum*.

    Byte ceilings are the usual constraint and the compressor is built for
    them: it searches downward for the largest file that fits. A published
    *floor* is the opposite problem, and several bodies publish both -- IBPS
    asks for a signature at 140x60 pixels and 10-20 KB.

    Those two are hard to satisfy together. A clean signature is two tones over
    8,400 pixels and there is simply not much to encode. Measured on the
    reference signature at exactly 140x60: 3.0 KB at quality 95, 3.9 KB at 98,
    5.0 KB at 100, and 7.1 KB at quality 100 with chroma subsampling disabled.
    The floor is not reachable, by a factor of about 1.4.

    So this takes the last legitimate step -- maximum quality, full chroma --
    and stops. What it deliberately does not do is inflate the file with
    padding or metadata to clear the number. That would satisfy a byte count by
    putting bytes in the file that are not the signature, which is the kind of
    thing that gets an application rejected on inspection rather than accepted,
    and it would undo the metadata stripping that is there for privacy.
    """
    buffer = io.BytesIO()
    image.convert("RGB").save(
        buffer, "JPEG", quality=100, subsampling=0, optimize=False
    )
    candidate = buffer.getvalue()
    if len(candidate) > ceiling:
        return current, False
    if len(candidate) <= current_size:
        return current, False
    return candidate, True


def _output_extension(spec: Optional[DeliverableFileSpec]) -> str:
    formats = spec.formats if spec else None
    if formats is None:
        return "jpg"
    preferred = (formats.preferred_format or "").lower().strip()
    return preferred if preferred else "jpg"


#: The first bytes of every PDF. Checked rather than trusting the filename,
#: because the extension is whatever the candidate's phone last called it.
_PDF_MAGIC = b"%PDF-"


def _wants_pdf(spec: Optional[DeliverableFileSpec]) -> bool:
    formats = spec.formats if spec else None
    if formats is None:
        return False
    return "pdf" in {f.lower().strip() for f in formats.allowed_formats}


def prepare_deliverable(
    data: bytes,
    filename: str,
    requirement_type: RequirementType,
    file_spec: Optional[DeliverableFileSpec] = None,
    limits: Optional[InputLimits] = None,
    name_stem: Optional[str] = None,
    exam_name: Optional[str] = None,
) -> DeliverableResult:
    """Prepare one uploaded file into the deliverable a requirement asks for.

    ``name_stem`` is the standard name used when the examination publishes no
    exact one; ``exam_name`` is how the plain-words findings name the body.
    """
    findings: list[str] = []
    stem = _published_name(file_spec) or name_stem or requirement_type.value
    size = file_spec.file_size if file_spec else None
    ceiling = size.maximum_bytes if size is not None else _UNSPECIFIED_BYTE_CEILING

    if data.startswith(_PDF_MAGIC):
        return _prepare_uploaded_pdf(
            data, requirement_type, file_spec, ceiling, size is None, stem
        )

    normalized = normalize_image_input(data, filename, limits or InputLimits())
    changes = [str(getattr(code, "value", code)) for code in normalized.warnings]

    treatment = treatment_for(requirement_type)
    prepared = prepare_ink_document(normalized.image.convert("RGB"), treatment)
    if prepared.is_blank:
        findings.append(
            "No mark was found on the page. The file is still produced so the "
            "candidate can see what was captured."
        )

    image: Image.Image = prepared.image

    dimensions = file_spec.dimensions if file_spec else None
    if (
        dimensions is not None
        and dimensions.mode == DimensionMode.EXACT
        and dimensions.width_px
        and dimensions.height_px
    ):
        target_aspect = dimensions.width_px / dimensions.height_px
        if (
            treatment is InkTreatment.PAGE
            and target_aspect >= 1.2
            and image.width / image.height <= 0.9
        ):
            # IBPS, SBI, RBI, LIC, NABARD and NIACL publish the declaration at
            # 800 x 400. An upright page can only be padded into that frame --
            # never stretched, never turned on its side -- so it arrives small,
            # and the candidate is told how to write it instead.
            findings.append(
                "Your page was upright, so it sits small in the "
                f"{dimensions.width_px} x {dimensions.height_px} px landscape "
                "frame this examination asks for. Write it across a sheet held "
                "sideways and upload that photo instead."
            )
        image = _pad_to_aspect(image, target_aspect)

    resize = _resize_config(file_spec)
    if resize is not None:
        prepared_output = DeterministicOutputPreparer().prepare_output(image, resize)
        if prepared_output.output_image is not None:
            image = prepared_output.output_image
        if not prepared_output.validation.is_valid:
            findings.append(
                "This file could not be sized exactly to the published "
                "dimensions, so it is delivered at its own size. Check it "
                "against the notice before you upload it."
            )

    if _wants_pdf(file_spec):
        assembled = build_pdf_from_images([image], maximum_bytes=ceiling)
        findings.extend(assembled.findings)
        return DeliverableResult(
            content=assembled.content,
            filename=generate_safe_filename(
                stem, config=FilenameGenerationConfig(extension="pdf")
            ),
            width=image.width,
            height=image.height,
            byte_size=assembled.byte_size,
            ceiling_was_unpublished=size is None,
            is_blank=prepared.is_blank,
            preparation=prepared,
            findings=findings,
            changes=changes,
        )

    compression = DeterministicJpegCompressor().compress_output(
        image.convert("RGB"),
        OutputCompressionConfig(
            target_format=CompressionFormat.JPEG,
            maximum_bytes=ceiling,
            minimum_bytes=size.minimum_bytes if size is not None else None,
        ),
    )
    content = compression.encoded_bytes or b""

    minimum = size.minimum_bytes if size is not None else None
    if minimum is not None and len(content) < minimum:
        content, _ = _largest_encoding(image, ceiling, len(content), content)
        if len(content) < minimum:
            assert size is not None
            unit = size.size_unit_as_published or "KB"
            floor = (
                f"{size.published_minimum:g} {unit}"
                if size.published_minimum
                else f"{minimum / 1000:g} KB"
            )
            findings.append(
                f"This file is {len(content) / 1000:.1f} KB; "
                f"{exam_name or 'this examination'} asks for at least {floor}."
            )

    name = generate_safe_filename(
        stem,
        config=FilenameGenerationConfig(extension=_output_extension(file_spec)),
    )

    return DeliverableResult(
        content=content,
        filename=name,
        width=image.width,
        height=image.height,
        byte_size=len(content),
        ceiling_was_unpublished=size is None,
        is_blank=prepared.is_blank,
        preparation=prepared,
        findings=findings,
        changes=changes,
    )


class PasswordProtectedPdfError(ValueError):
    """The upload is a PDF that cannot be opened without a password.

    Raised rather than reported as a finding. A locked PDF cannot be
    restructured, so the only file this could hand back is the candidate's
    own, unchanged and still unusable -- which the kit would then list, and
    price, as a prepared deliverable. The product never asks for the password
    (DEC-052 amendment): the candidate is told to upload a copy without one.
    """


def _prepare_uploaded_pdf(
    data: bytes,
    requirement_type: RequirementType,
    file_spec: Optional[DeliverableFileSpec],
    ceiling: int,
    ceiling_unpublished: bool,
    stem: str,
) -> DeliverableResult:
    """Prepare a PDF the candidate already had.

    Never re-rendered into an image, whatever the requirement's format says.
    If an examination wants a JPEG and the candidate holds a PDF, the honest
    answer is that this cannot convert it -- rasterising a digitally issued
    certificate would turn verifiable text into a picture of text, and doing so
    silently is worse than saying no.

    A PDF locked only against printing or copying opens with an empty password
    and is prepared as usual; one that needs a real password is refused.
    """
    result = prepare_existing_pdf(data, maximum_bytes=ceiling)
    if result.inspection.is_encrypted:
        raise PasswordProtectedPdfError("the PDF cannot be opened without a password")
    findings = list(result.findings)
    if file_spec is not None and not _wants_pdf(file_spec):
        findings.append(
            "The upload is a PDF and this requirement asks for an image. The "
            "PDF has been prepared as-is; converting it would turn the "
            "document into a picture of itself."
        )
    return DeliverableResult(
        content=result.content,
        filename=generate_safe_filename(
            stem, config=FilenameGenerationConfig(extension="pdf")
        ),
        width=0,
        height=0,
        byte_size=result.byte_size,
        ceiling_was_unpublished=ceiling_unpublished,
        is_blank=False,
        preparation=None,
        findings=findings,
    )


def _published_name(spec: Optional[DeliverableFileSpec]) -> Optional[str]:
    filename = spec.filename if spec else None
    if filename is None:
        return None
    exact: Any = filename.exact_filename
    return str(exact) if exact else None
