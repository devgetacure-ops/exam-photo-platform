from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image
from pydantic import ValidationError

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers import (
    DeterministicCropPlanner,
)
from exam_photo.providers.crop_planning import (
    CropConfig,
    CropIssueCode,
)
from exam_photo.providers.face_detection import FaceDetection


def test_crop_config_validation() -> None:
    # 1. Valid config
    cfg = CropConfig(target_width=300, target_height=400)
    assert cfg.target_width == 300
    assert cfg.target_height == 400

    # 2. Missing target aspects
    with pytest.raises(ValidationError):
        CropConfig(target_width=None, target_height=None, target_aspect_ratio=None)

    # 3. Invalid target dimensions
    with pytest.raises(ValidationError):
        CropConfig(target_width=0, target_height=400)
    with pytest.raises(ValidationError):
        CropConfig(target_width=300, target_height=-50)

    # 4. Conflicting/invalid float target aspect
    with pytest.raises(ValidationError):
        CropConfig(target_aspect_ratio=-1.0)
    with pytest.raises(ValidationError):
        CropConfig(target_aspect_ratio=float("nan"))

    # 5. Invalid margins
    with pytest.raises(ValidationError):
        CropConfig(target_width=300, target_height=400, minimum_top_margin_ratio=-0.05)
    with pytest.raises(ValidationError):
        # top + bottom sum >= 1.0
        CropConfig(
            target_width=300,
            target_height=400,
            minimum_top_margin_ratio=0.6,
            minimum_bottom_margin_ratio=0.5,
        )
    with pytest.raises(ValidationError):
        # 2 * side >= 1.0
        CropConfig(target_width=300, target_height=400, minimum_side_margin_ratio=0.55)


def test_gcd_integer_ratio_math() -> None:
    planner = DeterministicCropPlanner()
    face_box = BoundingBox(left=100, top=100, right=200, bottom=200)
    face = FaceDetection(bounding_box=face_box, confidence=0.99)
    head_est = BoundingBox(left=80, top=60, right=220, bottom=230)

    # Target 300x400: gcd is 100, ratio 3:4.
    # W_preservation = 220 - 80 = 140
    # H_preservation = 230 - 60 = 170
    # Margins top=0.06, bottom=0.08, side=0.06.
    # H_min_margin = 170 / (1 - 0.06 - 0.08) = 170 / 0.86 = 197.67
    # W_min_margin = 140 / (1 - 2 * 0.06) = 140 / 0.88 = 159.09
    #
    # We want smallest k such that 3*k >= 159.09 and 4*k >= 197.67
    # k_w = ceil(159.09 / 3) = ceil(53.03) = 54
    # k_h = ceil(197.67 / 4) = ceil(49.42) = 50
    # k = max(54, 50) = 54.
    # W_crop = 3 * 54 = 162
    # H_crop = 4 * 54 = 216
    cfg = CropConfig(
        target_width=300,
        target_height=400,
        minimum_top_margin_ratio=0.06,
        minimum_bottom_margin_ratio=0.08,
        minimum_side_margin_ratio=0.06,
    )
    res = planner.plan_crop(
        image_width=1000,
        image_height=1000,
        face=face,
        head_estimate=head_est,
        config=cfg,
    )

    assert res.crop_width == 162
    assert res.crop_height == 216
    assert res.crop_aspect_ratio == 162 / 216
    assert abs(res.crop_aspect_ratio - 3.0 / 4.0) < 1e-6


def test_centering_and_positioning() -> None:
    planner = DeterministicCropPlanner()
    face_box = BoundingBox(left=450, top=450, right=550, bottom=550)
    face = FaceDetection(bounding_box=face_box, confidence=0.99)
    head_est = BoundingBox(left=400, top=350, right=600, bottom=600)

    # Face center is at (500, 500)
    # Target square aspect (ratio 1:1)
    # W_preservation = 200, H_preservation = 250
    # H_min = max(250 / 0.86, 200 / 0.88) = max(290.7, 227.3) = 290.7
    # k = ceil(290.7) = 291
    # W_crop = 291, H_crop = 291
    cfg = CropConfig(
        target_width=300,
        target_height=300,
        preferred_face_center_y_ratio=0.44,
        minimum_top_margin_ratio=0.06,
        minimum_bottom_margin_ratio=0.08,
        minimum_side_margin_ratio=0.06,
    )
    res = planner.plan_crop(
        image_width=1000,
        image_height=1000,
        face=face,
        head_estimate=head_est,
        config=cfg,
    )

    # W_crop = 291, H_crop = 291
    # Ideal left: 500 - 145.5 = 354.5 -> rounded 354 (or 355 depending on round)
    # Ideal top: 500 - 0.44 * 291 = 500 - 128.04 = 371.96 -> rounded 372
    # Verify clamping inside bounds: ideal is within [0, 709], so clamping is inactive
    assert res.ideal_crop_box is not None
    assert abs(res.crop_box.left - res.ideal_crop_box.left) < 1e-4
    assert abs(res.crop_box.top - res.ideal_crop_box.top) < 1e-4


def test_padding_required_detection() -> None:
    planner = DeterministicCropPlanner()
    # Face lies close to the left boundary
    face_box = BoundingBox(left=50, top=500, right=150, bottom=600)
    face = FaceDetection(bounding_box=face_box, confidence=0.99)
    head_est = BoundingBox(left=30, top=400, right=170, bottom=650)

    cfg = CropConfig(
        target_width=300,
        target_height=400,
        allow_padding=False,
    )
    res = planner.plan_crop(
        image_width=1000,
        image_height=1000,
        face=face,
        head_estimate=head_est,
        config=cfg,
    )

    # Face center x is at 100.
    # W_crop must contain head width (140) with margin. Say it's 200.
    # Ideal left is 100 - 100 = 0.
    # But wait, if ideal left extends outside (e.g. left margin side causes ideal left to be negative),
    # then padding is required.
    assert res.padding_required is True
    assert res.can_crop_without_padding is False
    assert res.validation.is_valid is False
    assert CropIssueCode.CROP_PADDING_REQUIRED in res.validation.issue_codes
    assert CropIssueCode.CROP_BOX_OUT_OF_BOUNDS in res.validation.issue_codes


def test_invalid_inputs() -> None:
    planner = DeterministicCropPlanner()
    face_box = BoundingBox(left=10, top=10, right=50, bottom=50)
    face = FaceDetection(bounding_box=face_box, confidence=0.99)

    # Image dimension zero
    res = planner.plan_crop(
        image_width=0, image_height=100, face=face, head_estimate=None
    )
    assert res.validation.is_valid is False
    assert CropIssueCode.CROP_INPUT_INVALID in res.validation.issue_codes


def test_public_serialization_excludes_preview() -> None:
    planner = DeterministicCropPlanner()
    face_box = BoundingBox(left=100, top=100, right=200, bottom=200)
    face = FaceDetection(bounding_box=face_box, confidence=0.99)

    res = planner.plan_crop(
        image_width=500,
        image_height=500,
        face=face,
        head_estimate=None,
        config=CropConfig(target_width=3, target_height=4),
    )

    dumped = res.model_dump()
    assert "preview_image" not in dumped


@pytest.mark.mandatory_crop
def test_crop_mode_a_integration_fixtures() -> None:
    # Get repository root
    curr = Path(__file__).resolve().parent
    repo_root = None
    for _ in range(5):
        if (curr / "AGENTS.md").exists():
            repo_root = curr
            break
        curr = curr.parent

    assert repo_root is not None, "Could not find repository root"
    fixtures_dir = repo_root / "tests" / "fixtures"

    face_model_path = repo_root / "model-assets" / "blaze_face_short_range.tflite"
    assert face_model_path.exists(), f"Face detector model missing at {face_model_path}"

    with open(fixtures_dir / "segmentation" / "annotations.json") as f:
        manifest = json.load(f)

    planner = DeterministicCropPlanner()

    # Load face detector info
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector

    detector = MediapipeFaceDetector(face_model_path, "")

    for entry in manifest["entries"]:
        src_name = entry["source_fixture"]
        src_path = fixtures_dir / src_name
        img = Image.open(src_path)

        # Detect face
        expected_faces = entry.get("expected_face_count", 1)
        with detector:
            face_res = detector.detect_faces(img)

        # Check invalid inputs like no-person or multiple-person
        if expected_faces == 0 or len(face_res.detections) != 1:
            continue

        face = face_res.detections[0]

        # Estimate head
        from exam_photo.providers.landmark_geometric_head_estimator import (
            LandmarkGeometricHeadEstimator,
        )

        estimator = LandmarkGeometricHeadEstimator()
        head_res = estimator.estimate_head(img, face, face.landmarks)
        head_box = head_res.head_bounding_box

        # Plan Crop Mode A
        cfg = CropConfig(target_width=300, target_height=400)
        crop_res = planner.plan_crop(
            image_width=img.width,
            image_height=img.height,
            face=face,
            head_estimate=head_box,
            config=cfg,
        )

        assert crop_res is not None
        # Verify aspect ratio is exactly 3:4
        assert abs(crop_res.crop_aspect_ratio - 3.0 / 4.0) < 1e-4
        assert crop_res.crop_box.left >= 0
        assert crop_res.crop_box.right <= img.width
        assert crop_res.crop_box.top >= 0
        assert crop_res.crop_box.bottom <= img.height


def test_crop_mode_a_invalid_cases_unit() -> None:
    planner = DeterministicCropPlanner()
    cfg = CropConfig(target_width=300, target_height=400)

    # Unit test: face is None
    res = planner.plan_crop(
        image_width=100,
        image_height=100,
        face=None,  # type: ignore
        head_estimate=None,
        config=cfg,
    )
    assert res.validation.is_valid is False
    assert CropIssueCode.CROP_INPUT_INVALID in res.validation.issue_codes
    assert res.crop_width == 1
    assert res.crop_height == 1


def test_crop_mode_a_invalid_cases_cli(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    from exam_photo.cli import main

    # Find repository root
    curr = Path(__file__).resolve().parent
    repo_root = None
    for _ in range(5):
        if (curr / "AGENTS.md").exists():
            repo_root = curr
            break
        curr = curr.parent

    assert repo_root is not None, "Could not find repository root"

    # 1. No face case: violin_test.jpg
    violin_path = repo_root / "services" / "image-engine" / "violin_test.jpg"
    assert violin_path.exists(), f"violin_test.jpg not found at {violin_path}"

    preview_path = tmp_path / "violin_preview.png"
    exit_code = main(
        [
            "plan-crop-mode-a",
            "--input",
            str(violin_path),
            "--target-width",
            "300",
            "--target-height",
            "400",
            "--save-preview",
            str(preview_path),
        ]
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "CROP_INPUT_INVALID" in captured.err
    # Verify no preview image was saved
    assert not preview_path.exists()

    # 2. Multi-face case: roosevelt_muir_yosemite.jpg
    yosemite_path = repo_root / "tests" / "fixtures" / "roosevelt_muir_yosemite.jpg"
    assert yosemite_path.exists(), (
        f"roosevelt_muir_yosemite.jpg not found at {yosemite_path}"
    )

    preview_path_yosemite = tmp_path / "yosemite_preview.png"
    exit_code_y = main(
        [
            "plan-crop-mode-a",
            "--input",
            str(yosemite_path),
            "--target-width",
            "300",
            "--target-height",
            "400",
            "--save-preview",
            str(preview_path_yosemite),
        ]
    )

    assert exit_code_y == 1
    captured_y = capsys.readouterr()
    assert "CROP_INPUT_INVALID" in captured_y.err
    # Verify no preview image was saved
    assert not preview_path_yosemite.exists()


def test_crop_config_validation_extra_and_conflicts() -> None:
    # Conflicting target dimensions and aspect ratio
    with pytest.raises(ValidationError):
        CropConfig(target_width=300, target_height=400, target_aspect_ratio=1.0)

    # Extra/unknown config fields
    with pytest.raises(ValidationError):
        CropConfig(
            target_width=300, target_height=400, unknown_config_field_xyz="error"
        )  # type: ignore

    # Partial target dimensions
    with pytest.raises(ValidationError):
        CropConfig(target_width=300)
    with pytest.raises(ValidationError):
        CropConfig(target_height=400)


def test_crop_cli_save_preview_overwrite_protection(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    from exam_photo.cli import main

    # Find repository root
    curr = Path(__file__).resolve().parent
    repo_root = None
    for _ in range(5):
        if (curr / "AGENTS.md").exists():
            repo_root = curr
            break
        curr = curr.parent

    assert repo_root is not None, "Could not find repository root"

    img_path = repo_root / "tests" / "fixtures" / "marie_curie_curly_hair.jpg"
    assert img_path.exists()

    preview_path = tmp_path / "marie_preview.png"

    # First run: should succeed and create the preview
    exit_code = main(
        [
            "plan-crop-mode-a",
            "--input",
            str(img_path),
            "--target-width",
            "300",
            "--target-height",
            "400",
            "--save-preview",
            str(preview_path),
        ]
    )
    assert exit_code == 0
    assert preview_path.exists()

    # Second run without --overwrite: should fail
    exit_code_dup = main(
        [
            "plan-crop-mode-a",
            "--input",
            str(img_path),
            "--target-width",
            "300",
            "--target-height",
            "400",
            "--save-preview",
            str(preview_path),
        ]
    )
    assert exit_code_dup == 1
    captured = capsys.readouterr()
    assert "Output file already exists" in captured.err

    # Third run with --overwrite: should succeed
    exit_code_overwrite = main(
        [
            "plan-crop-mode-a",
            "--input",
            str(img_path),
            "--target-width",
            "300",
            "--target-height",
            "400",
            "--save-preview",
            str(preview_path),
            "--overwrite",
        ]
    )
    assert exit_code_overwrite == 0
