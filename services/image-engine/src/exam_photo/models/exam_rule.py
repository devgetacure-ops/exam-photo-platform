import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from exam_photo.models.provenance import ProvenanceType, ValueProvenance
from exam_photo.models.source_evidence import SourceEvidence
from exam_photo.providers.crop_planning import CropProfile, EarsPolicy


class RuleStatus(str, Enum):
    DRAFT = "draft"
    PROVISIONAL = "provisional"
    VERIFIED = "verified"
    VERIFIED_WITH_AMBIGUITY = "verified_with_ambiguity"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class ExamIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exam_id: str = Field(pattern=r"^[a-z0-9\-]+$")
    exam_name: str = Field(min_length=1)
    aliases: List[str] = Field(default_factory=list)
    conducting_body: str = Field(min_length=1)
    examination_year: int = Field(ge=1900)
    application_cycle: str = Field(min_length=1)
    application_stage: Optional[str] = None
    jurisdiction: Optional[str] = None
    category: Optional[str] = None
    language_display_key: Optional[str] = None

    @model_validator(mode="after")
    def validate_aliases(self) -> "ExamIdentity":
        norm_name = re.sub(r"\s+", "", self.exam_name.lower())
        for alias in self.aliases:
            if not alias.strip():
                raise ValueError("Aliases cannot be empty strings.")
            norm_alias = re.sub(r"\s+", "", alias.lower())
            if norm_alias == norm_name:
                raise ValueError(
                    f"Alias '{alias}' duplicates the primary exam name '{self.exam_name}'."
                )
        return self


class DimensionMode(str, Enum):
    EXACT = "exact"
    RANGE = "range"
    UNSPECIFIED = "unspecified"


class AspectRatioPolicy(str, Enum):
    FIXED = "fixed"
    FLEXIBLE = "flexible"
    DERIVED = "derived"
    NONE = "none"


class DimensionsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: DimensionMode
    width_px: Optional[int] = Field(default=None, gt=0)
    height_px: Optional[int] = Field(default=None, gt=0)
    dpi: Optional[int] = Field(default=None, gt=0)
    aspect_ratio: Optional[str] = Field(default=None, pattern=r"^[0-9]+:[0-9]+$")

    minimum_width_px: Optional[int] = Field(default=None, gt=0)
    maximum_width_px: Optional[int] = Field(default=None, gt=0)
    minimum_height_px: Optional[int] = Field(default=None, gt=0)
    maximum_height_px: Optional[int] = Field(default=None, gt=0)
    preferred_width_px: Optional[int] = Field(default=None, gt=0)
    preferred_height_px: Optional[int] = Field(default=None, gt=0)
    aspect_ratio_policy: Optional[AspectRatioPolicy] = None

    platform_default_profile: Optional[str] = None
    permitted_pixel_range: Optional[str] = None
    recommended_aspect_ratio: Optional[str] = None
    fallback_reason: Optional[str] = None

    @model_validator(mode="after")
    def validate_dimension_mode(self) -> "DimensionsConfig":
        if self.mode == DimensionMode.EXACT:
            if self.width_px is None or self.height_px is None:
                raise ValueError("Exact mode requires both width_px and height_px.")

            # Aspect ratio check
            if self.aspect_ratio is not None:
                match = re.match(r"^([0-9]+):([0-9]+)$", self.aspect_ratio)
                if match:
                    aw, ah = int(match.group(1)), int(match.group(2))
                    # Check tolerance (ratio equality)
                    diff = abs((self.width_px / self.height_px) - (aw / ah))
                    if diff > 1e-3:
                        raise ValueError(
                            f"Aspect ratio {self.aspect_ratio} contradicts dimensions {self.width_px}x{self.height_px}."
                        )

            # Assert range fields are not present
            range_fields = [
                self.minimum_width_px,
                self.maximum_width_px,
                self.minimum_height_px,
                self.maximum_height_px,
            ]
            if any(x is not None for x in range_fields):
                raise ValueError("Exact mode cannot coexist with range boundaries.")

        elif self.mode == DimensionMode.RANGE:
            if (
                self.minimum_width_px is None
                or self.maximum_width_px is None
                or self.minimum_height_px is None
                or self.maximum_height_px is None
            ):
                raise ValueError(
                    "Range mode requires minimum and maximum width/height values."
                )

            if self.minimum_width_px > self.maximum_width_px:
                raise ValueError("Minimum width cannot exceed maximum width.")
            if self.minimum_height_px > self.maximum_height_px:
                raise ValueError("Minimum height cannot exceed maximum height.")

            if self.preferred_width_px is not None:
                if not (
                    self.minimum_width_px
                    <= self.preferred_width_px
                    <= self.maximum_width_px
                ):
                    raise ValueError(
                        "Preferred width must fall within the min/max range."
                    )
            if self.preferred_height_px is not None:
                if not (
                    self.minimum_height_px
                    <= self.preferred_height_px
                    <= self.maximum_height_px
                ):
                    raise ValueError(
                        "Preferred height must fall within the min/max range."
                    )

        elif self.mode == DimensionMode.UNSPECIFIED:
            if not self.fallback_reason:
                raise ValueError(
                    "Unspecified dimensions mode requires a fallback_reason."
                )
            # ``platform_default_profile`` is deliberately no longer required.
            #
            # It used to be, because the resolver sized an unspecified-dimension
            # output by looking the profile name up in a table of fixed pixel
            # dimensions. That is gone: the output size is now chosen per
            # photograph from the crop's own geometry, so no named default is
            # consulted and demanding one would force every such rule to carry a
            # value nothing reads. The field remains available for recording
            # what a body's guidance implies, but a rule that omits it is
            # complete.

        return self


class FileSizeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    minimum_bytes: Optional[int] = Field(default=None, ge=0)
    maximum_bytes: int = Field(gt=0)
    target_ceiling_ratio: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    safety_margin_bytes: Optional[int] = Field(default=None, ge=0)
    size_unit_as_published: Optional[str] = None
    published_minimum: Optional[float] = None
    published_maximum: Optional[float] = None

    @model_validator(mode="after")
    def validate_file_sizes(self) -> "FileSizeConfig":
        if self.minimum_bytes is not None:
            if self.minimum_bytes > self.maximum_bytes:
                raise ValueError("Minimum file size cannot exceed maximum file size.")
        if self.safety_margin_bytes is not None:
            if self.safety_margin_bytes >= self.maximum_bytes:
                raise ValueError(
                    "Safety margin must not exceed maximum file size limit."
                )
        return self


class FormatsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allowed_formats: List[str] = Field(min_length=1)
    preferred_format: str
    preserve_transparency: bool = False
    strip_metadata: bool = True
    colour_space: Optional[str] = None
    extension_policy: Optional[str] = None

    @model_validator(mode="after")
    def validate_formats(self) -> "FormatsConfig":
        allowed_normalized = [f.lower().strip() for f in self.allowed_formats]
        pref_normalized = self.preferred_format.lower().strip()

        # ``pdf`` is valid for a *deliverable* file specification -- a
        # certificate or a mark sheet is very often required as one -- and never
        # for a photograph. The photograph case is refused by ImageRequirements
        # rather than here, because this same config type serves both and the
        # constraint belongs where the distinction is known.
        valid_formats = {"jpeg", "jpg", "png", "webp", "pdf"}
        for fmt in allowed_normalized:
            if fmt not in valid_formats:
                raise ValueError(
                    f"Format '{fmt}' is not a supported format. Must be one of {valid_formats}."
                )

        if pref_normalized not in allowed_normalized:
            raise ValueError(
                f"Preferred format '{self.preferred_format}' must be in allowed formats."
            )

        if "jpeg" in allowed_normalized or "jpg" in allowed_normalized:
            if self.preserve_transparency and pref_normalized in ["jpeg", "jpg"]:
                raise ValueError("JPEG format does not support transparency.")

        return self


class BackgroundMode(str, Enum):
    EXACT_COLOUR = "exact_colour"
    PLAIN_LIGHT = "plain_light"
    PLAIN_BACKGROUND = "plain_background"
    UNSPECIFIED = "unspecified"


class BackgroundConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: BackgroundMode
    required_colour: Optional[str] = None
    tolerance: Optional[float] = None
    plain_background_required: bool = True
    shadows_allowed: bool = False
    gradient_allowed: bool = False
    fallback_colour: Optional[str] = None
    instructions: Optional[str] = None

    @field_validator("required_colour")
    @classmethod
    def validate_hex_colour(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^#([A-Fa-f0-9]{6})$", v):
                raise ValueError("Hex colour must be in format #RRGGBB.")
        return v

    @model_validator(mode="after")
    def validate_background_mode(self) -> "BackgroundConfig":
        if self.mode == BackgroundMode.EXACT_COLOUR:
            if not self.required_colour:
                raise ValueError("Exact colour mode requires required_colour.")
        return self


class CompositionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    face_coverage_target: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    face_coverage_minimum: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    face_coverage_maximum: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    coverage_is_strict: bool = False
    complete_hair_visible: bool = False
    ears_visible: bool = False
    chin_visible: bool = False
    beard_boundary_visible: bool = False
    face_centred: bool = True
    frontal_pose: bool = True
    eye_visibility: bool = True
    spectacles_policy: Optional[str] = None
    headwear_policy: Optional[str] = None
    expression_policy: Optional[str] = None
    additional_instructions: Optional[str] = None

    crop_profile: Optional[CropProfile] = CropProfile.STANDARD_PASSPORT_PORTRAIT
    ears_policy: Optional[EarsPolicy] = EarsPolicy.UNSPECIFIED

    target_head_height_ratio: Optional[float] = Field(default=None, gt=0.0, le=1.0)
    minimum_head_height_ratio: Optional[float] = Field(default=None, gt=0.0, le=1.0)
    maximum_head_height_ratio: Optional[float] = Field(default=None, gt=0.0, le=1.0)

    target_head_width_ratio: Optional[float] = Field(default=None, gt=0.0, le=1.0)
    minimum_head_width_ratio: Optional[float] = Field(default=None, gt=0.0, le=1.0)
    maximum_head_width_ratio: Optional[float] = Field(default=None, gt=0.0, le=1.0)

    target_top_margin_ratio: Optional[float] = Field(default=None, ge=0.0, lt=1.0)
    minimum_top_margin_ratio: Optional[float] = Field(default=None, ge=0.0, lt=1.0)
    maximum_top_margin_ratio: Optional[float] = Field(default=None, ge=0.0, lt=1.0)

    target_eye_line_ratio: Optional[float] = Field(default=None, ge=0.0, lt=1.0)
    minimum_eye_line_ratio: Optional[float] = Field(default=None, ge=0.0, lt=1.0)
    maximum_eye_line_ratio: Optional[float] = Field(default=None, ge=0.0, lt=1.0)

    maximum_horizontal_center_offset_ratio: Optional[float] = Field(
        default=None, ge=0.0, lt=1.0
    )
    maximum_torso_inclusion_ratio: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    complete_hair_required: Optional[bool] = None
    complete_chin_required: Optional[bool] = None
    complete_beard_boundary_required: Optional[bool] = None

    @model_validator(mode="after")
    def validate_composition(self) -> "CompositionConfig":
        if (
            self.face_coverage_minimum is not None
            and self.face_coverage_maximum is not None
        ):
            if self.face_coverage_minimum > self.face_coverage_maximum:
                raise ValueError("Minimum coverage cannot exceed maximum coverage.")

        # Validate range parameters: minimum <= target <= maximum
        def check_range(
            val_min: float | None,
            val_tgt: float | None,
            val_max: float | None,
            name: str,
        ) -> None:
            if val_min is not None and val_max is not None:
                if val_min > val_max:
                    raise ValueError(f"Minimum {name} cannot exceed maximum {name}.")
            if val_tgt is not None:
                if val_min is not None and val_tgt < val_min:
                    raise ValueError(
                        f"Target {name} cannot be less than minimum {name}."
                    )
                if val_max is not None and val_tgt > val_max:
                    raise ValueError(f"Target {name} cannot exceed maximum {name}.")

        check_range(
            self.minimum_head_height_ratio,
            self.target_head_height_ratio,
            self.maximum_head_height_ratio,
            "head height ratio",
        )
        check_range(
            self.minimum_head_width_ratio,
            self.target_head_width_ratio,
            self.maximum_head_width_ratio,
            "head width ratio",
        )
        check_range(
            self.minimum_top_margin_ratio,
            self.target_top_margin_ratio,
            self.maximum_top_margin_ratio,
            "top margin ratio",
        )
        check_range(
            self.minimum_eye_line_ratio,
            self.target_eye_line_ratio,
            self.maximum_eye_line_ratio,
            "eye line ratio",
        )

        return self


class FilenameMode(str, Enum):
    EXACT = "exact"
    PATTERN = "pattern"
    UNSPECIFIED = "unspecified"


class FilenameConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: FilenameMode
    exact_filename: Optional[str] = None
    pattern: Optional[str] = None
    allowed_characters: Optional[str] = None
    case_sensitive: bool = True
    extension_required: bool = True
    fallback_basename: Optional[str] = None
    collision_policy: Optional[str] = None
    instructions: Optional[str] = None

    @model_validator(mode="after")
    def validate_filenames(self) -> "FilenameConfig":
        if self.mode == FilenameMode.EXACT:
            if not self.exact_filename:
                raise ValueError("Exact filename mode requires exact_filename.")
            name = self.exact_filename
        elif self.mode == FilenameMode.PATTERN:
            if not self.pattern:
                raise ValueError("Pattern filename mode requires pattern regex.")
            name = self.pattern
        else:
            name = ""

        if name:
            if "/" in name or "\\" in name:
                raise ValueError(
                    "Path separators are prohibited in filename properties."
                )
            if ".." in name:
                raise ValueError("Path traversal sequences are prohibited.")

        return self


class ProcessingSupportStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    NOT_YET_SUPPORTED = "not_yet_supported"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class ExceptionalInstructions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    printed_name: bool = False
    printed_date: bool = False
    signature_inclusion: bool = False
    black_and_white_restriction: bool = False
    recent_photo_requirement: bool = False
    spectacles_restriction: bool = False
    headwear_restriction: bool = False
    portal_specific_note: Optional[str] = None
    processing_support_status: ProcessingSupportStatus
    unsupported_requirement_reasons: List[str] = Field(default_factory=list)


class AppearancePolicyValue(str, Enum):
    PERMITTED = "permitted"
    PROHIBITED = "prohibited"
    CONDITIONAL = "conditional"


class AppearancePolicy(BaseModel):
    """A three-state candidate-appearance rule (DEC-042).

    ``CONDITIONAL`` exists because conducting bodies publish rules a boolean
    cannot express -- "prohibited except for religious reasons", "permitted
    only if regularly worn".  Forcing those into permitted/prohibited would
    assert something the body did not say, and those are exactly the cases
    with the highest cost of error: religious head coverings and prescription
    eyewear.
    """

    model_config = ConfigDict(extra="forbid")
    policy: AppearancePolicyValue
    condition: Optional[str] = None
    source_wording: Optional[str] = None

    @model_validator(mode="after")
    def validate_conditional_has_condition(self) -> "AppearancePolicy":
        if self.policy == AppearancePolicyValue.CONDITIONAL and not self.condition:
            raise ValueError(
                "A 'conditional' appearance policy must state its condition; "
                "otherwise it carries no more information than an omitted rule."
            )
        return self


class FaceCoverageBasis(str, Enum):
    FACE_BOX_AREA = "face_box_area"
    FACE_HEIGHT = "face_height"
    HEAD_HEIGHT = "head_height"
    UNSPECIFIED = "unspecified"


class ImprintPolicyValue(str, Enum):
    REQUIRED = "required"
    PROHIBITED = "prohibited"
    UNSPECIFIED = "unspecified"


class ImprintField(str, Enum):
    CANDIDATE_NAME = "candidate_name"
    PHOTOGRAPH_DATE = "photograph_date"


class ImprintPosition(str, Enum):
    BOTTOM = "bottom"
    BELOW_IMAGE = "below_image"
    UNSPECIFIED = "unspecified"


class ImprintConfig(BaseModel):
    """Text a body requires printed on, or forbids from, the photograph.

    Verified conflict: TNPSC, Kerala PSC and CBSE require a name and/or date;
    Railways prohibits any signature, name, date or mark on the photograph.
    """

    model_config = ConfigDict(extra="forbid")
    policy: ImprintPolicyValue = ImprintPolicyValue.UNSPECIFIED
    fields: List[ImprintField] = Field(default_factory=list)
    position: ImprintPosition = ImprintPosition.UNSPECIFIED
    source_wording: Optional[str] = None

    @model_validator(mode="after")
    def validate_required_names_fields(self) -> "ImprintConfig":
        if self.policy == ImprintPolicyValue.REQUIRED and not self.fields:
            raise ValueError(
                "A required imprint must name the fields to print; the engine "
                "cannot infer whether the body wants the name, the date or both."
            )
        return self


class ProhibitedProvenance(str, Enum):
    SELFIE = "selfie"
    MOBILE_PHOTOGRAPH = "mobile_photograph"
    SCANNED_PRINT = "scanned_print"
    PHOTOGRAPH_OF_A_PHOTOGRAPH = "photograph_of_a_photograph"
    GROUP_PHOTOGRAPH_CROP = "group_photograph_crop"
    DIGITALLY_ALTERED = "digitally_altered"
    WATERMARKED = "watermarked"
    COMPUTER_GENERATED = "computer_generated"


class AppearanceConfig(BaseModel):
    """Per-exam candidate-appearance rules (DEC-042).

    Every field is optional and absence means the conducting body did not
    specify it.  Absence must never be read as permission or prohibition --
    that is the no-silent-assumptions principle applied to appearance.

    These cannot be platform constants: across 48 examinations the verified
    rules contradict each other on background colour, spectacles, smiling,
    printed name/date, colour versus monochrome, and face occupancy.
    """

    model_config = ConfigDict(extra="forbid")
    spectacles: Optional[AppearancePolicy] = None
    headwear: Optional[AppearancePolicy] = None
    smile: Optional[AppearancePolicy] = None
    facial_hair: Optional[AppearancePolicy] = None
    face_mask: Optional[AppearancePolicy] = None
    monochrome_accepted: Optional[bool] = None
    # The published percentages (50, 60-70, ~75, 80) are not comparable across
    # bodies because the bodies do not agree on what is being measured.
    face_coverage_basis: Optional[FaceCoverageBasis] = None
    # Not checkable from a submitted image, so these drive guidance text only,
    # never a warning and never a block (DEC-041).
    live_capture_required: Optional[bool] = None
    recency_maximum_days: Optional[int] = Field(default=None, ge=1)
    prohibited_provenance: List[ProhibitedProvenance] = Field(default_factory=list)
    imprint: Optional[ImprintConfig] = None
    attestation_required: Optional[bool] = None
    source_wording: Optional[str] = None


class ImageRequirements(BaseModel):
    """The photograph specification. Always an image, never a document."""

    model_config = ConfigDict(extra="forbid")
    dimensions: DimensionsConfig
    file_size: FileSizeConfig
    formats: FormatsConfig
    background: BackgroundConfig
    composition: CompositionConfig
    # Optional so every existing rule record stays valid; an absent block means
    # no appearance rule was verified for that exam, not that anything is
    # permitted.
    appearance: Optional[AppearanceConfig] = None
    filename: FilenameConfig
    exceptional_instructions: ExceptionalInstructions

    @model_validator(mode="after")
    def validate_photograph_is_an_image(self) -> "ImageRequirements":
        if "pdf" in {f.lower().strip() for f in self.formats.allowed_formats}:
            raise ValueError(
                "A candidate photograph cannot be a PDF. The format is valid "
                "for document deliverables, which use file_spec rather than "
                "image_requirements."
            )
        return self


class RequirementType(str, Enum):
    """What a required item *is*.

    How it is provided is :class:`SubmissionMethod`, and the two are
    independent.  A live portal photograph is a ``PHOTOGRAPH`` submitted by
    ``OFFICIAL_LIVE_CAPTURE``, not a type of its own -- folding the method into
    the type would make "how many photographs does this exam want" unanswerable.
    """

    PHOTOGRAPH = "photograph"
    SIGNATURE = "signature"
    THUMB_IMPRESSION = "thumb_impression"
    HANDWRITTEN_DECLARATION = "handwritten_declaration"
    CERTIFICATE_SCAN = "certificate_scan"
    IDENTITY_DOCUMENT = "identity_document"
    PORTAL_DECLARATION = "portal_declaration"
    OTHER = "other"


class SubmissionMethod(str, Enum):
    """How the candidate provides an item, as classified by the research.

    This decides whether the platform can act at all.  The first three produce
    a file the platform can prepare; the last four happen inside the official
    portal or at a physical stage, and can only be explained.
    """

    FILE_UPLOAD = "file_upload"
    HANDWRITTEN_THEN_UPLOADED = "handwritten_then_uploaded"
    DOCUMENT_SCAN_UPLOAD = "document_scan_upload"
    OFFICIAL_LIVE_CAPTURE = "official_live_capture"
    EXTERNAL_IDENTITY_VERIFICATION = "external_identity_verification"
    TYPED_OR_SELECTED_DECLARATION = "typed_or_selected_declaration"
    PHYSICAL_STAGE_REQUIREMENT = "physical_stage_requirement"


#: Methods that produce a file the platform can prepare.  Everything else is
#: completed by the candidate elsewhere.
_DELIVERABLE_METHODS = frozenset(
    {
        SubmissionMethod.FILE_UPLOAD,
        SubmissionMethod.HANDWRITTEN_THEN_UPLOADED,
        SubmissionMethod.DOCUMENT_SCAN_UPLOAD,
    }
)


class RequirementStatus(str, Enum):
    MANDATORY = "mandatory"
    CONDITIONAL = "conditional"
    OPTIONAL = "optional"
    PORTAL_DEPENDENT = "portal_dependent"


class PlatformSupport(str, Enum):
    """What the platform does for one required item.

    Kept separate from :class:`ProcessingSupportStatus`, which answers a
    different question -- how completely the photograph pipeline satisfies a
    photograph rule.  One scale for two questions would force every consumer to
    know which subset of values applied to it.

    ``GUIDANCE_ONLY`` and ``PHYSICAL_STAGE`` exist to keep the boundary between
    an ordinary upload and an authority-controlled step visible in the data
    rather than in prose.  Nothing carrying either may be sold, bundled or
    counted as an output.
    """

    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    GUIDANCE_ONLY = "guidance_only"
    PHYSICAL_STAGE = "physical_stage"
    NOT_YET_SUPPORTED = "not_yet_supported"


class DeliverableFileSpec(BaseModel):
    """The output specification for one non-photograph deliverable.

    Every block is optional because the evidence is routinely partial -- a body
    publishes a signature's file size and nothing else -- and a block the
    research did not establish is omitted rather than defaulted, per the same
    rule that governs photograph fields.
    """

    model_config = ConfigDict(extra="forbid")
    dimensions: Optional[DimensionsConfig] = None
    file_size: Optional[FileSizeConfig] = None
    formats: Optional[FormatsConfig] = None
    filename: Optional[FilenameConfig] = None

    @property
    def is_actionable(self) -> bool:
        """True when there is enough here to prepare a file against.

        Dimensions alone are not enough: without a format the engine cannot
        decide what to encode, and without a size ceiling it cannot decide how
        hard to compress.
        """
        return self.file_size is not None or self.formats is not None


class ExamRequirement(BaseModel):
    """One item an examination requires during application.

    The list an exam carries is the *complete* inventory, including items the
    platform cannot produce.  Those are recorded with the support state that
    says so rather than omitted, because an omitted requirement reads as "this
    examination does not ask for it" -- which for a live-capture or
    physical-stage item is false, and is exactly the confusion that makes a
    candidate think the platform completed a step it never touched.
    """

    model_config = ConfigDict(extra="forbid")
    requirement_id: str = Field(pattern=r"^[a-z0-9_]+$")
    requirement_name: str = Field(min_length=1)
    requirement_type: RequirementType
    submission_method: SubmissionMethod
    requirement_status: RequirementStatus
    platform_support: PlatformSupport
    file_spec: Optional[DeliverableFileSpec] = None
    applicability: Optional[str] = None
    content_instructions: Optional[str] = None
    rejection_conditions: List[str] = Field(default_factory=list)
    evidence_status: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_requirement(self) -> "ExamRequirement":
        # The photograph's specification is ``image_requirements``. Allowing a
        # second copy here would create two places a photograph rule can live,
        # and the pipeline would have to pick one.
        if self.requirement_type == RequirementType.PHOTOGRAPH and self.file_spec:
            raise ValueError(
                "A photograph requirement must not carry a file_spec; its "
                "specification is the rule's image_requirements block."
            )

        # A method the platform cannot execute cannot be a supported output.
        # This is the structural form of the product rule that ordinary uploads
        # and authority-controlled steps must never be presented alike.
        if self.submission_method not in _DELIVERABLE_METHODS:
            if self.platform_support in (
                PlatformSupport.SUPPORTED,
                PlatformSupport.PARTIALLY_SUPPORTED,
            ):
                raise ValueError(
                    f"Submission method '{self.submission_method.value}' is "
                    "completed by the candidate outside the platform, so it "
                    "cannot be marked supported. Use 'guidance_only' or "
                    "'physical_stage'."
                )

        if self.submission_method == SubmissionMethod.PHYSICAL_STAGE_REQUIREMENT:
            if self.platform_support != PlatformSupport.PHYSICAL_STAGE:
                raise ValueError(
                    "A physical-stage requirement must carry platform_support "
                    "'physical_stage'."
                )
        elif self.platform_support == PlatformSupport.PHYSICAL_STAGE:
            raise ValueError(
                "platform_support 'physical_stage' applies only to a "
                "physical_stage_requirement submission method."
            )

        # "Supported" is a promise that the platform can produce this file. For
        # anything but the photograph, that promise needs a specification
        # behind it.
        if (
            self.platform_support == PlatformSupport.SUPPORTED
            and self.requirement_type != RequirementType.PHOTOGRAPH
        ):
            if self.file_spec is None or not self.file_spec.is_actionable:
                raise ValueError(
                    f"Requirement '{self.requirement_id}' is marked supported "
                    "but carries no file size or format to prepare against. "
                    "Mark it not_yet_supported until a specification exists."
                )

        # A conditional requirement that does not say when it applies carries no
        # more information than an omitted one -- the same reasoning as the
        # conditional appearance policies in DEC-042.
        if self.requirement_status == RequirementStatus.CONDITIONAL:
            if not self.applicability:
                raise ValueError(
                    "A conditional requirement must state its applicability."
                )

        return self


class VerificationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verification_status: RuleStatus
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    review_due_at: Optional[datetime] = None


class EffectivePeriod(BaseModel):
    model_config = ConfigDict(extra="forbid")
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None

    @field_validator("effective_from", "effective_until")
    @classmethod
    def validate_date_string(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
                raise ValueError("Date must be in YYYY-MM-DD format.")
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date value.") from None

        return v

    @model_validator(mode="after")
    def validate_period(self) -> "EffectivePeriod":
        if self.effective_from and self.effective_until:
            if self.effective_until < self.effective_from:
                raise ValueError(
                    "Effective end period cannot be before starting period."
                )
        return self


class Supersession(BaseModel):
    model_config = ConfigDict(extra="forbid")
    supersedes_rule_id: Optional[str] = None
    superseded_by_rule_id: Optional[str] = None
    change_summary: Optional[str] = None


def _unwrap_annotation(field_type: Any) -> Any:
    """Reduce ``Optional``/list/dict wrappers to the type they contain.

    Applied repeatedly rather than once, because annotations nest: a field
    typed ``Optional[List[ExamRequirement]]`` has to shed both the ``Union``
    and the ``list`` before the element model is reachable.  Handling only a
    single layer silently reported every path through such a field as invalid.
    """
    while True:
        origin = get_origin(field_type)
        if origin is Union:
            named = [arg for arg in get_args(field_type) if arg is not type(None)]
            if not named:
                return field_type
            field_type = named[0]
        elif origin in (list, set, frozenset, tuple):
            args = get_args(field_type)
            if not args:
                return field_type
            field_type = args[0]
        elif origin is dict:
            args = get_args(field_type)
            if len(args) < 2:
                return field_type
            field_type = args[1]
        else:
            return field_type


def is_valid_field_path(model_cls: Any, path: str) -> bool:
    parts = path.split(".")
    current_cls = model_cls
    for part in parts:
        part = re.sub(r"\[\d+\]", "", part)
        if not hasattr(current_cls, "model_fields"):
            return False
        if part not in current_cls.model_fields:
            return False
        current_cls = _unwrap_annotation(current_cls.model_fields[part].annotation)
    return True


class ExamRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str
    rule_id: str
    rule_version: str
    status: RuleStatus
    exam: ExamIdentity
    source_evidence: List[SourceEvidence] = Field(min_length=1)
    image_requirements: ImageRequirements
    # Optional so every record written before the inventory existed stays valid.
    # Absent means the deliverable research has not been done for this exam --
    # never that the photograph is the only thing the exam asks for.
    requirements: Optional[List[ExamRequirement]] = Field(default=None, min_length=1)
    provenance: Dict[str, ValueProvenance]
    verification: VerificationConfig
    effective_period: Optional[EffectivePeriod] = None
    supersession: Optional[Supersession] = None
    notes: Optional[str] = None
    fictional_example: bool

    @model_validator(mode="after")
    def validate_cross_field_rules(self) -> "ExamRule":
        # Verification status match check
        if self.status != self.verification.verification_status:
            raise ValueError(
                f"Top-level status ({self.status}) conflicts with verification status ({self.verification.verification_status})."
            )

        # Verification requirements
        if self.status in [RuleStatus.VERIFIED, RuleStatus.VERIFIED_WITH_AMBIGUITY]:
            if not self.source_evidence:
                raise ValueError("Verified rules require at least one source evidence.")
            # Verify evidence contains official sources
            has_official = any(ev.official_source for ev in self.source_evidence)
            if not has_official:
                raise ValueError(
                    "Verified rules must be supported by at least one official source (official_source must be true)."
                )
            if self.fictional_example:
                # Fictional example cannot be officially verified
                raise ValueError(
                    "Fictional examples cannot have officially verified status."
                )

        # Check self-supersession
        if self.supersession:
            if self.supersession.supersedes_rule_id == self.rule_id:
                raise ValueError("A rule cannot supersede itself.")

        # Check supersession lifecycle states
        if self.status == RuleStatus.SUPERSEDED:
            if not self.supersession or not self.supersession.superseded_by_rule_id:
                raise ValueError(
                    "A superseded rule must specify the replacing rule ID in superseded_by_rule_id."
                )
        if self.supersession and self.supersession.superseded_by_rule_id:
            if self.status != RuleStatus.SUPERSEDED:
                raise ValueError(
                    "A rule specifying superseded_by_rule_id must have status superseded."
                )

        # Validate provenance keys
        for path in self.provenance.keys():
            if not is_valid_field_path(ExamRule, path):
                raise ValueError(
                    f"Provenance path '{path}' does not map to any valid field path in the rule configuration."
                )

        # An interim default is a placeholder for a figure no source published,
        # and a photograph rule resting on one has not been verified whatever
        # else in it has. This is the enforcement half of the interim_default
        # provenance type.
        #
        # Scoped to ``image_requirements`` on purpose. ``status`` has always
        # been a statement about the photograph specification -- it is what the
        # catalogue tiers, the gap register and every current consumer read it
        # as -- so a placeholder in a signature's file size must not demote the
        # exam's photograph rule to provisional. A requirement's own
        # specification quality is carried by its own provenance entry, which is
        # equally findable. When requirements grow a per-item status of their
        # own, this scoping is the thing to revisit.
        if self.status in (RuleStatus.VERIFIED, RuleStatus.VERIFIED_WITH_AMBIGUITY):
            interim = sorted(
                path
                for path, entry in self.provenance.items()
                if entry.type == ProvenanceType.INTERIM_DEFAULT
                and path.startswith("image_requirements")
            )
            if interim:
                raise ValueError(
                    f"Status '{self.status.value}' conflicts with interim "
                    f"placeholder values in the photograph specification at "
                    f"{', '.join(interim)}. A photograph rule carrying an "
                    "interim default is provisional at best until the published "
                    "figure replaces it."
                )

        if self.requirements is not None:
            seen: set[str] = set()
            for requirement in self.requirements:
                if requirement.requirement_id in seen:
                    raise ValueError(
                        f"Duplicate requirement_id '{requirement.requirement_id}'. "
                        "Orders and packages reference it, so it must be unique "
                        "within a rule."
                    )
                seen.add(requirement.requirement_id)

            # The rule carries exactly one photograph specification, so at most
            # one requirement can be the thing that specification describes.
            # Live-capture photographs are unbounded: an exam may require an
            # uploaded photograph and a portal-captured one.
            uploaded_photographs = [
                requirement
                for requirement in self.requirements
                if requirement.requirement_type == RequirementType.PHOTOGRAPH
                and requirement.submission_method in _DELIVERABLE_METHODS
            ]
            if len(uploaded_photographs) > 1:
                raise ValueError(
                    "More than one uploaded photograph requirement, but a rule "
                    "carries only one image_requirements block to specify them "
                    "with."
                )

        return self
