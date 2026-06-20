#!/usr/bin/env python3
import json
import logging
import sys
import time
from pathlib import Path

from exam_photo.orchestration.rule_pipeline import RuleOrchestratedPipeline, RulePipelineConfig

logger = logging.getLogger("benchmark_rule_pipeline")
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
    examples_dir = repo_root / "examples" / "rules"

    # Define 7 single-face fixtures
    fixtures = [
        "single_face_frontal.jpg",
        "sarah_bernhardt_long_hair.jpg",
        "marie_curie_curly_hair.jpg",
        "lincoln_low_contrast.jpg",
        "roosevelt_muir_yosemite.jpg",
        "freud_spectacles_beard.jpg",
        "vivekananda_head_covering.jpg"
    ]

    # Define 2 valid rules
    rules = [
        "sample_exact_300x400_50kb_white_bg.json",
        "sample_range_200_300_width_230_400_height_50kb_white_bg.json"
    ]

    # Map combination -> expected is_valid
    # Einstein (single_face_frontal) has voluminous hair requiring padding, so fails crop without it.
    # Lincoln (low_contrast) fails face count 1 check under standard 0.5 confidence.
    # John Muir / Theodore Roosevelt (yosemite) fails face count 1 check.
    # Freud has spectacles/beard and fails crop margin constraints without padding.
    # Vivekananda has a head covering and fails crop margin constraints.
    # Sarah Bernhardt is valid in exact mode (Crop Mode A), but invalid in range mode (Crop Mode B) due to voluminous curls.
    # Marie Curie is valid in Crop Mode B, but invalid in Crop Mode A (Exact) due to hair clipping when subject clipping is strictly prohibited.
    expectations = {
        # sample_exact_300x400_50kb_white_bg.json (Exact / Crop Mode A)
        ("sample_exact_300x400_50kb_white_bg.json", "single_face_frontal.jpg"): False,
        ("sample_exact_300x400_50kb_white_bg.json", "sarah_bernhardt_long_hair.jpg"): True,
        ("sample_exact_300x400_50kb_white_bg.json", "marie_curie_curly_hair.jpg"): False,
        ("sample_exact_300x400_50kb_white_bg.json", "lincoln_low_contrast.jpg"): False,
        ("sample_exact_300x400_50kb_white_bg.json", "roosevelt_muir_yosemite.jpg"): False,
        ("sample_exact_300x400_50kb_white_bg.json", "freud_spectacles_beard.jpg"): False,
        ("sample_exact_300x400_50kb_white_bg.json", "vivekananda_head_covering.jpg"): False,

        # sample_range_200_300_width_230_400_height_50kb_white_bg.json (Range / Crop Mode B)
        ("sample_range_200_300_width_230_400_height_50kb_white_bg.json", "single_face_frontal.jpg"): False,
        ("sample_range_200_300_width_230_400_height_50kb_white_bg.json", "sarah_bernhardt_long_hair.jpg"): False,
        ("sample_range_200_300_width_230_400_height_50kb_white_bg.json", "marie_curie_curly_hair.jpg"): True,
        ("sample_range_200_300_width_230_400_height_50kb_white_bg.json", "lincoln_low_contrast.jpg"): False,
        ("sample_range_200_300_width_230_400_height_50kb_white_bg.json", "roosevelt_muir_yosemite.jpg"): False,
        ("sample_range_200_300_width_230_400_height_50kb_white_bg.json", "freud_spectacles_beard.jpg"): False,
        ("sample_range_200_300_width_230_400_height_50kb_white_bg.json", "vivekananda_head_covering.jpg"): False,
    }

    face_model_path = repo_root / "model-assets" / "blaze_face_short_range.tflite"
    segmenter_model_path = repo_root / "model-assets" / "selfie_segmentation.tflite"

    face_sha = ""
    seg_sha = ""
    face_manifest = repo_root / "model-manifests" / "face-detector.json"
    segmenter_manifest = repo_root / "model-manifests" / "subject-segmenter.json"
    
    if face_manifest.exists():
        try:
            with open(face_manifest) as mf:
                face_sha = json.load(mf).get("sha256", "")
        except Exception:
            pass
    if segmenter_manifest.exists():
        try:
            with open(segmenter_manifest) as mf:
                m_data = json.load(mf)
                seg_sha = (
                    m_data.get("variants", {})
                    .get("selfie_bin_general", {})
                    .get("sha256", "")
                )
        except Exception:
            pass

    # Enforce --require-real validation
    if "--require-real" in sys.argv:
        if not face_model_path.exists():
            logger.error(f"ERROR: Face detector model missing: {face_model_path}")
            sys.exit(1)
        if not segmenter_model_path.exists():
            logger.error(f"ERROR: Segmenter model missing: {segmenter_model_path}")
            sys.exit(1)

    # Initialize the orchestration pipeline
    pipeline = RuleOrchestratedPipeline(
        face_model_path=face_model_path,
        segmenter_model_path=segmenter_model_path,
        face_expected_sha256=face_sha,
        segmenter_expected_sha256=seg_sha
    )

    config = RulePipelineConfig(
        save_diagnostic_artifacts=False,
        allow_invalid_output=False
    )

    passed = 0
    failed = 0
    skipped = 0
    total_evaluations = 0

    for rule_name in rules:
        rule_path = examples_dir / rule_name
        if not rule_path.exists():
            logger.error(f"Rule file not found: {rule_path}")
            failed += 1
            continue

        try:
            with open(rule_path, "r", encoding="utf-8") as rf:
                rule_dict = json.load(rf)
        except Exception as e:
            logger.error(f"Failed to read rule file {rule_name}: {e}")
            failed += 1
            continue

        for fixture_name in fixtures:
            img_path = fixtures_dir / fixture_name
            if not img_path.exists():
                logger.error(f"Fixture image not found: {img_path}")
                failed += 1
                continue

            logger.info(f"Evaluating {fixture_name} with rule {rule_name}...")
            total_evaluations += 1
            start_time = time.perf_counter()

            try:
                with open(img_path, "rb") as f_img:
                    image_bytes = f_img.read()

                result = pipeline.process_rule(image_bytes, rule_dict, config)
                duration_ms = (time.perf_counter() - start_time) * 1000.0

                expected_valid = expectations.get((rule_name, fixture_name))
                
                if result.is_valid == expected_valid:
                    logger.info(
                        f"  [PASS] {fixture_name} + {rule_name} matched expected validity ({expected_valid}) in {duration_ms:.2f}ms. "
                        f"Actual is_valid: {result.is_valid}. Issue codes: {[c.value for c in result.issue_codes]}"
                    )
                    passed += 1
                else:
                    logger.error(
                        f"  [FAIL] {fixture_name} + {rule_name} did not match expected validity ({expected_valid}). "
                        f"Actual is_valid: {result.is_valid}. Issue codes: {[c.value for c in result.issue_codes]}"
                    )
                    failed += 1
            except Exception as e:
                logger.error(f"  [FAIL] {fixture_name} + {rule_name} raised exception: {e}")
                import traceback
                logger.error(traceback.format_exc())
                failed += 1

    logger.info(
        f"\nRule Pipeline Benchmark Complete.\n"
        f"Passed: {passed}, Failed: {failed}, Skipped: {skipped}, Total Evaluated: {total_evaluations}"
    )

    if "--require-real" in sys.argv:
        if total_evaluations < 14:
            logger.error(
                f"ERROR: Expected at least 14 evaluations under --require-real, got {total_evaluations}."
            )
            sys.exit(1)
        if skipped > 0:
            logger.error("ERROR: Skips are not allowed under --require-real.")
            sys.exit(1)

    if failed > 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    run_benchmark()
