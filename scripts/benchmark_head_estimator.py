#!/usr/bin/env python
"""Benchmark script for the complete head estimator.

Measures:
- Latency (first call, warm loops, separate vs. combined face/head estimation)
- Quality metrics (IoU, boundary errors, face containment, clamping, clipping-state agreement)
  across multiple annotated fixtures.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path
from PIL import Image

# Ensure the image-engine src is importable when run from the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_ENGINE_SRC = _REPO_ROOT / "services" / "image-engine" / "src"
if str(_ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(_ENGINE_SRC))

from exam_photo.input.limits import InputLimits
from exam_photo.input.normalization import normalize_image_input
from exam_photo.models.geometry import BoundingBox, Landmarks, Point, PoseEstimate
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.landmark_geometric_head_estimator import (
    LandmarkGeometricHeadEstimator,
)


def _get_model_details() -> tuple[Path, str]:
    model_path_str = os.environ.get("EXAM_PHOTO_FACE_MODEL_PATH")
    expected_sha256 = os.environ.get("EXAM_PHOTO_FACE_MODEL_SHA256", "")

    if not model_path_str:
        manifest_path = _REPO_ROOT / "model-manifests" / "face-detector.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as mf:
                    manifest = json.load(mf)
                model_path_str = manifest.get("local_model_path_default")
                expected_sha256 = manifest.get("sha256", "")
            except Exception:
                pass
        if not model_path_str:
            model_path_str = "model-assets/blaze_face_short_range.tflite"

    return Path(model_path_str), expected_sha256


def calculate_iou(boxA: any, boxB: any) -> float:
    xA = max(boxA.left, boxB.left)
    yA = max(boxA.top, boxB.top)
    xB = min(boxA.right, boxB.right)
    yB = min(boxA.bottom, boxB.bottom)

    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = (boxA.right - boxA.left) * (boxA.bottom - boxA.top)
    boxBArea = (boxB.right - boxB.left) * (boxB.bottom - boxB.top)

    union = boxAArea + boxBArea - interArea
    if union <= 0:
        return 0.0
    return float(interArea / union)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark Complete Head Estimator latency and quality across multiple fixtures."
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=50,
        help="Number of timed runs for latency (default: 50).",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=5,
        help="Number of warm-up runs (default: 5).",
    )
    parser.add_argument(
        "--require-real",
        action="store_true",
        help="Fail if any real fixture is missing or face detection fails.",
    )
    args = parser.parse_args()

    # Load annotations
    annotations_path = _REPO_ROOT / "tests" / "fixtures" / "head_annotations.json"
    if not annotations_path.exists():
        annotations_path = (
            _REPO_ROOT
            / "services"
            / "image-engine"
            / "tests"
            / "fixtures"
            / "head_annotations.json"
        )

    if not annotations_path.exists():
        print(f"Error: Annotations file not found: {annotations_path}", file=sys.stderr)
        sys.exit(1)

    with open(annotations_path, "r", encoding="utf-8") as f:
        fixtures_data = json.load(f)

    estimator = LandmarkGeometricHeadEstimator()
    detector = None

    # Load real detector if needed
    model_path, sha256 = _get_model_details()
    if model_path.exists() or (_REPO_ROOT / model_path).exists():
        try:
            from exam_photo.providers.mediapipe_face_detector import (
                MediapipeFaceDetector,
            )

            detector = MediapipeFaceDetector(
                model_path=model_path
                if model_path.exists()
                else (_REPO_ROOT / model_path),
                expected_sha256=sha256,
            )
        except ImportError:
            pass

    # 1. Quality Evaluation across ALL fixtures
    print("=" * 110)
    print(f"{'FIXTURE QUALITY EVALUATION SUMMARY':^110}")
    print("=" * 110)
    print(
        f"{'Fixture Name':<25} | {'Contain':<7} | {'Clamped':<7} | {'GT IoU':<7} | "
        f"{'Top Err':<7} | {'L/R Err':<7} | {'Bottom Err':<10} | {'Clip Agree':<10}"
    )
    print("-" * 110)

    quality_results = []
    real_bench_image = None
    real_bench_face = None
    real_bench_landmarks = None

    for name, data in fixtures_data.items():
        is_real = data.get("is_real", False)
        img_w, img_h = data["image_size"]

        image = None
        face = None
        landmarks = None

        if is_real:
            # Load real image from canonical path
            img_path = _REPO_ROOT / "tests" / "fixtures" / name

            if args.require_real:
                if not img_path.exists():
                    print(
                        f"Error: Required real fixture image '{name}' missing at '{img_path}'",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                if detector is None:
                    print(
                        "Error: Face detector is required for --require-real but not available.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                try:
                    limits = InputLimits()
                    with open(img_path, "rb") as fh:
                        bytes_data = fh.read()
                    norm_res = normalize_image_input(bytes_data, str(img_path), limits)
                    image = norm_res.image
                    face_res = detector.detect_faces(image)
                    if not face_res.detections:
                        print(
                            f"Error: Face detection failed on required real fixture '{name}' (no faces detected).",
                            file=sys.stderr,
                        )
                        sys.exit(1)
                    face = face_res.detections[0]
                    landmarks = face.landmarks
                    if name == "single_face_frontal.jpg":
                        real_bench_image = image
                        real_bench_face = face
                        real_bench_landmarks = landmarks
                except Exception as ex:
                    print(
                        f"Error processing real fixture '{name}': {ex}", file=sys.stderr
                    )
                    sys.exit(1)
            else:
                if img_path.exists() and detector is not None:
                    try:
                        limits = InputLimits()
                        with open(img_path, "rb") as fh:
                            bytes_data = fh.read()
                        norm_res = normalize_image_input(
                            bytes_data, str(img_path), limits
                        )
                        image = norm_res.image
                        face_res = detector.detect_faces(image)
                        if face_res.detections:
                            face = face_res.detections[0]
                            landmarks = face.landmarks
                            if name == "single_face_frontal.jpg":
                                real_bench_image = image
                                real_bench_face = face
                                real_bench_landmarks = landmarks
                    except Exception as ex:
                        print(f"Skipping real image {name} due to error: {ex}")
                else:
                    is_real = False

        if not is_real:
            # Create synthetic blank image
            image = Image.new("RGB", (img_w, img_h), (240, 240, 240))
            # Parse simulated face box and landmarks
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
            if "landmarks" in data:
                lm = data["landmarks"]
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

        if image is None or face is None:
            continue

        # Run head estimator
        cfg = data.get("config", {})
        result = estimator.estimate_head(image, face, landmarks, config=cfg)

        # Quality assertions/computations
        face_contained = result.head_bounding_box.contains(face.bounding_box)
        clamped = result.safe_internal_metadata.get("clamped", False)

        gt = data.get("ground_truth_head_box")
        gt_box = (
            BoundingBox(
                left=gt["left"], top=gt["top"], right=gt["right"], bottom=gt["bottom"]
            )
            if gt
            else None
        )

        gt_iou = calculate_iou(result.head_bounding_box, gt_box) if gt_box else 0.0

        top_err = abs(result.head_bounding_box.top - gt_box.top) if gt_box else 0.0
        left_err = abs(result.head_bounding_box.left - gt_box.left) if gt_box else 0.0
        right_err = (
            abs(result.head_bounding_box.right - gt_box.right) if gt_box else 0.0
        )
        bottom_err = (
            abs(result.head_bounding_box.bottom - gt_box.bottom) if gt_box else 0.0
        )
        lr_err = (left_err + right_err) / 2.0

        # Clipping state agreement
        expected_clipping = data.get("expected_clipping", {})
        clip_agree = True
        if "top_hair" in expected_clipping:
            expected_status = expected_clipping["top_hair"]
            actual_status = result.clipping_assessment.top_hair.status.value
            if expected_status != actual_status:
                clip_agree = False

        print(
            f"{name:<25} | {str(face_contained):<7} | {str(clamped):<7} | "
            f"{gt_iou:>.4f} | {top_err:>.1f}px | {lr_err:>.1f}px | {bottom_err:>.1f}px | {str(clip_agree):<10}"
        )

        quality_results.append(
            {
                "name": name,
                "face_contained": face_contained,
                "clamped": clamped,
                "gt_iou": gt_iou,
                "top_err": top_err,
                "lr_err": lr_err,
                "bottom_err": bottom_err,
                "clip_agree": clip_agree,
            }
        )

    # 2. Latency Benchmarking (on single_face_frontal.jpg if available)
    if detector is not None and real_bench_image is not None:
        print("\n" + "=" * 50)
        print("SPEED / LATENCY BENCHMARK RESULTS")
        print("=" * 50)
        print("Running timed latency iterations on single_face_frontal.jpg...")

        # First-call / cold latency
        t0 = time.perf_counter()
        _ = detector.detect_faces(real_bench_image)
        t1 = time.perf_counter()
        cold_detector_ms = (t1 - t0) * 1000.0

        t0 = time.perf_counter()
        _ = estimator.estimate_head(
            real_bench_image, real_bench_face, real_bench_landmarks
        )
        t1 = time.perf_counter()
        cold_estimator_ms = (t1 - t0) * 1000.0

        print(f"Cold detector latency: {cold_detector_ms:.2f} ms")
        print(f"Cold estimator latency: {cold_estimator_ms:.2f} ms")

        # Warm-up runs
        for _ in range(args.warmup):
            face_res = detector.detect_faces(real_bench_image)
            _ = estimator.estimate_head(
                real_bench_image,
                face_res.detections[0],
                face_res.detections[0].landmarks,
            )

        detector_latencies = []
        estimator_latencies = []
        combined_latencies = []

        for _ in range(args.runs):
            t0 = time.perf_counter()
            face_res = detector.detect_faces(real_bench_image)
            t_mid = time.perf_counter()
            _ = estimator.estimate_head(
                real_bench_image,
                face_res.detections[0],
                face_res.detections[0].landmarks,
            )
            t_end = time.perf_counter()

            detector_latencies.append((t_mid - t0) * 1000.0)
            estimator_latencies.append((t_end - t_mid) * 1000.0)
            combined_latencies.append((t_end - t0) * 1000.0)

        print("\nFace Detector Latency (Warm):")
        print(f"  Min:    {min(detector_latencies):.2f} ms")
        print(f"  Mean:   {statistics.mean(detector_latencies):.2f} ms")
        print(f"  Median: {statistics.median(detector_latencies):.2f} ms")
        print(f"  Max:    {max(detector_latencies):.2f} ms")

        print("\nHead Estimator Latency (Warm):")
        print(f"  Min:    {min(estimator_latencies):.2f} ms")
        print(f"  Mean:   {statistics.mean(estimator_latencies):.2f} ms")
        print(f"  Median: {statistics.median(estimator_latencies):.2f} ms")
        print(f"  Max:    {max(estimator_latencies):.2f} ms")

        print("\nCombined Latency (Warm):")
        print(f"  Min:    {min(combined_latencies):.2f} ms")
        print(f"  Mean:   {statistics.mean(combined_latencies):.2f} ms")
        print(f"  Median: {statistics.median(combined_latencies):.2f} ms")
        print(f"  Max:    {max(combined_latencies):.2f} ms")

    print("\nSystem Information:")
    print(f"  OS:        {platform.system()} {platform.release()}")
    print(f"  Processor: {platform.processor()}")
    print(f"  Python:    {platform.python_version()}")


if __name__ == "__main__":
    main()
