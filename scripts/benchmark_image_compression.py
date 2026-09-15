#!/usr/bin/env python3
import json
import logging
import sys
import time
from pathlib import Path

from exam_photo.input.limits import InputLimits
from exam_photo.input.normalization import normalize_image_input
from exam_photo.providers.output_preparation import OutputPreparationConfig, ResizeMode
from exam_photo.providers.output_preparers.deterministic_output_preparer import (
    DeterministicOutputPreparer,
)
from exam_photo.providers.output_compression import (
    OutputCompressionConfig,
    CompressionFormat,
)
from exam_photo.providers.compression.deterministic_image_compressor import (
    DeterministicJpegCompressor,
)

# Optional imports for fully realistic benchmark including previous pipeline stages
try:
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector
    from exam_photo.providers.segmenters.mediapipe_segmenter import (
        MediapipeSubjectSegmenter,
    )
    from exam_photo.providers.refiners.morphological_refiner import (
        MorphologicalForegroundRefiner,
    )
    from exam_photo.providers.landmark_geometric_head_estimator import (
        LandmarkGeometricHeadEstimator,
    )
    from exam_photo.providers.crop_planning import CropConfig, CropModeBConfig
    from exam_photo.providers.crop_planners.deterministic_crop_planner import (
        DeterministicCropPlanner,
    )
    from exam_photo.providers.crop_planners.deterministic_crop_mode_b_planner import (
        DeterministicCropModeBPlanner,
    )
    from exam_photo.providers.subject_segmentation import SegmentationConfig
    from exam_photo.providers.background_composers.solid_background_composer import (
        SolidBackgroundComposer,
    )
    from exam_photo.providers.background_composition import BackgroundCompositionConfig

    CAN_RUN_FULL_PIPELINE = True
except ImportError:
    CAN_RUN_FULL_PIPELINE = False

logger = logging.getLogger("benchmark_image_compression")
logging.basicConfig(level=logging.INFO)


def find_repo_root() -> Path:
    curr = Path(__file__).resolve().parent
    for _ in range(5):
        if (curr / "AGENTS.md").exists():
            return curr
        curr = curr.parent
    return Path(__file__).resolve().parent.parent


def run_benchmark():
    repo_root = find_repo_root()
    fixtures_dir = repo_root / "tests" / "fixtures"
    annotations_file = fixtures_dir / "segmentation" / "annotations.json"

    if not annotations_file.exists():
        logger.error(f"Annotations file not found at {annotations_file}")
        sys.exit(1)

    with open(annotations_file, "r") as f:
        annotations = json.load(f)

    entries = annotations.get("entries", [])
    if not entries:
        logger.error("No entries found in annotations")
        sys.exit(1)

    face_model_path = repo_root / "model-assets" / "blaze_face_short_range.tflite"
    segmenter_model_path = repo_root / "model-assets" / "selfie_segmentation.tflite"

    face_manifest = repo_root / "model-manifests" / "face-detector.json"
    segmenter_manifest = repo_root / "model-manifests" / "subject-segmenter.json"
    face_sha = ""
    seg_sha = ""
    if face_manifest.exists():
        with open(face_manifest) as mf:
            face_sha = json.load(mf).get("sha256", "")
    if segmenter_manifest.exists():
        with open(segmenter_manifest) as mf:
            m_data = json.load(mf)
            seg_sha = (
                m_data.get("variants", {})
                .get("selfie_bin_general", {})
                .get("sha256", "")
            )

    if "--require-real" in sys.argv:
        if not CAN_RUN_FULL_PIPELINE:
            logger.error(
                "ERROR: Cannot run full pipeline. Mandatory packages (e.g. mediapipe) missing."
            )
            sys.exit(1)
        if not face_model_path.exists():
            logger.error(f"ERROR: Face detector model missing: {face_model_path}")
            sys.exit(1)
        if not segmenter_model_path.exists():
            logger.error(f"ERROR: Segmenter model missing: {segmenter_model_path}")
            sys.exit(1)

    face_detector_05 = None
    face_detector_02 = None
    segmenter = None
    if (
        CAN_RUN_FULL_PIPELINE
        and face_model_path.exists()
        and segmenter_model_path.exists()
    ):
        face_detector_05 = MediapipeFaceDetector(
            model_path=face_model_path,
            expected_sha256=face_sha,
            min_detection_confidence=0.5,
        )
        face_detector_02 = MediapipeFaceDetector(
            model_path=face_model_path,
            expected_sha256=face_sha,
            min_detection_confidence=0.2,
        )
        segmenter = MediapipeSubjectSegmenter(
            model_path=segmenter_model_path, expected_sha256=seg_sha
        )
    else:
        logger.warning("Running limited benchmark (without pipeline orchestration).")

    preparer = DeterministicOutputPreparer()
    compressor = DeterministicJpegCompressor()
    passed = 0
    failed = 0
    evaluated_count = 0

    for entry in entries:
        fixture_name = entry["source_fixture"]
        img_path = fixtures_dir / fixture_name

        comp_exp = entry.get("output_compression_expectation", {})
        if not comp_exp:
            continue

        if not img_path.exists():
            logger.error(f"Image not found: {img_path}")
            if "--require-real" in sys.argv:
                failed += 1
            continue

        logger.info(f"Processing {fixture_name}...")

        crop_plan = None
        try:
            with open(img_path, "rb") as fb:
                data = fb.read()
            norm_result = normalize_image_input(data, str(img_path), InputLimits())
            current_image = norm_result.image

            if face_detector_05 and face_detector_02 and segmenter:
                # Use correct confidence face detector
                det = (
                    face_detector_02
                    if fixture_name
                    in ("lincoln_low_contrast.jpg", "roosevelt_muir_yosemite.jpg")
                    else face_detector_05
                )
                with det:
                    face_res = det.detect_faces(current_image)
                if len(face_res.detections) == 1:
                    face = face_res.detections[0]
                    estimator = LandmarkGeometricHeadEstimator()
                    head_res = estimator.estimate_head(
                        current_image,
                        face,
                        face.landmarks,
                        config={"minimum_face_confidence": min(0.5, face.confidence)},
                    )
                    with segmenter:
                        seg_res = segmenter.segment_subject(current_image, face=face)
                    refiner = MorphologicalForegroundRefiner()
                    ref_res = refiner.refine_mask(
                        image=current_image,
                        coarse_mask=seg_res.coarse_mask,
                        probability_mask=seg_res.probability_mask,
                        face=face,
                        head_estimate=head_res.head_bounding_box,
                    )

                    # Choose Crop Mode B or A based on expectations
                    crop_b_exp = entry.get("crop_mode_b_expectation", {})
                    crop_a_exp = entry.get("crop_mode_a_expectation", {})
                    if crop_b_exp.get("expected_valid"):
                        planner = DeterministicCropModeBPlanner()
                        crop_plan = planner.plan_crop(
                            image_width=current_image.width,
                            image_height=current_image.height,
                            face=face_res.detections[0],
                            head_estimate=head_res.head_bounding_box,
                            refined_mask=ref_res.refined_binary_mask,
                            config=CropModeBConfig(
                                min_head_height_ratio=crop_b_exp.get(
                                    "min_head_height_ratio", 0.30
                                ),
                                max_head_height_ratio=crop_b_exp.get(
                                    "max_head_height_ratio", 0.84
                                ),
                                allow_padding=crop_b_exp.get(
                                    "expected_padding_required", False
                                ),
                            ),
                        )
                    elif crop_a_exp.get("expected_valid_without_padding"):
                        planner = DeterministicCropPlanner()
                        crop_plan = planner.plan_crop(
                            image_width=current_image.width,
                            image_height=current_image.height,
                            face=face_res.detections[0],
                            head_estimate=head_res.head_bounding_box,
                            refined_mask=ref_res.refined_binary_mask,
                            config=CropConfig(target_width=300, target_height=400),
                        )

                    if crop_plan and crop_plan.validation.is_valid:
                        b = crop_plan.crop_box
                        current_image = current_image.crop(
                            (int(b.left), int(b.top), int(b.right), int(b.bottom))
                        )
                        ref_res.refined_alpha_mask = ref_res.refined_alpha_mask[
                            int(b.top) : int(b.bottom), int(b.left) : int(b.right)
                        ]

                        bg_composer = SolidBackgroundComposer()
                        bg_res = bg_composer.compose_background(
                            current_image,
                            ref_res.refined_alpha_mask,
                            BackgroundCompositionConfig(target_colour_hex="#FFFFFF"),
                        )
                        if bg_res.validation.is_valid:
                            current_image = bg_res.composed_image
            else:
                if "--require-real" in sys.argv:
                    logger.error(
                        "ERROR: Running in limited benchmark mode under --require-real."
                    )
                    failed += 1
                    continue

            # Run Output Preparation
            prep_exp = entry.get("output_preparation_expectation", {})
            if (
                crop_plan
                and crop_plan.validation.is_valid
                and abs((crop_plan.crop_box.width / crop_plan.crop_box.height) - 0.75)
                <= 0.01
            ):
                prep_config = OutputPreparationConfig(
                    resize_mode=ResizeMode.EXACT,
                    target_width=prep_exp.get("expected_output_width", 300),
                    target_height=prep_exp.get("expected_output_height", 400),
                )
            else:
                prep_config = OutputPreparationConfig(
                    resize_mode=ResizeMode.RANGE_SELECT,
                    min_width=100,
                    max_width=1000,
                    min_height=100,
                    max_height=1000,
                    preferred_width=300,
                    preferred_height=400,
                )

            prep_result = preparer.prepare_output(current_image, prep_config)
            if not prep_result.validation.is_valid or prep_result.output_image is None:
                raise AssertionError(
                    "Output preparation failed during pipeline benchmark run!"
                )

            prepared_image = prep_result.output_image

            # Run Output Compression
            comp_config = OutputCompressionConfig(
                target_format=CompressionFormat.JPEG,
                maximum_bytes=comp_exp.get("maximum_bytes", 51200),
                minimum_bytes=comp_exp.get("minimum_bytes", 10240),
                min_quality=comp_exp.get("min_quality", 35),
                max_quality=comp_exp.get("max_quality", 95),
            )

            start_t = time.perf_counter()
            result = compressor.compress_output(prepared_image, comp_config)
            duration_ms = (time.perf_counter() - start_t) * 1000.0

            # Check serialization leakage
            if "encoded_bytes" in result.model_dump():
                raise AssertionError("encoded_bytes leaked into model_dump()!")
            if "encoded_bytes" in result.model_dump_json():
                raise AssertionError("encoded_bytes leaked into model_dump_json()!")

            expected_valid = comp_exp.get("expected_valid", True)
            if result.validation.is_valid == expected_valid:
                logger.info(
                    f"  [PASS] Output Compression matches expectation ({expected_valid}). Size: {result.actual_bytes} bytes. Quality: {result.final_quality}. Duration: {duration_ms:.2f}ms"
                )
                passed += 1
            else:
                logger.error(
                    f"  [FAIL] Expected valid: {expected_valid}, got: {result.validation.is_valid}"
                )
                if not result.validation.is_valid:
                    logger.error(f"  Issues: {result.validation.issue_codes}")
                failed += 1

            evaluated_count += 1

        except Exception as e:
            logger.error(f"  [FAIL] Unhandled exception: {e}")
            import traceback

            logger.error(traceback.format_exc())
            failed += 1

    logger.info(
        f"\nBenchmark Complete. PASSED: {passed}, FAILED: {failed}, EVALUATED: {evaluated_count}"
    )
    if "--require-real" in sys.argv and evaluated_count < 7:
        logger.error(
            f"ERROR: Expected at least 7 evaluated fixtures under --require-real, got {evaluated_count}"
        )
        sys.exit(1)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_benchmark()
