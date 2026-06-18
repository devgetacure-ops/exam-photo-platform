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

    for entry in manifest["entries"]:
        src_name = entry["source_fixture"]
        mask_rel_path = entry["ground_truth_mask_filename"]
        expected_cov = entry["expected_coverage"]

        src_path = fixtures_dir / src_name
        mask_path = fixtures_dir / mask_rel_path

        assert src_path.exists(), f"Source image {src_name} is missing"
        assert mask_path.exists(), f"Ground-truth mask {mask_rel_path} is missing"

        # Load images
        img = Image.open(src_path)
        gt_mask = Image.open(mask_path).convert("L")

        with segmenter:
            res = segmenter.segment_subject(img)

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
