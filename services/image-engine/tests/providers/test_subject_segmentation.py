import os
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.model_errors import ModelChecksumError, ModelNotFoundError
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
        Path(__file__).resolve().parent.parent.parent.parent
        / "model-assets"
        / "selfie_multiclass_256x256.tflite"
    )
    if fallback.exists():
        _MODEL_PATH = fallback
        _MODEL_SHA256 = (
            "c6748b1253a99067ef71f7e26ca71096cd449baefa8f101900ea23016507e0e0"
        )

requires_model = pytest.mark.skipif(
    _MODEL_PATH is None or not _MEDIAPIPE_INSTALLED,
    reason="Model file or MediaPipe not available.",
)

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

    # Filtered noise components (under 5 pixels)
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[2:10, 2:10] = 255  # 64 pixels component
    mask[15:17, 15:16] = 255  # 2 pixels component (noise)
    count, ratio = count_connected_components_dsu(mask)
    assert count == 1


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

    # Full frame mask validation
    prob = np.ones((100, 100), dtype=np.float32)
    binary = np.ones((100, 100), dtype=np.uint8) * 255
    report = validate_segmentation_mask(prob, binary, cfg)
    assert not report.is_valid
    assert "SEGMENTATION_MASK_FULL_FRAME" in report.issue_codes

    # Excessive uncertain edge
    prob_unc = np.zeros((100, 100), dtype=np.float32)
    prob_unc[0:40, :] = 0.5  # 40% of the image is inside uncertain range [0.2, 0.8]
    binary_unc = np.where(prob_unc >= 0.5, 255, 0).astype(np.uint8)
    report = validate_segmentation_mask(prob_unc, binary_unc, cfg)
    assert "SEGMENTATION_UNCERTAIN_EDGE_HIGH" in report.issue_codes


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
    assert "SEGMENTATION_FACE_NOT_CONTAINED" not in report_cov.issue_codes

    # Face not covered
    prob_uncov = np.zeros((100, 100), dtype=np.float32)
    binary_uncov = np.zeros((100, 100), dtype=np.uint8)
    report_uncov = validate_segmentation_mask(prob_uncov, binary_uncov, cfg, face=face)
    assert report_uncov.face_contained is False
    assert "SEGMENTATION_FACE_NOT_CONTAINED" in report_uncov.issue_codes


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


@requires_model
def test_mediapipe_segmenter_integration() -> None:
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


@requires_model
def test_segmenter_missing_model_error() -> None:
    from exam_photo.providers.segmenters.mediapipe_segmenter import (
        MediapipeSubjectSegmenter,
    )

    segmenter = MediapipeSubjectSegmenter(Path("non_existent_file.tflite"))
    with pytest.raises(ModelNotFoundError):
        segmenter.segment_subject(Image.new("RGB", (100, 100)))


@requires_model
def test_segmenter_incorrect_checksum_error() -> None:
    from exam_photo.providers.segmenters.mediapipe_segmenter import (
        MediapipeSubjectSegmenter,
    )

    assert _MODEL_PATH is not None
    segmenter = MediapipeSubjectSegmenter(
        _MODEL_PATH, expected_sha256="incorrect_checksum"
    )
    with pytest.raises(ModelChecksumError):
        segmenter.segment_subject(Image.new("RGB", (100, 100)))
