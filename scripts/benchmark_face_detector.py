#!/usr/bin/env python
"""Benchmark script for the MediaPipe BlazeFace face-detection provider.

Reports separately:
* Cold initialization time (first detect_faces call that triggers _ensure_initialized)
* Warm-up runs (excluded from statistics)
* Inference latency statistics: min, median, mean, p95, max
* Image information: path, dimensions, colour mode
* Model information: variant, manifest path, MediaPipe version
* CPU / environment information
* Detection summary: count, confidence values, bounding-box summary per run
* Any failures encountered

The image is passed through the existing secure normalization stage
(exam_photo.input.normalization) rather than opened independently.

Usage
-----
    python scripts/benchmark_face_detector.py \\
        --image path/to/image.jpg \\
        --model model-assets/blaze_face_full_range.task \\
        --sha256 <hex>  \\
        --variant full_range \\
        --warmup 5 \\
        --runs 50
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

# Ensure the image-engine src is importable when run from the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_ENGINE_SRC = _REPO_ROOT / "services" / "image-engine" / "src"
if str(_ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(_ENGINE_SRC))


def _get_mediapipe_version() -> str:
    try:
        import mediapipe as mp  # type: ignore[import-untyped]

        return str(getattr(mp, "__version__", "unknown"))
    except ImportError:
        return "not-installed"


def _load_manifest(manifest_path: Path) -> dict[str, object]:
    if manifest_path.exists():
        with manifest_path.open() as fh:
            return json.load(fh)  # type: ignore[no-any-return]
    return {}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark MediaPipe BlazeFace face-detection latency."
    )
    parser.add_argument("--image", required=True, type=Path, help="Input image path.")
    parser.add_argument(
        "--model",
        required=True,
        type=Path,
        help="Path to the .task model asset file.",
    )
    parser.add_argument(
        "--sha256",
        default="",
        help="Expected SHA-256 of model file (leave empty to skip check).",
    )
    parser.add_argument(
        "--variant",
        default="unknown",
        help="Model variant name (short_range / full_range) for reporting.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.5,
        help="Minimum detection confidence threshold (default: 0.5).",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=5,
        help="Number of warm-up runs excluded from statistics (default: 5).",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=50,
        help="Number of timed inference runs (default: 50).",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # 1. Load and normalise image through the secure pipeline
    # ------------------------------------------------------------------
    from exam_photo.input.normalization import normalize_image_input
    from exam_photo.input.limits import InputLimits

    try:
        image_bytes = args.image.read_bytes()
    except OSError as exc:
        print(json.dumps({"error": f"Cannot read image: {exc}"}))
        sys.exit(1)

    try:
        norm_result = normalize_image_input(
            image_bytes,
            filename=args.image.name,
            limits=InputLimits(),
        )
        image = norm_result.image
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": f"Normalization failed: {exc}"}))
        sys.exit(1)

    img_w, img_h = image.size
    img_mode = image.mode

    # ------------------------------------------------------------------
    # 2. Build provider
    # ------------------------------------------------------------------
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector

    provider = MediapipeFaceDetector(
        model_path=args.model,
        expected_sha256=args.sha256,
        min_detection_confidence=args.confidence,
    )

    # ------------------------------------------------------------------
    # 3. Cold initialization (first call triggers _ensure_initialized)
    # ------------------------------------------------------------------
    cold_init_ms: float = 0.0
    cold_failures: list[str] = []
    try:
        cold_start = time.perf_counter()
        provider.detect_faces(image)
        cold_init_ms = (time.perf_counter() - cold_start) * 1000.0
    except Exception as exc:  # noqa: BLE001
        cold_failures.append(str(exc))

    # ------------------------------------------------------------------
    # 4. Warm-up runs (excluded from statistics)
    # ------------------------------------------------------------------
    warmup_failures: list[str] = []
    for _ in range(args.warmup):
        try:
            provider.detect_faces(image)
        except Exception as exc:  # noqa: BLE001
            warmup_failures.append(str(exc))

    # ------------------------------------------------------------------
    # 5. Timed inference runs
    # ------------------------------------------------------------------
    latencies_ms: list[float] = []
    detection_counts: list[int] = []
    confidence_values: list[list[float]] = []
    inference_failures: list[str] = []

    for _ in range(args.runs):
        try:
            t0 = time.perf_counter()
            result = provider.detect_faces(image)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(elapsed_ms)
            detection_counts.append(len(result.detections))
            confidence_values.append([d.confidence for d in result.detections])
        except Exception as exc:  # noqa: BLE001
            inference_failures.append(str(exc))

    provider.close()

    # ------------------------------------------------------------------
    # 6. Compute statistics
    # ------------------------------------------------------------------
    stats: dict[str, object] = {}
    if latencies_ms:
        sorted_lat = sorted(latencies_ms)
        n = len(sorted_lat)
        p95_idx = min(n - 1, int(round(0.95 * n)))
        stats = {
            "n": n,
            "min_ms": round(sorted_lat[0], 3),
            "median_ms": round(statistics.median(latencies_ms), 3),
            "mean_ms": round(statistics.mean(latencies_ms), 3),
            "p95_ms": round(sorted_lat[p95_idx], 3),
            "max_ms": round(sorted_lat[-1], 3),
            "stdev_ms": round(statistics.stdev(latencies_ms), 3) if n > 1 else 0.0,
        }

    # Detection-count agreement: all runs returned the same count?
    detection_agreement = len(set(detection_counts)) == 1 if detection_counts else None

    manifest = _load_manifest(_REPO_ROOT / "model-manifests" / "face-detector.json")

    report = {
        "benchmark": {
            "image": {
                "path": str(args.image),
                "width": img_w,
                "height": img_h,
                "mode": img_mode,
            },
            "model": {
                "path": str(args.model),
                "variant": args.variant,
                "manifest_sha256": manifest.get("sha256", "unknown"),
                "mediapipe_version": _get_mediapipe_version(),
            },
            "environment": {
                "python_version": platform.python_version(),
                "os": platform.platform(),
                "processor": platform.processor()
                or os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
            },
            "configuration": {
                "min_detection_confidence": args.confidence,
                "warmup_runs": args.warmup,
                "timed_runs": args.runs,
            },
            "cold_init_ms": round(cold_init_ms, 3),
            "latency_stats": stats,
            "detection_summary": {
                "counts_per_run": detection_counts,
                "agreement": detection_agreement,
                "mean_count": (
                    round(statistics.mean(detection_counts), 2)
                    if detection_counts
                    else None
                ),
                "sample_confidences_run_0": (
                    [round(c, 4) for c in confidence_values[0]]
                    if confidence_values
                    else []
                ),
            },
            "failures": {
                "cold_init": cold_failures,
                "warmup": warmup_failures,
                "inference": inference_failures,
            },
        }
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
