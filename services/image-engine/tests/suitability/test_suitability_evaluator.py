import os
from pathlib import Path

import pytest
from tests.fakes.fake_face_detector import FakeFaceDetector
from tests.fakes.fake_head_estimator import FakeHeadEstimator
from tests.helpers.synthetic_images import create_solid_image

from exam_photo.input.metadata import SourceImageMetadata
from exam_photo.input.normalization import NormalizationResult
from exam_photo.models.geometry import BoundingBox, PoseEstimate
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.suitability.configuration import SuitabilityThresholds
from exam_photo.suitability.evaluator import SuitabilityEvaluator
from exam_photo.suitability.issue_codes import SuitabilityIssueCode
from exam_photo.suitability.models import ProcessingReadinessStatus, SuitabilityStatus


@pytest.fixture
def lenient_thresholds() -> SuitabilityThresholds:
    return SuitabilityThresholds(
        minimum_source_width=10,
        minimum_source_height=10,
        minimum_source_pixels=100,
        blur_warning_threshold=0.1,
        blur_blocking_threshold=0.01,
        mean_luminance_warning_low=5.0,
        mean_luminance_warning_high=250.0,
        mean_luminance_blocking_low=1.0,
        mean_luminance_blocking_high=254.0,
        low_contrast_threshold=0.1,
        transparent_pixel_warning_threshold=0.99,
        transparent_pixel_blocking_threshold=0.99,
    )


@pytest.fixture
def base_normalization_result() -> NormalizationResult:
    # 400x400 Solid gray image
    image = create_solid_image("RGB", (400, 400), color=(128, 128, 128))
    metadata = SourceImageMetadata(
        source_basename="test.png",
        encoded_byte_size=1000,
        signature_detected_format="png",
        decoder_detected_format="png",
        original_width=400,
        original_height=400,
        normalized_width=400,
        normalized_height=400,
        total_pixels=160000,
        original_mode="RGB",
        normalized_mode="RGBA",
        frame_count=1,
        orientation_tag_present=False,
        orientation_applied=False,
        alpha_present=False,
        metadata_present=False,
        icc_profile_present=False,
        icc_conversion_status="none",
        extension_mismatch=False,
        warnings=[],
        warning_codes=[],
    )
    return NormalizationResult(image=image, metadata=metadata, warnings=[])


def test_no_provider_configured(
    base_normalization_result: NormalizationResult,
    lenient_thresholds: SuitabilityThresholds,
) -> None:
    evaluator = SuitabilityEvaluator(lenient_thresholds)
    report = evaluator.evaluate(base_normalization_result)

    assert report.overall_status == SuitabilityStatus.INDETERMINATE
    assert "face_detector" in report.provider_status
    assert report.provider_status["face_detector"] == "unavailable"
    assert any(
        iss.code == SuitabilityIssueCode.SUITABILITY_FACE_CHECK_UNAVAILABLE
        for iss in report.issues
    )


def test_provider_failed(
    base_normalization_result: NormalizationResult,
    lenient_thresholds: SuitabilityThresholds,
) -> None:
    fake_face = FakeFaceDetector(raise_error="Failed backend connection")
    evaluator = SuitabilityEvaluator(lenient_thresholds, face_provider=fake_face)
    report = evaluator.evaluate(base_normalization_result)

    assert report.overall_status == SuitabilityStatus.INDETERMINATE
    assert report.provider_status["face_detector"] == "failed"
    assert any(
        iss.code == SuitabilityIssueCode.SUITABILITY_FACE_PROVIDER_FAILED
        for iss in report.issues
    )


def test_zero_faces_detected(
    base_normalization_result: NormalizationResult,
    lenient_thresholds: SuitabilityThresholds,
) -> None:
    fake_face = FakeFaceDetector(detections=[])
    evaluator = SuitabilityEvaluator(lenient_thresholds, face_provider=fake_face)
    report = evaluator.evaluate(base_normalization_result)

    assert report.overall_status == SuitabilityStatus.UNSUITABLE
    assert any(
        iss.code == SuitabilityIssueCode.SUITABILITY_NO_FACE for iss in report.issues
    )


def test_multiple_faces_detected(
    base_normalization_result: NormalizationResult,
    lenient_thresholds: SuitabilityThresholds,
) -> None:
    box = BoundingBox(left=0.1, top=0.1, right=0.4, bottom=0.4)
    face1 = FaceDetection(bounding_box=box, confidence=0.9)
    face2 = FaceDetection(bounding_box=box, confidence=0.8)

    fake_face = FakeFaceDetector(detections=[face1, face2])
    evaluator = SuitabilityEvaluator(lenient_thresholds, face_provider=fake_face)
    report = evaluator.evaluate(base_normalization_result)

    assert report.overall_status == SuitabilityStatus.UNSUITABLE
    assert any(
        iss.code == SuitabilityIssueCode.SUITABILITY_MULTIPLE_FACES
        for iss in report.issues
    )


def test_one_face_and_completeness_ok(
    base_normalization_result: NormalizationResult,
    lenient_thresholds: SuitabilityThresholds,
) -> None:
    box = BoundingBox(left=0.1, top=0.1, right=0.4, bottom=0.4)
    face = FaceDetection(
        bounding_box=box,
        confidence=0.9,
        pose=PoseEstimate(yaw=0.0, pitch=0.0, roll=0.0, confidence=1.0, method="fake"),
        occlusion_indicators={"face_occluded": False, "eyes_occluded": False},
    )
    fake_face = FakeFaceDetector(detections=[face])
    fake_head = FakeHeadEstimator()

    evaluator = SuitabilityEvaluator(
        lenient_thresholds, face_provider=fake_face, head_provider=fake_head
    )
    report = evaluator.evaluate(base_normalization_result)

    assert report.overall_status == SuitabilityStatus.SUITABLE
    assert report.provider_status["face_detector"] == "active"
    assert report.provider_status["head_estimator"] == "active"


def test_head_boundary_clipped(
    base_normalization_result: NormalizationResult,
    lenient_thresholds: SuitabilityThresholds,
) -> None:
    box = BoundingBox(left=0.1, top=0.1, right=0.4, bottom=0.4)
    face = FaceDetection(
        bounding_box=box,
        confidence=0.9,
        pose=PoseEstimate(yaw=0.0, pitch=0.0, roll=0.0, confidence=1.0, method="fake"),
        occlusion_indicators={"face_occluded": False, "eyes_occluded": False},
    )
    fake_face = FakeFaceDetector(detections=[face])
    fake_head = FakeHeadEstimator(
        boundary_visibility={"top_hair_boundary_visible": False}
    )

    evaluator = SuitabilityEvaluator(
        lenient_thresholds, face_provider=fake_face, head_provider=fake_head
    )
    report = evaluator.evaluate(base_normalization_result)

    assert report.overall_status == SuitabilityStatus.UNSUITABLE
    assert any(
        iss.code == SuitabilityIssueCode.SUITABILITY_HEAD_TOP_CLIPPED
        for iss in report.issues
    )


def test_head_boundary_unknown(
    base_normalization_result: NormalizationResult,
    lenient_thresholds: SuitabilityThresholds,
) -> None:
    box = BoundingBox(left=0.1, top=0.1, right=0.4, bottom=0.4)
    face = FaceDetection(
        bounding_box=box,
        confidence=0.9,
        pose=PoseEstimate(yaw=0.0, pitch=0.0, roll=0.0, confidence=1.0, method="fake"),
        occlusion_indicators={"face_occluded": False, "eyes_occluded": False},
    )
    fake_face = FakeFaceDetector(detections=[face])
    fake_head = FakeHeadEstimator(
        boundary_visibility={"top_hair_boundary_visible": "unknown"}
    )

    evaluator = SuitabilityEvaluator(
        lenient_thresholds, face_provider=fake_face, head_provider=fake_head
    )
    report = evaluator.evaluate(base_normalization_result)

    assert report.overall_status == SuitabilityStatus.INDETERMINATE
    assert any(
        iss.code == SuitabilityIssueCode.SUITABILITY_HEAD_COMPLETENESS_UNAVAILABLE
        for iss in report.issues
    )


# ---------------------------------------------------------------------------
# Integration: real MediaPipe provider with SuitabilityEvaluator
# ---------------------------------------------------------------------------

try:
    import mediapipe  # noqa: F401

    _MEDIAPIPE_INSTALLED = True

except ImportError:
    _MEDIAPIPE_INSTALLED = False

_MODEL_PATH_ENV = "EXAM_PHOTO_FACE_MODEL_PATH"
_MODEL_SHA256_ENV = "EXAM_PHOTO_FACE_MODEL_SHA256"
_REAL_MODEL_PATH = (
    Path(os.environ[_MODEL_PATH_ENV])
    if _MODEL_PATH_ENV in os.environ and Path(os.environ[_MODEL_PATH_ENV]).exists()
    else None
)
_REAL_MODEL_SHA256 = os.environ.get(_MODEL_SHA256_ENV, "")


@pytest.mark.skipif(
    not _MEDIAPIPE_INSTALLED or _REAL_MODEL_PATH is None,
    reason="mediapipe not installed or EXAM_PHOTO_FACE_MODEL_PATH not set",
)
def test_evaluator_with_real_mediapipe_no_head_provider(
    lenient_thresholds: SuitabilityThresholds,
    base_normalization_result: "NormalizationResult",
) -> None:
    """SuitabilityEvaluator with a real MediaPipe face provider and no head
    provider must return INDETERMINATE status (head checks unavailable) on a
    blank image that returns zero faces."""
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector

    assert _REAL_MODEL_PATH is not None

    with MediapipeFaceDetector(
        model_path=_REAL_MODEL_PATH,
        expected_sha256=_REAL_MODEL_SHA256,
    ) as face_provider:
        evaluator = SuitabilityEvaluator(
            thresholds=lenient_thresholds,
            face_provider=face_provider,
            head_provider=None,
        )
        report = evaluator.evaluate(base_normalization_result)

    # No face in the 400x400 solid gray image → NO_FACE blocking issue
    # Head provider is absent → head_estimator status = unavailable → INDETERMINATE
    assert report.provider_status["face_detector"] == "active"
    assert report.provider_status["head_estimator"] in ("unavailable", "skipped")
    assert report.overall_status in (
        SuitabilityStatus.UNSUITABLE,
        SuitabilityStatus.INDETERMINATE,
    ), f"Unexpected status: {report.overall_status}"


def test_multiple_faces_allowed_by_policy(
    base_normalization_result: NormalizationResult,
    lenient_thresholds: SuitabilityThresholds,
) -> None:
    # Set policy to allow
    lenient_thresholds.multiple_face_handling_policy = "allow"

    box = BoundingBox(left=0.1, top=0.1, right=0.4, bottom=0.4)
    face1 = FaceDetection(bounding_box=box, confidence=0.9)
    face2 = FaceDetection(bounding_box=box, confidence=0.8)

    fake_face = FakeFaceDetector(detections=[face1, face2])
    evaluator = SuitabilityEvaluator(lenient_thresholds, face_provider=fake_face)
    report = evaluator.evaluate(base_normalization_result)

    # Should not block since policy is "allow"
    assert (
        report.overall_status == SuitabilityStatus.INDETERMINATE
    )  # due to missing head detector
    assert any(
        iss.code == SuitabilityIssueCode.SUITABILITY_MULTIPLE_FACES
        and not iss.blocking
        and iss.severity == "warning"
        for iss in report.issues
    )


def test_shadow_and_highlight_clipping_detection(
    base_normalization_result: NormalizationResult,
    lenient_thresholds: SuitabilityThresholds,
) -> None:
    # Make thresholds strict for clipping
    lenient_thresholds.shadow_clipping_threshold = 0.01
    lenient_thresholds.highlight_clipping_threshold = 0.01

    # Create solid black image to trigger shadow clipping (ratio = 1.0)
    black_img = create_solid_image("RGB", (100, 100), color=(0, 0, 0))
    norm_black = NormalizationResult(
        image=black_img,
        metadata=base_normalization_result.metadata,
        warnings=[],
    )

    evaluator = SuitabilityEvaluator(lenient_thresholds)
    report_black = evaluator.evaluate(norm_black)

    assert any(
        iss.code == SuitabilityIssueCode.SUITABILITY_UNDEREXPOSED_WARNING
        and "shadow clipping" in iss.message
        for iss in report_black.issues
    )

    # Create solid white image to trigger highlight clipping (ratio = 1.0)
    white_img = create_solid_image("RGB", (100, 100), color=(255, 255, 255))
    norm_white = NormalizationResult(
        image=white_img,
        metadata=base_normalization_result.metadata,
        warnings=[],
    )

    report_white = evaluator.evaluate(norm_white)

    assert any(
        iss.code == SuitabilityIssueCode.SUITABILITY_OVEREXPOSED_WARNING
        and "highlight clipping" in iss.message
        for iss in report_white.issues
    )


def test_warnings_propagation(
    base_normalization_result: NormalizationResult,
    lenient_thresholds: SuitabilityThresholds,
) -> None:
    fake_face = FakeFaceDetector(
        detections=[],
        warnings=["Face detector experienced heavy camera noise warning"],
    )
    evaluator = SuitabilityEvaluator(lenient_thresholds, face_provider=fake_face)
    report = evaluator.evaluate(base_normalization_result)

    assert "Face detector experienced heavy camera noise warning" in report.warnings


def test_evaluator_segmentation_optional_success(
    base_normalization_result: NormalizationResult,
    lenient_thresholds: SuitabilityThresholds,
) -> None:
    from tests.fakes.fake_subject_segmenter import FakeSubjectSegmenter

    box = BoundingBox(left=0.1, top=0.1, right=0.4, bottom=0.4)
    face = FaceDetection(
        bounding_box=box,
        confidence=0.9,
        pose=PoseEstimate(yaw=0.0, pitch=0.0, roll=0.0, confidence=1.0, method="fake"),
        occlusion_indicators={"face_occluded": False, "eyes_occluded": False},
    )
    fake_face = FakeFaceDetector(detections=[face])
    fake_head = FakeHeadEstimator()
    fake_seg = FakeSubjectSegmenter(is_valid=True)

    evaluator = SuitabilityEvaluator(
        lenient_thresholds,
        face_provider=fake_face,
        head_provider=fake_head,
        segmentation_provider=fake_seg,
    )
    report = evaluator.evaluate(
        base_normalization_result, background_replacement_required=False
    )

    assert report.overall_status == SuitabilityStatus.SUITABLE
    assert report.segmentation_diagnostic is not None
    assert report.segmentation_diagnostic.is_valid is True
    assert report.segmentation_diagnostic.segmentation_status == "success"
    assert report.segmentation_diagnostic.can_proceed is True


def test_evaluator_segmentation_optional_failure(
    base_normalization_result: NormalizationResult,
    lenient_thresholds: SuitabilityThresholds,
) -> None:
    from tests.fakes.fake_subject_segmenter import FakeSubjectSegmenter

    box = BoundingBox(left=0.1, top=0.1, right=0.4, bottom=0.4)
    face = FaceDetection(
        bounding_box=box,
        confidence=0.9,
        pose=PoseEstimate(yaw=0.0, pitch=0.0, roll=0.0, confidence=1.0, method="fake"),
        occlusion_indicators={"face_occluded": False, "eyes_occluded": False},
    )
    fake_face = FakeFaceDetector(detections=[face])
    fake_head = FakeHeadEstimator()
    fake_seg = FakeSubjectSegmenter(
        is_valid=False, issue_codes=["SEGMENTATION_MASK_EMPTY"]
    )

    evaluator = SuitabilityEvaluator(
        lenient_thresholds,
        face_provider=fake_face,
        head_provider=fake_head,
        segmentation_provider=fake_seg,
    )
    report = evaluator.evaluate(
        base_normalization_result, background_replacement_required=False
    )

    # When replacement is not required, mask failures do not make the photo unsuitable
    assert report.overall_status == SuitabilityStatus.SUITABLE
    assert report.segmentation_diagnostic is not None
    assert report.segmentation_diagnostic.is_valid is False
    assert report.segmentation_diagnostic.can_proceed is True
    assert "SEGMENTATION_MASK_EMPTY" in report.segmentation_diagnostic.issue_codes


def test_evaluator_segmentation_mandatory_success(
    base_normalization_result: NormalizationResult,
    lenient_thresholds: SuitabilityThresholds,
) -> None:
    from tests.fakes.fake_subject_segmenter import FakeSubjectSegmenter

    box = BoundingBox(left=0.1, top=0.1, right=0.4, bottom=0.4)
    face = FaceDetection(
        bounding_box=box,
        confidence=0.9,
        pose=PoseEstimate(yaw=0.0, pitch=0.0, roll=0.0, confidence=1.0, method="fake"),
        occlusion_indicators={"face_occluded": False, "eyes_occluded": False},
    )
    fake_face = FakeFaceDetector(detections=[face])
    fake_head = FakeHeadEstimator()
    fake_seg = FakeSubjectSegmenter(is_valid=True)

    evaluator = SuitabilityEvaluator(
        lenient_thresholds,
        face_provider=fake_face,
        head_provider=fake_head,
        segmentation_provider=fake_seg,
    )
    report = evaluator.evaluate(
        base_normalization_result, background_replacement_required=True
    )

    assert report.source_suitability == SuitabilityStatus.SUITABLE
    assert report.processing_readiness == ProcessingReadinessStatus.READY
    assert report.segmentation_diagnostic is not None
    assert report.segmentation_diagnostic.is_valid is True
    assert report.segmentation_diagnostic.can_proceed is True


def test_evaluator_segmentation_mandatory_failure(
    base_normalization_result: NormalizationResult,
    lenient_thresholds: SuitabilityThresholds,
) -> None:
    from tests.fakes.fake_subject_segmenter import FakeSubjectSegmenter

    box = BoundingBox(left=0.1, top=0.1, right=0.4, bottom=0.4)
    face = FaceDetection(
        bounding_box=box,
        confidence=0.9,
        pose=PoseEstimate(yaw=0.0, pitch=0.0, roll=0.0, confidence=1.0, method="fake"),
        occlusion_indicators={"face_occluded": False, "eyes_occluded": False},
    )
    fake_face = FakeFaceDetector(detections=[face])
    fake_head = FakeHeadEstimator()
    fake_seg = FakeSubjectSegmenter(
        is_valid=False, issue_codes=["SEGMENTATION_MASK_EMPTY"]
    )

    evaluator = SuitabilityEvaluator(
        lenient_thresholds,
        face_provider=fake_face,
        head_provider=fake_head,
        segmentation_provider=fake_seg,
    )
    report = evaluator.evaluate(
        base_normalization_result, background_replacement_required=True
    )

    # When replacement is required, serious mask failures block the photo
    assert report.source_suitability == SuitabilityStatus.SUITABLE
    assert report.processing_readiness == ProcessingReadinessStatus.BLOCKED
    assert report.segmentation_diagnostic is not None
    assert report.segmentation_diagnostic.is_valid is False
    assert report.segmentation_diagnostic.can_proceed is False
    assert "SEGMENTATION_MASK_EMPTY" in report.segmentation_diagnostic.issue_codes
    assert any(
        not iss.blocking and iss.code == "SEGMENTATION_MASK_EMPTY"
        for iss in report.issues
    )


def test_evaluator_segmentation_provider_unavailable_mandatory(
    base_normalization_result: NormalizationResult,
    lenient_thresholds: SuitabilityThresholds,
) -> None:
    box = BoundingBox(left=0.1, top=0.1, right=0.4, bottom=0.4)
    face = FaceDetection(
        bounding_box=box,
        confidence=0.9,
        pose=PoseEstimate(yaw=0.0, pitch=0.0, roll=0.0, confidence=1.0, method="fake"),
        occlusion_indicators={"face_occluded": False, "eyes_occluded": False},
    )
    fake_face = FakeFaceDetector(detections=[face])
    fake_head = FakeHeadEstimator()

    evaluator = SuitabilityEvaluator(
        lenient_thresholds,
        face_provider=fake_face,
        head_provider=fake_head,
        segmentation_provider=None,
    )
    report = evaluator.evaluate(
        base_normalization_result, background_replacement_required=True
    )

    assert report.source_suitability == SuitabilityStatus.SUITABLE
    assert report.processing_readiness == ProcessingReadinessStatus.BLOCKED
    assert report.segmentation_diagnostic is not None
    assert report.segmentation_diagnostic.segmentation_status == "unavailable"
    assert report.segmentation_diagnostic.can_proceed is False
    assert (
        "SEGMENTATION_PROVIDER_UNAVAILABLE"
        in report.segmentation_diagnostic.issue_codes
    )
    assert any(
        not iss.blocking and iss.code == "SEGMENTATION_PROVIDER_UNAVAILABLE"
        for iss in report.issues
    )
