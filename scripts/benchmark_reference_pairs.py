"""Compare engine results with matched, user-approved ideal output photos.

This benchmark intentionally treats the ideal outputs as the composition and
edge-quality specification.  It does not store source photos, output photos,
alpha masks, or model weights; only numeric measurements and issue codes are
written to JSON/CSV.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import statistics
import time
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_SRC = REPO_ROOT / "services" / "image-engine" / "src"
if str(ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(ENGINE_SRC))

from exam_photo.orchestration.rule_pipeline import (  # noqa: E402
    RuleOrchestratedPipeline,
    RulePipelineConfig,
)
from exam_photo.providers.face_detection import FaceDetection  # noqa: E402
from exam_photo.providers.mediapipe_face_detector import (  # noqa: E402
    MediapipeFaceDetector,
)
from exam_photo.providers.mediapipe_face_landmarker import (  # noqa: E402
    MediapipeFaceLandmarker,
    load_manifest_defaults as load_landmarker_defaults,
)
from exam_photo.providers.segmenters.birefnet_segmenter import (  # noqa: E402
    load_manifest_defaults as load_birefnet_defaults,
)


PAIR_KEY = re.compile(r"(?<!\d)(\d+-\d+)(?!\d)")
DIMENSIONS = re.compile(r"(\d+)\s*[xX\u00d7]\s*(\d+)")
FACE_CONFIDENCES = (0.5, 0.35, 0.25, 0.15)
EDGE_REGIONS = ("hair", "ears", "beard_line", "chin", "neck")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the 60-photo matched engine-vs-ideal benchmark."
    )
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--ideals", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument(
        "--ideal-cache",
        type=Path,
        help="Optional numeric-only ideal measurement cache.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Diagnostic only. Omit for the required complete benchmark.",
    )
    return parser.parse_args()


def pair_key(path: Path) -> str:
    match = PAIR_KEY.search(path.name)
    if match is None:
        raise ValueError(f"Cannot derive pair key from {path}")
    return match.group(1)


def target_dimensions(path: Path) -> tuple[int, int]:
    for parent in path.parents:
        match = DIMENSIONS.search(parent.name)
        if match is not None:
            return int(match.group(1)), int(match.group(2))
    raise ValueError(f"Cannot derive target dimensions from {path}")


def discover_pairs(inputs: Path, ideals: Path) -> list[tuple[str, Path, Path]]:
    input_files = {
        pair_key(path): path
        for path in inputs.rglob("*")
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    }
    ideal_files = {
        pair_key(path): path
        for path in ideals.rglob("*")
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    }
    if set(input_files) != set(ideal_files):
        missing_ideals = sorted(set(input_files) - set(ideal_files))
        missing_inputs = sorted(set(ideal_files) - set(input_files))
        raise ValueError(
            f"Pair mismatch: missing ideals={missing_ideals}, "
            f"missing inputs={missing_inputs}"
        )

    def sort_key(key: str) -> tuple[int, int]:
        first, second = key.split("-")
        return int(first), int(second)

    return [
        (key, input_files[key], ideal_files[key])
        for key in sorted(input_files, key=sort_key)
    ]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rule_for_dimensions(width: int, height: int) -> dict[str, Any]:
    path = (
        REPO_ROOT
        / "examples"
        / "rules"
        / f"benchmark_exact_{width}x{height}_72dpi_white_bg.json"
    )
    return load_json(path)


def detect_one(
    detector: MediapipeFaceDetector, image: Image.Image
) -> tuple[FaceDetection | None, str]:
    for confidence in FACE_CONFIDENCES:
        result = detector.detect_faces(
            image, {"min_detection_confidence": confidence, "max_num_faces": 10}
        )
        if len(result.detections) == 1:
            return result.detections[0], f"single@{confidence:.2f}"
        if len(result.detections) > 1:
            return None, f"multiple@{confidence:.2f}"
    return None, "none"


def refine_face(
    landmarker: MediapipeFaceLandmarker,
    image: Image.Image,
    face: FaceDetection | None,
) -> FaceDetection | None:
    if face is None:
        return None
    return landmarker.refine(image, face)


def normalise_alpha(alpha: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    result = alpha.astype(np.float32, copy=False)
    if result.size and float(np.nanmax(result)) > 1.01:
        result = result / 255.0
    return np.clip(result, 0.0, 1.0)


def _region_masks(
    shape: tuple[int, int], face: FaceDetection, crown: float, chin: float
) -> dict[str, np.ndarray[Any, Any]]:
    height, width = shape
    box = face.bounding_box
    fw = max(1.0, box.width)
    fh = max(1.0, box.height)
    yy, xx = np.mgrid[0:height, 0:width]

    def rect(
        left: float, top: float, right: float, bottom: float
    ) -> np.ndarray[Any, Any]:
        return (xx >= left) & (xx < right) & (yy >= top) & (yy < bottom)

    hair = rect(
        box.left - 0.55 * fw,
        crown - 0.04 * fh,
        box.right + 0.55 * fw,
        box.top + 0.18 * fh,
    )
    ears_left = rect(
        box.left - 0.42 * fw, box.top + 0.08 * fh, box.left + 0.16 * fw, box.bottom
    )
    ears_right = rect(
        box.right - 0.16 * fw, box.top + 0.08 * fh, box.right + 0.42 * fw, box.bottom
    )
    beard_line = rect(
        box.left + 0.05 * fw, chin - 0.18 * fh, box.right - 0.05 * fw, chin + 0.22 * fh
    )
    chin_region = rect(
        box.left + 0.20 * fw, chin - 0.10 * fh, box.right - 0.20 * fw, chin + 0.13 * fh
    )
    neck = rect(
        box.left + 0.12 * fw, chin + 0.05 * fh, box.right - 0.12 * fw, chin + 0.55 * fh
    )
    return {
        "hair": hair,
        "ears": ears_left | ears_right,
        "beard_line": beard_line,
        "chin": chin_region,
        "neck": neck,
    }


def _boundary(binary: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    result = np.zeros_like(binary, dtype=bool)
    result[1:, :] |= binary[1:, :] != binary[:-1, :]
    result[:-1, :] |= binary[:-1, :] != binary[1:, :]
    result[:, 1:] |= binary[:, 1:] != binary[:, :-1]
    result[:, :-1] |= binary[:, :-1] != binary[:, 1:]
    return result


def _dilate_once(mask: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    result = mask.copy()
    result[1:, :] |= mask[:-1, :]
    result[:-1, :] |= mask[1:, :]
    result[:, 1:] |= mask[:, :-1]
    result[:, :-1] |= mask[:, 1:]
    return result


def analyse_alpha(
    alpha: np.ndarray[Any, Any], face: FaceDetection | None
) -> dict[str, Any] | None:
    if face is None:
        return None
    alpha = normalise_alpha(alpha)
    height, width = alpha.shape
    box = face.bounding_box
    fw = max(1.0, box.width)
    x0 = max(0, int(math.floor(box.left - 0.65 * fw)))
    x1 = min(width, int(math.ceil(box.right + 0.65 * fw)))
    y1 = min(height, int(math.ceil(box.bottom)))
    head_roi = alpha[:y1, x0:x1] >= 0.5
    ys, xs = np.where(head_roi)
    if len(ys) == 0:
        return None

    crown = float(np.min(ys))
    landmarks = face.landmarks
    chin = float(box.bottom)
    if landmarks is not None and landmarks.chin is not None:
        chin = float(landmarks.chin.y)
    chin = min(float(height), max(crown + 1.0, chin))

    band_top = max(0, int(math.floor(crown)))
    band_bottom = min(height, max(band_top + 1, int(math.ceil(chin))))
    head_band = alpha[band_top:band_bottom, x0:x1] >= 0.5
    band_ys, band_xs = np.where(head_band)
    if len(band_xs) == 0:
        return None
    head_left = float(np.min(band_xs) + x0)
    head_right = float(np.max(band_xs) + x0 + 1)

    binary = alpha >= 0.5
    hard_boundary = _boundary(binary)
    boundary_band = hard_boundary
    for _ in range(3):
        boundary_band = _dilate_once(boundary_band)
    uncertain = (alpha > 0.05) & (alpha < 0.95)
    grad_y, grad_x = np.gradient(alpha)
    gradient = np.sqrt(grad_x**2 + grad_y**2)
    regions = _region_masks(alpha.shape, face, crown, chin)

    edge: dict[str, dict[str, float | bool | None]] = {}
    for name, region in regions.items():
        boundary_pixels = int(np.count_nonzero(hard_boundary & region))
        uncertain_pixels = int(np.count_nonzero(uncertain & boundary_band & region))
        uncertain_region = uncertain & region
        edge[name] = {
            "boundary_pixels": float(boundary_pixels),
            "soft_width_px": (
                float(uncertain_pixels / boundary_pixels)
                if boundary_pixels > 0
                else None
            ),
            "mean_alpha_gradient": (
                float(np.mean(gradient[uncertain_region]))
                if np.any(uncertain_region)
                else None
            ),
            "touches_frame": bool(
                np.any(binary[0, :] & region[0, :])
                or np.any(binary[-1, :] & region[-1, :])
                or np.any(binary[:, 0] & region[:, 0])
                or np.any(binary[:, -1] & region[:, -1])
            ),
        }

    return {
        "width": width,
        "height": height,
        "head_left_px": head_left,
        "head_right_px": head_right,
        "crown_y_px": crown,
        "chin_y_px": chin,
        "negative_space_left": head_left / width,
        "negative_space_right": (width - head_right) / width,
        "headspace_above_hair": crown / height,
        "space_below_chin": (height - chin) / height,
        "head_height_ratio": (chin - crown) / height,
        "head_width_ratio": (head_right - head_left) / width,
        "edge": edge,
    }


def visible_foreground_proxy(image: Image.Image) -> np.ndarray[Any, Any]:
    """Return a common visible-edge signal for engine and ideal outputs.

    Both result families have a white target background.  Distance from white
    therefore measures the edge that a reviewer actually sees, including
    residual halos and hard cut-outs.  Scaling the distance before clipping
    keeps antialiased pale skin/hair boundary pixels in the soft range.  This
    is deliberately used for *both* sides of the comparison; the ideal image
    is never passed through the engine's own model and treated as truth.
    """
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    distance = np.max(1.0 - rgb, axis=2)
    return np.clip(distance / 0.25, 0.0, 1.0).astype(np.float32)


def equivalent_crop_size(
    source_face: FaceDetection | None,
    ideal_face: FaceDetection | None,
    ideal_size: tuple[int, int],
) -> tuple[float | None, float | None]:
    if source_face is None or ideal_face is None:
        return None, None
    src = source_face.bounding_box
    dst = ideal_face.bounding_box
    scale_samples = [dst.width / max(1.0, src.width), dst.height / max(1.0, src.height)]
    if (
        source_face.landmarks is not None
        and ideal_face.landmarks is not None
        and source_face.landmarks.left_eye is not None
        and source_face.landmarks.right_eye is not None
        and ideal_face.landmarks.left_eye is not None
        and ideal_face.landmarks.right_eye is not None
    ):
        src_eye = math.dist(
            (source_face.landmarks.left_eye.x, source_face.landmarks.left_eye.y),
            (source_face.landmarks.right_eye.x, source_face.landmarks.right_eye.y),
        )
        dst_eye = math.dist(
            (ideal_face.landmarks.left_eye.x, ideal_face.landmarks.left_eye.y),
            (ideal_face.landmarks.right_eye.x, ideal_face.landmarks.right_eye.y),
        )
        if src_eye > 1.0:
            scale_samples.append(dst_eye / src_eye)
    scale = statistics.median(scale_samples)
    if scale <= 0:
        return None, None
    return ideal_size[0] / scale, ideal_size[1] / scale


def deltas(
    engine: dict[str, Any] | None, ideal: dict[str, Any] | None
) -> dict[str, Any]:
    if engine is None or ideal is None:
        return {}
    result: dict[str, Any] = {}
    for key in (
        "negative_space_left",
        "negative_space_right",
        "headspace_above_hair",
        "space_below_chin",
        "head_height_ratio",
        "head_width_ratio",
    ):
        result[key] = engine[key] - ideal[key]
    result["margin_mae"] = statistics.mean(
        abs(result[key])
        for key in (
            "negative_space_left",
            "negative_space_right",
            "headspace_above_hair",
            "space_below_chin",
        )
    )
    result["edge"] = {}
    for region in EDGE_REGIONS:
        engine_edge = engine["edge"][region]
        ideal_edge = ideal["edge"][region]
        soft_engine = engine_edge["soft_width_px"]
        soft_ideal = ideal_edge["soft_width_px"]
        grad_engine = engine_edge["mean_alpha_gradient"]
        grad_ideal = ideal_edge["mean_alpha_gradient"]
        result["edge"][region] = {
            "soft_width_px": (
                soft_engine - soft_ideal
                if soft_engine is not None and soft_ideal is not None
                else None
            ),
            "mean_alpha_gradient": (
                grad_engine - grad_ideal
                if grad_engine is not None and grad_ideal is not None
                else None
            ),
            "touches_frame_mismatch": engine_edge["touches_frame"]
            != ideal_edge["touches_frame"],
        }
    return result


def mean(values: list[float]) -> float | None:
    return float(statistics.mean(values)) if values else None


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    produced = [row for row in rows if row["produced_output"]]
    measured = [row for row in produced if row.get("engine") and row.get("ideal")]
    no_output = [row["key"] for row in rows if not row["produced_output"]]
    floor_met = [
        row for row in measured if float(row["engine"]["head_height_ratio"]) >= 0.75
    ]
    margin_keys = (
        "negative_space_left",
        "negative_space_right",
        "headspace_above_hair",
        "space_below_chin",
    )
    aggregate_margin_delta = {
        key: mean([abs(float(row["delta"][key])) for row in measured])
        for key in margin_keys
    }
    edge_delta: dict[str, Any] = {}
    for region in EDGE_REGIONS:
        soft_values = [
            abs(float(row["delta"]["edge"][region]["soft_width_px"]))
            for row in measured
            if row["delta"]["edge"][region]["soft_width_px"] is not None
        ]
        gradient_values = [
            abs(float(row["delta"]["edge"][region]["mean_alpha_gradient"]))
            for row in measured
            if row["delta"]["edge"][region]["mean_alpha_gradient"] is not None
        ]
        edge_delta[region] = {
            "soft_width_px_mae": mean(soft_values),
            "alpha_gradient_mae": mean(gradient_values),
            "frame_touch_mismatches": sum(
                bool(row["delta"]["edge"][region]["touches_frame_mismatch"])
                for row in measured
            ),
        }
    crop_w = [
        abs(float(row["crop"]["engine_width"] - row["crop"]["ideal_equivalent_width"]))
        / max(1.0, float(row["crop"]["ideal_equivalent_width"]))
        for row in measured
        if row["crop"]["ideal_equivalent_width"] is not None
    ]
    crop_h = [
        abs(
            float(row["crop"]["engine_height"] - row["crop"]["ideal_equivalent_height"])
        )
        / max(1.0, float(row["crop"]["ideal_equivalent_height"]))
        for row in measured
        if row["crop"]["ideal_equivalent_height"] is not None
    ]
    return {
        "total": len(rows),
        "produced_output": len(produced),
        "no_output_count": len(no_output),
        "no_output_keys": no_output,
        "measured_pairs": len(measured),
        "meet_75_percent_floor": len(floor_met),
        "margin_absolute_error_mean": aggregate_margin_delta,
        "margin_mae_mean": mean(
            [float(row["delta"]["margin_mae"]) for row in measured]
        ),
        "crop_relative_error_mean": {"width": mean(crop_w), "height": mean(crop_h)},
        "edge_absolute_error": edge_delta,
    }


def flatten_row(row: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {
        "key": row["key"],
        "produced_output": row["produced_output"],
        "is_valid": row["is_valid"],
        "failure_stages": "|".join(row["failure_stages"]),
        "issue_codes": "|".join(row["issue_codes"]),
    }
    for key in (
        "engine_width",
        "engine_height",
        "ideal_equivalent_width",
        "ideal_equivalent_height",
    ):
        flat[f"crop_{key}"] = row["crop"].get(key)
    for prefix in ("engine", "ideal"):
        metrics = row.get(prefix) or {}
        for key in (
            "negative_space_left",
            "negative_space_right",
            "headspace_above_hair",
            "space_below_chin",
            "head_height_ratio",
            "head_width_ratio",
        ):
            flat[f"{prefix}_{key}"] = metrics.get(key)
    delta = row.get("delta") or {}
    flat["margin_mae"] = delta.get("margin_mae")
    for key in (
        "negative_space_left",
        "negative_space_right",
        "headspace_above_hair",
        "space_below_chin",
        "head_height_ratio",
        "head_width_ratio",
    ):
        flat[f"delta_{key}"] = delta.get(key)
    for region in EDGE_REGIONS:
        for prefix in ("engine", "ideal"):
            edge = ((row.get(prefix) or {}).get("edge") or {}).get(region, {})
            flat[f"{prefix}_{region}_soft_width_px"] = edge.get("soft_width_px")
            flat[f"{prefix}_{region}_alpha_gradient"] = edge.get("mean_alpha_gradient")
            flat[f"{prefix}_{region}_touches_frame"] = edge.get("touches_frame")
    return flat


def main() -> int:
    args = parse_args()
    print("[setup] phase=torch-thread-limit", flush=True)
    # PyTorch can expose the machine's full logical-CPU count here (114 worker
    # threads on the benchmark workstation), which oversubscribes this model so
    # severely that a 512px inference takes minutes.  Keep the benchmark batch
    # bounded and repeatable; this affects latency only, not model output.
    torch.set_num_threads(min(8, max(1, torch.get_num_threads())))
    print("[setup] phase=discover-pairs", flush=True)
    pairs = discover_pairs(args.inputs, args.ideals)
    if args.limit is not None:
        pairs = pairs[: args.limit]
    if args.limit is None and len(pairs) != 60:
        raise ValueError(f"Expected 60 matched photos, found {len(pairs)}")

    print(f"[00/{len(pairs):02d}] phase=model-manifests", flush=True)
    face_manifest = load_json(REPO_ROOT / "model-manifests" / "face-detector.json")
    segmenter_manifest = load_json(
        REPO_ROOT / "model-manifests" / "subject-segmenter.json"
    )
    face_path = REPO_ROOT / str(face_manifest["local_model_path_default"])
    segmenter_path = REPO_ROOT / str(segmenter_manifest["local_model_path_default"])
    face_sha = str(face_manifest["sha256"])
    segmenter_sha = str(segmenter_manifest["sha256"])
    birefnet_dir, _weights_name, birefnet_sha, _inference_size = load_birefnet_defaults(
        REPO_ROOT
    )
    landmarker_path, landmarker_sha = load_landmarker_defaults(REPO_ROOT)

    print(f"[00/{len(pairs):02d}] phase=pipeline-constructor", flush=True)
    pipeline = RuleOrchestratedPipeline(
        face_model_path=face_path,
        segmenter_model_path=segmenter_path,
        face_expected_sha256=face_sha,
        segmenter_expected_sha256=segmenter_sha,
        matting_backend="birefnet",
        birefnet_model_dir=birefnet_dir,
        birefnet_expected_sha256=birefnet_sha,
    )
    print(f"[00/{len(pairs):02d}] phase=face-detector-constructor", flush=True)
    detector = MediapipeFaceDetector(face_path, face_sha)
    print(f"[00/{len(pairs):02d}] phase=landmarker-constructor", flush=True)
    landmarker = MediapipeFaceLandmarker(landmarker_path, landmarker_sha)
    print(f"[00/{len(pairs):02d}] phase=ready", flush=True)
    ideal_cache: dict[str, Any] = {}
    if args.ideal_cache is not None and args.ideal_cache.exists():
        ideal_cache = load_json(args.ideal_cache)

    rows: list[dict[str, Any]] = []
    for index, (key, input_path, ideal_path) in enumerate(pairs, start=1):
        photo_started = time.perf_counter()
        print(
            f"[{index:02d}/{len(pairs):02d}] {key} phase=reference-analysis",
            flush=True,
        )
        width, height = target_dimensions(input_path)
        source_image = Image.open(input_path).convert("RGB")
        source_face_raw, source_detection = detect_one(detector, source_image)
        source_face = refine_face(landmarker, source_image, source_face_raw)

        cached = ideal_cache.get(key)
        if cached is None:
            ideal_image = Image.open(ideal_path).convert("RGB")
            ideal_face_raw, ideal_detection = detect_one(detector, ideal_image)
            ideal_face = refine_face(landmarker, ideal_image, ideal_face_raw)
            ideal_metrics = analyse_alpha(
                visible_foreground_proxy(ideal_image), ideal_face
            )
            equiv_w, equiv_h = equivalent_crop_size(
                source_face, ideal_face, ideal_image.size
            )
            cached = {
                "metrics": ideal_metrics,
                "detection": ideal_detection,
                "equivalent_crop_width": equiv_w,
                "equivalent_crop_height": equiv_h,
            }
            ideal_cache[key] = cached

        pipeline_started = time.perf_counter()
        print(
            f"[{index:02d}/{len(pairs):02d}] {key} phase=engine",
            flush=True,
        )
        result = pipeline.process_rule(
            input_path.read_bytes(),
            rule_for_dimensions(width, height),
            RulePipelineConfig(
                allow_padding=True,
                allow_invalid_output=True,
                allow_quality_below_minimum=True,
                allow_oversize_output=True,
                quality_mode="high",
            ),
        )
        report = result.portrait_quality_report or {}
        crop = report.get("crop_box")
        produced = bool(
            result.encoded_bytes and crop and result.refined_alpha_mask is not None
        )
        engine_metrics = None
        if produced:
            engine_image = Image.open(io.BytesIO(result.encoded_bytes)).convert("RGB")
            engine_face_raw, engine_detection = detect_one(detector, engine_image)
            engine_face = refine_face(landmarker, engine_image, engine_face_raw)
            engine_metrics = analyse_alpha(
                visible_foreground_proxy(engine_image), engine_face
            )
        else:
            engine_detection = "not-produced"

        failed_stages = [
            f"{stage.stage.value}:{','.join(stage.issue_codes)}"
            for stage in result.stage_reports
            if stage.status.value == "failed"
        ]
        stage_durations = {
            stage.stage.value: float(stage.duration_ms)
            for stage in result.stage_reports
        }
        slow_stages = sorted(
            stage_durations.items(), key=lambda item: item[1], reverse=True
        )[:4]
        row = {
            "key": key,
            "source_filename": input_path.name,
            "ideal_filename": ideal_path.name,
            "target_width": width,
            "target_height": height,
            "produced_output": produced,
            "is_valid": result.is_valid,
            "source_detection": source_detection,
            "ideal_detection": cached["detection"],
            "engine_detection": engine_detection,
            "failure_stages": failed_stages,
            "stage_durations_ms": stage_durations,
            "issue_codes": [code.value for code in result.issue_codes],
            "crop": {
                "engine_width": (float(crop["right"] - crop["left"]) if crop else None),
                "engine_height": (
                    float(crop["bottom"] - crop["top"]) if crop else None
                ),
                "ideal_equivalent_width": cached["equivalent_crop_width"],
                "ideal_equivalent_height": cached["equivalent_crop_height"],
            },
            "engine": engine_metrics,
            "ideal": cached["metrics"],
            "delta": deltas(engine_metrics, cached["metrics"]),
        }
        rows.append(row)
        print(
            f"[{index:02d}/{len(pairs):02d}] {key} "
            f"output={int(produced)} valid={int(result.is_valid)} "
            f"slow={slow_stages} "
            f"engine_s={time.perf_counter() - pipeline_started:.1f} "
            f"total_s={time.perf_counter() - photo_started:.1f}",
            flush=True,
        )

    payload = {"aggregate": aggregate(rows), "photos": rows}
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.output_csv is not None:
        flat_rows = [flatten_row(row) for row in rows]
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(flat_rows[0]))
            writer.writeheader()
            writer.writerows(flat_rows)
    if args.ideal_cache is not None:
        args.ideal_cache.parent.mkdir(parents=True, exist_ok=True)
        args.ideal_cache.write_text(json.dumps(ideal_cache, indent=2), encoding="utf-8")

    print(json.dumps(payload["aggregate"], indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
