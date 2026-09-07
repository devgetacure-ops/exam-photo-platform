import math
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
from exam_photo.providers.crop_planning import (
    CropIssueCode,
    CropModeBResult,
    CropPlanResult,
)
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
    snap_alpha_contrast,
)
from exam_photo.providers.segmenters.mediapipe_segmenter import (
    MediapipeSubjectSegmenter,
)
from exam_photo.rule_validation import validate_exam_rule
from exam_photo.suitability.appearance_signals import (
    measure_appearance_signals,
    measure_face_tone,
)
from exam_photo.suitability.disposition import (
    AppearanceFinding,
    Disposition,
    DispositionReport,
    FindingLevel,
    evaluate_disposition,
)
from exam_photo.suitability.enhancement_planner import (
    EnhancementPlan,
    apply_enhancement,
    plan_enhancement,
    severe_cast_detected,
)
from exam_photo.suitability.issue_codes import SuitabilityIssueCode

# Face-detection confidence ladder.  The primary threshold is the provider
# default; the recovery levels are only consulted when the primary pass returns
# no detections at all (see Stage 3).
_FACE_PRIMARY_CONFIDENCE = 0.5
_FACE_RECOVERY_CONFIDENCES = (0.35, 0.25, 0.15)


def _monochrome_accepted(rule: Optional[ExamRule]) -> Optional[bool]:
    """Whether this exam accepts a black-and-white photograph.

    ``None`` when the conducting body did not specify it, which is neither
    permission nor prohibition and produces no finding (DEC-042).
    """
    if rule is None:
        return None
    if rule.image_requirements is None:
        # DEC-079. Unspecified rather than prohibited, which is the same
        # answer this function already gives for a body that said nothing:
        # an examination with no uploaded photograph has no opinion about
        # whether one may be monochrome.
        return None
    appearance = rule.image_requirements.appearance
    return appearance.monochrome_accepted if appearance is not None else None


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


# Crop issues that leave no usable geometry behind, and therefore genuinely
# stop the pipeline.
#
# The list is short on purpose, and everything absent from it is deliberately
# absent. A clipped head, a head under the exam's coverage floor, a crop that
# could not hold the whole preservation box, a face off centre -- these are
# composition defects, and DEC-041 requires the photograph to be produced and
# the defect reported. What is here instead is structural: no usable input, no
# resolvable target aspect, an output whose aspect does not match the one that
# was asked for, or a provider that failed outright. In each of those the plan
# does not describe a photograph anyone could deliver.
_CROP_UNUSABLE_CODES = frozenset(
    {
        CropIssueCode.CROP_INPUT_INVALID,
        CropIssueCode.CROP_PROVIDER_FAILED,
        CropIssueCode.CROP_TARGET_ASPECT_MISSING,
        CropIssueCode.CROP_TARGET_ASPECT_INVALID,
        CropIssueCode.CROP_ASPECT_RATIO_MISMATCH,
        CropIssueCode.CROP_B_INPUT_INVALID,
        CropIssueCode.CROP_B_PROVIDER_FAILED,
        CropIssueCode.CROP_B_RANGE_MISSING,
        CropIssueCode.CROP_B_RANGE_INVALID,
        CropIssueCode.CROP_B_ASPECT_OUT_OF_RANGE,
    }
)


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
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    save_diagnostic_artifacts: bool = False
    allow_invalid_output: bool = False
    allow_padding: bool = True
    allow_quality_below_minimum: bool = False
    allow_oversize_output: bool = False
    allow_subject_clipping: bool = False

    quality_mode: str = Field(default="balanced", pattern="^(fast|balanced|high)$")

    # DEC-074. Whether the natural enhancement of DEC-043 runs at all. The
    # candidate decides, before they pay, and the default is on because the
    # planner already declines to touch a photograph that needs nothing --
    # a correctly exposed capture comes out of it byte-identical either way.
    enhancement_enabled: bool = True

    # DEC-075. Called with each stage's name as it completes, so a caller can
    # report real progress. Excluded from serialisation -- a callable has no
    # place in the report written to disk -- and never allowed to break a
    # preparation: a courtesy to the interface must not be able to cost a
    # candidate their photograph.
    progress_callback: Optional[Any] = Field(default=None, exclude=True)

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

    # Accept / warn / block, plus the findings behind it (DEC-041). A warn
    # disposition still carries a finished photograph: appearance is never a
    # blocking reason.
    appearance_disposition: Optional[str] = None
    appearance_findings: list[dict[str, Any]] = Field(default_factory=list)
    # What natural enhancement was applied, for disclosure to the candidate
    # (DEC-043). Empty when the photograph needed none, which is the common case.
    enhancements_applied: list[str] = Field(default_factory=list)

    encoded_bytes: bytes | None = Field(default=None, exclude=True)
    #: DEC-076. The same photograph with the lighting correction *not* applied,
    #: composed and compressed in the same pass. Present only where the
    #: correction actually changed something and the alternate compressed under
    #: the same ceiling; `None` means there is nothing to toggle to.
    alternate_encoded_bytes: bytes | None = Field(default=None, exclude=True)
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
        matting_backend: str = "birefnet_onnx",
        birefnet_model_dir: Optional[Path] = None,
        birefnet_expected_sha256: str = "",
    ):
        """``matting_backend`` selects the subject segmentation model.

        ``"birefnet_onnx"`` is the default subject matting backend
        (faster-matting Step 1): the ONNX export of the same BiRefNet
        checkpoint the ``"birefnet"`` (PyTorch) backend uses, same weights
        and same maths, verified numerically equivalent to float tolerance
        by ``scripts/export_birefnet_onnx.py`` before it is trusted, and
        roughly 2x faster on CPU with no torch/transformers dependency.
        ``"birefnet"`` (PyTorch) remains selectable for comparison, and
        ``"mediapipe"`` remains selectable for lightweight diagnostics and
        legacy tests. When either BiRefNet backend is chosen without
        explicit model arguments, the vendored model manifest is resolved
        from the repository root.
        """
        if matting_backend not in ("mediapipe", "birefnet", "birefnet_onnx"):
            raise ValueError(
                f"Unknown matting_backend '{matting_backend}'; expected "
                "'mediapipe', 'birefnet' or 'birefnet_onnx'."
            )
        if (
            matting_backend in ("birefnet", "birefnet_onnx")
            and birefnet_model_dir is None
        ):
            if matting_backend == "birefnet":
                from exam_photo.providers.segmenters.birefnet_segmenter import (
                    load_manifest_defaults,
                )
            else:
                from exam_photo.providers.segmenters.birefnet_onnx_segmenter import (
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
        self._matting_segmenter: Optional[Any] = None
        self._face_landmarker: Optional[Any] = None
        self._face_landmarker_unavailable = False

    def _segmenter_for_matting(self) -> Any:
        """The subject segmenter this pipeline mattes with.

        Both BiRefNet backends are kept warm across calls: their load and
        verification cost real time (the weights, and for the PyTorch backend
        torch itself), unlike MediaPipe's cheap per-call reinitialisation.

        Separated from ``process_rule`` so that a service can build it at boot
        rather than on a candidate's request (DEC-064). It used to be inline,
        which meant the only way to construct the model was to run a whole
        photograph through the pipeline.
        """
        if self.matting_backend not in ("birefnet", "birefnet_onnx"):
            return MediapipeSubjectSegmenter(
                model_path=self.segmenter_model_path,
                expected_sha256=self.segmenter_expected_sha256,
            )

        if self._matting_segmenter is None:
            assert self.birefnet_model_dir is not None
            if self.matting_backend == "birefnet":
                from exam_photo.providers.segmenters.birefnet_segmenter import (
                    BiRefNetSubjectSegmenter,
                )

                self._matting_segmenter = BiRefNetSubjectSegmenter(
                    model_dir=self.birefnet_model_dir,
                    expected_sha256=self.birefnet_expected_sha256,
                )
            else:
                from exam_photo.providers.segmenters.birefnet_onnx_segmenter import (
                    BiRefNetONNXSubjectSegmenter,
                )

                self._matting_segmenter = BiRefNetONNXSubjectSegmenter(
                    model_dir=self.birefnet_model_dir,
                    expected_sha256=self.birefnet_expected_sha256,
                )
        return self._matting_segmenter

    def warmup(self) -> None:
        """Pay the first-inference cost now, so a candidate does not (DEC-064).

        onnxruntime spins up its thread pool and memory arena on the **first
        inference** in a process and never again (DEC-054), which is why this
        runs a real segmentation rather than only constructing the session:
        loading the graph and calling nothing would leave the entire 100-150 s
        penalty for the first candidate while reporting the process ready.

        The image is small and synthetic. The point is to execute the graph,
        not to produce a result, so nothing here is read.
        """
        segmenter = self._segmenter_for_matting()
        probe = Image.new("RGB", (256, 256), (128, 128, 128))
        with segmenter:
            segmenter.segment_subject(probe)

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
            if config.progress_callback is not None:
                try:
                    config.progress_callback(stage.value)
                except Exception:  # noqa: BLE001
                    # DEC-075: progress is a courtesy. Nothing it does may
                    # stop the photograph being made.
                    pass

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
        appearance_report: Optional[DispositionReport] = None
        enhancement_plan: Optional[EnhancementPlan] = None
        decon_image_plain: Any = None
        alternate_prepared: Any = None
        alternate_encoded_bytes: bytes | None = None
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
                                # Possibly ambiguous -- the disposition policy
                                # decides.  Recording the tier matters as much
                                # here as in the single-face branch: leaving it
                                # unset made a multi-face recovery look like a
                                # full-confidence detection, which blocked a
                                # single candidate standing in front of a
                                # printed banner whose spurious second face
                                # exists only at the lowest tier.
                                face_result = retry
                                recovery_used = level
                                break
                dur_stage = (time.perf_counter() - t_stage) * 1000.0

                # A second detection is not automatically a second person
                # (DEC-041).  Requiring exactly one detection rejected a
                # photograph of a single candidate standing in front of a
                # printed banner, where a spurious face appears only at the
                # lowest confidence tier and carries no landmarks.  The
                # disposition policy decides instead, on how large the second
                # face is relative to the first and how hard the detector had
                # to work to find it; anything it does not consider ambiguous
                # proceeds with the largest face.
                subject_ambiguous = False
                if face_result.detections:
                    face = max(
                        face_result.detections,
                        key=lambda d: d.bounding_box.height,
                    )
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

                    detections_for_policy = [
                        face if d is not face else face for d in face_result.detections
                    ]
                    appearance_signals = measure_appearance_signals(
                        norm_result.image,
                        detections_for_policy,
                        detection_confidence=(
                            recovery_used
                            if recovery_used is not None
                            else _FACE_PRIMARY_CONFIDENCE
                        ),
                        landmarks_available=bool(
                            (face.provider_metadata or {}).get(
                                "dense_landmarks_found", False
                            )
                        ),
                        target_height_px=(
                            plan.output_preparation_config.target_height
                            if plan is not None and plan.output_preparation_config
                            else None
                        ),
                        target_head_height_ratio=(
                            plan.crop_config.target_head_height_ratio
                            if plan is not None and plan.crop_config
                            else None
                        ),
                    )
                    appearance_report = evaluate_disposition(
                        appearance_signals,
                        monochrome_accepted=_monochrome_accepted(rule),
                    )
                    subject_ambiguous = (
                        appearance_report.disposition is Disposition.BLOCK
                    )

                if face_result.detections and not subject_ambiguous:
                    count = len(face_result.detections)
                    detected = (
                        "Exactly 1 face detected."
                        if count == 1
                        else f"{count} faces detected; the largest is the subject."
                    )
                    if recovery_used is not None:
                        detected = (
                            detected[:-1]
                            + f" at recovery confidence {recovery_used:.2f}."
                        )
                    record_stage(
                        PipelineStage.FACE_DETECTION,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage,
                        summary=detected + landmark_note,
                    )
                else:
                    face = None
                    failed = True
                    pipeline_issues.append(
                        PipelineIssueCode.PIPELINE_FACE_COUNT_INVALID
                    )
                    record_stage(
                        PipelineStage.FACE_DETECTION,
                        PipelineStageStatus.FAILED,
                        issues=["FACE_COUNT_INVALID"],
                        dur=dur_stage,
                        summary=(
                            appearance_report.block_reason
                            if appearance_report is not None
                            and appearance_report.block_reason
                            else "No face was detected in this photograph."
                        ),
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
                segmenter: Any = self._segmenter_for_matting()
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
                    trust_input_alpha=(
                        self.matting_backend in ("birefnet", "birefnet_onnx")
                    ),
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

                crop_unusable = [
                    code
                    for code in crop_res.validation.issue_codes
                    if code in _CROP_UNUSABLE_CODES
                ]
                if not crop_res.validation.is_valid and crop_unusable:
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
                        summary=(
                            "Crop planning produced no usable geometry: "
                            f"{', '.join(str(c) for c in crop_unusable)}."
                        ),
                    )
                elif not crop_res.validation.is_valid:
                    # Composition fell short, but the plan is geometrically
                    # usable, so the candidate still receives a photograph.
                    #
                    # DEC-041 states it without qualification: no stage anywhere
                    # in the pipeline may block for an appearance or composition
                    # reason. Only an undecodable file, no detectable face, or a
                    # genuinely ambiguous subject may refuse. This branch used to
                    # fail on any invalid crop, which quietly made the crop
                    # planner an exception to that policy -- and the constraints
                    # it was failing on are precisely composition ones. Measured
                    # on the reviewed set, a photograph the owner had labelled
                    # perfect produced nothing at all on three of five real exam
                    # rules, because its subject's hair pins the crop's sides and
                    # head coverage lands under the exam's published floor.
                    #
                    # A crop under the coverage floor is exactly the compromise
                    # DEC-039 already decided to deliver and report rather than
                    # refuse; blocking here discarded the tightest crop the
                    # geometry allowed and returned nothing in its place, which
                    # is worse on the published requirement and on every other
                    # axis. The issue codes travel with the result, so the
                    # compromise stays visible downstream.
                    pipeline_issues.append(PipelineIssueCode.PIPELINE_CROP_FAILED)
                    record_stage(
                        PipelineStage.CROP_CANDIDATE_SCORING,
                        PipelineStageStatus.WARNING,
                        issues=crop_res.validation.issue_codes,
                        dur=dur_stage / 2,
                        summary="Crop selected under a composition compromise.",
                    )
                    record_stage(
                        PipelineStage.CROP_PLANNING,
                        PipelineStageStatus.WARNING,
                        issues=crop_res.validation.issue_codes,
                        dur=dur_stage / 2,
                        summary=(
                            "Crop planned with composition compromises: "
                            f"{crop_res.crop_box}"
                        ),
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

        # Stage 7A: Crop-region matte refinement (DEC-040).
        #
        # The matting model sees a fixed-size square (512 for BiRefNet), so the
        # alpha detail any part of the subject receives is set by how much of
        # the *source frame* that part occupies -- not by how large it will be
        # in the finished photo.  Candidates routinely submit half- or
        # full-body photos, and the finished exam photo is a tight head crop,
        # so the head is the small part of the input that becomes the whole
        # output.  Measured over the 60-photo reference set: the head arrives
        # with a median of 121 px of alpha detail (worst 42 px) and is then
        # magnified by a median 2.1x, worst 17.4x, into the output.  Every
        # photo with visible hair-edge streaking, halo or colour bleed sits in
        # the high-magnification group.
        #
        # Re-running the matte on just the planned crop region spends the
        # model's whole resolution budget on the part that survives, at the
        # cost of one extra inference.  The crop geometry is already decided
        # and is not revisited here, so this cannot feed back into planning.
        if (
            not failed
            and norm_result is not None
            and ref_result is not None
            and crop_res is not None
            and crop_res.crop_box is not None
            and self._matting_segmenter is not None
        ):
            t_stage = time.perf_counter()
            try:
                alpha_full = ref_result.refined_alpha_mask
                src_w, src_h = norm_result.image.size
                box = crop_res.crop_box
                # A margin beyond the crop keeps the model from having to guess
                # at the frame edge, where it is least reliable, and gives
                # decontamination opaque neighbours to propagate from.
                margin_x = 0.12 * (box.right - box.left)
                margin_y = 0.12 * (box.bottom - box.top)
                rx0 = max(0, int(math.floor(box.left - margin_x)))
                ry0 = max(0, int(math.floor(box.top - margin_y)))
                rx1 = min(src_w, int(math.ceil(box.right + margin_x)))
                ry1 = min(src_h, int(math.ceil(box.bottom + margin_y)))

                region_area = max(1, (rx1 - rx0) * (ry1 - ry0))
                gain = math.sqrt((src_w * src_h) / region_area)
                if rx1 - rx0 >= 32 and ry1 - ry0 >= 32 and gain >= 1.15:
                    region = norm_result.image.crop((rx0, ry0, rx1, ry1))
                    region_result = self._matting_segmenter.segment_subject(region)
                    region_alpha = np.clip(
                        region_result.probability_mask.astype(np.float32), 0.0, 1.0
                    )
                    # This splice bypasses MorphologicalForegroundRefiner
                    # entirely (it calls the segmenter directly), so the
                    # trusted-alpha path's anti-halo contrast snap never runs
                    # on it unless it is applied here too -- otherwise the
                    # crop region, which is what most of the delivered photo
                    # actually shows, would keep the raw model's broad
                    # low-confidence band even after the whole-frame alpha it
                    # replaces was corrected.
                    default_alpha_thresholds = RefinementConfig()
                    region_alpha = snap_alpha_contrast(
                        region_alpha,
                        default_alpha_thresholds.alpha_snap_low_threshold,
                        default_alpha_thresholds.alpha_snap_high_threshold,
                    )
                    refreshed = np.array(alpha_full, dtype=np.float32, copy=True)
                    refreshed[ry0:ry1, rx0:rx1] = region_alpha
                    ref_result.refined_alpha_mask = refreshed
                    dur_stage = (time.perf_counter() - t_stage) * 1000.0
                    record_stage(
                        PipelineStage.MASK_REFINEMENT,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage,
                        summary=(
                            "Matte recomputed on the crop region at "
                            f"{gain:.1f}x the effective alpha resolution."
                        ),
                    )
                else:
                    record_stage(
                        PipelineStage.MASK_REFINEMENT,
                        PipelineStageStatus.SKIPPED,
                        dur=(time.perf_counter() - t_stage) * 1000.0,
                        summary=(
                            "Crop region is close to the full frame; the "
                            "existing matte already carries full detail."
                        ),
                    )
            except Exception as e:  # noqa: BLE001
                # The full-frame matte is still perfectly usable, so a failure
                # here degrades edge detail rather than the whole photo.
                record_stage(
                    PipelineStage.MASK_REFINEMENT,
                    PipelineStageStatus.WARNING,
                    issues=["CROP_REGION_MATTE_FAILED"],
                    dur=0.0,
                    summary=f"Crop-region matte refinement failed: {e}",
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

                # Natural enhancement (DEC-043), applied to the source before
                # compositing so the replacement background is laid down at the
                # rule's exact colour afterwards and cannot be tinted by an
                # adjustment meant for the subject.
                tone = (
                    measure_face_tone(norm_result.image, [face])
                    if config.enhancement_enabled
                    and norm_result is not None
                    and face is not None
                    else None
                )
                if tone is not None:
                    enhancement_plan = plan_enhancement(tone)
                    if not enhancement_plan.is_noop:
                        # DEC-076: keep the uncorrected foreground so the other
                        # variant can be composed in the same pass. Only when
                        # the correction actually changes something -- for a
                        # photograph that needed nothing the two are the same
                        # image and there is nothing to toggle between.
                        decon_image_plain = decon_image
                        decon_image = apply_enhancement(decon_image, enhancement_plan)
                    if severe_cast_detected(tone) and appearance_report is not None:
                        appearance_report.findings.append(
                            AppearanceFinding(
                                code=SuitabilityIssueCode.SUITABILITY_LOW_CONTRAST_WARNING,
                                level=FindingLevel.LIKELY_REJECTION,
                                message=(
                                    "This photograph was taken under strongly "
                                    "coloured lighting. We have reduced it, but "
                                    "the skin tone may still look unnatural."
                                ),
                                remedy=(
                                    "Retake the photograph in daylight or under "
                                    "ordinary white indoor lighting."
                                ),
                                measured_value=tone.blue_minus_red,
                            )
                        )

                prepared_image = premultiply_crop_resize_composite(
                    image=decon_image,
                    alpha=ref_result.refined_alpha_mask,
                    crop_box=crop_res.crop_box,
                    target_size=(target_w, target_h),
                    background_color=rgb_color_tuple,
                    allow_transparent_output=allow_trans,
                )
                if decon_image_plain is not None:
                    # DEC-076. The same geometry, the same mask, the same
                    # background -- only the foreground's tone differs, so the
                    # two variants can never disagree about anything a rule
                    # measures except their byte size. Costs one composite and
                    # no model inference, which is why toggling can be instant.
                    alternate_prepared = premultiply_crop_resize_composite(
                        image=decon_image_plain,
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
                    # Reported, never blocking (DEC-041).  A subject that fills
                    # too little of the frame, or whose hair reaches the top
                    # edge, is a composition concern -- and the approved
                    # reference outputs let hair reach or leave the edge on most
                    # photographs.  Failing here contradicted the disposition
                    # contract from inside the pipeline: two photographs that
                    # the policy had already judged acceptable still produced
                    # nothing, which is the outcome the policy exists to
                    # prevent.  Genuinely unusable mattes are caught earlier by
                    # the segmentation mask validation.
                    record_stage(
                        PipelineStage.BACKGROUND_COMPOSITION,
                        PipelineStageStatus.WARNING,
                        issues=bg_issues,
                        dur=dur_stage / 2,
                        summary=(
                            "Composed with a background composition concern: "
                            + ", ".join(bg_issues)
                        ),
                    )
                    if appearance_report is not None:
                        appearance_report.findings.append(
                            AppearanceFinding(
                                code=SuitabilityIssueCode.SUITABILITY_FACE_REGION_TOO_SMALL
                                if "BACKGROUND_FOREGROUND_TOO_SMALL" in bg_issues
                                else SuitabilityIssueCode.SUITABILITY_HEAD_TOP_CLIPPED,
                                level=FindingLevel.POSSIBLE_ISSUE,
                                message=(
                                    "You appear small in the frame, so the crop "
                                    "is loose."
                                    if "BACKGROUND_FOREGROUND_TOO_SMALL" in bg_issues
                                    else "Your hair reaches the edge of the photo."
                                ),
                                remedy=(
                                    "Retake the photograph standing closer to "
                                    "the camera."
                                    if "BACKGROUND_FOREGROUND_TOO_SMALL" in bg_issues
                                    else "Retake with a little more space above "
                                    "your head."
                                ),
                            )
                        )
                    record_stage(
                        PipelineStage.OUTPUT_PREPARATION,
                        PipelineStageStatus.PASSED,
                        dur=dur_stage / 2,
                        summary=f"Prepared output successfully with dimensions {target_w}x{target_h}.",
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
                if alternate_prepared is not None:
                    # DEC-076: the same ceiling and the same search, so the
                    # alternate is a compliant file in its own right rather
                    # than a preview of one. If it cannot be compressed under
                    # the ceiling it is dropped and there is simply nothing to
                    # toggle to -- never served as though it passed.
                    try:
                        alt = compressor.compress_output(
                            alternate_prepared, plan.compression_config
                        )
                        if alt.validation.is_valid:
                            alternate_encoded_bytes = alt.encoded_bytes
                    except Exception:  # noqa: BLE001
                        alternate_encoded_bytes = None
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
            appearance_disposition=(
                appearance_report.disposition.value
                if appearance_report is not None
                else None
            ),
            appearance_findings=(
                [f.model_dump(mode="json") for f in appearance_report.findings]
                if appearance_report is not None
                else []
            ),
            enhancements_applied=(
                list(enhancement_plan.applied) if enhancement_plan is not None else []
            ),
            portrait_quality_report=portrait_quality_report,
            matte_quality_report=matte_quality_report,
            encoded_bytes=comp_result.encoded_bytes
            if comp_result is not None
            else None,
            alternate_encoded_bytes=alternate_encoded_bytes,
            refined_alpha_mask=ref_result.refined_alpha_mask
            if ref_result is not None
            else None,
        )
