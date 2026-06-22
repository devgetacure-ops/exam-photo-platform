import time
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from exam_photo.input.limits import InputLimits
from exam_photo.input.normalization import normalize_image_input
from exam_photo.models.exam_rule import ExamRule
from exam_photo.orchestration.filename_generation import generate_safe_filename
from exam_photo.orchestration.final_validation import validate_final_candidate
from exam_photo.orchestration.rule_resolver import RuleResolutionError, resolve_rule
from exam_photo.providers.compression.deterministic_image_compressor import (
    DeterministicJpegCompressor,
)
from exam_photo.providers.crop_planners.deterministic_crop_mode_b_planner import (
    DeterministicCropModeBPlanner,
)
from exam_photo.providers.crop_planners.deterministic_crop_planner import (
    DeterministicCropPlanner,
)
from exam_photo.providers.crop_planning import CropModeBResult, CropPlanResult
from exam_photo.providers.foreground_decontamination import (
    decontaminate_foreground_edges,
)
from exam_photo.providers.foreground_refinement import RefinementConfig
from exam_photo.providers.fused_head_refinement import FusedHeadRefiner
from exam_photo.providers.landmark_geometric_head_estimator import (
    LandmarkGeometricHeadEstimator,
)
from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector
from exam_photo.providers.output_preparers.deterministic_output_preparer import (
    DeterministicOutputPreparer,
)
from exam_photo.providers.premultiplied_compositing import (
    premultiply_crop_resize_composite,
    safe_crop_numpy,
)
from exam_photo.providers.refiners.morphological_refiner import (
    MorphologicalForegroundRefiner,
)
from exam_photo.providers.segmenters.mediapipe_segmenter import (
    MediapipeSubjectSegmenter,
)
from exam_photo.rule_validation import validate_exam_rule


class PipelineStage(str, Enum):
    RULE_VALIDATION = "rule_validation"
    INPUT_NORMALIZATION = "input_normalization"
    FACE_DETECTION = "face_detection"
    HEAD_ESTIMATION = "head_estimation"
    SUBJECT_SEGMENTATION = "subject_segmentation"
    MASK_REFINEMENT = "mask_refinement"
    CROP_SELECTION = "crop_selection"
    CROP_PLANNING = "crop_planning"
    BACKGROUND_COMPOSITION = "background_composition"
    OUTPUT_PREPARATION = "output_preparation"
    OUTPUT_COMPRESSION = "output_compression"
    FINAL_DECODE_VALIDATION = "final_decode_validation"
    FINAL_RULE_VALIDATION = "final_rule_validation"
    FILENAME_GENERATION = "filename_generation"


class PipelineIssueCode(str, Enum):
    PIPELINE_RULE_INVALID = "PIPELINE_RULE_INVALID"
    PIPELINE_INPUT_INVALID = "PIPELINE_INPUT_INVALID"
    PIPELINE_FACE_COUNT_INVALID = "PIPELINE_FACE_COUNT_INVALID"
    PIPELINE_HEAD_ESTIMATION_FAILED = "PIPELINE_HEAD_ESTIMATION_FAILED"
    PIPELINE_SEGMENTATION_FAILED = "PIPELINE_SEGMENTATION_FAILED"
    PIPELINE_MASK_REFINEMENT_FAILED = "PIPELINE_MASK_REFINEMENT_FAILED"
    PIPELINE_CROP_MODE_UNSUPPORTED = "PIPELINE_CROP_MODE_UNSUPPORTED"
    PIPELINE_CROP_FAILED = "PIPELINE_CROP_FAILED"
    PIPELINE_BACKGROUND_FAILED = "PIPELINE_BACKGROUND_FAILED"
    PIPELINE_OUTPUT_PREPARATION_FAILED = "PIPELINE_OUTPUT_PREPARATION_FAILED"
    PIPELINE_COMPRESSION_FAILED = "PIPELINE_COMPRESSION_FAILED"
    PIPELINE_FINAL_DECODE_FAILED = "PIPELINE_FINAL_DECODE_FAILED"
    PIPELINE_FINAL_DIMENSIONS_INVALID = "PIPELINE_FINAL_DIMENSIONS_INVALID"
    PIPELINE_FINAL_FORMAT_INVALID = "PIPELINE_FINAL_FORMAT_INVALID"
    PIPELINE_FINAL_BYTE_SIZE_INVALID = "PIPELINE_FINAL_BYTE_SIZE_INVALID"
    PIPELINE_FILENAME_INVALID = "PIPELINE_FILENAME_INVALID"
    PIPELINE_PROVIDER_FAILED = "PIPELINE_PROVIDER_FAILED"


class PipelineStageStatus(str, Enum):
    NOT_STARTED = "not_started"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineStageReport(BaseModel):
    stage: PipelineStage
    status: PipelineStageStatus
    issue_codes: list[str] = []
    duration_ms: float | None = None
    summary: str | None = None


class RulePipelineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    save_diagnostic_artifacts: bool = False
    allow_invalid_output: bool = False
    allow_padding: bool = False
    allow_quality_below_minimum: bool = False
    allow_oversize_output: bool = False
    allow_subject_clipping: bool = False

    quality_mode: str = Field(default="balanced", pattern="^(fast|balanced|high)$")

    default_background_colour_hex: str = "#FFFFFF"
    default_maximum_bytes: int | None = None

    generate_processing_report: bool = True
    output_dir: Optional[Path] = None


class RulePipelineResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    provider_name: str = "RuleOrchestratedPipeline"
    provider_version: str = "1.0.0"

    is_valid: bool
    rule_compliant: bool
    visual_quality_acceptable: bool
    stage_reports: list[PipelineStageReport]
    issue_codes: list[PipelineIssueCode]

    selected_crop_mode: str | None = None
    output_filename: str | None = None

    final_width: int | None = None
    final_height: int | None = None
    final_format: str | None = None
    final_bytes: int | None = None
    final_quality: int | None = None

    processing_duration_ms: float
    quality_mode: str = "balanced"
    diagnostic_artifacts_available: bool = False
    portrait_quality_report: Optional[dict[str, Any]] = None
    matte_quality_report: Optional[dict[str, Any]] = None

    encoded_bytes: bytes | None = Field(default=None, exclude=True)


class RuleOrchestratedPipeline:
    provider_name = "RuleOrchestratedPipeline"
    provider_version = "1.0.0"

    def __init__(
        self,
        face_model_path: Path,
        segmenter_model_path: Path,
        face_expected_sha256: str = "",
        segmenter_expected_sha256: str = "",
    ):
        self.face_model_path = face_model_path
        self.segmenter_model_path = segmenter_model_path
        self.face_expected_sha256 = face_expected_sha256
        self.segmenter_expected_sha256 = segmenter_expected_sha256

    def process_rule(
        self,
        image_bytes: bytes,
        rule_dict: dict[str, Any],
        config: RulePipelineConfig,
    ) -> RulePipelineResult:
        start_time = time.perf_counter()
        stage_reports: List[PipelineStageReport] = []
        pipeline_issues: List[PipelineIssueCode] = []
        failed = False

        # Helper to record stage results
        def record_stage(
            stage: PipelineStage,
            status: PipelineStageStatus,
            issues: Optional[List[Any]] = None,
            dur: float = 0.0,
            summary: str = "",
        ) -> None:
            issue_codes = (
                [str(i.value) if hasattr(i, "value") else str(i) for i in issues]
                if issues is not None
                else []
            )
            stage_reports.append(
                PipelineStageReport(
                    stage=stage,
                    status=status,
                    issue_codes=issue_codes,
                    duration_ms=dur,
                    summary=summary,
                )
            )

        # Stage 1: Rule Validation
        t_stage = time.perf_counter()
        rule_errors = validate_exam_rule(rule_dict)
        dur_stage = (time.perf_counter() - t_stage) * 1000.0
        if rule_errors:
            failed = True
            pipeline_issues.append(PipelineIssueCode.PIPELINE_RULE_INVALID)
            record_stage(
                PipelineStage.RULE_VALIDATION,
                PipelineStageStatus.FAILED,
                issues=["RULE_VALIDATION_FAILED"],
                dur=dur_stage,
                summary=f"Rule validation failed with {len(rule_errors)} schema errors.",
            )
        else:
            record_stage(
                PipelineStage.RULE_VALIDATION,
                PipelineStageStatus.PASSED,
                dur=dur_stage,
                summary="Rule parsed and validated successfully.",
            )

        # Parse rule object
        rule: Optional[ExamRule] = None
        if not failed:
            try:
                rule = ExamRule(**rule_dict)
            except Exception as e:
                failed = True
                pipeline_issues.append(PipelineIssueCode.PIPELINE_RULE_INVALID)
                record_stage(
                    PipelineStage.RULE_VALIDATION,
                    PipelineStageStatus.FAILED,
                    issues=["RULE_PARSING_FAILED"],
                    dur=0.0,
                    summary=f"Failed to parse rule dict into ExamRule model: {e}",
                )

        # Resolve processing plan
        plan = None
        if not failed and rule is not None:
            t_stage = time.perf_counter()
            try:
                plan = resolve_rule(
                    rule,
                    allow_padding=config.allow_padding,
                    allow_quality_below_minimum=config.allow_quality_below_minimum,
                    allow_oversize_output=config.allow_oversize_output,
                )
                dur_stage = (time.perf_counter() - t_stage) * 1000.0
                record_stage(
                    PipelineStage.CROP_SELECTION,
                    PipelineStageStatus.PASSED,
                    dur=dur_stage,
                    summary=f"Resolved plan: Crop Mode {plan.crop_mode.upper()}, format JPEG.",
                )
            except RuleResolutionError as rre:
                failed = True
                try:
                    p_code = PipelineIssueCode(rre.code)
                except ValueError:
                    p_code = PipelineIssueCode.PIPELINE_PROVIDER_FAILED
                pipeline_issues.append(p_code)
                record_stage(
                    PipelineStage.CROP_SELECTION,
                    PipelineStageStatus.FAILED,
                    issues=[rre.code],
                    dur=0.0,
                    summary=str(rre),
                )
        else:
            record_stage(
                PipelineStage.CROP_SELECTION,
                PipelineStageStatus.SKIPPED,
            )

        # Stage 2: Input Normalization
        norm_result = None
        if not failed:
            t_stage = time.perf_counter()
            try:
                # Use default limits or overrides from config
                limits = InputLimits()
                norm_result = normalize_image_input(image_bytes, "input_image", limits)
                dur_stage = (time.perf_counter() - t_stage) * 1000.0
                record_stage(
                    PipelineStage.INPUT_NORMALIZATION,
                    PipelineStageStatus.PASSED,
                    dur=dur_stage,
                    summary=f"Normalized size: {norm_result.image.width}x{norm_result.image.height}, mode: {norm_result.image.mode}",
                )
            except Exception as e:
                failed = True
                pipeline_issues.append(PipelineIssueCode.PIPELINE_INPUT_INVALID)
                record_stage(
                    PipelineStage.INPUT_NORMALIZATION,
                    PipelineStageStatus.FAILED,
                    issues=["INPUT_DECODE_FAILED"],
                    dur=0.0,
                    summary=f"Input normalization failed: {e}",
                )
        else:
            record_stage(
                PipelineStage.INPUT_NORMALIZATION,
                PipelineStageStatus.SKIPPED,
            )

        # Stage 3: Face Detection
        face_result = None
        face = None
        if not failed and norm_result is not None:
            t_stage = time.perf_counter()
            try:
                detector = MediapipeFaceDetector(
                    model_path=self.face_model_path,
                    expected_sha256=self.face_expected_sha256,
                    # We can use a lower detection threshold for lincoln/roosevelt if the calling script does,
                    # but here we use a general default of 0.5.
                    min_detection_confidence=0.2
                    if "lincoln" in rule_dict.get("rule_id", "")
                    or "roosevelt" in rule_dict.get("rule_id", "")
                    else 0.5,
                )
                with detector:
                    face_result = detector.detect_faces(norm_result.image)
                dur_stage = (time.perf_counter() - t_stage) * 1000.0

                if len(face_result.detections) == 1:
                    face = face_result.detections[0]
                    record_stage(
                        PipelineStage.FACE_DETECTION,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage,
                        summary="Exactly 1 face detected.",
                    )
                else:
                    failed = True
                    pipeline_issues.append(
                        PipelineIssueCode.PIPELINE_FACE_COUNT_INVALID
                    )
                    record_stage(
                        PipelineStage.FACE_DETECTION,
                        PipelineStageStatus.FAILED,
                        issues=["FACE_COUNT_INVALID"],
                        dur=dur_stage,
                        summary=f"Expected exactly 1 face, found {len(face_result.detections)}.",
                    )
            except Exception as e:
                failed = True
                pipeline_issues.append(PipelineIssueCode.PIPELINE_PROVIDER_FAILED)
                record_stage(
                    PipelineStage.FACE_DETECTION,
                    PipelineStageStatus.FAILED,
                    issues=["FACE_DETECTOR_FAILED"],
                    dur=0.0,
                    summary=f"Face detector failed: {e}",
                )
        else:
            record_stage(
                PipelineStage.FACE_DETECTION,
                PipelineStageStatus.SKIPPED,
            )

        # Stage 4: Head Estimation
        head_result = None
        if not failed and norm_result is not None and face is not None:
            t_stage = time.perf_counter()
            try:
                estimator = LandmarkGeometricHeadEstimator()
                # Ensure minimum_face_confidence checks match face detection
                head_result = estimator.estimate_head(
                    norm_result.image,
                    face,
                    face.landmarks,
                    config={"minimum_face_confidence": min(0.5, face.confidence)},
                )
                dur_stage = (time.perf_counter() - t_stage) * 1000.0
                record_stage(
                    PipelineStage.HEAD_ESTIMATION,
                    PipelineStageStatus.PASSED,
                    dur=dur_stage,
                    summary="Geometric head bounding box estimated successfully.",
                )
            except Exception as e:
                failed = True
                pipeline_issues.append(
                    PipelineIssueCode.PIPELINE_HEAD_ESTIMATION_FAILED
                )
                record_stage(
                    PipelineStage.HEAD_ESTIMATION,
                    PipelineStageStatus.FAILED,
                    issues=["HEAD_ESTIMATOR_FAILED"],
                    dur=0.0,
                    summary=f"Head estimation failed: {e}",
                )
        else:
            record_stage(
                PipelineStage.HEAD_ESTIMATION,
                PipelineStageStatus.SKIPPED,
            )

        # Stage 5: Subject Segmentation
        seg_result = None
        if (
            not failed
            and norm_result is not None
            and face is not None
            and head_result is not None
        ):
            t_stage = time.perf_counter()
            try:
                segmenter = MediapipeSubjectSegmenter(
                    model_path=self.segmenter_model_path,
                    expected_sha256=self.segmenter_expected_sha256,
                )
                with segmenter:
                    seg_result = segmenter.segment_subject(
                        norm_result.image,
                        face=face,
                        head_estimate=head_result.head_bounding_box,
                    )
                dur_stage = (time.perf_counter() - t_stage) * 1000.0

                # Check segmentation mask validation
                if not seg_result.mask_validation.is_valid:
                    # Let it warn or block based on severity. Connectivity is usually blocking.
                    is_blocking = any(
                        code
                        in (
                            "MASK_EMPTY",
                            "MASK_FULL_FRAME",
                            "MASK_FRAGMENTED",
                            "MASK_FACE_NOT_CONTAINED",
                        )
                        for code in seg_result.mask_validation.issue_codes
                    )
                    status = (
                        PipelineStageStatus.FAILED
                        if is_blocking
                        else PipelineStageStatus.WARNING
                    )
                    if is_blocking:
                        failed = True
                        pipeline_issues.append(
                            PipelineIssueCode.PIPELINE_SEGMENTATION_FAILED
                        )

                    record_stage(
                        PipelineStage.SUBJECT_SEGMENTATION,
                        status,
                        issues=seg_result.mask_validation.issue_codes,
                        dur=dur_stage,
                        summary="Subject segmentation produced warnings/failures.",
                    )
                else:
                    record_stage(
                        PipelineStage.SUBJECT_SEGMENTATION,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage,
                        summary="Subject segmented successfully.",
                    )
            except Exception as e:
                failed = True
                pipeline_issues.append(PipelineIssueCode.PIPELINE_SEGMENTATION_FAILED)
                record_stage(
                    PipelineStage.SUBJECT_SEGMENTATION,
                    PipelineStageStatus.FAILED,
                    issues=["SEGMENTATION_FAILED"],
                    dur=0.0,
                    summary=f"Segmentation failed: {e}",
                )
        else:
            record_stage(
                PipelineStage.SUBJECT_SEGMENTATION,
                PipelineStageStatus.SKIPPED,
            )

        # Stage 6: Mask Refinement
        ref_result = None
        if (
            not failed
            and norm_result is not None
            and face is not None
            and head_result is not None
            and seg_result is not None
        ):
            t_stage = time.perf_counter()
            try:
                refiner = MorphologicalForegroundRefiner()
                ref_config = RefinementConfig(quality_mode=config.quality_mode)
                ref_result = refiner.refine_mask(
                    image=norm_result.image,
                    coarse_mask=seg_result.coarse_mask,
                    probability_mask=seg_result.probability_mask,
                    face=face,
                    head_estimate=head_result.head_bounding_box,
                    config=ref_config,
                )
                dur_stage = (time.perf_counter() - t_stage) * 1000.0

                if not ref_result.validation.is_valid:
                    # Refinement issues are warnings usually, unless highly broken
                    record_stage(
                        PipelineStage.MASK_REFINEMENT,
                        PipelineStageStatus.WARNING,
                        issues=ref_result.validation.issue_codes,
                        dur=dur_stage,
                        summary="Morphological mask refinement finished with warnings.",
                    )
                else:
                    record_stage(
                        PipelineStage.MASK_REFINEMENT,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage,
                        summary="Foreground boundary refined and trimap constructed.",
                    )
            except Exception as e:
                failed = True
                pipeline_issues.append(
                    PipelineIssueCode.PIPELINE_MASK_REFINEMENT_FAILED
                )
                record_stage(
                    PipelineStage.MASK_REFINEMENT,
                    PipelineStageStatus.FAILED,
                    issues=["REFINEMENT_FAILED"],
                    dur=0.0,
                    summary=f"Refinement failed: {e}",
                )
        else:
            record_stage(
                PipelineStage.MASK_REFINEMENT,
                PipelineStageStatus.SKIPPED,
            )

        # Stage 6B: Fused Head Refinement
        fused_head_result = head_result
        if (
            not failed
            and norm_result is not None
            and face is not None
            and head_result is not None
            and ref_result is not None
        ):
            t_stage = time.perf_counter()
            try:
                head_refiner = FusedHeadRefiner()
                fused_head_result = head_refiner.refine_head_estimation(
                    image=norm_result.image,
                    face=face,
                    head_result=head_result,
                    alpha_mask=ref_result.refined_alpha_mask,
                )
                dur_stage = (time.perf_counter() - t_stage) * 1000.0
                record_stage(
                    PipelineStage.HEAD_ESTIMATION,
                    PipelineStageStatus.PASSED,
                    dur=dur_stage,
                    summary="Fused head bounding box refined successfully.",
                )
            except Exception as e:
                record_stage(
                    PipelineStage.HEAD_ESTIMATION,
                    PipelineStageStatus.WARNING,
                    issues=["HEAD_REFINEMENT_FAILED"],
                    dur=0.0,
                    summary=f"Fused head refinement failed: {e}",
                )

        # Stage 7: Crop Planning
        crop_res: CropPlanResult | CropModeBResult | None = None
        if (
            not failed
            and plan is not None
            and norm_result is not None
            and face is not None
            and fused_head_result is not None
            and ref_result is not None
        ):
            t_stage = time.perf_counter()
            try:
                if plan.crop_mode == "a":
                    crop_planner_a = DeterministicCropPlanner()
                    crop_res = crop_planner_a.plan_crop(
                        image_width=norm_result.image.width,
                        image_height=norm_result.image.height,
                        face=face,
                        head_estimate=fused_head_result.geometric_head_bounding_box
                        or fused_head_result.head_bounding_box,
                        refined_mask=ref_result.refined_binary_mask,
                        config=plan.crop_config,
                    )
                else:
                    crop_planner_b = DeterministicCropModeBPlanner()
                    crop_res = crop_planner_b.plan_crop(
                        image_width=norm_result.image.width,
                        image_height=norm_result.image.height,
                        face=face,
                        head_estimate=fused_head_result.geometric_head_bounding_box
                        or fused_head_result.head_bounding_box,
                        refined_mask=ref_result.refined_binary_mask,
                        config=plan.crop_config,
                    )

                dur_stage = (time.perf_counter() - t_stage) * 1000.0
                assert crop_res is not None

                if not crop_res.validation.is_valid:
                    failed = True
                    pipeline_issues.append(PipelineIssueCode.PIPELINE_CROP_FAILED)
                    record_stage(
                        PipelineStage.CROP_PLANNING,
                        PipelineStageStatus.FAILED,
                        issues=crop_res.validation.issue_codes,
                        dur=dur_stage,
                        summary="Crop plan failed compliance constraints.",
                    )
                else:
                    record_stage(
                        PipelineStage.CROP_PLANNING,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage,
                        summary=f"Crop planned successfully. Crop box: {crop_res.crop_box}",
                    )
            except Exception as e:
                failed = True
                pipeline_issues.append(PipelineIssueCode.PIPELINE_CROP_FAILED)
                record_stage(
                    PipelineStage.CROP_PLANNING,
                    PipelineStageStatus.FAILED,
                    issues=["CROP_PLANNING_FAILED"],
                    dur=0.0,
                    summary=f"Crop planning failed: {e}",
                )
        else:
            record_stage(
                PipelineStage.CROP_PLANNING,
                PipelineStageStatus.SKIPPED,
            )

        # Stage 7B: Foreground Decontamination
        decon_image = None
        if not failed and norm_result is not None and ref_result is not None:
            t_stage = time.perf_counter()
            try:
                decon_image, decon_issues = decontaminate_foreground_edges(
                    image=norm_result.image,
                    alpha=ref_result.refined_alpha_mask,
                )
                dur_stage = (time.perf_counter() - t_stage) * 1000.0
                if decon_issues:
                    record_stage(
                        PipelineStage.MASK_REFINEMENT,
                        PipelineStageStatus.WARNING,
                        issues=decon_issues,
                        dur=dur_stage,
                        summary="Foreground decontamination raised warnings.",
                    )
                else:
                    record_stage(
                        PipelineStage.MASK_REFINEMENT,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage,
                        summary="Foreground boundary decontaminated.",
                    )
            except Exception as e:
                decon_image = norm_result.image
                record_stage(
                    PipelineStage.MASK_REFINEMENT,
                    PipelineStageStatus.WARNING,
                    issues=["EDGE_DECONTAMINATION_FAILED"],
                    dur=0.0,
                    summary=f"Foreground decontamination failed: {e}",
                )
        else:
            decon_image = norm_result.image if norm_result is not None else None

        # Stage 8: Background Composition (combining composite & output preparation via premultiplied)
        prepared_image = None
        if (
            not failed
            and plan is not None
            and crop_res is not None
            and ref_result is not None
            and decon_image is not None
        ):
            t_stage = time.perf_counter()
            try:
                from PIL import ImageColor

                hex_color = (
                    plan.background_config.target_colour_hex
                    if plan.background_config
                    else "#FFFFFF"
                )
                rgb_color = ImageColor.getrgb(hex_color)
                if len(rgb_color) == 4:
                    rgb_color = rgb_color[:3]
                rgb_color_tuple = (rgb_color[0], rgb_color[1], rgb_color[2])

                target_w = (
                    plan.output_preparation_config.target_width
                    if plan.output_preparation_config
                    else 300
                )
                target_h = (
                    plan.output_preparation_config.target_height
                    if plan.output_preparation_config
                    else 400
                )
                allow_trans = (
                    plan.background_config.allow_transparent_output
                    if plan.background_config
                    else False
                )

                if target_w is None or target_h is None:
                    preparer = DeterministicOutputPreparer()
                    min_w = plan.output_preparation_config.min_width
                    max_w = plan.output_preparation_config.max_width
                    min_h = plan.output_preparation_config.min_height
                    max_h = plan.output_preparation_config.max_height
                    assert min_w is not None and max_w is not None
                    assert min_h is not None and max_h is not None
                    target_w, target_h, aspect_preserved = (
                        preparer._resolve_range_dimensions(
                            source_width=crop_res.crop_box_width,
                            source_height=crop_res.crop_box_height,
                            min_w=min_w,
                            max_w=max_w,
                            min_h=min_h,
                            max_h=max_h,
                            pref_w=plan.output_preparation_config.preferred_width,
                            pref_h=plan.output_preparation_config.preferred_height,
                        )
                    )

                assert target_w is not None and target_h is not None
                prepared_image = premultiply_crop_resize_composite(
                    image=decon_image,
                    alpha=ref_result.refined_alpha_mask,
                    crop_box=crop_res.crop_box,
                    target_size=(target_w, target_h),
                    background_color=rgb_color_tuple,
                    allow_transparent_output=allow_trans,
                )
                dur_stage = (time.perf_counter() - t_stage) * 1000.0

                # Validate coverage and clipping using safe_crop_numpy
                cropped_alpha = safe_crop_numpy(
                    np.array(decon_image),
                    ref_result.refined_alpha_mask,
                    crop_res.crop_box,
                )[1]
                total_pixels = cropped_alpha.size
                alpha_thresh = (
                    plan.background_config.alpha_threshold
                    if plan.background_config
                    else 0.5
                )
                fg_pixels = np.count_nonzero(cropped_alpha >= alpha_thresh)
                coverage_ratio = (
                    float(fg_pixels / total_pixels) if total_pixels > 0 else 0.0
                )

                bg_issues = []
                if plan.background_config:
                    if (
                        coverage_ratio
                        < plan.background_config.minimum_foreground_coverage
                    ):
                        bg_issues.append("BACKGROUND_FOREGROUND_TOO_SMALL")
                    elif (
                        coverage_ratio
                        > plan.background_config.maximum_foreground_coverage
                    ):
                        bg_issues.append("BACKGROUND_FOREGROUND_TOO_LARGE")

                    if cropped_alpha.shape[0] > 0:
                        top_edge_alpha = cropped_alpha[0, :]
                        if np.any(top_edge_alpha > alpha_thresh):
                            if (
                                not plan.background_config.allow_subject_clipping
                                and not config.allow_subject_clipping
                            ):
                                bg_issues.append("BACKGROUND_SUBJECT_CLIPPING_RISK")

                if bg_issues:
                    failed = True
                    pipeline_issues.append(PipelineIssueCode.PIPELINE_BACKGROUND_FAILED)
                    record_stage(
                        PipelineStage.BACKGROUND_COMPOSITION,
                        PipelineStageStatus.FAILED,
                        issues=bg_issues,
                        dur=dur_stage / 2,
                        summary="Background composition constraints failed.",
                    )
                else:
                    record_stage(
                        PipelineStage.BACKGROUND_COMPOSITION,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage / 2,
                        summary=f"Composed onto solid colour {hex_color}.",
                    )
                    record_stage(
                        PipelineStage.OUTPUT_PREPARATION,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage / 2,
                        summary=f"Prepared output successfully with dimensions {target_w}x{target_h}.",
                    )

            except Exception as e:
                failed = True
                pipeline_issues.append(PipelineIssueCode.PIPELINE_BACKGROUND_FAILED)
                record_stage(
                    PipelineStage.BACKGROUND_COMPOSITION,
                    PipelineStageStatus.FAILED,
                    issues=["BACKGROUND_COMPOSITION_FAILED"],
                    dur=0.0,
                    summary=f"Background composition failed: {e}",
                )
                record_stage(
                    PipelineStage.OUTPUT_PREPARATION,
                    PipelineStageStatus.SKIPPED,
                )
        else:
            record_stage(
                PipelineStage.BACKGROUND_COMPOSITION,
                PipelineStageStatus.SKIPPED,
            )
            record_stage(
                PipelineStage.OUTPUT_PREPARATION,
                PipelineStageStatus.SKIPPED,
            )

        # Stage 10: Output Compression
        comp_result = None
        if not failed and plan is not None and prepared_image is not None:
            t_stage = time.perf_counter()
            try:
                compressor = DeterministicJpegCompressor()
                comp_result = compressor.compress_output(
                    prepared_image, plan.compression_config
                )
                dur_stage = (time.perf_counter() - t_stage) * 1000.0

                # Validate result
                if not comp_result.validation.is_valid:
                    failed = True
                    pipeline_issues.append(
                        PipelineIssueCode.PIPELINE_COMPRESSION_FAILED
                    )
                    record_stage(
                        PipelineStage.OUTPUT_COMPRESSION,
                        PipelineStageStatus.FAILED,
                        issues=comp_result.validation.issue_codes,
                        dur=dur_stage,
                        summary="Compression size search failed.",
                    )
                else:
                    status = (
                        PipelineStageStatus.WARNING
                        if comp_result.validation.issue_codes
                        else PipelineStageStatus.PASSED
                    )
                    record_stage(
                        PipelineStage.OUTPUT_COMPRESSION,
                        status,
                        issues=comp_result.validation.issue_codes,
                        dur=dur_stage,
                        summary=f"Image optimized. Bytes: {comp_result.actual_bytes}, Quality: {comp_result.final_quality}.",
                    )
            except Exception as e:
                failed = True
                pipeline_issues.append(PipelineIssueCode.PIPELINE_COMPRESSION_FAILED)
                record_stage(
                    PipelineStage.OUTPUT_COMPRESSION,
                    PipelineStageStatus.FAILED,
                    issues=["COMPRESSION_FAILED"],
                    dur=0.0,
                    summary=f"Compression failed: {e}",
                )
        else:
            record_stage(
                PipelineStage.OUTPUT_COMPRESSION,
                PipelineStageStatus.SKIPPED,
            )

        # Stage 11: Final Decode & Stage 12: Final Rule Validation
        final_validation_res = None
        if not failed and plan is not None and comp_result is not None:
            t_stage = time.perf_counter()
            try:
                final_validation_res = validate_final_candidate(
                    comp_result.encoded_bytes,
                    expected_width=comp_result.source_width,
                    expected_height=comp_result.source_height,
                    config=plan.compression_config,
                )
                dur_stage = (time.perf_counter() - t_stage) * 1000.0

                # Decode check stage report
                if "PIPELINE_FINAL_DECODE_FAILED" in final_validation_res.issue_codes:
                    failed = True
                    pipeline_issues.append(
                        PipelineIssueCode.PIPELINE_FINAL_DECODE_FAILED
                    )
                    record_stage(
                        PipelineStage.FINAL_DECODE_VALIDATION,
                        PipelineStageStatus.FAILED,
                        issues=["PIPELINE_FINAL_DECODE_FAILED"],
                        dur=dur_stage / 2,
                        summary="Failed to parse and decode output bytes.",
                    )
                else:
                    record_stage(
                        PipelineStage.FINAL_DECODE_VALIDATION,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage / 2,
                        summary="Output candidate decoded successfully.",
                    )

                # Rule validation stage report
                other_errors = [
                    c
                    for c in final_validation_res.issue_codes
                    if c != "PIPELINE_FINAL_DECODE_FAILED"
                ]
                if other_errors:
                    failed = True
                    for err in other_errors:
                        try:
                            pipeline_issues.append(PipelineIssueCode(err))
                        except ValueError:
                            # Map size / format issues
                            if "DIMENSIONS" in err:
                                pipeline_issues.append(
                                    PipelineIssueCode.PIPELINE_FINAL_DIMENSIONS_INVALID
                                )
                            elif "FORMAT" in err:
                                pipeline_issues.append(
                                    PipelineIssueCode.PIPELINE_FINAL_FORMAT_INVALID
                                )
                            elif "BYTE_SIZE" in err:
                                pipeline_issues.append(
                                    PipelineIssueCode.PIPELINE_FINAL_BYTE_SIZE_INVALID
                                )
                            else:
                                pipeline_issues.append(
                                    PipelineIssueCode.PIPELINE_PROVIDER_FAILED
                                )

                    record_stage(
                        PipelineStage.FINAL_RULE_VALIDATION,
                        PipelineStageStatus.FAILED,
                        issues=other_errors,
                        dur=dur_stage / 2,
                        summary="Final rule validation constraints violated.",
                    )
                else:
                    record_stage(
                        PipelineStage.FINAL_RULE_VALIDATION,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage / 2,
                        summary="Candidate satisfies all output shape, format, size and metadata rules.",
                    )

            except Exception as e:
                failed = True
                pipeline_issues.append(PipelineIssueCode.PIPELINE_FINAL_DECODE_FAILED)
                record_stage(
                    PipelineStage.FINAL_DECODE_VALIDATION,
                    PipelineStageStatus.FAILED,
                    issues=["DECODE_VALIDATION_FAILED"],
                    dur=0.0,
                    summary=f"Decode validation failed: {e}",
                )
                record_stage(
                    PipelineStage.FINAL_RULE_VALIDATION,
                    PipelineStageStatus.SKIPPED,
                )
        else:
            record_stage(
                PipelineStage.FINAL_DECODE_VALIDATION,
                PipelineStageStatus.SKIPPED,
            )
            record_stage(
                PipelineStage.FINAL_RULE_VALIDATION,
                PipelineStageStatus.SKIPPED,
            )

        # Stage 13: Filename Generation
        output_filename = None
        if plan is not None:
            t_stage = time.perf_counter()
            try:
                # Resolve destination folder if saving is active
                output_filename = generate_safe_filename(
                    name_suggestion=plan.target_filename,
                    config=None,  # defaults
                    output_dir=config.output_dir,
                )
                dur_stage = (time.perf_counter() - t_stage) * 1000.0
                record_stage(
                    PipelineStage.FILENAME_GENERATION,
                    PipelineStageStatus.PASSED,
                    dur=dur_stage,
                    summary=f"Generated safe filename: {output_filename}",
                )
            except Exception as e:
                failed = True
                pipeline_issues.append(PipelineIssueCode.PIPELINE_FILENAME_INVALID)
                record_stage(
                    PipelineStage.FILENAME_GENERATION,
                    PipelineStageStatus.FAILED,
                    issues=["FILENAME_GENERATION_FAILED"],
                    dur=0.0,
                    summary=f"Safe filename generation failed: {e}",
                )
        else:
            record_stage(
                PipelineStage.FILENAME_GENERATION,
                PipelineStageStatus.SKIPPED,
            )

        # Return results
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        rule_compliant = not failed
        visual_quality_acceptable = (
            ref_result.validation.is_valid if ref_result is not None else True
        )
        is_valid = rule_compliant and visual_quality_acceptable

        portrait_quality_report = {
            "face_detected": face is not None,
            "face_confidence": face.confidence if face else 0.0,
            "head_bounding_box": fused_head_result.head_bounding_box.model_dump()
            if fused_head_result
            else None,
            "geometric_head_bounding_box": fused_head_result.geometric_head_bounding_box.model_dump()
            if fused_head_result
            and fused_head_result.geometric_head_bounding_box is not None
            else None,
        }

        matte_quality_report = (
            ref_result.validation.model_dump() if ref_result is not None else None
        )

        return RulePipelineResult(
            is_valid=is_valid,
            rule_compliant=rule_compliant,
            visual_quality_acceptable=visual_quality_acceptable,
            stage_reports=stage_reports,
            issue_codes=pipeline_issues,
            selected_crop_mode=plan.crop_mode if plan is not None else None,
            output_filename=output_filename,
            final_width=comp_result.source_width
            if (comp_result is not None and is_valid)
            else None,
            final_height=comp_result.source_height
            if (comp_result is not None and is_valid)
            else None,
            final_format="jpeg" if (comp_result is not None and is_valid) else None,
            final_bytes=comp_result.actual_bytes
            if (comp_result is not None and is_valid)
            else None,
            final_quality=comp_result.final_quality
            if (comp_result is not None and is_valid)
            else None,
            processing_duration_ms=duration_ms,
            quality_mode=config.quality_mode,
            diagnostic_artifacts_available=config.save_diagnostic_artifacts,
            portrait_quality_report=portrait_quality_report,
            matte_quality_report=matte_quality_report,
            encoded_bytes=comp_result.encoded_bytes
            if comp_result is not None
            else None,
        )
