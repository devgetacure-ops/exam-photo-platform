#!/usr/bin/env python
"""Benchmark tool comparing multiclass and binary segmenters on licensed fixtures."""

import argparse
import json
import os
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
from exam_photo.providers.landmark_geometric_head_estimator import LandmarkGeometricHeadEstimator
from exam_photo.providers.segmenters.mediapipe_segmenter import MediapipeSubjectSegmenter


def get_cpu_info() -> str:
    try:
        return platform.processor() or platform.machine()
    except Exception:
        return "Unknown CPU"


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark subject segmenters.")
    parser.add_argument("--require-real", action="store_true", help="Fail if real models are missing or regression is detected.")
    parser.add_argument("--runs", type=int, default=5, help="Number of warm runs for averaging.")
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
            face_model_path = _REPO_ROOT / fm.get("local_model_path_default", "model-assets/blaze_face_short_range.tflite")
            face_sha = fm.get("sha256", "")

    # Set up fixtures
    fixtures_dir = _REPO_ROOT / "tests" / "fixtures"
    
    # Load ground-truth masks metadata from annotations.json if available
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
            print(f"Warning: could not load annotations.json: {e}")
            
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
            print(f"Warning: could not initialize face detector: {e}")

    for img_name in fixture_images:
        path = fixtures_dir / img_name
        if not path.exists():
            print(f"Error: Fixture image {path} not found.")
            sys.exit(1)
        
        with open(path, "rb") as f:
            data = f.read()
        norm_res = normalize_image_input(data, str(path), limits)
        
        face = None
        head_box = None
        if face_detector:
            try:
                with face_detector:
                    face_res = face_detector.detect_faces(norm_res.image)
                    if len(face_res.detections) == 1:
                        face = face_res.detections[0]
                        head_est = LandmarkGeometricHeadEstimator()
                        head_res = head_est.estimate_head(norm_res.image, face, face.landmarks)
                        head_box = head_res.head_bounding_box
            except Exception as e:
                print(f"  Warning on {img_name}: {e}")

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
            print(f"  Failed cold init: {e}")
            segmenter.close()
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
            
            # Print warm-up statistics separately
            t_warm0 = time.perf_counter()
            segmenter.segment_subject(image, face=face, head_estimate=head_box)
            warmup_ms = (time.perf_counter() - t_warm0) * 1000.0
            print(f"    Warm-up run: {warmup_ms:.2f} ms")

            run_durations = []
            val_reports = []
            
            for run_idx in range(args.runs):
                t0 = time.perf_counter()
                res = segmenter.segment_subject(image, face=face, head_estimate=head_box)
                dur = (time.perf_counter() - t0) * 1000.0
                run_durations.append(dur)
                if run_idx == 0:
                    val_reports.append(res.mask_validation)
                    # Get internal post-processing time
                    results[var_name]["model_name"] = res.model_name
                    results[var_name]["model_version"] = res.model_version
                    
                    # Calculate IoU if ground truth mask is available
                    iou = None
                    gt_entry = annotations.get(img_name)
                    if gt_entry:
                        gt_mask_path = fixtures_dir / gt_entry["ground_truth_mask_filename"]
                        if gt_mask_path.exists():
                            from PIL import Image
                            gt_mask = Image.open(gt_mask_path).convert("L")
                            gt_arr = np.array(gt_mask)
                            pred_arr = np.array(res.coarse_mask)
                            bin_pred = (pred_arr == 255)
                            bin_gt = (gt_arr == 255)
                            intersection = np.logical_and(bin_pred, bin_gt).sum()
                            union = np.logical_or(bin_pred, bin_gt).sum()
                            if union == 0:
                                iou = 1.0
                            else:
                                iou = float(intersection / union)
            
            mean_dur = np.mean(run_durations)
            median_dur = np.median(run_durations)
            min_dur = np.min(run_durations)
            max_dur = np.max(run_durations)
            
            val = val_reports[0]
            iou_str = f", IoU={iou:.4f}" if iou is not None else ""
            print(f"    Warm runs ({args.runs} iterations): Mean={mean_dur:.2f}ms, Median={median_dur:.2f}ms, Min={min_dur:.2f}ms")
            print(f"    Validation: is_valid={val.is_valid}, components={val.connected_components_count}, coverage={val.foreground_coverage_ratio:.4f}{iou_str}")
            
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
                "iou": iou,
            }

        segmenter.close()

    # Generate Markdown Summary Report
    print("\n" + "=" * 60)
    print("Benchmark Summary Report")
    print("=" * 60)
    print(f"CPU: {get_cpu_info()}\n")
    
    headers = ["Variant / Model", "Cold Init (ms)", "Fixture", "Mean Latency (ms)", "Coverage", "Components", "IoU", "Is Valid?"]
    row_fmt = "| {:<22} | {:<14} | {:<25} | {:<17} | {:<8} | {:<10} | {:<6} | {:<9} |"
    sep = "|" + "-" * 24 + "|" + "-" * 16 + "|" + "-" * 27 + "|" + "-" * 19 + "|" + "-" * 10 + "|" + "-" * 12 + "|" + "-" * 8 + "|" + "-" * 11 + "|"
    
    print(row_fmt.format(*headers))
    print(sep)
    
    for var_name, var_res in results.items():
        cold_str = f"{var_res['cold_init_ms']:.1f}"
        model_str = f"{var_res['model_name']} ({var_name})"
        
        for img_name, fix_res in var_res["fixtures"].items():
            iou_val = fix_res.get("iou")
            iou_str = f"{iou_val:.4f}" if iou_val is not None else "N/A"
            print(row_fmt.format(
                model_str[:22],
                cold_str,
                img_name,
                f"{fix_res['mean_ms']:.2f}",
                f"{fix_res['coverage']:.3f}",
                str(fix_res["components"]),
                iou_str,
                "YES" if fix_res["is_valid"] else "NO"
            ))
            cold_str = ""
            model_str = ""
    print("-" * 60)

    # Hardened --require-real exit codes on quality errors
    if args.require_real:
        print("\nVerifying Quality Gate Requirements (--require-real)...")
        # Ensure all variants in manifest are evaluated
        for var_name in variants:
            if var_name not in results:
                print(f"ERROR: Model variant {var_name} was not evaluated.", file=sys.stderr)
                sys.exit(1)
        
        has_regression = False
        for var_name, var_res in results.items():
            # Only enforce quality checks on the primary binary baseline
            if "bin" in var_name:
                for img_name, fix_res in var_res["fixtures"].items():
                    iou_val = fix_res.get("iou")
                    if iou_val is not None:
                        expected_min_iou = 0.99
                        if iou_val < expected_min_iou:
                            print(f"  [FAIL] {var_name} on {img_name}: IoU is {iou_val:.4f} (expected >= {expected_min_iou})", file=sys.stderr)
                            has_regression = True
                        else:
                            print(f"  [PASS] {var_name} on {img_name}: IoU is {iou_val:.4f}")
        
        if has_regression:
            print("ERROR: Quality gate validation failed due to regressions.", file=sys.stderr)
            sys.exit(1)
        else:
            print("All quality gate validations passed successfully.")


if __name__ == "__main__":
    main()
