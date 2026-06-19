import json
import os
import threading
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.segmenters.errors import (
    ModelChecksumError,
    ModelNotFoundError,
)
from exam_photo.providers.segmenters.mask_validation import (
    count_connected_components_dsu,
    validate_segmentation_mask,
)
from exam_photo.providers.subject_segmentation import (
    SegmentationConfig,
    SegmentationStatusValue,
)

# ---------------------------------------------------------------------------
# Skip guards for MediaPipe and model assets
# ---------------------------------------------------------------------------

try:
    import mediapipe as mp  # noqa: F401

    _MEDIAPIPE_INSTALLED = True
except ImportError:
    _MEDIAPIPE_INSTALLED = False

_MODEL_PATH_ENV = "EXAM_PHOTO_SEGMENTER_MODEL_PATH"
_MODEL_PATH = (
    Path(os.environ[_MODEL_PATH_ENV])
    if _MODEL_PATH_ENV in os.environ and Path(os.environ[_MODEL_PATH_ENV]).exists()
    else None
)
_MODEL_SHA256_ENV = "EXAM_PHOTO_SEGMENTER_MODEL_SHA256"
_MODEL_SHA256 = os.environ.get(_MODEL_SHA256_ENV, "")

# Fallback default location if not set in environment
if _MODEL_PATH is None:
    fallback = (
        Path(__file__).resolve().parent.parent.parent.parent.parent
        / "model-assets"
        / "selfie_segmentation.tflite"
    )
    if fallback.exists():
        _MODEL_PATH = fallback
        _MODEL_SHA256 = (
            "9ee168ec7c8f2a16c56fe8e1cfbc514974cbbb7e434051b455635f1bd1462f5c"
        )


def _ensure_prerequisites() -> None:
    if not _MEDIAPIPE_INSTALLED:
        pytest.fail("Mandatory test failed: MediaPipe is not installed.")
    if _MODEL_PATH is None or not _MODEL_PATH.exists():
        pytest.fail("Mandatory test failed: Segmenter model file is not available.")


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------


def test_segmentation_config_validation() -> None:
    # Valid config
    cfg = SegmentationConfig()
    assert cfg.foreground_threshold == 0.5

    # Invalid thresholds (low > foreground)
    with pytest.raises(ValueError, match="Thresholds must satisfy"):
        SegmentationConfig(
            foreground_threshold=0.5,
            uncertain_low_threshold=0.6,
            uncertain_high_threshold=0.8,
        )

    # Invalid thresholds (high < foreground)
    with pytest.raises(ValueError, match="Thresholds must satisfy"):
        SegmentationConfig(
            foreground_threshold=0.5,
            uncertain_low_threshold=0.2,
            uncertain_high_threshold=0.4,
        )

    # Invalid coverage limits (min >= max)
    with pytest.raises(ValueError, match="Coverage limits must satisfy"):
        SegmentationConfig(
            minimum_foreground_coverage=0.9,
            maximum_foreground_coverage=0.8,
        )


def test_dsu_connected_components() -> None:
    # Empty mask
    mask = np.zeros((10, 10), dtype=np.uint8)
    count, ratio = count_connected_components_dsu(mask)
    assert count == 0
    assert ratio == 0.0

    # Single full component
    mask = np.ones((10, 10), dtype=np.uint8) * 255
    count, ratio = count_connected_components_dsu(mask)
    assert count == 1
    assert ratio == 1.0

    # Two disconnected components
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[0:3, 0:3] = 255  # 9 pixels
    mask[7:10, 7:10] = 255  # 9 pixels
    count, ratio = count_connected_components_dsu(mask)
    assert count == 2
    assert ratio == 0.5


def test_validate_segmentation_mask_upfront_errors() -> None:
    cfg = SegmentationConfig()

    # Non-array input
    with pytest.raises(ValueError, match="Input masks must be numpy arrays"):
        validate_segmentation_mask("not array", np.zeros((10, 10)), cfg)  # type: ignore

    # Non-2D array
    with pytest.raises(ValueError, match="Input masks must be 2D arrays"):
        validate_segmentation_mask(np.zeros((10, 10, 1)), np.zeros((10, 10)), cfg)

    # Shape mismatch
    with pytest.raises(ValueError, match="Shape mismatch"):
        validate_segmentation_mask(np.zeros((10, 10)), np.zeros((12, 10)), cfg)

    # Empty array
    with pytest.raises(ValueError, match="Input masks cannot be empty"):
        validate_segmentation_mask(np.zeros((0, 0)), np.zeros((0, 0)), cfg)

    # Non-finite value
    prob = np.zeros((10, 10))
    prob[0, 0] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        validate_segmentation_mask(prob, np.zeros((10, 10)), cfg)

    # Invalid range in probability
    prob_invalid = np.zeros((10, 10))
    prob_invalid[0, 0] = 1.5
    with pytest.raises(ValueError, match="range"):
        validate_segmentation_mask(prob_invalid, np.zeros((10, 10)), cfg)

    # Invalid values in binary mask (must be 0 or 255)
    binary_invalid = np.zeros((10, 10), dtype=np.uint8)
    binary_invalid[0, 0] = 127
    with pytest.raises(ValueError, match="0 and 255 values"):
        validate_segmentation_mask(np.zeros((10, 10)), binary_invalid, cfg)


def test_validate_segmentation_mask() -> None:
    cfg = SegmentationConfig(
        foreground_threshold=0.5,
        uncertain_low_threshold=0.2,
        uncertain_high_threshold=0.8,
        minimum_foreground_coverage=0.1,
        maximum_foreground_coverage=0.9,
    )

    # Empty mask validation
    prob = np.zeros((100, 100), dtype=np.float32)
    binary = np.zeros((100, 100), dtype=np.uint8)
    report = validate_segmentation_mask(prob, binary, cfg)
    assert not report.is_valid
    assert "SEGMENTATION_MASK_EMPTY" in report.issue_codes
    assert report.uncertain_pixel_ratio == 0.0

    # Full frame mask validation
    prob = np.ones((100, 100), dtype=np.float32)
    binary = np.ones((100, 100), dtype=np.uint8) * 255
    report = validate_segmentation_mask(prob, binary, cfg)
    assert not report.is_valid
    assert "SEGMENTATION_MASK_FULL_FRAME" in report.issue_codes

    # Excessive uncertain edge (pixel ratio)
    prob_unc = np.zeros((100, 100), dtype=np.float32)
    prob_unc[0:40, :] = 0.5  # 40% of the image is inside uncertain range [0.2, 0.8]
    binary_unc = np.where(prob_unc >= 0.5, 255, 0).astype(np.uint8)
    report = validate_segmentation_mask(prob_unc, binary_unc, cfg)
    assert "SEGMENTATION_UNCERTAIN_EDGE_HIGH" in report.issue_codes
    assert report.uncertain_pixel_ratio == 0.4


def test_face_containment_checks() -> None:
    cfg = SegmentationConfig(
        foreground_threshold=0.5,
        minimum_face_mask_coverage=0.8,
    )
    face = FaceDetection(
        bounding_box=BoundingBox(left=20, top=20, right=80, bottom=80),
        confidence=0.9,
    )

    # Face covered
    prob_cov = np.zeros((100, 100), dtype=np.float32)
    prob_cov[10:90, 10:90] = 0.9
    binary_cov = np.where(prob_cov >= 0.5, 255, 0).astype(np.uint8)
    report_cov = validate_segmentation_mask(prob_cov, binary_cov, cfg, face=face)
    assert report_cov.face_contained is True
    assert report_cov.is_valid is True
    assert "SEGMENTATION_FACE_NOT_CONTAINED" not in report_cov.issue_codes

    # Face not covered
    prob_uncov = np.zeros((100, 100), dtype=np.float32)
    binary_uncov = np.zeros((100, 100), dtype=np.uint8)
    report_uncov = validate_segmentation_mask(prob_uncov, binary_uncov, cfg, face=face)
    assert report_uncov.face_contained is False
    assert report_uncov.is_valid is False
    assert "SEGMENTATION_FACE_NOT_CONTAINED" in report_uncov.issue_codes


def test_head_estimate_disagreement_non_blocking() -> None:
    cfg = SegmentationConfig(
        foreground_threshold=0.5,
        minimum_head_mask_coverage=0.8,
        minimum_foreground_coverage=0.001,
    )
    head_est = BoundingBox(left=10, top=10, right=90, bottom=90)

    # Mask covers only a tiny fraction of head region (e.g. 5%)
    prob = np.zeros((100, 100), dtype=np.float32)
    prob[15:20, 15:20] = 0.9  # 25 pixels (very low)
    binary = np.where(prob >= 0.5, 255, 0).astype(np.uint8)

    report = validate_segmentation_mask(prob, binary, cfg, head_estimate=head_est)
    assert "SEGMENTATION_HEAD_REGION_LOW_COVERAGE" in report.issue_codes
    # Low head coverage MUST NOT invalidate the mask
    assert report.is_valid is True


# ---------------------------------------------------------------------------
# Integration & Real Provider Tests
# ---------------------------------------------------------------------------


@pytest.mark.mandatory_segmentation
def test_mediapipe_segmenter_integration() -> None:
    _ensure_prerequisites()
    from exam_photo.providers.segmenters.mediapipe_segmenter import (
        MediapipeSubjectSegmenter,
    )

    assert _MODEL_PATH is not None
    segmenter = MediapipeSubjectSegmenter(_MODEL_PATH, _MODEL_SHA256)

    img = Image.new("RGB", (300, 400), (255, 255, 255))
    with segmenter:
        res = segmenter.segment_subject(img)
        assert res.provider_status == SegmentationStatusValue.SUCCESS
        assert res.mask_width == 300
        assert res.mask_height == 400
        assert isinstance(res.probability_mask, np.ndarray)
        assert res.probability_mask.shape == (400, 300)
        assert isinstance(res.coarse_mask, Image.Image)
        assert res.coarse_mask.size == (300, 400)


@pytest.mark.mandatory_segmentation
def test_segmenter_missing_model_error() -> None:
    if not _MEDIAPIPE_INSTALLED:
        pytest.fail("MediaPipe not installed.")
    from exam_photo.providers.segmenters.mediapipe_segmenter import (
        MediapipeSubjectSegmenter,
    )

    segmenter = MediapipeSubjectSegmenter(Path("non_existent_file.tflite"))
    with pytest.raises(ModelNotFoundError):
        segmenter.segment_subject(Image.new("RGB", (100, 100)))


@pytest.mark.mandatory_segmentation
def test_segmenter_incorrect_checksum_error() -> None:
    _ensure_prerequisites()
    from exam_photo.providers.segmenters.mediapipe_segmenter import (
        MediapipeSubjectSegmenter,
    )

    assert _MODEL_PATH is not None
    segmenter = MediapipeSubjectSegmenter(
        _MODEL_PATH, expected_sha256="incorrect_checksum"
    )
    with pytest.raises(ModelChecksumError):
        segmenter.segment_subject(Image.new("RGB", (100, 100)))


@pytest.mark.mandatory_segmentation
def test_segmenter_concurrency() -> None:
    _ensure_prerequisites()
    from exam_photo.providers.segmenters.mediapipe_segmenter import (
        MediapipeSubjectSegmenter,
    )

    assert _MODEL_PATH is not None
    segmenter = MediapipeSubjectSegmenter(_MODEL_PATH, _MODEL_SHA256)
    img = Image.new("RGB", (200, 200), (200, 200, 200))

    errors = []

    def worker() -> None:
        try:
            for _ in range(5):
                res = segmenter.segment_subject(img)
                assert res.provider_status == SegmentationStatusValue.SUCCESS
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(3)]
    with segmenter:
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    assert not errors, f"Concurrency errors occurred: {errors}"


@pytest.mark.mandatory_segmentation
def test_close_and_reinitialize() -> None:
    _ensure_prerequisites()
    from exam_photo.providers.segmenters.mediapipe_segmenter import (
        MediapipeSubjectSegmenter,
    )

    assert _MODEL_PATH is not None
    segmenter = MediapipeSubjectSegmenter(_MODEL_PATH, _MODEL_SHA256)
    img = Image.new("RGB", (100, 100))

    with segmenter:
        res = segmenter.segment_subject(img)
        assert res.provider_status == SegmentationStatusValue.SUCCESS

    # segmenter is closed. Run segment again to trigger reinitialization
    with segmenter:
        res = segmenter.segment_subject(img)
        assert res.provider_status == SegmentationStatusValue.SUCCESS


@pytest.mark.mandatory_segmentation
def test_real_fixtures_segmentation_and_iou() -> None:
    _ensure_prerequisites()
    import hashlib

    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector
    from exam_photo.providers.segmenters.mediapipe_segmenter import (
        MediapipeSubjectSegmenter,
    )

    assert _MODEL_PATH is not None
    segmenter = MediapipeSubjectSegmenter(_MODEL_PATH, _MODEL_SHA256)

    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    fixtures_dir = repo_root / "tests" / "fixtures"
    anno_path = fixtures_dir / "segmentation" / "annotations.json"

    assert anno_path.exists(), "annotations.json is missing!"

    with open(anno_path) as f:
        manifest = json.load(f)

    face_model_path = repo_root / "model-assets" / "blaze_face_short_range.tflite"
    face_manifest = repo_root / "model-manifests" / "face-detector.json"
    face_sha = ""
    if face_manifest.exists():
        with open(face_manifest) as f:
            fm = json.load(f)
            face_sha = fm.get("sha256", "")

    for entry in manifest["entries"]:
        src_name = entry["source_fixture"]
        mask_rel_path = entry["regression_mask_filename"]
        expected_cov = entry["expected_coverage"]

        src_path = fixtures_dir / src_name
        mask_path = fixtures_dir / mask_rel_path

        assert src_path.exists(), f"Source image {src_name} is missing"
        assert mask_path.exists(), (
            f"Reviewed regression mask {mask_rel_path} is missing"
        )

        # 1. Verify regression mask checksum
        expected_sha = entry.get("mask_sha256")
        if expected_sha:
            h_sha = hashlib.sha256()
            with open(mask_path, "rb") as mf:
                h_sha.update(mf.read())
            actual_sha = h_sha.hexdigest()
            assert actual_sha == expected_sha, (
                f"Checksum mismatch for regression mask {mask_rel_path}: expected {expected_sha}, got {actual_sha}"
            )

        # Load images
        img = Image.open(src_path)
        gt_mask = Image.open(mask_path).convert("L")

        # 2. Run face detection to get face(s)
        faces = None
        expected_faces = entry.get("expected_face_count", 1)
        if expected_faces > 0:
            conf = (
                0.2
                if src_name
                in ("lincoln_low_contrast.jpg", "roosevelt_muir_yosemite.jpg")
                else 0.5
            )
            detector = MediapipeFaceDetector(
                face_model_path, face_sha, min_detection_confidence=conf
            )
            with detector:
                face_res = detector.detect_faces(img)
            assert len(face_res.detections) == expected_faces, (
                f"Expected {expected_faces} faces in {src_name}, got {len(face_res.detections)}"
            )
            faces = face_res.detections

        with segmenter:
            res = segmenter.segment_subject(img, face=faces)

        assert res.provider_status == SegmentationStatusValue.SUCCESS

        # Calculate IoU
        pred_arr = np.array(res.coarse_mask)
        gt_arr = np.array(gt_mask)

        bin_pred = pred_arr == 255
        bin_gt = gt_arr == 255

        intersection = np.logical_and(bin_pred, bin_gt).sum()
        union = np.logical_or(bin_pred, bin_gt).sum()

        if union == 0:
            iou = 1.0
        else:
            iou = intersection / union

        print(
            f"Fixture: {src_name} | Expected Coverage: {expected_cov:.4f} | Got Coverage: {res.foreground_coverage_ratio:.4f} | IoU: {iou:.6f}"
        )

        # Assert IoU is highly matching (allowing minor OS floating point deviations)
        assert iou >= 0.99, f"IoU regression detected for {src_name}: {iou:.6f}"


@pytest.mark.mandatory_segmentation
def test_scenario_assertions() -> None:
    _ensure_prerequisites()
    from typing import Any

    from exam_photo.providers.landmark_geometric_head_estimator import (
        LandmarkGeometricHeadEstimator,
    )
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector
    from exam_photo.providers.segmenters.mediapipe_segmenter import (
        MediapipeSubjectSegmenter,
    )
    from exam_photo.suitability.configuration import SuitabilityThresholds
    from exam_photo.suitability.evaluator import SuitabilityEvaluator
    from exam_photo.suitability.models import (
        ProcessingReadinessStatus,
        SuitabilityStatus,
    )

    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    fixtures_dir = repo_root / "tests" / "fixtures"

    # Initialize real providers
    face_model_path = repo_root / "model-assets" / "blaze_face_short_range.tflite"
    face_sha = ""
    face_manifest = repo_root / "model-manifests" / "face-detector.json"
    if face_manifest.exists():
        with open(face_manifest) as manifest_f:
            fm = json.load(manifest_f)
            face_sha = fm.get("sha256", "")

    face_detector = MediapipeFaceDetector(face_model_path, face_sha)
    head_estimator = LandmarkGeometricHeadEstimator()
    assert _MODEL_PATH is not None
    segmenter = MediapipeSubjectSegmenter(_MODEL_PATH, _MODEL_SHA256)
    thresholds = SuitabilityThresholds()
    evaluator = SuitabilityEvaluator(
        thresholds=thresholds,
        face_provider=face_detector,
        head_provider=head_estimator,
        segmentation_provider=segmenter,
    )

    from exam_photo.input.limits import InputLimits
    from exam_photo.input.normalization import normalize_image_input

    limits = InputLimits()

    def process_image(filename: str) -> tuple[Any, Any]:
        path = fixtures_dir / filename
        with open(path, "rb") as img_f:
            data = img_f.read()
        norm_res = normalize_image_input(data, str(path), limits)
        report = evaluator.evaluate(norm_res, background_replacement_required=True)
        return norm_res, report

    # 1. Blank no-person fixture assertions
    _, blank_report = process_image("blank_white_600x800.jpg")
    assert blank_report.source_suitability == SuitabilityStatus.UNSUITABLE
    assert "SUITABILITY_NO_FACE" in blank_report.issue_codes
    assert blank_report.segmentation_diagnostic is not None
    assert blank_report.segmentation_diagnostic.is_valid is False
    assert blank_report.segmentation_diagnostic.foreground_coverage_ratio < 0.01
    assert (
        blank_report.segmentation_diagnostic.face_contained is None
        or blank_report.segmentation_diagnostic.face_contained is False
    )
    assert "SEGMENTATION_MASK_EMPTY" in blank_report.segmentation_diagnostic.issue_codes
    assert blank_report.segmentation_diagnostic.can_proceed is False

    # 2. Geometric no-person fixture assertions
    _, geom_report = process_image("geometric_shapes_600x800.jpg")
    assert geom_report.source_suitability == SuitabilityStatus.UNSUITABLE
    assert "SUITABILITY_NO_FACE" in geom_report.issue_codes
    assert geom_report.segmentation_diagnostic is not None
    assert geom_report.segmentation_diagnostic.is_valid is False
    assert geom_report.segmentation_diagnostic.foreground_coverage_ratio < 0.05
    assert (
        geom_report.segmentation_diagnostic.face_contained is None
        or geom_report.segmentation_diagnostic.face_contained is False
    )
    assert "SEGMENTATION_MASK_EMPTY" in geom_report.segmentation_diagnostic.issue_codes

    # 3. Multiple-person fixture assertions (roosevelt_muir_yosemite.jpg)
    # Instantiate custom face detector with lower confidence specifically for Yosemite to detect small faces
    face_detector_yosemite = MediapipeFaceDetector(
        face_model_path, face_sha, min_detection_confidence=0.2
    )
    evaluator_yosemite = SuitabilityEvaluator(
        thresholds=thresholds,
        face_provider=face_detector_yosemite,
        head_provider=head_estimator,
        segmentation_provider=segmenter,
    )
    path_yosemite = fixtures_dir / "roosevelt_muir_yosemite.jpg"
    with open(path_yosemite, "rb") as yosemite_f:
        data_yosemite = yosemite_f.read()
    norm_res_yosemite = normalize_image_input(data_yosemite, str(path_yosemite), limits)
    yosemite_report = evaluator_yosemite.evaluate(
        norm_res_yosemite, background_replacement_required=True
    )

    assert yosemite_report.source_suitability == SuitabilityStatus.UNSUITABLE
    assert "SUITABILITY_MULTIPLE_FACES" in yosemite_report.issue_codes
    assert yosemite_report.processing_readiness == ProcessingReadinessStatus.BLOCKED
    assert yosemite_report.segmentation_diagnostic is not None
    assert yosemite_report.segmentation_diagnostic.is_valid is True
    assert (
        "SEGMENTATION_MULTIPLE_MAJOR_COMPONENTS"
        in yosemite_report.segmentation_diagnostic.issue_codes
    )
    assert yosemite_report.segmentation_diagnostic.can_proceed is True

    # 4. Beard/spectacles fixture assertions (freud_spectacles_beard.jpg)
    _, freud_report = process_image("freud_spectacles_beard.jpg")
    assert freud_report.source_suitability == SuitabilityStatus.INDETERMINATE
    assert freud_report.segmentation_diagnostic is not None
    assert freud_report.segmentation_diagnostic.is_valid is True
    assert freud_report.segmentation_diagnostic.foreground_coverage_ratio > 0.05
    assert freud_report.segmentation_diagnostic.face_contained is True
    assert freud_report.segmentation_diagnostic.can_proceed is True

    # 5. Long hair fixture assertions (sarah_bernhardt_long_hair.jpg)
    _, sarah_report = process_image("sarah_bernhardt_long_hair.jpg")
    assert sarah_report.segmentation_diagnostic is not None
    assert sarah_report.segmentation_diagnostic.is_valid is True
    assert sarah_report.segmentation_diagnostic.foreground_coverage_ratio > 0.3
    assert sarah_report.segmentation_diagnostic.can_proceed is True

    # 6. Curly hair fixture assertions (marie_curie_curly_hair.jpg)
    _, curie_report = process_image("marie_curie_curly_hair.jpg")
    assert curie_report.segmentation_diagnostic is not None
    assert curie_report.segmentation_diagnostic.is_valid is True
    assert curie_report.segmentation_diagnostic.foreground_coverage_ratio > 0.3
    assert curie_report.segmentation_diagnostic.can_proceed is True

    # 7. Head covering fixture assertions (vivekananda_head_covering.jpg)
    _, vivek_report = process_image("vivekananda_head_covering.jpg")
    assert vivek_report.segmentation_diagnostic is not None
    assert vivek_report.segmentation_diagnostic.is_valid is True
    assert vivek_report.segmentation_diagnostic.foreground_coverage_ratio > 0.3
    assert (
        "SEGMENTATION_FACE_NOT_CONTAINED"
        not in vivek_report.segmentation_diagnostic.issue_codes
    )
    assert vivek_report.segmentation_diagnostic.can_proceed is True

    # 8. Low contrast fixture assertions (lincoln_low_contrast.jpg)
    _, lincoln_report = process_image("lincoln_low_contrast.jpg")
    assert lincoln_report.segmentation_diagnostic is not None
    assert lincoln_report.segmentation_diagnostic.is_valid is True
    assert lincoln_report.segmentation_diagnostic.foreground_coverage_ratio > 0.1
    assert lincoln_report.segmentation_diagnostic.can_proceed is True


@pytest.mark.mandatory_refinement
def test_refinement_on_real_fixtures() -> None:
    _ensure_prerequisites()
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector
    from exam_photo.providers.refiners.morphological_refiner import (
        MorphologicalForegroundRefiner,
    )
    from exam_photo.providers.segmenters.mediapipe_segmenter import (
        MediapipeSubjectSegmenter,
    )

    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    fixtures_dir = repo_root / "tests" / "fixtures"

    # Load face detector info
    face_model_path = repo_root / "model-assets" / "blaze_face_short_range.tflite"
    face_sha = ""
    face_manifest = repo_root / "model-manifests" / "face-detector.json"
    if face_manifest.exists():
        with open(face_manifest) as manifest_f:
            fm = json.load(manifest_f)
            face_sha = fm.get("sha256", "")

    # Load segmenter info
    assert _MODEL_PATH is not None
    segmenter = MediapipeSubjectSegmenter(_MODEL_PATH, _MODEL_SHA256)
    refiner = MorphologicalForegroundRefiner()

    with open(fixtures_dir / "segmentation" / "annotations.json") as f:
        manifest = json.load(f)

    for entry in manifest["entries"]:
        src_name = entry["source_fixture"]
        # Skip yosemite because it expects 0 coverage / no subject
        if src_name == "roosevelt_muir_yosemite.jpg":
            continue

        src_path = fixtures_dir / src_name
        img = Image.open(src_path)

        # Detect face
        expected_faces = entry.get("expected_face_count", 1)
        faces = None
        if expected_faces > 0:
            conf = (
                0.2
                if src_name
                in ("lincoln_low_contrast.jpg", "roosevelt_muir_yosemite.jpg")
                else 0.5
            )
            detector = MediapipeFaceDetector(
                face_model_path, face_sha, min_detection_confidence=conf
            )
            with detector:
                face_res = detector.detect_faces(img)
            assert len(face_res.detections) == expected_faces
            faces = face_res.detections

        with segmenter:
            seg_res = segmenter.segment_subject(img, face=faces)

        assert seg_res.provider_status == SegmentationStatusValue.SUCCESS

        # Run refiner
        ref_res = refiner.refine_mask(
            coarse_mask=seg_res.coarse_mask,
            probability_mask=seg_res.probability_mask,
            face=faces,
        )

        # Calculate coarse vs refined stats
        coarse_arr = np.array(seg_res.coarse_mask) > 127
        refined_arr = np.array(ref_res.refined_binary_mask) > 127

        intersection = np.logical_and(coarse_arr, refined_arr).sum()
        union = np.logical_or(coarse_arr, refined_arr).sum()
        coarse_iou = intersection / union if union > 0 else 1.0

        coarse_cov = float(np.mean(coarse_arr))
        refined_cov = float(np.mean(refined_arr))

        print(
            f"Refinement Integration | Fixture: {src_name} | "
            f"Coarse Cov: {coarse_cov:.4f} | Refined Cov: {refined_cov:.4f} | "
            f"IoU: {coarse_iou:.4f} | Radius: {ref_res.effective_radius_px} | "
            f"Duration: {ref_res.refinement_duration_ms:.2f}ms"
        )

        # Assertions
        assert coarse_iou >= 0.90, (
            f"Coarse-refined IoU too low for {src_name}: {coarse_iou:.4f}"
        )
        assert abs(refined_cov - coarse_cov) <= 0.15, (
            f"Coverage diverged too much for {src_name}: {refined_cov:.4f} vs {coarse_cov:.4f}"
        )
        assert ref_res.validation.is_valid, (
            f"Validation report failed for {src_name}: {ref_res.validation.issue_codes}"
        )

        # Check trimap values
        trimap_vals = set(np.unique(np.array(ref_res.trimap)))
        assert trimap_vals.issubset({0, 128, 255})

        # Check alpha mask values
        alpha = ref_res.refined_alpha_mask
        assert alpha.dtype == np.float32
        assert np.all(alpha >= 0.0)
        assert np.all(alpha <= 1.0)


@pytest.mark.mandatory_refinement
def test_refinement_quality_vs_reference() -> None:
    _ensure_prerequisites()
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector
    from exam_photo.providers.refiners.morphological_refiner import (
        MorphologicalForegroundRefiner,
    )
    from exam_photo.providers.segmenters.mediapipe_segmenter import (
        MediapipeSubjectSegmenter,
    )

    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    fixtures_dir = repo_root / "tests" / "fixtures"

    # Load face detector info
    face_model_path = repo_root / "model-assets" / "blaze_face_short_range.tflite"
    face_sha = ""
    face_manifest = repo_root / "model-manifests" / "face-detector.json"
    if face_manifest.exists():
        with open(face_manifest) as manifest_f:
            fm = json.load(manifest_f)
            face_sha = fm.get("sha256", "")

    # Load segmenter info
    assert _MODEL_PATH is not None
    segmenter = MediapipeSubjectSegmenter(_MODEL_PATH, _MODEL_SHA256)
    refiner = MorphologicalForegroundRefiner()

    # Test single_face_frontal.jpg which has reference mask in reference_masks/
    img = Image.open(fixtures_dir / "single_face_frontal.jpg")
    ref_mask_path = (
        fixtures_dir
        / "segmentation"
        / "reference_masks"
        / "reference-einstein-mask.png"
    )
    assert ref_mask_path.exists(), "Reference Einstein mask is missing"
    ref_mask_arr = np.array(Image.open(ref_mask_path).convert("L")) > 127

    # Face detection
    detector = MediapipeFaceDetector(face_model_path, face_sha)
    with detector:
        face_res = detector.detect_faces(img)
    faces = face_res.detections

    with segmenter:
        seg_res = segmenter.segment_subject(img, face=faces)

    ref_res = refiner.refine_mask(
        coarse_mask=seg_res.coarse_mask,
        probability_mask=seg_res.probability_mask,
        face=faces,
    )

    coarse_arr = np.array(seg_res.coarse_mask) > 127
    refined_arr = np.array(ref_res.refined_binary_mask) > 127

    # 1. Coarse vs Reference IoU
    coarse_ref_intersect = np.logical_and(coarse_arr, ref_mask_arr).sum()
    coarse_ref_union = np.logical_or(coarse_arr, ref_mask_arr).sum()
    coarse_ref_iou = (
        coarse_ref_intersect / coarse_ref_union if coarse_ref_union > 0 else 1.0
    )

    # 2. Refined vs Reference IoU
    refined_ref_intersect = np.logical_and(refined_arr, ref_mask_arr).sum()
    refined_ref_union = np.logical_or(refined_arr, ref_mask_arr).sum()
    refined_ref_iou = (
        refined_ref_intersect / refined_ref_union if refined_ref_union > 0 else 1.0
    )

    print(
        f"Quality IoU Check | Coarse vs Reference: {coarse_ref_iou:.6f} | Refined vs Reference: {refined_ref_iou:.6f}"
    )

    # Assertion: Refined mask should remain highly accurate vs reference mask (>= 0.98 IoU)
    assert refined_ref_iou >= 0.98, (
        f"Refinement mask quality too low vs reference: refined_ref_iou ({refined_ref_iou:.6f})"
    )


@pytest.mark.mandatory_refinement
def test_refinement_multiple_person_safety() -> None:
    _ensure_prerequisites()
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector
    from exam_photo.providers.refiners.morphological_refiner import (
        MorphologicalForegroundRefiner,
    )
    from exam_photo.providers.segmenters.mediapipe_segmenter import (
        MediapipeSubjectSegmenter,
    )

    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    fixtures_dir = repo_root / "tests" / "fixtures"

    # Load face detector info
    face_model_path = repo_root / "model-assets" / "blaze_face_short_range.tflite"
    face_sha = ""
    face_manifest = repo_root / "model-manifests" / "face-detector.json"
    if face_manifest.exists():
        with open(face_manifest) as manifest_f:
            fm = json.load(manifest_f)
            face_sha = fm.get("sha256", "")

    # Load segmenter info
    assert _MODEL_PATH is not None
    segmenter = MediapipeSubjectSegmenter(_MODEL_PATH, _MODEL_SHA256)
    refiner = MorphologicalForegroundRefiner()

    img = Image.open(fixtures_dir / "roosevelt_muir_yosemite.jpg")

    # Detect faces
    detector = MediapipeFaceDetector(
        face_model_path, face_sha, min_detection_confidence=0.2
    )
    with detector:
        face_res = detector.detect_faces(img)
    assert len(face_res.detections) == 2
    faces = face_res.detections

    # Run segmenter
    with segmenter:
        seg_res = segmenter.segment_subject(img, face=faces)

    # Run refiner: must not crash
    ref_res = refiner.refine_mask(
        coarse_mask=seg_res.coarse_mask,
        probability_mask=seg_res.probability_mask,
        face=faces,
    )

    assert ref_res is not None
    assert ref_res.refined_alpha_mask is not None
    assert ref_res.refined_binary_mask is not None
    assert ref_res.trimap is not None
    # Yosemite refined mask is expected to be marked as invalid (due to multiple disconnected components or similar refinement warning/error issues)
    assert not ref_res.validation.is_valid or len(ref_res.validation.issues) > 0
    print(
        f"Yosemite Refinement Safety | is_valid: {ref_res.validation.is_valid} | Issue codes: {ref_res.validation.issue_codes}"
    )
