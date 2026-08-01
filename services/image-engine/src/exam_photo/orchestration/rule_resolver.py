from typing import Any, Optional

from pydantic import BaseModel

from exam_photo.models.exam_rule import BackgroundMode, DimensionMode, ExamRule
from exam_photo.providers.background_composition import BackgroundCompositionConfig
from exam_photo.providers.crop_planning import (
    CropConfig,
    CropModeBConfig,
    CropProfile,
)
from exam_photo.providers.output_compression import (
    CompressionFormat,
    OutputCompressionConfig,
)
from exam_photo.providers.output_preparation import OutputPreparationConfig, ResizeMode

PROFILE_DEFAULTS = {
    CropProfile.STANDARD_PASSPORT_PORTRAIT: {
        "target_head_height_ratio": 0.60,
        "minimum_head_height_ratio": 0.50,
        "maximum_head_height_ratio": 0.70,
        "target_top_margin_ratio": 0.10,
        "minimum_top_margin_ratio": 0.06,
        "maximum_top_margin_ratio": 0.15,
        "target_eye_line_ratio": 0.44,
        "minimum_eye_line_ratio": 0.40,
        "maximum_eye_line_ratio": 0.48,
        "maximum_horizontal_center_offset_ratio": 0.05,
        "maximum_torso_inclusion_ratio": 0.35,
    },
    # Calibrated against 60 reference exam photos across six exam size classes.
    # Ratios are crown-to-chin fractions of the output frame; bounds track the
    # p10/p90 of the reference distribution so ordinary variation stays valid.
    #   head height  mean 0.840  p10 0.768  p90 0.900
    #   top margin   mean 0.048  p10 0.027  p90 0.075
    #   eye line     mean 0.486  p10 0.452  p90 0.525
    #   below chin   mean 0.112
    CropProfile.TIGHT_EXAM_PORTRAIT: {
        # 0.75 is a hard floor: exams publish face coverage as a minimum, so
        # falling under it fails outright.  Tighter is better, so the target
        # sits above the reference mean (0.840) rather than on it, and the
        # ceiling only guards against a crop so tight it would clip.
        "target_head_height_ratio": 0.86,
        "minimum_head_height_ratio": 0.75,
        "maximum_head_height_ratio": 0.93,
        "target_top_margin_ratio": 0.05,
        "minimum_top_margin_ratio": 0.02,
        "maximum_top_margin_ratio": 0.10,
        "target_eye_line_ratio": 0.487,
        "minimum_eye_line_ratio": 0.43,
        "maximum_eye_line_ratio": 0.54,
        "maximum_horizontal_center_offset_ratio": 0.06,
        "maximum_torso_inclusion_ratio": 0.20,
        # Reference photos routinely let hair reach or leave the frame edge
        # (head silhouette touches the left edge in 31/60 and the right edge in
        # 44/60), so side margins are near zero and a 0.995 foreground-retention
        # bar is unreachable.  Face containment and head coverage remain the
        # hard guarantees; these bound how much hair may leave the frame.
        "minimum_side_margin_ratio": 0.01,
        "minimum_bottom_margin_ratio": 0.05,
        # Only a catastrophe guard: face containment and full retention of the
        # mandatory crown-to-chin head box are the real guarantees.  The seven
        # subjects that score lowest here (long or voluminous hair) have
        # reference outputs whose head silhouette spans ~99.5% of frame width
        # and touches both edges, so heavy hair loss is correct, not a defect.
        "mask_preservation_threshold": 0.75,
        # At the reference head size the detector face box centres at ~0.62 of
        # frame height (chin sits at ~0.87, face box spans ~0.52). The 0.44
        # passport value would flag every correctly composed tight crop.
        "preferred_face_center_y_ratio": 0.62,
    },
    CropProfile.RELAXED_IDENTITY_PORTRAIT: {
        "target_head_height_ratio": 0.40,
        "minimum_head_height_ratio": 0.30,
        "maximum_head_height_ratio": 0.55,
        "target_top_margin_ratio": 0.15,
        "minimum_top_margin_ratio": 0.10,
        "maximum_top_margin_ratio": 0.20,
        "target_eye_line_ratio": 0.44,
        "minimum_eye_line_ratio": 0.40,
        "maximum_eye_line_ratio": 0.48,
        "maximum_horizontal_center_offset_ratio": 0.05,
        "maximum_torso_inclusion_ratio": 0.50,
    },
    CropProfile.CUSTOM: {
        "target_head_height_ratio": 0.60,
        "minimum_head_height_ratio": 0.50,
        "maximum_head_height_ratio": 0.70,
        "target_top_margin_ratio": 0.10,
        "minimum_top_margin_ratio": 0.06,
        "maximum_top_margin_ratio": 0.15,
        "target_eye_line_ratio": 0.44,
        "minimum_eye_line_ratio": 0.40,
        "maximum_eye_line_ratio": 0.48,
        "maximum_horizontal_center_offset_ratio": 0.05,
        "maximum_torso_inclusion_ratio": 0.35,
    },
}

PLATFORM_DEFAULT_DIMENSIONS = {
    "standard_passport_350_450": (350, 450),
    "tight_exam_portrait_300_400": (300, 400),
}


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
    allow_subject_clipping: bool = False,
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
    comp = rule.image_requirements.composition

    def ratio_from_percent(value: float | None) -> float | None:
        if value is None:
            return None
        return value / 100.0

    def resolve_composition_ratio(
        field_name: str,
        coverage_value: float | None,
        defaults: dict[str, Any],
    ) -> Any:
        """Resolve a head-geometry ratio: explicit rule value, else profile default.

        ``face_coverage_*`` is deliberately NOT used as a source here.  Face
        coverage is a percentage-of-frame diagnostic (AGENTS.md: "an expected
        result of correct natural cropping and a diagnostic indicator, not a
        rigid mathematical rejection threshold"), whereas
        ``*_head_height_ratio`` is a crown-to-chin fraction of frame height.
        They are different quantities: over the benchmark set a correctly
        composed photo measures 0.84 head height but only 0.29 face area and
        0.58 face height.  Treating "77% coverage" as "0.77 head height" both
        mis-scales the crop and turns a diagnostic into a hard reject bound.
        ``coverage_value`` is retained in the signature for call-site clarity.
        """
        explicit = getattr(comp, field_name, None)
        if explicit is not None:
            return explicit
        return defaults.get(field_name)

    def resolve_mode_b_ratio(field_name: str, hard_default: float) -> float:
        """Resolve a Crop Mode B head ratio: explicit rule value, else its own default.

        Mode B's planner still measures head height against the preservation
        box, whereas the Mode A profile ratios in ``PROFILE_DEFAULTS`` are
        crown-to-chin fractions (see DEC-029).  The two are not interchangeable
        -- the preservation box runs ~1.14x taller than the real head -- so the
        Mode A numbers must not leak in here.  Mode B keeps the calibration
        documented on ``CropModeBConfig`` until it has its own reference set.
        """
        explicit = getattr(comp, field_name, None)
        return hard_default if explicit is None else float(explicit)

    def resolve_platform_dimensions(profile_name: str | None) -> tuple[int, int]:
        if profile_name and profile_name in PLATFORM_DEFAULT_DIMENSIONS:
            return PLATFORM_DEFAULT_DIMENSIONS[profile_name]
        return PLATFORM_DEFAULT_DIMENSIONS["tight_exam_portrait_300_400"]

    if dim.mode == DimensionMode.EXACT:
        crop_mode = "a"
        if dim.width_px is None or dim.height_px is None:
            raise RuleResolutionError(
                "PIPELINE_CROP_MODE_UNSUPPORTED",
                "Exact dimension mode is missing width_px or height_px.",
            )
        # Resolve Composition Ratio defaults from presets
        profile = comp.crop_profile or CropProfile.STANDARD_PASSPORT_PORTRAIT
        defaults = PROFILE_DEFAULTS.get(
            profile, PROFILE_DEFAULTS[CropProfile.STANDARD_PASSPORT_PORTRAIT]
        )

        def resolve_margin(field_name: str, hard_default: float) -> float:
            """Rule value, else crop-profile default, else the CropConfig default."""
            val = getattr(comp, field_name, None)
            if val is None:
                val = defaults.get(field_name)
            return hard_default if val is None else float(val)

        def resolve_field(field_name: str) -> Any:
            val = getattr(comp, field_name, None)
            if val is None:
                return defaults.get(field_name)
            return val

        target_head_height = resolve_composition_ratio(
            "target_head_height_ratio",
            comp.face_coverage_target,
            defaults,
        )
        min_head_height = resolve_composition_ratio(
            "minimum_head_height_ratio",
            comp.face_coverage_minimum,
            defaults,
        )
        max_head_height = resolve_composition_ratio(
            "maximum_head_height_ratio",
            comp.face_coverage_maximum,
            defaults,
        )

        target_head_width = resolve_field("target_head_width_ratio")
        min_head_width = resolve_field("minimum_head_width_ratio")
        max_head_width = resolve_field("maximum_head_width_ratio")

        target_top_margin = resolve_field("target_top_margin_ratio")
        val = (
            comp.minimum_top_margin_ratio
            if comp.minimum_top_margin_ratio is not None
            else defaults.get("minimum_top_margin_ratio")
        )
        min_top_margin = val if val is not None else 0.06
        max_top_margin = resolve_field("maximum_top_margin_ratio")

        target_eye_line = resolve_field("target_eye_line_ratio")
        min_eye_line = resolve_field("minimum_eye_line_ratio")
        max_eye_line = resolve_field("maximum_eye_line_ratio")

        max_center_offset = resolve_field("maximum_horizontal_center_offset_ratio")
        max_torso_inclusion = resolve_field("maximum_torso_inclusion_ratio")

        complete_hair = getattr(comp, "complete_hair_required", None)
        if complete_hair is None:
            complete_hair = comp.complete_hair_visible

        complete_chin = getattr(comp, "complete_chin_required", None)
        if complete_chin is None:
            complete_chin = comp.chin_visible

        complete_beard = getattr(comp, "complete_beard_boundary_required", None)
        if complete_beard is None:
            complete_beard = comp.beard_boundary_visible

        crop_config = CropConfig(
            target_width=dim.width_px,
            target_height=dim.height_px,
            target_aspect_ratio=dim.width_px / dim.height_px,
            allow_padding=allow_padding,
            allow_subject_clipping=allow_subject_clipping,
            crop_profile=profile,
            ears_policy=comp.ears_policy,
            target_head_height_ratio=target_head_height,
            minimum_head_height_ratio=min_head_height,
            maximum_head_height_ratio=max_head_height,
            target_head_width_ratio=target_head_width,
            minimum_head_width_ratio=min_head_width,
            maximum_head_width_ratio=max_head_width,
            target_top_margin_ratio=target_top_margin,
            minimum_top_margin_ratio=min_top_margin,
            maximum_top_margin_ratio=max_top_margin,
            minimum_side_margin_ratio=resolve_margin("minimum_side_margin_ratio", 0.06),
            minimum_bottom_margin_ratio=resolve_margin(
                "minimum_bottom_margin_ratio", 0.08
            ),
            mask_preservation_threshold=resolve_margin(
                "mask_preservation_threshold", 0.995
            ),
            preferred_face_center_y_ratio=resolve_margin(
                "preferred_face_center_y_ratio", 0.44
            ),
            target_eye_line_ratio=target_eye_line,
            minimum_eye_line_ratio=min_eye_line,
            maximum_eye_line_ratio=max_eye_line,
            maximum_horizontal_center_offset_ratio=max_center_offset,
            maximum_torso_inclusion_ratio=max_torso_inclusion,
            complete_hair_required=complete_hair,
            complete_chin_required=complete_chin,
            complete_beard_boundary_required=complete_beard,
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
        profile = comp.crop_profile or CropProfile.TIGHT_EXAM_PORTRAIT
        defaults = PROFILE_DEFAULTS.get(
            profile, PROFILE_DEFAULTS[CropProfile.TIGHT_EXAM_PORTRAIT]
        )

        crop_config = CropModeBConfig(
            min_aspect_ratio=min_aspect,
            max_aspect_ratio=max_aspect,
            target_head_height_ratio=resolve_mode_b_ratio(
                "target_head_height_ratio", 0.76
            ),
            min_head_height_ratio=resolve_mode_b_ratio(
                "minimum_head_height_ratio", 0.68
            ),
            max_head_height_ratio=resolve_mode_b_ratio(
                "maximum_head_height_ratio", 0.84
            ),
            allow_padding=allow_padding,
            allow_subject_clipping=allow_subject_clipping,
        )
    elif dim.mode == DimensionMode.UNSPECIFIED:
        crop_mode = "b"
        profile = comp.crop_profile or CropProfile.TIGHT_EXAM_PORTRAIT
        defaults = PROFILE_DEFAULTS.get(
            profile, PROFILE_DEFAULTS[CropProfile.TIGHT_EXAM_PORTRAIT]
        )
        crop_config = CropModeBConfig(
            preferred_aspect_ratio=0.75,
            min_aspect_ratio=0.65,
            max_aspect_ratio=0.90,
            target_head_height_ratio=resolve_mode_b_ratio(
                "target_head_height_ratio", 0.76
            ),
            min_head_height_ratio=resolve_mode_b_ratio(
                "minimum_head_height_ratio", 0.68
            ),
            max_head_height_ratio=resolve_mode_b_ratio(
                "maximum_head_height_ratio", 0.84
            ),
            allow_padding=allow_padding,
            allow_subject_clipping=allow_subject_clipping,
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
    elif bg.mode in (
        BackgroundMode.PLAIN_LIGHT,
        BackgroundMode.PLAIN_BACKGROUND,
        BackgroundMode.UNSPECIFIED,
    ):
        target_color = bg.fallback_colour or "#FFFFFF"
    else:
        raise RuleResolutionError(
            "PIPELINE_BACKGROUND_FAILED",
            f"Failing resolution: Background mode '{bg.mode.value}' is not supported.",
        )

    background_config = BackgroundCompositionConfig(
        target_colour_hex=target_color,
        allow_transparent_output=False,
        allow_subject_clipping=False,
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
    elif dim.mode == DimensionMode.RANGE:
        prep_config = OutputPreparationConfig(
            resize_mode=ResizeMode.RANGE_SELECT,
            min_width=dim.minimum_width_px,
            max_width=dim.maximum_width_px,
            min_height=dim.minimum_height_px,
            max_height=dim.maximum_height_px,
            preferred_width=dim.preferred_width_px or 300,
            preferred_height=dim.preferred_height_px or 400,
        )
    else:
        default_width, default_height = resolve_platform_dimensions(
            dim.platform_default_profile
        )
        prep_config = OutputPreparationConfig(
            resize_mode=ResizeMode.EXACT,
            target_width=default_width,
            target_height=default_height,
            min_width=default_width,
            max_width=default_width,
            min_height=default_height,
            max_height=default_height,
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
        target_dpi=rule.image_requirements.dimensions.dpi,
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
