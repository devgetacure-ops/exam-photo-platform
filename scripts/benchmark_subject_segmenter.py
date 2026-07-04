#!/usr/bin/env python
"""Benchmark tool comparing multiclass and binary segmenters on licensed fixtures."""

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

# Add src to path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "services" / "image-engine" / "src"))

from exam_photo.input.limits import InputLimits
from exam_photo.input.normalization import normalize_image_input
from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector
from exam_photo.providers.landmark_geometric_head_estimator import (
    LandmarkGeometricHeadEstimator,
)
from exam_photo.providers.segmenters.mediapipe_segmenter import (
    MediapipeSubjectSegmenter,
)


def get_cpu_info() -> str:
    try:
        return platform.processor() or platform.machine()
    except Exception:
        return "Unknown CPU"


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark subject segmenters.")
    parser.add_argument(
        "--require-real",
        action="store_true",
        help="Fail if real models are missing or regression is detected.",
    )
    parser.add_argument(
        "--runs", type=int, default=5, help="Number of warm runs for averaging."
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Subject Segmentation Benchmarking Tool")
    print("=" * 60)
    print(f"System Platform: {platform.system()} {platform.release()}")
    print(f"CPU Info:        {get_cpu_info()}")
    print(f"Python Version:  {platform.python_version()}")
    print("-" * 60)

    # 1. Check/Load models
    manifest_path = _REPO_ROOT / "model-manifests" / "subject-segmenter.json"
    if not manifest_path.exists():
        print(f"ERROR: manifest not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Detect face model
    face_manifest_path = _REPO_ROOT / "model-manifests" / "face-detector.json"
    face_model_path = _REPO_ROOT / "model-assets" / "blaze_face_short_range.tflite"
    face_sha = ""
    if face_manifest_path.exists():
        with open(face_manifest_path, "r", encoding="utf-8") as f:
            fm = json.load(f)
            face_model_path = _REPO_ROOT / fm.get(
                "local_model_path_default", "model-assets/blaze_face_short_range.tflite"
            )
            face_sha = fm.get("sha256", "")

    # Set up fixtures
    fixtures_dir = _REPO_ROOT / "tests" / "fixtures"

    # Load annotations metadata
    anno_path = fixtures_dir / "segmentation" / "annotations.json"
    annotations = {}
    fixture_images = []
    if anno_path.exists():
        try:
            with open(anno_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
                for entry in manifest_data.get("entries", []):
                    annotations[entry["source_fixture"]] = entry
                    if (fixtures_dir / entry["source_fixture"]).exists():
                        fixture_images.append(entry["source_fixture"])
        except Exception as e:
            print(f"Error: could not load annotations.json: {e}", file=sys.stderr)
            if args.require_real:
                sys.exit(1)
    else:
        print("Error: annotations.json not found.", file=sys.stderr)
        if args.require_real:
            sys.exit(1)

    expected_fixtures = [
        "sarah_bernhardt_long_hair.jpg",
        "marie_curie_curly_hair.jpg",
        "vivekananda_head_covering.jpg",
        "lincoln_low_contrast.jpg",
        "single_face_frontal.jpg",
        "roosevelt_muir_yosemite.jpg",
        "freud_spectacles_beard.jpg",
    ]
    if args.require_real:
        for fname in expected_fixtures:
            if fname not in annotations:
                print(
                    f"Error: Required annotation entry '{fname}' is missing.",
                    file=sys.stderr,
                )
                sys.exit(1)
            entry = annotations[fname]
            if not (fixtures_dir / fname).exists():
                print(
                    f"Error: Referenced source file '{fname}' is missing.",
                    file=sys.stderr,
                )
                sys.exit(1)
            mask_rel = entry.get("regression_mask_filename")
            if not mask_rel or not (fixtures_dir / mask_rel).exists():
                print(
                    f"Error: Referenced mask file '{mask_rel}' is missing for '{fname}'.",
                    file=sys.stderr,
                )
                sys.exit(1)

    # Fallback/ensure default images are included
    for extra_fix in ["blank_white_600x800.jpg", "geometric_shapes_600x800.jpg"]:
        if (fixtures_dir / extra_fix).exists() and extra_fix not in fixture_images:
            fixture_images.append(extra_fix)

    # Run face detection and head estimation to have inputs ready
    normalized_fixtures = {}
    limits = InputLimits()

    print("Pre-processing fixtures (Normalizing and running face/head detection)...")

    face_detector = None
    if face_model_path.exists():
        try:
            face_detector = MediapipeFaceDetector(face_model_path, face_sha)
        except Exception as e:
            print(f"Error: could not initialize face detector: {e}", file=sys.stderr)
            if args.require_real:
                sys.exit(1)
    else:
        print(
            f"Error: face detector model not found at {face_model_path}",
            file=sys.stderr,
        )
        if args.require_real:
            sys.exit(1)

    for img_name in fixture_images:
        path = fixtures_dir / img_name
        if not path.exists():
            print(f"Error: Fixture image {path} not found.", file=sys.stderr)
            sys.exit(1)

        with open(path, "rb") as f:
            data = f.read()
        norm_res = normalize_image_input(data, str(path), limits)

        face = None
        head_box = None

        expected_faces = 1
        entry = annotations.get(img_name)
        if entry and "expected_face_count" in entry:
            expected_faces = entry["expected_face_count"]
        elif img_name in ("blank_white_600x800.jpg", "geometric_shapes_600x800.jpg"):
            expected_faces = 0

        if face_detector:
            try:
                # Use custom lower confidence for Yosemite and Lincoln
                if img_name in (
                    "roosevelt_muir_yosemite.jpg",
                    "lincoln_low_contrast.jpg",
                ):
                    curr_detector = MediapipeFaceDetector(
                        face_model_path, face_sha, min_detection_confidence=0.2
                    )
                else:
                    curr_detector = face_detector

                with curr_detector:
                    face_res = curr_detector.detect_faces(norm_res.image)
                    detected_count = len(face_res.detections)
                    if args.require_real and detected_count != expected_faces:
                        print(
                            f"Error: Expected {expected_faces} face(s) in {img_name}, but detected {detected_count}.",
                            file=sys.stderr,
                        )
                        sys.exit(1)

                    # Store all detections for segmenter
                    face = face_res.detections if detected_count > 0 else None

                    if detected_count == 1:
                        single_face = face_res.detections[0]
                        head_est = LandmarkGeometricHeadEstimator()
                        head_cfg = (
                            {"minimum_face_confidence": 0.2}
                            if single_face.confidence < 0.5
                            else None
                        )
                        head_res = head_est.estimate_head(
                            norm_res.image,
                            single_face,
                            single_face.landmarks,
                            config=head_cfg,
                        )
                        head_box = head_res.head_bounding_box
            except Exception as e:
                print(
                    f"  Error on {img_name} face/head processing: {e}", file=sys.stderr
                )
                if args.require_real:
                    sys.exit(1)

        normalized_fixtures[img_name] = {
            "norm_res": norm_res,
            "face": face,
            "head_box": head_box,
        }

    # Iterate over segmenter variants
    variants = manifest.get("variants", {})
    results = {}

    for var_name, var_info in variants.items():
        filename = var_info.get("filename")
        sha = var_info.get("sha256")
        model_path = _REPO_ROOT / "model-assets" / filename

        print(f"\nEvaluating variant: {var_name}")
        if not model_path.exists():
            print(f"  Model file missing: {model_path}")
            if args.require_real:
                print("  ERROR: --require-real specified, aborting.", file=sys.stderr)
                sys.exit(1)
            continue

        results[var_name] = {}

        # Measure Cold Initialization
        t_start = time.perf_counter()
        segmenter = MediapipeSubjectSegmenter(model_path, sha)
        try:
            # We run segmentation once on blank image to measure cold init (loading models)
            dummy_res = normalized_fixtures.get("blank_white_600x800.jpg")
            if not dummy_res:
                # Fallback to the first available fixture
                dummy_res = list(normalized_fixtures.values())[0]
            segmenter.segment_subject(
                dummy_res["norm_res"].image,
                face=dummy_res["face"],
                head_estimate=dummy_res["head_box"],
            )
            cold_init_ms = (time.perf_counter() - t_start) * 1000.0
            print(f"  Cold Initialization time: {cold_init_ms:.2f} ms")
        except Exception as e:
            print(f"  Failed cold init: {e}", file=sys.stderr)
            segmenter.close()
            if args.require_real:
                sys.exit(1)
            continue

        # Benchmark warm runs on each fixture
        results[var_name]["cold_init_ms"] = cold_init_ms
        results[var_name]["fixtures"] = {}

        for img_name in fixture_images:
            fix_data = normalized_fixtures[img_name]
            image = fix_data["norm_res"].image
            face = fix_data["face"]
            head_box = fix_data["head_box"]

            print(f"  Benchmarking on {img_name} ({image.width}x{image.height})...")

            # At least three warm-up runs
            warmup_durations = []
            for wu in range(3):
                t_w = time.perf_counter()
                segmenter.segment_subject(image, face=face, head_estimate=head_box)
                warmup_durations.append((time.perf_counter() - t_w) * 1000.0)
            print(
                f"    3 Warm-up runs: {', '.join(f'{w:.2f}ms' for w in warmup_durations)}"
            )

            inference_durations = []
            mask_extraction_durations = []
            resize_threshold_durations = []
            validation_durations = []
            total_durations = []
            val_reports = []

            for run_idx in range(args.runs):
                res = segmenter.segment_subject(
                    image, face=face, head_estimate=head_box
                )
                inference_durations.append(res.inference_duration_ms or 0.0)
                mask_extraction_durations.append(res.mask_extraction_duration_ms or 0.0)
                resize_threshold_durations.append(
                    res.resize_threshold_duration_ms or 0.0
                )
                validation_durations.append(res.validation_duration_ms or 0.0)
                total_durations.append(res.processing_duration)
                if run_idx == 0:
                    val_reports.append(res.mask_validation)
                    # Get internal post-processing time
                    results[var_name]["model_name"] = res.model_name
                    results[var_name]["model_version"] = res.model_version

                    # Calculate Stability IoU (Regression) if regression mask is available
                    stability_iou = None
                    quality_iou = None
                    gt_entry = annotations.get(img_name)
                    if gt_entry:
                        # Verify regression mask checksum
                        gt_mask_path = (
                            fixtures_dir / gt_entry["regression_mask_filename"]
                        )
                        if gt_mask_path.exists():
                            expected_sha = gt_entry.get("mask_sha256")
                            if expected_sha:
                                import hashlib

                                h_sha = hashlib.sha256()
                                with open(gt_mask_path, "rb") as mf:
                                    h_sha.update(mf.read())
                                actual_sha = h_sha.hexdigest()
                                if actual_sha != expected_sha:
                                    print(
                                        f"Error: Checksum mismatch for regression mask {gt_mask_path}: expected {expected_sha}, got {actual_sha}",
                                        file=sys.stderr,
                                    )
                                    sys.exit(1)

                            from PIL import Image

                            gt_mask = Image.open(gt_mask_path).convert("L")
                            gt_arr = np.array(gt_mask)
                            pred_arr = np.array(res.coarse_mask)
                            bin_pred = pred_arr == 255
                            bin_gt = gt_arr == 255
                            intersection = np.logical_and(bin_pred, bin_gt).sum()
                            union = np.logical_or(bin_pred, bin_gt).sum()
                            if union == 0:
                                stability_iou = 1.0
                            else:
                                stability_iou = float(intersection / union)

                        # Calculate Quality IoU (Reference) if reference mask is available
                        ref_mask_rel = gt_entry.get("reference_mask_filename")
                        if ref_mask_rel:
                            ref_mask_path = fixtures_dir / ref_mask_rel
                            if ref_mask_path.exists():
                                ref_expected_sha = gt_entry.get("reference_mask_sha256")
                                if ref_expected_sha:
                                    import hashlib

                                    h_sha = hashlib.sha256()
                                    with open(ref_mask_path, "rb") as mf:
                                        h_sha.update(mf.read())
                                    actual_ref_sha = h_sha.hexdigest()
                                    if actual_ref_sha != ref_expected_sha:
                                        print(
                                            f"Error: Checksum mismatch for reference mask {ref_mask_path}: expected {ref_expected_sha}, got {actual_ref_sha}",
                                            file=sys.stderr,
                                        )
                                        sys.exit(1)

                                ref_mask = Image.open(ref_mask_path).convert("L")
                                ref_arr = np.array(ref_mask)
                                pred_arr = np.array(res.coarse_mask)
                                bin_pred = pred_arr == 255
                                bin_ref = ref_arr == 255
                                intersection = np.logical_and(bin_pred, bin_ref).sum()
                                union = np.logical_or(bin_pred, bin_ref).sum()
                                if union == 0:
                                    quality_iou = 1.0
                                else:
                                    quality_iou = float(intersection / union)

            mean_dur = np.mean(total_durations)
            median_dur = np.median(total_durations)
            p95_dur = np.percentile(total_durations, 95)
            min_dur = np.min(total_durations)
            max_dur = np.max(total_durations)

            mean_inf = np.mean(inference_durations)
            p95_inf = np.percentile(inference_durations, 95)

            mean_ext = np.mean(mask_extraction_durations)
            p95_ext = np.percentile(mask_extraction_durations, 95)

            mean_res = np.mean(resize_threshold_durations)
            p95_res = np.percentile(resize_threshold_durations, 95)

            mean_val = np.mean(validation_durations)
            p95_val = np.percentile(validation_durations, 95)

            val = val_reports[0]
            iou_str = ""
            if stability_iou is not None:
                iou_str += f", Stability IoU (Regression)={stability_iou:.4f}"
            if quality_iou is not None:
                iou_str += f", Quality IoU (Reference)={quality_iou:.4f}"
            print(
                f"    Warm runs ({args.runs} iterations) Total Timing: Mean={mean_dur:.2f}ms, Median={median_dur:.2f}ms, p95={p95_dur:.2f}ms, Min={min_dur:.2f}ms"
            )
            print(
                f"    Timing Breakdowns (Mean / p95): Inference={mean_inf:.2f}ms/{p95_inf:.2f}ms, Extraction={mean_ext:.2f}ms/{p95_ext:.2f}ms, Resize/Threshold={mean_res:.2f}ms/{p95_res:.2f}ms, Validation={mean_val:.2f}ms/{p95_val:.2f}ms"
            )
            print(
                f"    Validation: is_valid={val.is_valid}, components={val.connected_components_count}, coverage={val.foreground_coverage_ratio:.4f}{iou_str}"
            )

            if args.require_real:
                is_invalid_expected = img_name in (
                    "blank_white_600x800.jpg",
                    "geometric_shapes_600x800.jpg",
                )
                if is_invalid_expected:
                    if val.is_valid:
                        print(
                            f"    [FAIL] Expected invalid result for {img_name}, but mask was valid.",
                            file=sys.stderr,
                        )
                        sys.exit(1)
                    if (
                        img_name
                        in ("blank_white_600x800.jpg", "geometric_shapes_600x800.jpg")
                        and val.foreground_coverage_ratio > 0.05
                    ):
                        print(
                            f"    [FAIL] Expected coverage < 0.05 for {img_name}, got {val.foreground_coverage_ratio:.4f}",
                            file=sys.stderr,
                        )
                        sys.exit(1)
                else:
                    if not val.is_valid:
                        print(
                            f"    [FAIL] Expected valid result for {img_name}, but mask was invalid. Issues: {val.issue_codes}",
                            file=sys.stderr,
                        )
                        sys.exit(1)

            results[var_name]["fixtures"][img_name] = {
                "mean_ms": mean_dur,
                "median_ms": median_dur,
                "min_ms": min_dur,
                "max_ms": max_dur,
                "is_valid": val.is_valid,
                "components": val.connected_components_count,
                "coverage": val.foreground_coverage_ratio,
                "uncertain_pixel_ratio": val.uncertain_pixel_ratio,
                "face_contained": val.face_contained,
                "head_coverage": val.head_region_coverage_ratio,
                "issue_codes": val.issue_codes,
                "stability_iou": stability_iou,
                "quality_iou": quality_iou,
            }

        segmenter.close()

    # Generate Markdown Summary Report
    print("\n" + "=" * 60)
    print("Benchmark Summary Report")
    print("=" * 60)
    print(f"CPU: {get_cpu_info()}\n")

    headers = [
        "Variant / Model",
        "Cold Init (ms)",
        "Fixture",
        "Mean Latency (ms)",
        "Coverage",
        "Components",
        "Stability IoU",
        "Quality IoU",
        "Is Valid?",
    ]
    row_fmt = "| {:<22} | {:<14} | {:<25} | {:<17} | {:<8} | {:<10} | {:<13} | {:<11} | {:<9} |"
    sep = (
        "|"
        + "-" * 24
        + "|"
        + "-" * 16
        + "|"
        + "-" * 27
        + "|"
        + "-" * 19
        + "|"
        + "-" * 10
        + "|"
        + "-" * 12
        + "|"
        + "-" * 15
        + "|"
        + "-" * 13
        + "|"
        + "-" * 11
        + "|"
    )

    print(row_fmt.format(*headers))
    print(sep)

    for var_name, var_res in results.items():
        cold_str = f"{var_res['cold_init_ms']:.1f}"
        model_str = f"{var_res['model_name']} ({var_name})"

        for img_name, fix_res in var_res["fixtures"].items():
            stab_iou = fix_res.get("stability_iou")
            qual_iou = fix_res.get("quality_iou")
            stab_str = f"{stab_iou:.4f}" if stab_iou is not None else "N/A"
            qual_str = f"{qual_iou:.4f}" if qual_iou is not None else "N/A"
            print(
                row_fmt.format(
                    model_str[:22],
                    cold_str,
                    img_name,
                    f"{fix_res['mean_ms']:.2f}",
                    f"{fix_res['coverage']:.3f}",
                    str(fix_res["components"]),
                    stab_str,
                    qual_str,
                    "YES" if fix_res["is_valid"] else "NO",
                )
            )
            cold_str = ""
            model_str = ""
    print("-" * 60)

    # Hardened --require-real exit codes on quality errors
    if args.require_real:
        print("\nVerifying Quality Gate Requirements (--require-real)...")
        # Ensure all variants in manifest are evaluated
        for var_name in variants:
            if var_name not in results:
                print(
                    f"ERROR: Model variant {var_name} was not evaluated.",
                    file=sys.stderr,
                )
                sys.exit(1)

        has_regression = False
        for var_name, var_res in results.items():
            # Only enforce quality checks on the primary binary baseline
            if "bin" in var_name:
                for img_name, fix_res in var_res["fixtures"].items():
                    # For real person fixtures, verify stability IoU exists and meets threshold
                    is_special = img_name in (
                        "blank_white_600x800.jpg",
                        "geometric_shapes_600x800.jpg",
                    )
                    stab_iou = fix_res.get("stability_iou")
                    if not is_special:
                        if stab_iou is None:
                            print(
                                f"  [FAIL] {var_name} on {img_name}: Stability IoU (Regression) metric is missing or could not be calculated.",
                                file=sys.stderr,
                            )
                            sys.exit(1)
                        expected_min_iou = 0.99
                        if stab_iou < expected_min_iou:
                            print(
                                f"  [FAIL] {var_name} on {img_name}: Stability IoU is {stab_iou:.4f} (expected >= {expected_min_iou})",
                                file=sys.stderr,
                            )
                            has_regression = True
                        else:
                            print(
                                f"  [PASS] {var_name} on {img_name}: Stability IoU is {stab_iou:.4f}"
                            )

        if has_regression:
            print(
                "ERROR: Quality gate validation failed due to regressions.",
                file=sys.stderr,
            )
            sys.exit(1)
        else:
            print("All quality gate validations passed successfully.")


if __name__ == "__main__":
    main()
