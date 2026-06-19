from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image
from pydantic import ValidationError

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers import (
    CropModeBConfig,
    DeterministicCropModeBPlanner,
)
from exam_photo.providers.crop_planning import (
    CropIssueCode,
    CropMode,
)
from exam_photo.providers.face_detection import FaceDetection


def test_crop_mode_b_config_validation() -> None:
    # 1. Valid config
    cfg = CropModeBConfig(min_width=200, max_width=400)
    assert cfg.min_width == 200
    assert cfg.max_width == 400

    # 2. Invalid negative dimensions
    with pytest.raises(ValidationError):
        CropModeBConfig(min_width=-10)

    # 3. Invalid min > max dimensions
    with pytest.raises(ValidationError):
        CropModeBConfig(min_width=500, max_width=300)

    # 4. Invalid min > max aspect ratios
    with pytest.raises(ValidationError):
        CropModeBConfig(min_aspect_ratio=1.5, max_aspect_ratio=1.0)

    # 5. Invalid target head ratios
    with pytest.raises(ValidationError):
        CropModeBConfig(target_head_height_ratio=-0.5)
    with pytest.raises(ValidationError):
        CropModeBConfig(min_head_height_ratio=0.8, max_head_height_ratio=0.7)
    with pytest.raises(ValidationError):
        # target head ratio outside range
        CropModeBConfig(
            target_head_height_ratio=0.9,
            min_head_height_ratio=0.6,
            max_head_height_ratio=0.8,
        )

    # 6. Invalid margin sums
    with pytest.raises(ValidationError):
        CropModeBConfig(minimum_top_margin_ratio=0.6, minimum_bottom_margin_ratio=0.5)
    with pytest.raises(ValidationError):
        CropModeBConfig(minimum_side_margin_ratio=0.65)

    # 7. Rejects unknown fields
    with pytest.raises(ValidationError):
        CropModeBConfig(min_width=300, unknown_config_field="xyz")  # type: ignore


def test_crop_mode_b_head_ratio_math() -> None:
    planner = DeterministicCropModeBPlanner()
    face_box = BoundingBox(left=100, top=100, right=200, bottom=200)
    face = FaceDetection(bounding_box=face_box, confidence=0.99)
    head_est = BoundingBox(left=80, top=60, right=220, bottom=230)

    # head_height = 230 - 60 = 170.
    # target_head_height_ratio = 0.76 => desired_crop_height = 170 / 0.76 = 223.68.
    # default preferred aspect ratio is 0.75.
    cfg = CropModeBConfig(
        target_head_height_ratio=0.76,
        preferred_aspect_ratio=0.75,
        min_aspect_ratio=0.65,
        max_aspect_ratio=0.90,
    )
    res = planner.plan_crop(
        image_width=1000,
        image_height=1000,
        face=face,
        head_estimate=head_est,
        config=cfg,
    )

    assert res.crop_mode == CropMode.HEAD_LED_RANGE
    # Executable crop height should be around 224 pixels (rounded to int)
    assert abs(res.crop_box_height - 224) <= 2
    assert abs(res.crop_box_aspect_ratio - 0.75) < 0.05


def test_crop_mode_b_centering_and_positioning() -> None:
    planner = DeterministicCropModeBPlanner()
    face_box = BoundingBox(left=450, top=400, right=550, bottom=500)
    face = FaceDetection(bounding_box=face_box, confidence=0.99)
    head_est = BoundingBox(left=430, top=350, right=570, bottom=520)

    cfg = CropModeBConfig(
        target_head_height_ratio=0.76,
        preferred_aspect_ratio=0.75,
        preferred_face_center_y_ratio=0.44,
    )

    res = planner.plan_crop(
        image_width=1000,
        image_height=1000,
        face=face,
        head_estimate=head_est,
        config=cfg,
    )

    # Horizontal center of face is 500. Crop box left-right center should be close to 500.
    crop_cx = (res.crop_box.left + res.crop_box.right) / 2.0
    assert abs(crop_cx - 500) <= 2.0

    # Face center is at y=450. Face center ratio y should be close to 0.44
    assert abs(res.face_center_y_ratio - 0.44) < 0.05


def test_crop_mode_b_inward_shifting_and_clamping() -> None:
    planner = DeterministicCropModeBPlanner()
    # Face placed close to the left edge (cx = 100)
    face_box = BoundingBox(left=50, top=400, right=150, bottom=500)
    face = FaceDetection(bounding_box=face_box, confidence=0.99)
    head_est = BoundingBox(left=30, top=350, right=170, bottom=520)

    # w_crop should be around 224 * 0.75 = 168.
    # Centered: left = 100 - 84 = 16.
    # This is > 0, so it fits inside source bounds without padding.
    cfg = CropModeBConfig(
        target_head_height_ratio=0.76,
        preferred_aspect_ratio=0.75,
    )

    res = planner.plan_crop(
        image_width=1000,
        image_height=1000,
        face=face,
        head_estimate=head_est,
        config=cfg,
    )

    assert not res.padding_required
    assert res.can_crop_without_padding
    assert res.crop_box.left >= 0.0


def test_crop_mode_b_invalid_inputs() -> None:
    # 1. Invalid dimensions
    planner = DeterministicCropModeBPlanner()
    face_box = BoundingBox(left=100, top=100, right=200, bottom=200)
    face = FaceDetection(bounding_box=face_box, confidence=0.99)
    head_est = BoundingBox(left=80, top=60, right=220, bottom=230)

    res = planner.plan_crop(
        image_width=0,
        image_height=1000,
        face=face,
        head_estimate=head_est,
    )
    assert not res.validation.is_valid
    assert CropIssueCode.CROP_B_INPUT_INVALID in res.validation.issue_codes

    # 2. Unknown face detections count behavior: validated by CLI/benchmark


@pytest.mark.mandatory_crop_b
def test_crop_mode_b_integration_fixtures() -> None:
    # Resolve repository root
    curr = Path(__file__).resolve().parent
    repo_root = None
    for _ in range(5):
        if (curr / "AGENTS.md").exists():
            repo_root = curr
            break
        curr = curr.parent

    assert repo_root is not None, "Could not find repository root"

    fixtures_dir = repo_root / "tests" / "fixtures"
    annotations_path = fixtures_dir / "segmentation" / "annotations.json"
    assert annotations_path.exists()

    with open(annotations_path, "r", encoding="utf-8") as f:
        annotations = json.load(f)

    planner = DeterministicCropModeBPlanner()

    for entry in annotations["entries"]:
        src_name = entry["source_fixture"]
        src_path = fixtures_dir / src_name
        assert src_path.exists(), f"Fixture {src_name} not found"

        expected_faces = entry.get("expected_face_count", 1)
        expect_b = entry.get("crop_mode_b_expectation")

        if expected_faces != 1 or expect_b is None:
            continue

        # Load image
        img = Image.open(src_path)

        # Detect face & head
        from exam_photo.providers.landmark_geometric_head_estimator import (
            LandmarkGeometricHeadEstimator,
        )
        from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector

        face_model_path = repo_root / "model-assets" / "blaze_face_short_range.tflite"
        assert face_model_path.exists()

        face_manifest = repo_root / "model-manifests" / "face-detector.json"
        face_sha = ""
        if face_manifest.exists():
            with open(face_manifest, "r", encoding="utf-8") as f_man:
                face_sha = json.load(f_man).get("sha256", "")

        # Instantiate face detector with low confidence for Lincoln, standard for others
        conf = 0.2 if src_name == "lincoln_low_contrast.jpg" else 0.5
        detector = MediapipeFaceDetector(
            face_model_path, face_sha, min_detection_confidence=conf
        )
        with detector:
            face_res = detector.detect_faces(img)

        assert len(face_res.detections) == 1
        face = face_res.detections[0]

        estimator = LandmarkGeometricHeadEstimator()
        head_res = estimator.estimate_head(
            img,
            face,
            face.landmarks,
            config={"minimum_face_confidence": min(0.5, face.confidence)},
        )
        head_box = head_res.head_bounding_box

        # Optional segmentation refiner
        refined_mask = None
        seg_model_path = repo_root / "model-assets" / "selfie_segmentation.tflite"
        if seg_model_path.exists():
            from exam_photo.providers.refiners.morphological_refiner import (
                MorphologicalForegroundRefiner,
            )
            from exam_photo.providers.segmenters.mediapipe_segmenter import (
                MediapipeSubjectSegmenter,
            )

            seg_manifest = repo_root / "model-manifests" / "subject-segmenter.json"
            seg_sha = ""
            if seg_manifest.exists():
                with open(seg_manifest, "r", encoding="utf-8") as f_man:
                    m = json.load(f_man)
                    variant = m.get("variants", {}).get("selfie_bin_general", {})
                    seg_sha = variant.get("sha256", "")

            segmenter = MediapipeSubjectSegmenter(seg_model_path, seg_sha)
            with segmenter:
                seg_res = segmenter.segment_subject(img, face=face)

            refiner = MorphologicalForegroundRefiner()
            ref_res = refiner.refine_mask(
                coarse_mask=seg_res.coarse_mask,
                probability_mask=seg_res.probability_mask,
                face=face,
                head_estimate=head_box,
            )
            refined_mask = ref_res.refined_binary_mask

        # Plan Crop Mode B (allowing padding to check ideal aspect bounds if config specifies)
        cfg = CropModeBConfig(
            target_head_height_ratio=0.76,
            min_head_height_ratio=expect_b.get("min_head_height_ratio", 0.30),
            max_head_height_ratio=expect_b.get("max_head_height_ratio", 0.84),
            allow_padding=True,
        )

        res = planner.plan_crop(
            image_width=img.width,
            image_height=img.height,
            face=face,
            head_estimate=head_box,
            refined_mask=refined_mask,
            config=cfg,
        )

        # Assert expectations
        assert res.padding_required == expect_b["expected_padding_required"]
        assert (
            res.can_crop_without_padding == expect_b["expected_valid_without_padding"]
        )


def test_crop_mode_b_serialization() -> None:
    # Verify preview_image is excluded from serialization
    planner = DeterministicCropModeBPlanner()
    face_box = BoundingBox(left=100, top=100, right=200, bottom=200)
    face = FaceDetection(bounding_box=face_box, confidence=0.99)
    head_est = BoundingBox(left=80, top=60, right=220, bottom=230)

    res = planner.plan_crop(
        image_width=1000,
        image_height=1000,
        face=face,
        head_estimate=head_est,
    )
    # Set fake preview image
    res.preview_image = Image.new("RGB", (100, 100))

    dump = res.model_dump()
    assert "preview_image" not in dump

    dump_json = res.model_dump_json()
    assert "preview_image" not in dump_json


def test_crop_mode_b_cli_invalid_cases(
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

    assert repo_root is not None

    # No face case
    violin_path = repo_root / "services" / "image-engine" / "violin_test.jpg"
    assert violin_path.exists()

    preview_path = tmp_path / "violin_preview.png"
    exit_code = main(
        [
            "plan-crop-mode-b",
            "--input",
            str(violin_path),
            "--save-preview",
            str(preview_path),
        ]
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "CROP_B_INPUT_INVALID" in captured.err
    assert not preview_path.exists()

    # Multi-face case
    yosemite_path = repo_root / "tests" / "fixtures" / "roosevelt_muir_yosemite.jpg"
    assert yosemite_path.exists()

    preview_path_y = tmp_path / "yosemite_preview.png"
    exit_code_y = main(
        [
            "plan-crop-mode-b",
            "--input",
            str(yosemite_path),
            "--save-preview",
            str(preview_path_y),
        ]
    )

    assert exit_code_y == 1
    captured_y = capsys.readouterr()
    assert "CROP_B_INPUT_INVALID" in captured_y.err
    assert not preview_path_y.exists()
