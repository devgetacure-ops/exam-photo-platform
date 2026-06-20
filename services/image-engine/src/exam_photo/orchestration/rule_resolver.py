from typing import Any, Optional

from pydantic import BaseModel

from exam_photo.models.exam_rule import BackgroundMode, DimensionMode, ExamRule
from exam_photo.providers.background_composition import BackgroundCompositionConfig
from exam_photo.providers.crop_planning import CropConfig, CropModeBConfig
from exam_photo.providers.output_compression import (
    CompressionFormat,
    OutputCompressionConfig,
)
from exam_photo.providers.output_preparation import OutputPreparationConfig, ResizeMode


class RuleResolutionError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class ResolvedProcessingPlan(BaseModel):
    crop_mode: str  # "a" or "b"
    crop_config: Any
    background_config: Optional[BackgroundCompositionConfig] = None
    output_preparation_config: OutputPreparationConfig
    compression_config: OutputCompressionConfig
    target_filename: str


def resolve_rule(
    rule: ExamRule,
    allow_padding: bool = False,
    allow_quality_below_minimum: bool = False,
    allow_oversize_output: bool = False,
) -> ResolvedProcessingPlan:
    # 1. Resolve format compatibility
    pref_format = rule.image_requirements.formats.preferred_format.lower().strip()
    if pref_format not in ("jpeg", "jpg"):
        raise RuleResolutionError(
            "PIPELINE_FINAL_FORMAT_INVALID",
            f"Failing resolution: Preferred format '{pref_format}' is not supported. Milestone 14 only supports JPEG/JPG.",
        )

    allowed = [
        f.lower().strip() for f in rule.image_requirements.formats.allowed_formats
    ]
    if "jpeg" not in allowed and "jpg" not in allowed:
        raise RuleResolutionError(
            "PIPELINE_FINAL_FORMAT_INVALID",
            "Failing resolution: Exam rule allowed formats do not include JPEG or JPG.",
        )

    # Transparency conflict check
    if rule.image_requirements.formats.preserve_transparency:
        raise RuleResolutionError(
            "PIPELINE_FINAL_FORMAT_INVALID",
            "Failing resolution: Transparency preservation is requested, which is not supported by JPEG format.",
        )

    # 2. Resolve Crop Mode and Config
    dim = rule.image_requirements.dimensions
    crop_config: CropConfig | CropModeBConfig
    if dim.mode == DimensionMode.EXACT:
        crop_mode = "a"
        if dim.width_px is None or dim.height_px is None:
            raise RuleResolutionError(
                "PIPELINE_CROP_MODE_UNSUPPORTED",
                "Exact dimension mode is missing width_px or height_px.",
            )
        crop_config = CropConfig(
            target_width=dim.width_px,
            target_height=dim.height_px,
            target_aspect_ratio=dim.width_px / dim.height_px,
        )
    elif dim.mode == DimensionMode.RANGE:
        crop_mode = "b"
        if (
            dim.minimum_width_px is None
            or dim.maximum_width_px is None
            or dim.minimum_height_px is None
            or dim.maximum_height_px is None
        ):
            raise RuleResolutionError(
                "PIPELINE_CROP_MODE_UNSUPPORTED",
                "Range dimension mode is missing range boundary pixels.",
            )

        min_aspect = dim.minimum_width_px / dim.maximum_height_px
        max_aspect = dim.maximum_width_px / dim.minimum_height_px

        crop_config = CropModeBConfig(
            min_aspect_ratio=min_aspect,
            max_aspect_ratio=max_aspect,
            min_head_height_ratio=0.30,
            max_head_height_ratio=0.85,
            allow_padding=allow_padding,
        )
    else:
        raise RuleResolutionError(
            "PIPELINE_CROP_MODE_UNSUPPORTED",
            f"Failing resolution: Dimension mode '{dim.mode.value}' is not supported by Crop Planners.",
        )

    # 3. Resolve Background Config
    bg = rule.image_requirements.background
    if bg.mode == BackgroundMode.EXACT_COLOUR:
        if not bg.required_colour:
            raise RuleResolutionError(
                "PIPELINE_BACKGROUND_FAILED",
                "Failing resolution: Exact background colour mode requires required_colour hex code.",
            )
        target_color = bg.required_colour
    elif bg.mode in (BackgroundMode.PLAIN_LIGHT, BackgroundMode.PLAIN_BACKGROUND):
        target_color = bg.fallback_colour or "#FFFFFF"
    else:
        raise RuleResolutionError(
            "PIPELINE_BACKGROUND_FAILED",
            f"Failing resolution: Background mode '{bg.mode.value}' is not supported.",
        )

    background_config = BackgroundCompositionConfig(
        target_colour_hex=target_color,
        allow_transparent_output=False,
        allow_subject_clipping=True,
    )

    # 4. Resolve Output Preparation Config
    if dim.mode == DimensionMode.EXACT:
        prep_config = OutputPreparationConfig(
            resize_mode=ResizeMode.EXACT,
            target_width=dim.width_px,
            target_height=dim.height_px,
            min_width=dim.width_px,
            max_width=dim.width_px,
            min_height=dim.height_px,
            max_height=dim.height_px,
        )
    else:
        prep_config = OutputPreparationConfig(
            resize_mode=ResizeMode.RANGE_SELECT,
            min_width=dim.minimum_width_px,
            max_width=dim.maximum_width_px,
            min_height=dim.minimum_height_px,
            max_height=dim.maximum_height_px,
            preferred_width=dim.preferred_width_px or 300,
            preferred_height=dim.preferred_height_px or 400,
        )

    # 5. Resolve Output Compression Config
    fs = rule.image_requirements.file_size
    comp_config = OutputCompressionConfig(
        target_format=CompressionFormat.JPEG,
        maximum_bytes=fs.maximum_bytes,
        minimum_bytes=fs.minimum_bytes,
        target_ceiling_ratio=fs.target_ceiling_ratio or 0.96,
        safety_margin_bytes=fs.safety_margin_bytes or 512,
        strip_metadata=rule.image_requirements.formats.strip_metadata,
        allow_quality_below_minimum=allow_quality_below_minimum,
        allow_oversize_output=allow_oversize_output,
    )

    # 6. Resolve safe output filename base
    fn = rule.image_requirements.filename
    if fn.mode == "exact" and fn.exact_filename:
        # Check traversal and path separators
        if (
            "/" in fn.exact_filename
            or "\\" in fn.exact_filename
            or ".." in fn.exact_filename
        ):
            raise RuleResolutionError(
                "PIPELINE_FILENAME_INVALID",
                "Failing resolution: exact_filename contains path traversal or separators.",
            )
        target_filename = fn.exact_filename
    elif fn.mode == "pattern" and fn.pattern:
        if "/" in fn.pattern or "\\" in fn.pattern or ".." in fn.pattern:
            raise RuleResolutionError(
                "PIPELINE_FILENAME_INVALID",
                "Failing resolution: pattern contains path traversal or separators.",
            )
        target_filename = fn.fallback_basename or "exam_photo"
    else:
        target_filename = fn.fallback_basename or "exam_photo"

    return ResolvedProcessingPlan(
        crop_mode=crop_mode,
        crop_config=crop_config,
        background_config=background_config,
        output_preparation_config=prep_config,
        compression_config=comp_config,
        target_filename=target_filename,
    )
