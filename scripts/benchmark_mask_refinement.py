import argparse
import json
import os
import sys
import time
from pathlib import Path
import numpy as np
from PIL import Image

# Add services/image-engine/src to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "services" / "image-engine" / "src"))

from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector
from exam_photo.providers.segmenters.mediapipe_segmenter import MediapipeSubjectSegmenter
from exam_photo.providers.refiners.morphological_refiner import MorphologicalForegroundRefiner
from exam_photo.providers.foreground_refinement import RefinementConfig


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark foreground mask refinement.")
    parser.add_argument(
        "--require-real",
        action="store_true",
        help="Fail if stability IoU < 0.90 or quality regresses.",
    )
    args = parser.parse_args()

    face_model_path = repo_root / "model-assets" / "blaze_face_short_range.tflite"
    face_manifest = repo_root / "model-manifests" / "face-detector.json"
    face_sha = ""
    if face_manifest.exists():
        with open(face_manifest, "r", encoding="utf-8") as f:
            face_sha = json.load(f).get("sha256", "")

    seg_model_path = repo_root / "model-assets" / "selfie_segmentation.tflite"
    seg_manifest = repo_root / "model-manifests" / "subject-segmenter.json"
    seg_sha = ""
    if seg_manifest.exists():
        with open(seg_manifest, "r", encoding="utf-8") as f:
            m = json.load(f)
            variant = m.get("variants", {}).get("selfie_bin_general", {})
            seg_sha = variant.get("sha256", "")

    # Instantiate detectors
    face_detector_05 = MediapipeFaceDetector(face_model_path, face_sha, min_detection_confidence=0.5)
    face_detector_02 = MediapipeFaceDetector(face_model_path, face_sha, min_detection_confidence=0.2)
    segmenter = MediapipeSubjectSegmenter(seg_model_path, seg_sha)
    refiner = MorphologicalForegroundRefiner()

    fixtures_dir = repo_root / "tests" / "fixtures"
    with open(fixtures_dir / "segmentation" / "annotations.json", "r", encoding="utf-8") as f:
        annotations = json.load(f)

    results = []
    failed = False

    if args.require_real:
        required_refs = [
            "segmentation/reference_masks/reference-einstein-mask.png",
            "segmentation/reference_masks/reference-freud-mask.png",
        ]
        for ref_file in required_refs:
            if not (fixtures_dir / ref_file).exists():
                print(f"ERROR: Required reference mask is missing from disk: {ref_file}", file=sys.stderr)
                failed = True

    for entry in annotations["entries"]:
        src_name = entry["source_fixture"]

        src_path = fixtures_dir / src_name
        img = Image.open(src_path)

        # 1. Detect faces
        expected_faces = entry.get("expected_face_count", 1)
        faces = None
        if expected_faces > 0:
            detector = face_detector_02 if src_name in ("lincoln_low_contrast.jpg", "roosevelt_muir_yosemite.jpg") else face_detector_05
            with detector:
                face_res = detector.detect_faces(img)
            assert len(face_res.detections) == expected_faces, f"Expected {expected_faces} faces, got {len(face_res.detections)}"
            faces = face_res.detections

        # 2. Run segmenter
        with segmenter:
            seg_res = segmenter.segment_subject(img, face=faces)

        # 3. Run Refinement
        ref_res = refiner.refine_mask(
            coarse_mask=seg_res.coarse_mask,
            probability_mask=seg_res.probability_mask,
            face=faces
        )

        # 4. Coverage and IoU calculations
        coarse_arr = np.array(seg_res.coarse_mask) > 127
        refined_arr = np.array(ref_res.refined_binary_mask) > 127

        coarse_cov = float(np.mean(coarse_arr))
        refined_cov = float(np.mean(refined_arr))
        delta_cov = refined_cov - coarse_cov

        # Stability IoU (coarse vs refined)
        intersect_stable = np.logical_and(coarse_arr, refined_arr).sum()
        union_stable = np.logical_or(coarse_arr, refined_arr).sum()
        stability_iou = float(intersect_stable / union_stable) if union_stable > 0 else 1.0

        # Quality IoU (refined vs reference, if reference exists)
        quality_iou = None
        coarse_ref_iou = None

        ref_mask_filename = None
        if src_name == "single_face_frontal.jpg":
            ref_mask_filename = "segmentation/reference_masks/reference-einstein-mask.png"
        elif src_name == "freud_spectacles_beard.jpg":
            ref_mask_filename = "segmentation/reference_masks/reference-freud-mask.png"

        if ref_mask_filename:
            ref_path = fixtures_dir / ref_mask_filename
            if ref_path.exists():
                ref_arr = np.array(Image.open(ref_path).convert("L")) > 127
                # Coarse vs Reference
                intersect_coarse_ref = np.logical_and(coarse_arr, ref_arr).sum()
                union_coarse_ref = np.logical_or(coarse_arr, ref_arr).sum()
                coarse_ref_iou = float(intersect_coarse_ref / union_coarse_ref) if union_coarse_ref > 0 else 1.0

                # Refined vs Reference
                intersect_ref_ref = np.logical_and(refined_arr, ref_arr).sum()
                union_ref_ref = np.logical_or(refined_arr, ref_arr).sum()
                quality_iou = float(intersect_ref_ref / union_ref_ref) if union_ref_ref > 0 else 1.0

        results.append({
            "fixture": src_name,
            "coarse_cov": coarse_cov,
            "refined_cov": refined_cov,
            "delta_cov": delta_cov,
            "stability_iou": stability_iou,
            "coarse_ref_iou": coarse_ref_iou,
            "quality_iou": quality_iou,
            "radius": ref_res.effective_radius_px,
            "latency_ms": ref_res.refinement_duration_ms
        })

        # Failure checks
        if args.require_real:
            if stability_iou < 0.90:
                print(f"ERROR: Stability IoU for {src_name} ({stability_iou:.4f}) is below 0.90", file=sys.stderr)
                failed = True
            if quality_iou is not None:
                if quality_iou < 0.98:
                    print(
                        f"ERROR: Quality IoU for {src_name} is below 0.98: {quality_iou:.4f}",
                        file=sys.stderr,
                    )
                    failed = True

    print("\n" + "=" * 80)
    print("MASK REFINEMENT BENCHMARK REPORT")
    print("=" * 80)
    for r in results:
        print(f"Fixture: {r['fixture']}")
        print(f"  Coarse Coverage:   {r['coarse_cov']:.4f}")
        print(f"  Refined Coverage:  {r['refined_cov']:.4f} (Delta: {r['delta_cov']:.4f})")
        print(f"  Stability IoU:     {r['stability_iou']:.4f}")
        if r['quality_iou'] is not None:
            print(f"  Coarse vs Ref IoU: {r['coarse_ref_iou']:.4f}")
            print(f"  Quality IoU:       {r['quality_iou']:.4f} (Delta: {r['quality_iou'] - r['coarse_ref_iou']:.4f})")
        print(f"  Effective Radius:  {r['radius']}px")
        print(f"  Refinement Time:   {r['latency_ms']:.2f}ms")
        print("-" * 80)

    # Aggregate
    mean_stability = float(np.mean([r['stability_iou'] for r in results]))
    mean_latency = float(np.mean([r['latency_ms'] for r in results]))
    print(f"Aggregate Stats:")
    print(f"  Mean Stability IoU: {mean_stability:.4f}")
    print(f"  Mean Latency:       {mean_latency:.2f}ms")

    qualities = [r['quality_iou'] for r in results if r['quality_iou'] is not None]
    if qualities:
        mean_quality = float(np.mean(qualities))
        print(f"  Mean Quality IoU:   {mean_quality:.4f}")

    if failed:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
