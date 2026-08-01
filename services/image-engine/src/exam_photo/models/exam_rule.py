import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from exam_photo.models.provenance import ValueProvenance
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
            if not self.platform_default_profile:
                raise ValueError(
                    "Unspecified dimensions mode requires platform_default_profile."
                )

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

        valid_formats = {"jpeg", "jpg", "png", "webp"}
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


class ImageRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dimensions: DimensionsConfig
    file_size: FileSizeConfig
    formats: FormatsConfig
    background: BackgroundConfig
    composition: CompositionConfig
    filename: FilenameConfig
    exceptional_instructions: ExceptionalInstructions


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


def is_valid_field_path(model_cls: Any, path: str) -> bool:
    parts = path.split(".")
    current_cls = model_cls
    for part in parts:
        part = re.sub(r"\[\d+\]", "", part)
        if not hasattr(current_cls, "model_fields"):
            return False
        if part not in current_cls.model_fields:
            return False
        field_info = current_cls.model_fields[part]
        field_type = field_info.annotation

        from typing import Union, get_args, get_origin

        origin = get_origin(field_type)
        if origin is Union:
            args = get_args(field_type)
            next_cls = None
            for arg in args:
                if arg is not type(None) and hasattr(arg, "model_fields"):
                    next_cls = arg
                    break
            if next_cls:
                current_cls = next_cls
            else:
                current_cls = args[0]
        elif origin is list:
            args = get_args(field_type)
            if args and hasattr(args[0], "model_fields"):
                current_cls = args[0]
            else:
                current_cls = args[0] if args else Any
        elif origin is dict:
            args = get_args(field_type)
            if len(args) > 1 and hasattr(args[1], "model_fields"):
                current_cls = args[1]
            else:
                current_cls = args[1] if len(args) > 1 else Any
        else:
            current_cls = field_type
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

        return self
