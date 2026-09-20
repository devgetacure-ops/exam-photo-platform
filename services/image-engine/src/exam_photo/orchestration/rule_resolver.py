from typing import Any, Optional

from pydantic import BaseModel

from exam_photo.models.exam_rule import BackgroundMode, DimensionMode, ExamRule
from exam_photo.orchestration.filename_generation import standard_file_stem
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

# One composition, used for every examination.
#
# There is deliberately no second profile and no fallback. The presets that used
# to sit here -- standard passport (0.60 head height) and relaxed identity
# (0.40) -- existed on the assumption that different examinations want different
# framings. Measured against 48 examinations' published rules, they do not: not
# one publishes a face-coverage *maximum* that a tight crop would breach, and
# the single upper bound anywhere in the set (GATE, "60-70%") is stated on a
# different basis from head height and is satisfied by this composition anyway
# -- a tight crop measures ~0.58-0.60 *face* height at 0.86 head height, which
# lands inside GATE's band.
#
# What the published rules do carry is minima: UPSC "at least 75%", RRB "at
# least 50%", NTA "80% face", CBSE "80% of the image". A single tight
# composition clears all of them, and where an examination's own dimensions make
# 0.86 unreachable the relaxation ladder already delivers the tightest crop the
# geometry allows and reports the compromise (DEC-039). So a looser profile was
# never the mechanism for handling tight targets -- it just produced a looser
# photograph than the examination asked for.
#
# Keeping them was actively harmful rather than merely unused, because the two
# loose presets omit four settings this one carries -- side margin, bottom
# margin, mask-preservation threshold and expected face-centre height. A rule
# naming a loose profile therefore fell back to CropConfig defaults (0.06 side,
# 0.08 bottom, 0.995 retention, 0.44 face centre) that the comments below record
# as wrong for exam framing: at reference head size the face box centres at 0.62
# of frame height, so the 0.44 value alone would flag every correctly composed
# crop as mis-centred.
#
# ``CropProfile`` remains in the canonical schema and a rule may still name a
# value; it simply no longer selects geometry. Per-examination deviation is
# expressed by overriding individual ratios on the rule record, which the
# resolver already prefers over these defaults and which requires published
# evidence to justify.
#
# Calibrated against 60 reference exam photos across six exam size classes.
# Ratios are crown-to-chin fractions of the output frame; bounds track the
# p10/p90 of the reference distribution so ordinary variation stays valid.
#   head height  mean 0.840  p10 0.768  p90 0.900
#   top margin   mean 0.048  p10 0.027  p90 0.075
#   eye line     mean 0.486  p10 0.452  p90 0.525
#   below chin   mean 0.112
EXAM_COMPOSITION_DEFAULTS: dict[str, Any] = {
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
}

# Output envelope for an examination that publishes no pixel dimensions at all.
#
# These are bounds, not a target. The delivered size is chosen per photograph
# from the crop's own aspect, so the subject is never stretched to meet a
# constant. Fifteen of the 48 researched examinations land here -- UPSC, the
# whole NTA family, CBSE, ICAI, ICSI among them -- so this path carries real
# volume and is not a rare fallback.
#
# The floor is set by legibility rather than by any published rule: the smallest
# dimension any body in the set does publish is Kerala PSC at 150x200, and the
# tightest file-size ceiling is CBSE at 40 KB, which a 240px edge clears
# comfortably in JPEG. The ceiling keeps the output inside the range the engine
# is calibrated on -- the reference set spans 150x200 to 1200x1800 -- and avoids
# upscaling a crop beyond the detail the source actually holds.
_UNSPECIFIED_MIN_EDGE_PX = 240
_UNSPECIFIED_MAX_EDGE_PX = 1200
# Passport-shaped starting point at a size that satisfies every published
# file-size ceiling in the set without resampling most crops far from native.
_UNSPECIFIED_PREFERRED_WIDTH_PX = 413
_UNSPECIFIED_PREFERRED_HEIGHT_PX = 531


def size_within_range(
    minimum_width: int,
    maximum_width: int,
    minimum_height: int,
    maximum_height: int,
    preferred_width: Optional[int] = None,
    preferred_height: Optional[int] = None,
) -> tuple[int, int]:
    """A concrete size to deliver for a rule that publishes a range (DEC-105).

    The examination's own preferred size when it named one inside its range;
    otherwise the platform's passport shape scaled to fit, which is the shape
    the crop calibration and the owner's reviewed outputs are built on. A range
    too narrow to hold that shape gets its own largest size, and the crop is
    framed to that shape rather than squeezed into it.
    """
    if (
        preferred_width
        and preferred_height
        and minimum_width <= preferred_width <= maximum_width
        and minimum_height <= preferred_height <= maximum_height
    ):
        return preferred_width, preferred_height

    width = _UNSPECIFIED_PREFERRED_WIDTH_PX
    height = _UNSPECIFIED_PREFERRED_HEIGHT_PX
    largest = min(maximum_width / width, maximum_height / height)
    smallest = max(minimum_width / width, minimum_height / height)
    if smallest > largest:
        return maximum_width, maximum_height
    scale = min(max(1.0, smallest), largest)
    return (
        max(minimum_width, min(maximum_width, round(width * scale))),
        max(minimum_height, min(maximum_height, round(height * scale))),
    )


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
    # DEC-079. `image_requirements` is optional so an examination can be served
    # for its signature alone, and everything below this line specifies a
    # photograph. Refusing here, once and by name, is why the twelve reads
    # that follow need no guard of their own.
    if rule.image_requirements is None:
        raise RuleResolutionError(
            "PIPELINE_RULE_HAS_NO_PHOTOGRAPH_SPECIFICATION",
            "This examination carries no photograph specification, so no "
            "photograph can be prepared for it. Its other deliverables are "
            "unaffected.",
        )

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
        box, whereas the Mode A ratios in ``EXAM_COMPOSITION_DEFAULTS`` are
        crown-to-chin fractions (see DEC-029).  The two are not interchangeable
        -- the preservation box runs ~1.14x taller than the real head -- so the
        Mode A numbers must not leak in here.  Mode B keeps the calibration
        documented on ``CropModeBConfig`` until it has its own reference set.
        """
        explicit = getattr(comp, field_name, None)
        return hard_default if explicit is None else float(explicit)

    # DEC-103. A published preferred size ("200 x 230 pixels (preferred)", the
    # IBPS, SBI, RBI, LIC, NABARD, NIACL and XAT records) is delivered at exactly
    # that size, so it is planned as one: Crop Mode A, which frames the head in
    # a box of the published shape and composes onto the background where the
    # photograph is short. It was Mode B with the aspect range pinned to the
    # single value 200/230 (DEC-090) and a tolerance of 1e-4. A crop measured
    # in whole pixels misses that by more than the tolerance on almost any real
    # photograph, and Mode B may not pad, so every photograph for those twelve
    # examinations failed with CROP_B_ASPECT_OUT_OF_RANGE on the live site.
    #
    # DEC-105 carries that further: **every** rule now resolves to a size and
    # so to Mode A. A published range takes a size inside it, and a rule that
    # publishes nothing takes the platform's passport shape. Mode B framed the
    # head against its preservation box and refused to compose onto the
    # background, which made it both looser than the owner's reviewed outputs
    # and unable to accept a photograph already cropped close to the head --
    # the sweep of DEC-104 found it refusing two of four portraits on all four
    # examinations that still used it, and accepting the rest with the head at
    # 0.74 of the frame against the reviewed 0.9.
    preferred_exact = (
        dim.mode == DimensionMode.UNSPECIFIED
        and dim.preferred_width_px is not None
        and dim.preferred_height_px is not None
    )
    exact_width = dim.preferred_width_px if preferred_exact else dim.width_px
    exact_height = dim.preferred_height_px if preferred_exact else dim.height_px

    if dim.mode == DimensionMode.RANGE:
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
        exact_width, exact_height = size_within_range(
            dim.minimum_width_px,
            dim.maximum_width_px,
            dim.minimum_height_px,
            dim.maximum_height_px,
            dim.preferred_width_px,
            dim.preferred_height_px,
        )
    elif dim.mode == DimensionMode.UNSPECIFIED and not preferred_exact:
        # Nothing published at all: the passport shape, as DEC-095 settled for
        # every other record that publishes no size.
        exact_width = _UNSPECIFIED_PREFERRED_WIDTH_PX
        exact_height = _UNSPECIFIED_PREFERRED_HEIGHT_PX

    if exact_width is not None and exact_height is not None:
        crop_mode = "a"
        if exact_width is None or exact_height is None:
            raise RuleResolutionError(
                "PIPELINE_CROP_MODE_UNSUPPORTED",
                "Exact dimension mode is missing width_px or height_px.",
            )
        # Resolve Composition Ratio defaults from presets
        defaults = EXAM_COMPOSITION_DEFAULTS

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
            target_width=exact_width,
            target_height=exact_height,
            target_aspect_ratio=exact_width / exact_height,
            allow_padding=allow_padding,
            allow_subject_clipping=allow_subject_clipping,
            # Passed through for reporting only. It no longer selects geometry
            # -- every ratio above is already resolved from
            # ``EXAM_COMPOSITION_DEFAULTS`` or an explicit per-rule override --
            # but the planner reads its presence to decide adaptive mode, and
            # downstream diagnostics echo whatever the rule declared.
            crop_profile=comp.crop_profile or CropProfile.TIGHT_EXAM_PORTRAIT,
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
    if exact_width is not None and exact_height is not None:
        # The size resolved above, delivered exactly: the examination's own
        # number where it published one (DEC-103), a size inside its range, or
        # the platform's passport shape (DEC-105). The crop already has that
        # shape, so nothing here resizes against it.
        prep_config = OutputPreparationConfig(
            resize_mode=ResizeMode.EXACT,
            target_width=exact_width,
            target_height=exact_height,
            min_width=exact_width,
            max_width=exact_width,
            min_height=exact_height,
            max_height=exact_height,
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
        # Nothing published at all. The size is ours to choose, and it is chosen
        # from the photograph rather than from a constant.
        #
        # The previous behaviour resized to a fixed platform default under
        # ``ResizeMode.EXACT``, which only *warns* on aspect mismatch and
        # otherwise resizes anyway. Crop Mode B -- which is what an unspecified
        # rule resolves to -- produces a head-led crop whose aspect varies with
        # the subject, so forcing it into a constant frame stretches the face.
        # That breaches the identity-preservation principle outright, and it
        # did so silently.
        #
        # The envelope below bounds the output to a sane print-portrait size
        # while leaving the crop's own aspect intact: the range is wide enough
        # that ``_resolve_range_dimensions`` can always satisfy it without
        # distortion, and every published file-size ceiling in the set (40 KB
        # upward) is reachable at these pixel counts.
        prep_config = OutputPreparationConfig(
            resize_mode=ResizeMode.RANGE_SELECT,
            min_width=_UNSPECIFIED_MIN_EDGE_PX,
            max_width=_UNSPECIFIED_MAX_EDGE_PX,
            min_height=_UNSPECIFIED_MIN_EDGE_PX,
            max_height=_UNSPECIFIED_MAX_EDGE_PX,
            preferred_width=_UNSPECIFIED_PREFERRED_WIDTH_PX,
            preferred_height=_UNSPECIFIED_PREFERRED_HEIGHT_PX,
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
        # No published name: the standard `<exam>_photo`, so a candidate's
        # downloads folder says which examination each photograph is for.
        target_filename = fn.fallback_basename or standard_file_stem(
            rule.exam.exam_id, rule.exam.aliases, "photograph"
        )

    return ResolvedProcessingPlan(
        crop_mode=crop_mode,
        crop_config=crop_config,
        background_config=background_config,
        output_preparation_config=prep_config,
        compression_config=comp_config,
        target_filename=target_filename,
    )
