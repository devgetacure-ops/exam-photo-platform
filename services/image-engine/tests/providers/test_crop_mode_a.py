from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from pydantic import ValidationError

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers import (
    DeterministicCropPlanner,
)
from exam_photo.providers.crop_planners.deterministic_crop_planner import (
    _CHIN_BEARD_MARGIN_RATIO,
)
from exam_photo.providers.crop_planning import (
    CropConfig,
    CropIssueCode,
    CropProfile,
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

    # 1. No face case: a tracked synthetic fixture. This was violin_test.jpg,
    # which only ever existed on one machine, so the test failed on every clone.
    no_face_path = repo_root / "tests" / "fixtures" / "geometric_shapes_600x800.jpg"
    assert no_face_path.exists(), f"no-face fixture not found at {no_face_path}"

    preview_path = tmp_path / "no_face_preview.png"
    exit_code = main(
        [
            "plan-crop-mode-a",
            "--input",
            str(no_face_path),
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


def test_crop_aspect_ratio_preservation_new() -> None:
    planner = DeterministicCropPlanner()
    face_box = BoundingBox(left=200, top=200, right=300, bottom=300)
    face = FaceDetection(bounding_box=face_box, confidence=0.99)
    head_est = BoundingBox(left=180, top=150, right=320, bottom=350)

    for aspect in [0.75, 1.0, 1.33, 1.5]:
        cfg = CropConfig(
            target_aspect_ratio=aspect,
            crop_profile=CropProfile.STANDARD_PASSPORT_PORTRAIT,
            target_head_height_ratio=0.60,
        )
        res = planner.plan_crop(
            image_width=1000,
            image_height=1000,
            face=face,
            head_estimate=head_est,
            config=cfg,
        )
        assert res.ideal_crop_aspect_ratio is not None
        assert abs(res.ideal_crop_aspect_ratio - aspect) <= 5e-3
        assert abs(res.crop_box_aspect_ratio - aspect) <= 5e-3


def test_crop_tight_vs_relaxed_profiles() -> None:
    planner = DeterministicCropPlanner()
    face_box = BoundingBox(left=200, top=200, right=300, bottom=300)
    face = FaceDetection(bounding_box=face_box, confidence=0.99)
    head_est = BoundingBox(left=180, top=150, right=320, bottom=350)

    cfg_tight = CropConfig(
        target_aspect_ratio=1.0,
        crop_profile=CropProfile.TIGHT_EXAM_PORTRAIT,
        target_head_height_ratio=0.78,
        minimum_head_height_ratio=0.70,
        maximum_head_height_ratio=0.85,
    )
    res_tight = planner.plan_crop(
        image_width=1000,
        image_height=1000,
        face=face,
        head_estimate=head_est,
        config=cfg_tight,
    )

    cfg_relaxed = CropConfig(
        target_aspect_ratio=1.0,
        crop_profile=CropProfile.RELAXED_IDENTITY_PORTRAIT,
        target_head_height_ratio=0.40,
        minimum_head_height_ratio=0.30,
        maximum_head_height_ratio=0.55,
    )
    res_relaxed = planner.plan_crop(
        image_width=1000,
        image_height=1000,
        face=face,
        head_estimate=head_est,
        config=cfg_relaxed,
    )

    ratio_tight = head_est.height / res_tight.crop_height
    ratio_relaxed = head_est.height / res_relaxed.crop_height
    assert ratio_tight > ratio_relaxed
    assert res_tight.crop_height < res_relaxed.crop_height


def test_crop_complete_head_containment() -> None:
    """The crop keeps the whole head, and stops just below the chin.

    Hair, ears and the crown are kept in full: the crop reaches past the head
    estimate on the top and both sides.

    The bottom is a different promise, and this test used to assert the wrong
    one.  A head estimate extends below the jaw by a fixed expansion -- here
    50px, half a face height below a chin at y=300 -- and requiring the crop to
    reach it made the bottom edge a consequence of the head estimator's padding
    rather than of the subject's anatomy.  That is the "too loose below the
    chin" defect: what the crop owes the candidate is the chin plus a small
    beard margin, and tighter than that whenever the target dimensions allow.

    The precise bottom is asserted as a bound rather than a pixel so this reads
    as the contract it is: at least the chin-plus-margin line, and not so far
    below it that the delivered photograph would violate the below-chin
    invariant in exam_photo.orchestration.output_invariants.
    """
    planner = DeterministicCropPlanner()
    face_box = BoundingBox(left=200, top=200, right=300, bottom=300)
    face = FaceDetection(bounding_box=face_box, confidence=0.99)
    head_est = BoundingBox(left=180, top=150, right=320, bottom=350)

    cfg = CropConfig(
        target_aspect_ratio=1.0,
        crop_profile=CropProfile.STANDARD_PASSPORT_PORTRAIT,
        target_head_height_ratio=0.60,
        complete_hair_required=True,
        allow_subject_clipping=False,
    )
    res = planner.plan_crop(
        image_width=1000,
        image_height=1000,
        face=face,
        head_estimate=head_est,
        config=cfg,
    )

    assert res.crop_box.left <= head_est.left
    assert res.crop_box.top <= head_est.top
    assert res.crop_box.right >= head_est.right

    # No landmarks, so the planner's chin estimate is the face box bottom and
    # the crown is the head estimate's top: a 150px span.
    chin_y = face_box.bottom
    span = chin_y - head_est.top
    crop_height = res.crop_box.bottom - res.crop_box.top
    assert res.crop_box.bottom >= chin_y + _CHIN_BEARD_MARGIN_RATIO * span
    assert (res.crop_box.bottom - chin_y) / crop_height <= 0.175

    assert res.validation.subject_clipping_detected is False


def test_crop_mode_a_falls_back_to_best_preservation_candidate() -> None:
    planner = DeterministicCropPlanner()
    face_box = BoundingBox(left=200, top=200, right=300, bottom=300)
    face = FaceDetection(bounding_box=face_box, confidence=0.99)
    head_est = BoundingBox(left=180, top=150, right=320, bottom=350)

    cfg = CropConfig(
        target_width=300,
        target_height=400,
        crop_profile=CropProfile.TIGHT_EXAM_PORTRAIT,
        target_head_height_ratio=0.78,
        minimum_head_height_ratio=0.70,
        maximum_head_height_ratio=0.80,
        target_eye_line_ratio=0.10,
        minimum_eye_line_ratio=0.10,
        maximum_eye_line_ratio=0.11,
        maximum_torso_inclusion_ratio=0.0,
        allow_subject_clipping=False,
    )

    res = planner.plan_crop(
        image_width=1000,
        image_height=1000,
        face=face,
        head_estimate=head_est,
        config=cfg,
    )

    assert res.validation.is_valid is True
    assert CropIssueCode.CROP_NO_VALID_COMPOSITION in res.validation.issue_codes
    assert res.crop_box.contains(head_est)
    assert res.crop_box_aspect_ratio == pytest.approx(0.75)


def test_crop_mode_a_does_not_double_expand_supplied_head_estimate_with_mask_noise() -> (
    None
):
    planner = DeterministicCropPlanner()
    face_box = BoundingBox(left=140, top=120, right=220, bottom=210)
    face = FaceDetection(bounding_box=face_box, confidence=0.99)
    head_est = BoundingBox(left=115, top=70, right=245, bottom=250)
    cfg = CropConfig(
        target_width=300,
        target_height=400,
        crop_profile=CropProfile.TIGHT_EXAM_PORTRAIT,
        target_head_height_ratio=0.75,
        minimum_head_height_ratio=0.70,
        maximum_head_height_ratio=0.80,
    )

    noisy_mask = Image.new("L", (500, 500), 0)
    mask_arr = np.array(noisy_mask)
    mask_arr[0:260, 115:245] = 255
    mask_arr[0:260, 320:360] = 255
    noisy_mask = Image.fromarray(mask_arr, mode="L")

    without_mask = planner.plan_crop(
        image_width=500,
        image_height=500,
        face=face,
        head_estimate=head_est,
        config=cfg,
    )
    with_mask = planner.plan_crop(
        image_width=500,
        image_height=500,
        face=face,
        head_estimate=head_est,
        refined_mask=noisy_mask,
        config=cfg,
    )

    assert with_mask.crop_box == without_mask.crop_box
    assert with_mask.crop_box.right < 320


def test_crop_source_resolution_invariance() -> None:
    planner = DeterministicCropPlanner()

    face_box_1x = BoundingBox(left=200, top=200, right=300, bottom=300)
    face_1x = FaceDetection(bounding_box=face_box_1x, confidence=0.99)
    head_est_1x = BoundingBox(left=180, top=150, right=320, bottom=350)

    cfg = CropConfig(
        target_aspect_ratio=1.0,
        crop_profile=CropProfile.STANDARD_PASSPORT_PORTRAIT,
        target_head_height_ratio=0.60,
    )

    res_1x = planner.plan_crop(
        image_width=1000,
        image_height=1000,
        face=face_1x,
        head_estimate=head_est_1x,
        config=cfg,
    )

    face_box_05x = BoundingBox(left=100, top=100, right=150, bottom=150)
    face_05x = FaceDetection(bounding_box=face_box_05x, confidence=0.99)
    head_est_05x = BoundingBox(left=90, top=75, right=160, bottom=175)

    res_05x = planner.plan_crop(
        image_width=500,
        image_height=500,
        face=face_05x,
        head_estimate=head_est_05x,
        config=cfg,
    )

    face_box_2x = BoundingBox(left=400, top=400, right=600, bottom=600)
    face_2x = FaceDetection(bounding_box=face_box_2x, confidence=0.99)
    head_est_2x = BoundingBox(left=360, top=300, right=640, bottom=700)

    res_2x = planner.plan_crop(
        image_width=2000,
        image_height=2000,
        face=face_2x,
        head_estimate=head_est_2x,
        config=cfg,
    )

    box_1x_norm = res_1x.crop_box.to_normalized(1000, 1000)
    box_05x_norm = res_05x.crop_box.to_normalized(500, 500)
    box_2x_norm = res_2x.crop_box.to_normalized(2000, 2000)

    for field in ["left", "top", "right", "bottom"]:
        v_1x = getattr(box_1x_norm, field)
        v_05x = getattr(box_05x_norm, field)
        v_2x = getattr(box_2x_norm, field)
        assert abs(v_1x - v_05x) <= 0.015, (
            f"{field} difference between 1.0x and 0.5x exceeds tolerance"
        )
        assert abs(v_1x - v_2x) <= 0.015, (
            f"{field} difference between 1.0x and 2.0x exceeds tolerance"
        )
