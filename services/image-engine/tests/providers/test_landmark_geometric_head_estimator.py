import pytest
from PIL import Image

from exam_photo.models.geometry import BoundingBox, Landmarks, Point, PoseEstimate
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.head_estimation import (
    BoundaryVisibilityValue,
    ClippingFindingValue,
    HeadEstimationConfig,
)
from exam_photo.providers.landmark_geometric_head_estimator import (
    LandmarkGeometricHeadEstimator,
)


def test_config_validation() -> None:
    # Test valid defaults
    config = HeadEstimationConfig()
    assert config.top_expansion_ratio == 0.6
    assert config.side_expansion_ratio == 0.25

    # Test constraints (e.g. ratios must be >= 0)
    with pytest.raises(ValueError):
        HeadEstimationConfig(top_expansion_ratio=-0.1)

    with pytest.raises(ValueError):
        HeadEstimationConfig(maximum_expansion_ratio=0.5)  # must be > 1.0


def test_landmark_fallback_and_combinations() -> None:
    estimator = LandmarkGeometricHeadEstimator()
    image = Image.new("RGB", (600, 800))

    # Face box in the center
    face_box = BoundingBox(left=200, top=300, right=400, bottom=500)
    face = FaceDetection(
        bounding_box=face_box,
        confidence=0.9,
        pose=PoseEstimate(yaw=0.0, pitch=0.0, roll=0.0, confidence=1.0, method="fake"),
        occlusion_indicators={"face_occluded": False, "eyes_occluded": False},
    )

    # Scenario A: Full landmarks (eyes, ears, mouth center)
    landmarks = Landmarks(
        left_eye=Point(x=250, y=350),
        right_eye=Point(x=350, y=350),
        custom_landmarks={
            "left_ear_tragion": Point(x=180, y=400),
            "right_ear_tragion": Point(x=420, y=400),
            "mouth_center": Point(x=300, y=450),
        },
    )

    result_full = estimator.estimate_head(image, face, landmarks)
    assert result_full.confidence == 0.9
    assert (
        result_full.boundary_visibility.left_head_boundary.basis == "landmark_inferred"
    )
    assert (
        result_full.boundary_visibility.right_head_boundary.basis == "landmark_inferred"
    )
    assert result_full.boundary_visibility.chin_boundary.basis == "landmark_inferred"
    assert result_full.head_bounding_box.left < face_box.left
    assert result_full.head_bounding_box.right > face_box.right

    # Scenario B: Missing ear tragions
    landmarks_no_ears = Landmarks(
        left_eye=Point(x=250, y=350),
        right_eye=Point(x=350, y=350),
        custom_landmarks={
            "mouth_center": Point(x=300, y=450),
        },
    )
    result_no_ears = estimator.estimate_head(image, face, landmarks_no_ears)
    assert (
        result_no_ears.boundary_visibility.left_head_boundary.basis
        == "geometry_inferred"
    )
    assert (
        result_no_ears.boundary_visibility.right_head_boundary.basis
        == "geometry_inferred"
    )
    assert result_no_ears.boundary_visibility.chin_boundary.basis == "landmark_inferred"

    # Scenario C: Face-box-only fallback (No landmarks)
    result_fallback = estimator.estimate_head(image, face, None)
    assert (
        result_fallback.boundary_visibility.left_head_boundary.basis
        == "geometry_inferred"
    )
    assert (
        result_fallback.boundary_visibility.right_head_boundary.basis
        == "geometry_inferred"
    )
    assert (
        result_fallback.boundary_visibility.chin_boundary.basis == "geometry_inferred"
    )


def test_face_confidence_threshold() -> None:
    estimator = LandmarkGeometricHeadEstimator()
    image = Image.new("RGB", (600, 800))
    face_box = BoundingBox(left=200, top=300, right=400, bottom=500)

    # Face confidence below minimum
    face = FaceDetection(
        bounding_box=face_box,
        confidence=0.4,
        pose=PoseEstimate(yaw=0.0, pitch=0.0, roll=0.0, confidence=1.0, method="fake"),
        occlusion_indicators={"face_occluded": False, "eyes_occluded": False},
    )
    config = {"minimum_face_confidence": 0.5}

    with pytest.raises(ValueError, match="confidence"):
        estimator.estimate_head(image, face, None, config=config)


def test_invalid_face_bounding_box() -> None:
    estimator = LandmarkGeometricHeadEstimator()
    image = Image.new("RGB", (600, 800))

    # Face box coordinates invalid (e.g. right exceeds image width of 600)
    invalid_box = BoundingBox(left=200, top=300, right=700, bottom=500)
    face = FaceDetection(
        bounding_box=invalid_box,
        confidence=0.9,
        pose=PoseEstimate(yaw=0.0, pitch=0.0, roll=0.0, confidence=1.0, method="fake"),
        occlusion_indicators={"face_occluded": False, "eyes_occluded": False},
    )

    with pytest.raises(ValueError, match="Invalid face bounding box"):
        estimator.estimate_head(image, face, None)


def test_containment_and_aspect_ratios() -> None:
    estimator = LandmarkGeometricHeadEstimator()
    image = Image.new("RGB", (600, 800))

    # Unusually tall/narrow face
    face_box = BoundingBox(left=280, top=200, right=320, bottom=600)
    face = FaceDetection(
        bounding_box=face_box,
        confidence=0.9,
    )
    result = estimator.estimate_head(image, face, None)

    # Head box must contain the face box
    assert result.head_bounding_box.left <= face_box.left
    assert result.head_bounding_box.top <= face_box.top
    assert result.head_bounding_box.right >= face_box.right
    assert result.head_bounding_box.bottom >= face_box.bottom

    # Validate aspect ratio constraint
    head_w = result.head_bounding_box.right - result.head_bounding_box.left
    head_h = result.head_bounding_box.bottom - result.head_bounding_box.top
    aspect = head_w / head_h
    assert aspect >= 0.5  # min_aspect_ratio is 0.5 by default


def test_clamping_and_suspected_clipping() -> None:
    estimator = LandmarkGeometricHeadEstimator()
    image = Image.new("RGB", (600, 800))

    # Face touching the top edge (top = 0)
    face_box = BoundingBox(left=200, top=0, right=400, bottom=200)
    face = FaceDetection(
        bounding_box=face_box,
        confidence=0.9,
    )
    result = estimator.estimate_head(image, face, None)

    # Should clamp top of head to 0.0
    assert result.head_bounding_box.top == 0.0

    # Clipping status should be "suspected" (not "confirmed")
    assert result.clipping_assessment.top_hair.status == ClippingFindingValue.SUSPECTED
    assert result.clipping_assessment.top_hair.confidence < 0.9
    assert (
        result.boundary_visibility.top_hair_boundary.state
        == BoundaryVisibilityValue.NOT_VISIBLE
    )

    # Other boundaries not touching edges should be not_detected/unknown
    assert (
        result.clipping_assessment.left_side.status == ClippingFindingValue.NOT_DETECTED
    )
    assert (
        result.boundary_visibility.left_head_boundary.state
        == BoundaryVisibilityValue.UNKNOWN
    )

    # Confidence should be degraded slightly due to clamping
    assert result.confidence < 0.9
    assert "clamped" in result.warnings[0]


def test_determinism_and_output_safety() -> None:
    estimator = LandmarkGeometricHeadEstimator()
    image = Image.new("RGB", (600, 800))
    face_box = BoundingBox(left=200, top=300, right=400, bottom=500)
    face = FaceDetection(
        bounding_box=face_box,
        confidence=0.9,
    )

    # Run twice, verify identical output
    r1 = estimator.estimate_head(image, face, None)
    r2 = estimator.estimate_head(image, face, None)

    assert r1.head_bounding_box == r2.head_bounding_box
    assert r1.confidence == r2.confidence
    assert r1.boundary_visibility == r2.boundary_visibility

    # No absolute paths or private data leakage in warnings or details
    for w in r1.warnings:
        assert "/" not in w and "\\" not in w
    assert "/" not in r1.confidence_basis and "\\" not in r1.confidence_basis


def test_backwards_compatibility_properties() -> None:
    estimator = LandmarkGeometricHeadEstimator()
    image = Image.new("RGB", (600, 800))
    face_box = BoundingBox(left=200, top=300, right=400, bottom=500)
    face = FaceDetection(
        bounding_box=face_box,
        confidence=0.9,
    )
    result = estimator.estimate_head(image, face, None)

    # Verify deprecated property estimated_bounding_box maps to normalized_head_bounding_box
    assert result.estimated_bounding_box == result.normalized_head_bounding_box
    # Check normalized coordinates are correct
    norm = result.normalized_head_bounding_box
    assert norm.left == result.head_bounding_box.left / 600.0
    assert norm.top == result.head_bounding_box.top / 800.0

    # Verify deprecated properties return bool | None
    # beard_boundary_visible is unknown/unsupported by default -> None
    assert result.boundary_visibility.beard_boundary_visible is None
    # left_head_boundary_visible is unknown by default -> None
    assert result.boundary_visibility.left_head_boundary_visible is None

    # Force visibility states to test mapping
    from exam_photo.providers.head_estimation import (
        BoundaryAssessment,
        BoundaryVisibilityValue,
        HeadBoundaryVisibility,
    )

    vis = HeadBoundaryVisibility(
        top_hair_boundary=BoundaryAssessment(
            state=BoundaryVisibilityValue.VISIBLE, basis="observed"
        ),
        left_head_boundary=BoundaryAssessment(
            state=BoundaryVisibilityValue.NOT_VISIBLE, basis="observed"
        ),
        right_head_boundary=BoundaryAssessment(
            state=BoundaryVisibilityValue.UNKNOWN, basis="observed"
        ),
        chin_boundary=BoundaryAssessment(
            state=BoundaryVisibilityValue.NOT_APPLICABLE, basis="observed"
        ),
        lower_beard_boundary=BoundaryAssessment(
            state=BoundaryVisibilityValue.VISIBLE, basis="observed"
        ),
        left_ear=BoundaryAssessment(
            state=BoundaryVisibilityValue.UNKNOWN, basis="observed"
        ),
        right_ear=BoundaryAssessment(
            state=BoundaryVisibilityValue.UNKNOWN, basis="observed"
        ),
    )
    assert vis.top_hair_boundary_visible is True
    assert vis.left_head_boundary_visible is False
    assert vis.right_head_boundary_visible is None
    assert vis.chin_boundary_visible is None
    assert vis.beard_boundary_visible is True


def test_annotated_fixtures_quality() -> None:
    import json
    from pathlib import Path

    # Locate head_annotations.json
    base_path = Path(__file__).parent.parent / "fixtures" / "head_annotations.json"
    assert base_path.exists()

    with open(base_path, "r", encoding="utf-8") as f:
        fixtures_data = json.load(f)

    estimator = LandmarkGeometricHeadEstimator()

    for _name, data in fixtures_data.items():
        if data.get("is_real", False):
            # For real fixtures, we skip in unit test to avoid requiring face detector model
            continue

        img_w, img_h = data["image_size"]
        image = Image.new("RGB", (img_w, img_h), (240, 240, 240))
        fb = data["face_box"]
        face_box = BoundingBox(
            left=fb["left"], top=fb["top"], right=fb["right"], bottom=fb["bottom"]
        )
        face = FaceDetection(
            bounding_box=face_box,
            confidence=0.9,
            pose=PoseEstimate(
                yaw=0.0, pitch=0.0, roll=0.0, confidence=1.0, method="fake"
            ),
            occlusion_indicators={"face_occluded": False, "eyes_occluded": False},
        )
        lm = data.get("landmarks", {})
        clm = {}
        if "custom_landmarks" in lm:
            for k, point in lm["custom_landmarks"].items():
                clm[k] = Point(x=point["x"], y=point["y"])
        landmarks = Landmarks(
            left_eye=Point(x=lm["left_eye"]["x"], y=lm["left_eye"]["y"])
            if "left_eye" in lm
            else None,
            right_eye=Point(x=lm["right_eye"]["x"], y=lm["right_eye"]["y"])
            if "right_eye" in lm
            else None,
            custom_landmarks=clm,
        )

        cfg = data.get("config", {})
        result = estimator.estimate_head(image, face, landmarks, config=cfg)

        # 1. Face Containment
        assert result.head_bounding_box.contains(face.bounding_box)

        # 2. Bounded geometry
        assert result.head_bounding_box.left >= 0.0
        assert result.head_bounding_box.top >= 0.0
        assert result.head_bounding_box.right <= img_w
        assert result.head_bounding_box.bottom <= img_h

        # 3. Ground truth matching within tolerance (0.1 pixel)
        gt = data.get("ground_truth_head_box")
        if gt:
            assert abs(result.head_bounding_box.left - gt["left"]) < 0.1
            assert abs(result.head_bounding_box.top - gt["top"]) < 0.1
            assert abs(result.head_bounding_box.right - gt["right"]) < 0.1
            assert abs(result.head_bounding_box.bottom - gt["bottom"]) < 0.1

        # 4. Clipping expected match
        expected_clipping = data.get("expected_clipping", {})
        if "top_hair" in expected_clipping:
            assert (
                result.clipping_assessment.top_hair.status.value
                == expected_clipping["top_hair"]
            )
        if "chin" in expected_clipping:
            assert (
                result.clipping_assessment.chin.status.value
                == expected_clipping["chin"]
            )
