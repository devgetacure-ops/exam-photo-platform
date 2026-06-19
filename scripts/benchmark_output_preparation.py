#!/usr/bin/env python3
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from PIL import Image

from exam_photo.input.limits import InputLimits
from exam_photo.input.normalization import normalize_image_input
from exam_photo.providers.output_preparation import (
    OutputPreparationConfig,
    ResizeMode,
)
from exam_photo.providers.output_preparers.deterministic_output_preparer import DeterministicOutputPreparer

# Optional imports for fully realistic benchmark including previous pipeline stages
try:
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector
    from exam_photo.providers.segmenters.mediapipe_segmenter import MediapipeSubjectSegmenter
    from exam_photo.providers.refiners.morphological_refiner import MorphologicalForegroundRefiner
    from exam_photo.providers.landmark_geometric_head_estimator import LandmarkGeometricHeadEstimator
    from exam_photo.providers.crop_planning import CropConfig, CropModeBConfig
    from exam_photo.providers.crop_planners.deterministic_crop_planner import DeterministicCropPlanner
    from exam_photo.providers.crop_planners.deterministic_crop_mode_b_planner import DeterministicCropModeBPlanner
    from exam_photo.providers.subject_segmentation import SegmentationConfig
    from exam_photo.providers.background_composers.solid_background_composer import SolidBackgroundComposer
    from exam_photo.providers.background_composition import BackgroundCompositionConfig
    CAN_RUN_FULL_PIPELINE = True
except ImportError:
    CAN_RUN_FULL_PIPELINE = False

logger = logging.getLogger("benchmark_output_preparation")
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
    fixtures_dir = repo_root / "tests" / "fixtures" / "segmentation"
    annotations_file = fixtures_dir / "annotations.json"
    
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
    segmenter_model_path = repo_root / "model-assets" / "selfie_multiclass_256x256.tflite"
    
    detector = None
    segmenter = None
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
            seg_sha = m_data.get("variants", {}).get("selfie_multiclass_256x256", {}).get("sha256", "")

    if CAN_RUN_FULL_PIPELINE and face_model_path.exists() and segmenter_model_path.exists():
        detector = MediapipeFaceDetector(model_path=face_model_path, expected_sha256=face_sha)
        segmenter = MediapipeSubjectSegmenter(model_path=segmenter_model_path, expected_sha256=seg_sha)
    else:
        logger.warning("Running limited benchmark (without pipeline orchestration).")
        
    preparer = DeterministicOutputPreparer()
    passed = 0
    failed = 0
    
    for entry in entries:
        fixture_name = entry["source_fixture"]
        img_path = fixtures_dir / "images" / fixture_name
        if not img_path.exists():
            logger.warning(f"Image not found: {img_path}")
            continue
            
        prep_exp = entry.get("output_preparation_expectation", {})
        if not prep_exp:
            continue
            
        logger.info(f"Processing {fixture_name}...")
        
        crop_plan = None
        try:
            with open(img_path, "rb") as fb:
                data = fb.read()
            norm_result = normalize_image_input(data, str(img_path), InputLimits())
            current_image = norm_result.image
            
            if detector and segmenter:
                with detector:
                    face_res = detector.detect_faces(current_image)
                if len(face_res.detections) == 1:
                    face = face_res.detections[0]
                    estimator = LandmarkGeometricHeadEstimator()
                    head_res = estimator.estimate_head(current_image, face, face.landmarks)
                    with segmenter:
                        seg_res = segmenter.segment_subject(current_image, config=SegmentationConfig())
                    refiner = MorphologicalForegroundRefiner()
                    ref_res = refiner.refine_mask(
                        coarse_mask=seg_res.coarse_mask,
                        probability_mask=seg_res.probability_mask,
                        face=face_res.detections,
                        head_estimate=head_res.head_bounding_box
                    )
                    
                    # Choose Crop Mode A or B based on expectations
                    if entry.get("crop_mode_b_expectation", {}).get("expected_valid"):
                        planner = DeterministicCropModeBPlanner()
                        crop_plan = planner.plan_crop(
                            image_width=current_image.width,
                            image_height=current_image.height,
                            face=face_res.detections[0],
                            head_estimate=head_res.head_bounding_box,
                            refined_mask=ref_res.refined_binary_mask,
                            config=CropModeBConfig()
                        )
                    elif entry.get("crop_mode_a_expectation", {}).get("expected_valid_without_padding"):
                        planner = DeterministicCropPlanner()
                        crop_plan = planner.plan_crop(
                            image_width=current_image.width,
                            image_height=current_image.height,
                            face=face_res.detections[0],
                            head_estimate=head_res.head_bounding_box,
                            refined_mask=ref_res.refined_binary_mask,
                            alpha_mask=ref_res.refined_alpha_mask,
                            config=CropConfig(target_aspect_ratio=3/4)
                        )
                    
                    if crop_plan and crop_plan.validation.is_valid:
                        b = crop_plan.crop_box
                        current_image = current_image.crop((int(b.left), int(b.top), int(b.right), int(b.bottom)))
                        ref_res.refined_alpha_mask = ref_res.refined_alpha_mask[int(b.top):int(b.bottom), int(b.left):int(b.right)]
                        
                        bg_composer = SolidBackgroundComposer()
                        bg_res = bg_composer.compose_background(current_image, ref_res.refined_alpha_mask, BackgroundCompositionConfig(target_colour_hex="#FFFFFF"))
                        if bg_res.validation.is_valid:
                            current_image = bg_res.composed_image

            # Run Output Preparation
            if crop_plan and crop_plan.validation.is_valid and abs((crop_plan.crop_box.width / crop_plan.crop_box.height) - 0.75) <= 0.01:
                # If we cropped to exactly 3:4, use EXACT mode
                config = OutputPreparationConfig(
                    resize_mode=ResizeMode.EXACT,
                    target_width=prep_exp.get("expected_output_width", 300),
                    target_height=prep_exp.get("expected_output_height", 400),
                )
            else:
                # If no crop, or if aspect ratio is not 3:4, use RANGE_SELECT to preserve aspect ratio
                config = OutputPreparationConfig(
                    resize_mode=ResizeMode.RANGE_SELECT,
                    min_width=100, max_width=1000,
                    min_height=100, max_height=1000,
                    preferred_width=300, preferred_height=400
                )
            
            result = preparer.prepare_output(current_image, config)
            
            # Check serialization leakage
            if "output_image" in result.model_dump():
                raise AssertionError("output_image leaked into model_dump()!")
            if "output_image" in result.model_dump_json():
                raise AssertionError("output_image leaked into model_dump_json()!")
            
            expected_valid = prep_exp.get("expected_valid", True)
            if result.validation.is_valid == expected_valid:
                logger.info(f"  [PASS] Output Preparation Validation matches expectation ({expected_valid})")
                passed += 1
            else:
                logger.error(f"  [FAIL] Expected valid: {expected_valid}, got: {result.validation.is_valid}")
                if not result.validation.is_valid:
                    logger.error(f"  Issues: {result.validation.issue_codes}")
                failed += 1
                
        except Exception as e:
            logger.error(f"  [FAIL] Unhandled exception: {e}")
            import traceback
            logger.error(traceback.format_exc())
            failed += 1
            
    logger.info(f"\nBenchmark Complete. PASSED: {passed}, FAILED: {failed}")
    if failed > 0:
        sys.exit(1)
        
if __name__ == "__main__":
    run_benchmark()
