import os
import time
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional

import numpy as np
from PIL import Image
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
from exam_photo.providers.portrait_composition import (
    DeterministicPortraitCompositionEstimator,
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

# Face-detection confidence ladder.  The primary threshold is the provider
# default; the recovery levels are only consulted when the primary pass returns
# no detections at all (see Stage 3).
_FACE_PRIMARY_CONFIDENCE = 0.5
_FACE_RECOVERY_CONFIDENCES = (0.35, 0.25, 0.15)


def _find_repo_root() -> Path:
    """Locate the repository root holding model-manifests/ and model-assets/.

    Defined here rather than imported from the API layer so the engine does not
    depend on the service that wraps it.
    """
    env_val = os.environ.get("EXAM_PHOTO_REPO_ROOT")
    if env_val:
        candidate = Path(env_val).resolve()
        if candidate.exists():
            return candidate

    current = Path(__file__).resolve().parent
    for _ in range(7):
        if (current / "AGENTS.md").exists() or (current / "model-manifests").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return Path(".").resolve()


class PipelineStage(str, Enum):
    RULE_VALIDATION = "rule_validation"
    INPUT_NORMALIZATION = "input_normalization"
    FACE_DETECTION = "face_detection"
    HEAD_ESTIMATION = "head_estimation"
    FUSED_HEAD_REFINEMENT = "fused_head_refinement"
    PORTRAIT_COMPOSITION = "portrait_composition"
    SUBJECT_SEGMENTATION = "subject_segmentation"
    MASK_REFINEMENT = "mask_refinement"
    CROP_SELECTION = "crop_selection"
    CROP_CANDIDATE_SCORING = "crop_candidate_scoring"
    CROP_PLANNING = "crop_planning"
    FOREGROUND_DECONTAMINATION = "foreground_decontamination"
    BACKGROUND_COMPOSITION = "background_composition"
    COMPOSITION_QUALITY_VALIDATION = "composition_quality_validation"
    MATTE_QUALITY_VALIDATION = "matte_quality_validation"
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
    PIPELINE_FINAL_DPI_INVALID = "PIPELINE_FINAL_DPI_INVALID"
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
    allow_padding: bool = True
    allow_quality_below_minimum: bool = False
    allow_oversize_output: bool = False
    allow_subject_clipping: bool = False

    quality_mode: str = Field(default="balanced", pattern="^(fast|balanced|high)$")

    default_background_colour_hex: str = "#FFFFFF"
    default_maximum_bytes: int | None = None

    generate_processing_report: bool = True
    output_dir: Optional[Path] = None


def compute_halo_score_float(
    composite_arr: np.ndarray[Any, Any],
    alpha_mask: np.ndarray[Any, Any],
) -> float:
    gray = (
        0.299 * composite_arr[..., 0]
        + 0.587 * composite_arr[..., 1]
        + 0.114 * composite_arr[..., 2]
    )
    gray = gray * 255.0
    mask = (alpha_mask > 0.05) & (alpha_mask < 0.95)
    if not np.any(mask):
        return 0.0
    dy, dx = np.gradient(gray)
    grad_mag = np.sqrt(dx**2 + dy**2)
    return float(np.mean(grad_mag[mask]))


def compute_spill_score_float(
    original_arr: np.ndarray[Any, Any],
    alpha_mask: np.ndarray[Any, Any],
) -> float:
    mask = (alpha_mask > 0.05) & (alpha_mask < 0.95)
    if not np.any(mask):
        return 0.0
    fg_mask = alpha_mask >= 0.95
    bg_mask = alpha_mask <= 0.05
    if not np.any(fg_mask) or not np.any(bg_mask):
        return 0.0
    c_fg = np.mean(original_arr[fg_mask], axis=0)
    c_bg = np.mean(original_arr[bg_mask], axis=0)
    v = c_bg - c_fg
    v_norm_sq = np.dot(v, v)
    if v_norm_sq < (100.0 / 255.0 / 255.0):
        return 0.0
    pixels = original_arr[mask]
    diff = pixels - c_fg
    projections = np.dot(diff, v) / v_norm_sq
    projections = np.clip(projections, 0.0, 1.0)
    return float(np.mean(projections))


def compute_alpha_continuity_float(
    alpha_mask: np.ndarray[Any, Any],
) -> float:
    mask = (alpha_mask > 0.05) & (alpha_mask < 0.95)
    if not np.any(mask):
        return 0.0
    dy, dx = np.gradient(alpha_mask * 255.0)
    grad_mag = np.sqrt(dx**2 + dy**2)
    return float(np.std(grad_mag[mask]))


def compute_background_uniformity_float(
    composite_arr: np.ndarray[Any, Any],
    alpha_mask: np.ndarray[Any, Any],
) -> float:
    mask = alpha_mask <= 0.05
    if not np.any(mask):
        return 0.0
    target_bg = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    diff = (composite_arr[mask] - target_bg) * 255.0
    return float(np.mean(np.abs(diff)))


class PortraitQualityReport(BaseModel):
    passed: bool
    face_detected: bool
    face_confidence: float
    head_bounding_box: Optional[dict[str, Any]] = None
    geometric_head_bounding_box: Optional[dict[str, Any]] = None
    head_height_ratio: Optional[float] = None
    head_width_ratio: Optional[float] = None
    top_margin_ratio: Optional[float] = None
    eye_line_ratio: Optional[float] = None
    center_offset_ratio: Optional[float] = None
    torso_inclusion_ratio: Optional[float] = None


class MatteQualityReport(BaseModel):
    passed: bool
    halo_score: float
    color_spill_score: float
    alpha_continuity: float
    background_uniformity: float
    validation_issues: list[str] = []


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
    refined_alpha_mask: Any = Field(default=None, exclude=True)


class RuleOrchestratedPipeline:
    provider_name = "RuleOrchestratedPipeline"
    provider_version = "1.0.0"

    def __init__(
        self,
        face_model_path: Path,
        segmenter_model_path: Path,
        face_expected_sha256: str = "",
        segmenter_expected_sha256: str = "",
        matting_backend: str = "birefnet",
        birefnet_model_dir: Optional[Path] = None,
        birefnet_expected_sha256: str = "",
    ):
        """``matting_backend`` selects the subject segmentation model.

        ``"birefnet"`` is the default subject matting backend (DEC-036) because
        the product requirement is realistic portrait edges, not the old
        coarse selfie-segmentation matte.  ``"mediapipe"`` remains selectable
        for lightweight diagnostics and legacy tests.  When BiRefNet is chosen
        without explicit model arguments, the vendored model manifest is
        resolved from the repository root.
        """
        if matting_backend not in ("mediapipe", "birefnet"):
            raise ValueError(
                f"Unknown matting_backend '{matting_backend}'; expected "
                "'mediapipe' or 'birefnet'."
            )
        if matting_backend == "birefnet" and birefnet_model_dir is None:
            from exam_photo.providers.segmenters.birefnet_segmenter import (
                load_manifest_defaults,
            )

            repo_root = _find_repo_root()
            birefnet_model_dir, _weights_name, default_sha, _size = (
                load_manifest_defaults(repo_root)
            )
            if not birefnet_expected_sha256:
                birefnet_expected_sha256 = default_sha
        self.face_model_path = face_model_path
        self.segmenter_model_path = segmenter_model_path
        self.face_expected_sha256 = face_expected_sha256
        self.segmenter_expected_sha256 = segmenter_expected_sha256
        self.matting_backend = matting_backend
        self.birefnet_model_dir = birefnet_model_dir
        self.birefnet_expected_sha256 = birefnet_expected_sha256
        self._birefnet_segmenter: Optional[Any] = None
        self._face_landmarker: Optional[Any] = None
        self._face_landmarker_unavailable = False

    def _refine_face_landmarks(self, image: Image.Image, face: Any) -> Any:
        """Sharpen the chin and eye line of a detected face (DEC-032).

        Returns ``face`` unchanged when the optional landmarker asset is not
        vendored, so this stays an enhancement rather than a new hard
        dependency.  The first failure latches, avoiding a repeated model-load
        attempt on every image of a batch.
        """
        if self._face_landmarker_unavailable:
            return face
        if self._face_landmarker is None:
            from exam_photo.providers.mediapipe_face_landmarker import (
                MediapipeFaceLandmarker,
                load_manifest_defaults,
            )

            repo_root = _find_repo_root()
            model_path, expected_sha = load_manifest_defaults(repo_root)
            if not model_path.exists():
                self._face_landmarker_unavailable = True
                return face
            self._face_landmarker = MediapipeFaceLandmarker(
                model_path=model_path, expected_sha256=expected_sha
            )
        return self._face_landmarker.refine(image, face)

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
                    allow_subject_clipping=config.allow_subject_clipping,
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
                    min_detection_confidence=_FACE_PRIMARY_CONFIDENCE,
                )
                recovery_used: float | None = None
                with detector:
                    face_result = detector.detect_faces(norm_result.image)
                    # The short-range BlazeFace model is tuned for close selfie
                    # framing and scores confidently-detectable faces below 0.5
                    # on ordinary half-body exam submissions (no detections at
                    # all on 9 of 60 reference photos, all of which resolve to a
                    # single face at a lower threshold).  When the primary pass
                    # finds nothing, step the threshold down and accept only an
                    # unambiguous single face; anything else stays a failure so
                    # genuine multi-person photos are never silently accepted.
                    if not face_result.detections:
                        for level in _FACE_RECOVERY_CONFIDENCES:
                            retry = detector.detect_faces(
                                norm_result.image,
                                config={"min_detection_confidence": level},
                            )
                            if len(retry.detections) == 1:
                                face_result = retry
                                recovery_used = level
                                break
                            if len(retry.detections) > 1:
                                # Ambiguous: report the ambiguity, do not guess.
                                face_result = retry
                                break
                dur_stage = (time.perf_counter() - t_stage) * 1000.0

                if len(face_result.detections) == 1:
                    face = face_result.detections[0]
                    # Refine the chin and eye line with dense landmarks where
                    # the asset is available (DEC-032).  Detection and face
                    # counting stay with BlazeFace, which has the better
                    # coverage on raw photos; this only sharpens the two points
                    # the crop planner is most sensitive to.  Any failure here
                    # leaves the detector's own points in place.
                    landmark_note = ""
                    try:
                        refined_face = self._refine_face_landmarks(
                            norm_result.image, face
                        )
                        if refined_face is not face:
                            face = refined_face
                            landmark_note = (
                                " Chin and eye line refined by dense landmarks."
                            )
                    except Exception as exc:  # noqa: BLE001
                        landmark_note = f" Landmark refinement unavailable: {exc}."
                    record_stage(
                        PipelineStage.FACE_DETECTION,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage,
                        summary=(
                            "Exactly 1 face detected."
                            if recovery_used is None
                            else f"Exactly 1 face detected at recovery confidence {recovery_used:.2f}."
                        )
                        + landmark_note,
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
                segmenter: Any
                if self.matting_backend == "birefnet":
                    # Kept warm across calls: BiRefNet load/verification costs
                    # real time (torch + weights), unlike MediaPipe's cheap
                    # per-call reinitialisation.
                    if self._birefnet_segmenter is None:
                        from exam_photo.providers.segmenters.birefnet_segmenter import (
                            BiRefNetSubjectSegmenter,
                        )

                        assert self.birefnet_model_dir is not None
                        self._birefnet_segmenter = BiRefNetSubjectSegmenter(
                            model_dir=self.birefnet_model_dir,
                            expected_sha256=self.birefnet_expected_sha256,
                        )
                    segmenter = self._birefnet_segmenter
                else:
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
                # A matting backend already resolves the boundary accurately, so
                # the morphological reconstruction is skipped for it (DEC-033);
                # the coarse selfie segmenter still needs the full treatment.
                ref_config = RefinementConfig(
                    quality_mode=config.quality_mode,
                    trust_input_alpha=(self.matting_backend == "birefnet"),
                )
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
                    PipelineStage.FUSED_HEAD_REFINEMENT,
                    PipelineStageStatus.PASSED,
                    dur=dur_stage,
                    summary="Fused head bounding box refined successfully.",
                )
                if config.save_diagnostic_artifacts and config.output_dir:
                    alpha_pil = Image.fromarray(
                        (ref_result.refined_alpha_mask * 255.0).astype(np.uint8),
                        mode="L",
                    )
                    alpha_pil.save(config.output_dir / "refined_alpha.png")
            except Exception as e:
                record_stage(
                    PipelineStage.FUSED_HEAD_REFINEMENT,
                    PipelineStageStatus.WARNING,
                    issues=["HEAD_REFINEMENT_FAILED"],
                    dur=0.0,
                    summary=f"Fused head refinement failed: {e}",
                )

        # Stage 7: Crop Planning
        portrait_composition = None
        if (
            not failed
            and norm_result is not None
            and face is not None
            and fused_head_result is not None
            and ref_result is not None
        ):
            t_stage = time.perf_counter()
            try:
                composition_estimator = DeterministicPortraitCompositionEstimator()
                portrait_composition = composition_estimator.estimate_composition(
                    image=norm_result.image,
                    face=face,
                    head_result=fused_head_result,
                    alpha_mask=ref_result.refined_alpha_mask,
                )
                dur_stage = (time.perf_counter() - t_stage) * 1000.0
                record_stage(
                    PipelineStage.PORTRAIT_COMPOSITION,
                    PipelineStageStatus.PASSED,
                    issues=portrait_composition.warnings,
                    dur=dur_stage,
                    summary="Semantic exam-portrait composition estimated successfully.",
                )
            except Exception as e:
                record_stage(
                    PipelineStage.PORTRAIT_COMPOSITION,
                    PipelineStageStatus.WARNING,
                    issues=["PORTRAIT_COMPOSITION_FAILED"],
                    dur=0.0,
                    summary=f"Portrait composition fell back to head geometry: {e}",
                )
        else:
            record_stage(
                PipelineStage.PORTRAIT_COMPOSITION,
                PipelineStageStatus.SKIPPED,
            )

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
                crop_cfg = plan.crop_config.model_copy(
                    update={
                        "allow_subject_clipping": plan.crop_config.allow_subject_clipping
                        or config.allow_subject_clipping
                    }
                )
                if plan.crop_mode == "a":
                    crop_planner_a = DeterministicCropPlanner()
                    crop_res = crop_planner_a.plan_crop(
                        image_width=norm_result.image.width,
                        image_height=norm_result.image.height,
                        face=face,
                        head_estimate=(
                            fused_head_result.refined_head_bounding_box
                            or fused_head_result.head_bounding_box
                            or fused_head_result.geometric_head_bounding_box
                        ),
                        refined_mask=ref_result.refined_binary_mask,
                        portrait_composition=portrait_composition,
                        config=crop_cfg,
                    )
                else:
                    crop_planner_b = DeterministicCropModeBPlanner()
                    crop_res = crop_planner_b.plan_crop(
                        image_width=norm_result.image.width,
                        image_height=norm_result.image.height,
                        face=face,
                        head_estimate=(
                            fused_head_result.refined_head_bounding_box
                            or fused_head_result.head_bounding_box
                            or fused_head_result.geometric_head_bounding_box
                        ),
                        refined_mask=ref_result.refined_binary_mask,
                        portrait_composition=portrait_composition,
                        config=crop_cfg,
                    )

                dur_stage = (time.perf_counter() - t_stage) * 1000.0
                assert crop_res is not None

                if not crop_res.validation.is_valid:
                    failed = True
                    pipeline_issues.append(PipelineIssueCode.PIPELINE_CROP_FAILED)
                    record_stage(
                        PipelineStage.CROP_CANDIDATE_SCORING,
                        PipelineStageStatus.FAILED,
                        issues=crop_res.validation.issue_codes,
                        dur=dur_stage / 2,
                        summary="Crop candidate selection failed.",
                    )
                    record_stage(
                        PipelineStage.CROP_PLANNING,
                        PipelineStageStatus.FAILED,
                        issues=crop_res.validation.issue_codes,
                        dur=dur_stage / 2,
                        summary="Crop plan failed compliance constraints.",
                    )
                else:
                    record_stage(
                        PipelineStage.CROP_CANDIDATE_SCORING,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage / 2,
                        summary="Crop candidates scored and selected successfully.",
                    )
                    record_stage(
                        PipelineStage.CROP_PLANNING,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage / 2,
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
                        PipelineStage.FOREGROUND_DECONTAMINATION,
                        PipelineStageStatus.WARNING,
                        issues=decon_issues,
                        dur=dur_stage,
                        summary="Foreground decontamination raised warnings.",
                    )
                else:
                    record_stage(
                        PipelineStage.FOREGROUND_DECONTAMINATION,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage,
                        summary="Foreground boundary decontaminated.",
                    )
                if (
                    config.save_diagnostic_artifacts
                    and config.output_dir
                    and decon_image
                ):
                    decon_image.save(config.output_dir / "decontaminate_foreground.png")
            except Exception as e:
                decon_image = norm_result.image
                record_stage(
                    PipelineStage.FOREGROUND_DECONTAMINATION,
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

        # Stage 9B: Composition & Matte Quality Validation
        portrait_quality_passed = not failed and (
            crop_res is not None and crop_res.validation.is_valid
        )
        matte_quality_passed = not failed and (
            ref_result is not None and ref_result.validation.is_valid
        )
        portrait_report_dict = {}
        matte_report_dict = {}

        if not failed and crop_res is not None and ref_result is not None:
            t_stage = time.perf_counter()
            try:
                assert norm_result is not None
                assert plan is not None
                cropped_rgb_arr, cropped_alpha_arr = safe_crop_numpy(
                    np.array(norm_result.image.convert("RGB"), dtype=np.float32)
                    / 255.0,
                    ref_result.refined_alpha_mask,
                    crop_res.crop_box,
                )
                hex_color = (
                    plan.background_config.target_colour_hex
                    if plan.background_config
                    else "#FFFFFF"
                )
                from PIL import ImageColor

                rgb_color = ImageColor.getrgb(hex_color)
                bg_rgb_arr = np.array(rgb_color[:3], dtype=np.float32) / 255.0
                composed_rgb_arr = (
                    cropped_rgb_arr * cropped_alpha_arr[..., None]
                    + bg_rgb_arr * (1.0 - cropped_alpha_arr)[..., None]
                )
                composed_rgb_arr = np.clip(composed_rgb_arr, 0.0, 1.0)

                halo = compute_halo_score_float(composed_rgb_arr, cropped_alpha_arr)
                spill = compute_spill_score_float(cropped_rgb_arr, cropped_alpha_arr)
                continuity = compute_alpha_continuity_float(cropped_alpha_arr)
                bg_uni = compute_background_uniformity_float(
                    composed_rgb_arr, cropped_alpha_arr
                )
            except Exception:
                halo = 0.0
                spill = 0.0
                continuity = 0.0
                bg_uni = 999.0

            portrait_report_dict = {
                "passed": portrait_quality_passed,
                "face_detected": face is not None,
                "face_confidence": face.confidence if face else 0.0,
                "crop_box": crop_res.crop_box.model_dump() if crop_res else None,
                "head_bounding_box": fused_head_result.head_bounding_box.model_dump()
                if fused_head_result
                else None,
                "geometric_head_bounding_box": fused_head_result.geometric_head_bounding_box.model_dump()
                if fused_head_result
                and fused_head_result.geometric_head_bounding_box is not None
                else None,
                "portrait_composition_box": portrait_composition.preservation_box.model_dump()
                if portrait_composition is not None
                else None,
                "portrait_lower_body_exclusion_y": portrait_composition.lower_body_exclusion_y
                if portrait_composition is not None
                else None,
                "head_height_ratio": getattr(crop_res, "head_height_ratio", None),
                "head_width_ratio": getattr(crop_res, "head_width_ratio", None),
                "top_margin_ratio": getattr(crop_res, "top_margin_ratio", None),
                "eye_line_ratio": getattr(crop_res, "eye_line_ratio", None),
                "center_offset_ratio": getattr(crop_res, "center_offset_ratio", None),
                "torso_inclusion_ratio": getattr(
                    crop_res, "torso_inclusion_ratio", None
                ),
            }

            matte_report_dict = {
                "passed": matte_quality_passed,
                "halo_score": halo,
                "color_spill_score": spill,
                "alpha_continuity": continuity,
                "background_uniformity": bg_uni,
                "validation_issues": ref_result.validation.issue_codes,
            }

            dur_stage = (time.perf_counter() - t_stage) * 1000.0
            record_stage(
                PipelineStage.COMPOSITION_QUALITY_VALIDATION,
                PipelineStageStatus.PASSED
                if portrait_quality_passed
                else PipelineStageStatus.FAILED,
                dur=dur_stage / 2,
                summary=f"Composition quality validation: {'PASSED' if portrait_quality_passed else 'FAILED'}",
            )
            record_stage(
                PipelineStage.MATTE_QUALITY_VALIDATION,
                PipelineStageStatus.PASSED
                if matte_quality_passed
                else PipelineStageStatus.FAILED,
                dur=dur_stage / 2,
                summary=f"Matte quality validation: {'PASSED' if matte_quality_passed else 'FAILED'}",
            )
        else:
            record_stage(
                PipelineStage.COMPOSITION_QUALITY_VALIDATION,
                PipelineStageStatus.SKIPPED,
            )
            record_stage(
                PipelineStage.MATTE_QUALITY_VALIDATION,
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
                            elif "DPI" in err:
                                pipeline_issues.append(
                                    PipelineIssueCode.PIPELINE_FINAL_DPI_INVALID
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
        visual_quality_acceptable = portrait_quality_passed and matte_quality_passed
        is_valid = rule_compliant and visual_quality_acceptable

        portrait_quality_report = (
            portrait_report_dict
            if portrait_report_dict
            else {
                "passed": False,
                "face_detected": face is not None,
                "face_confidence": face.confidence if face else 0.0,
                "crop_box": None,
                "head_bounding_box": None,
                "geometric_head_bounding_box": None,
                "portrait_composition_box": None,
            }
        )

        matte_quality_report = (
            matte_report_dict
            if matte_report_dict
            else {
                "passed": False,
                "halo_score": 0.0,
                "color_spill_score": 0.0,
                "alpha_continuity": 0.0,
                "background_uniformity": 999.0,
            }
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
            refined_alpha_mask=ref_result.refined_alpha_mask
            if ref_result is not None
            else None,
        )
