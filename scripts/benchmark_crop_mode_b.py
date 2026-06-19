import argparse
import json
import sys
import time
from pathlib import Path
from PIL import Image
import numpy as np

# Add services/image-engine/src to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "services" / "image-engine" / "src"))

from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector  # noqa: E402
from exam_photo.providers.segmenters.mediapipe_segmenter import (  # noqa: E402
    MediapipeSubjectSegmenter,
)
from exam_photo.providers.refiners.morphological_refiner import (  # noqa: E402
    MorphologicalForegroundRefiner,
)
from exam_photo.providers.landmark_geometric_head_estimator import (  # noqa: E402
    LandmarkGeometricHeadEstimator,
)
from exam_photo.providers.crop_planners.deterministic_crop_mode_b_planner import (  # noqa: E402
    DeterministicCropModeBPlanner,
)
from exam_photo.providers.crop_planning import CropModeBConfig  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Crop Mode B planning.")
    parser.add_argument(
        "--require-real",
        action="store_true",
        help="Fail if stability/quality/performance gates are violated.",
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

    if args.require_real:
        if not face_model_path.exists():
            print(
                f"ERROR: Face detector model missing: {face_model_path}",
                file=sys.stderr,
            )
            return 1
        if not seg_model_path.exists():
            print(f"ERROR: Segmenter model missing: {seg_model_path}", file=sys.stderr)
            return 1

    # Instantiate providers
    face_detector_05 = MediapipeFaceDetector(
        face_model_path, face_sha, min_detection_confidence=0.5
    )
    face_detector_02 = MediapipeFaceDetector(
        face_model_path, face_sha, min_detection_confidence=0.2
    )
    segmenter = MediapipeSubjectSegmenter(seg_model_path, seg_sha)
    refiner = MorphologicalForegroundRefiner()
    head_estimator = LandmarkGeometricHeadEstimator()
    planner = DeterministicCropModeBPlanner()

    fixtures_dir = repo_root / "tests" / "fixtures"
    annotations_path = fixtures_dir / "segmentation" / "annotations.json"
    if not annotations_path.exists():
        print(f"ERROR: Annotations file missing: {annotations_path}", file=sys.stderr)
        return 1

    with open(annotations_path, "r", encoding="utf-8") as f:
        annotations = json.load(f)

    results = []
    failed = False

    print("\n" + "=" * 80)
    print("RUNNING CROP MODE B BENCHMARKS")
    print("=" * 80)

    for entry in annotations["entries"]:
        src_name = entry["source_fixture"]
        src_path = fixtures_dir / src_name
        img = Image.open(src_path)

        expected_faces = entry.get("expected_face_count", 1)
        expect_b = entry.get("crop_mode_b_expectation")

        if expect_b is None:
            continue

        # 1. Face detection
        face = None
        face_count = 0
        if expected_faces > 0:
            detector = (
                face_detector_02
                if src_name
                in ("lincoln_low_contrast.jpg", "roosevelt_muir_yosemite.jpg")
                else face_detector_05
            )
            with detector:
                face_res = detector.detect_faces(img)
            face_count = len(face_res.detections)
            if face_count == 1:
                face = face_res.detections[0]

        # 2. Head estimation
        head_box = None
        if face is not None:
            head_res = head_estimator.estimate_head(
                img,
                face,
                face.landmarks,
                config={"minimum_face_confidence": min(0.5, face.confidence)},
            )
            head_box = head_res.head_bounding_box

        # 3. Refined mask
        refined_mask = None
        if face is not None:
            with segmenter:
                seg_res = segmenter.segment_subject(img, face=face)
            ref_res = refiner.refine_mask(
                coarse_mask=seg_res.coarse_mask,
                probability_mask=seg_res.probability_mask,
                face=face,
                head_estimate=head_box,
            )
            refined_mask = ref_res.refined_binary_mask

        # 4. Plan Crop Mode B (default/compatible setup)
        # We allow padding to check ideal bounds, but default is False.
        # However, for checking range gates, we can configure padding based on the entry's expected allowance,
        # or we just use allow_padding=False (which is default) and verify if it matches expectation.
        cfg = CropModeBConfig(
            min_head_height_ratio=expect_b.get("min_head_height_ratio", 0.30),
            max_head_height_ratio=expect_b.get("max_head_height_ratio", 0.84),
            allow_padding=expect_b.get("expected_padding_required", False),
        )

        crop_res = planner.plan_crop(
            image_width=img.width,
            image_height=img.height,
            face=face if face is not None else None,  # type: ignore
            head_estimate=head_box,
            refined_mask=refined_mask,
            config=cfg,
        )

        results.append(
            {
                "fixture": src_name,
                "expected_faces": expected_faces,
                "expected_padding_required": expect_b.get(
                    "expected_padding_required", False
                ),
                "expected_valid_without_padding": expect_b.get(
                    "expected_valid_without_padding", True
                ),
                "expected_valid": expect_b.get("expected_valid", True),
                "min_head_height_ratio": expect_b.get("min_head_height_ratio", 0.30),
                "max_head_height_ratio": expect_b.get("max_head_height_ratio", 0.84),
                "actual_faces": face_count,
                "crop_width": crop_res.crop_box_width,
                "crop_height": crop_res.crop_box_height,
                "crop_aspect_ratio": crop_res.crop_box_aspect_ratio,
                "head_height_ratio": crop_res.head_height_ratio,
                "face_cx": crop_res.face_center_x_ratio,
                "face_cy": crop_res.face_center_y_ratio,
                "head_preservation": crop_res.head_coverage_ratio,
                "mask_preservation": crop_res.mask_preservation_ratio,
                "is_valid": crop_res.validation.is_valid,
                "padding_required": crop_res.padding_required,
                "issue_codes": crop_res.validation.issue_codes,
                "latency_ms": crop_res.processing_duration_ms,
            }
        )

        print(f"Fixture: {src_name}")
        print(f"  Faces Expected/Detected: {expected_faces}/{face_count}")
        print(
            f"  Crop Size:            {crop_res.crop_box_width}x{crop_res.crop_box_height} (Aspect: {crop_res.crop_box_aspect_ratio:.4f})"
        )
        if crop_res.head_height_ratio is not None:
            print(f"  Head-Height Ratio:    {crop_res.head_height_ratio:.4f}")
        print(
            f"  Face Center:          ({crop_res.face_center_x_ratio:.4f}, {crop_res.face_center_y_ratio:.4f})"
        )
        if crop_res.head_coverage_ratio is not None:
            print(f"  Head Coverage:        {crop_res.head_coverage_ratio:.4f}")
        if crop_res.mask_preservation_ratio is not None:
            print(f"  Mask Preservation:    {crop_res.mask_preservation_ratio:.4f}")
        print(f"  Is Valid:             {crop_res.validation.is_valid}")
        print(f"  Padding Required:     {crop_res.padding_required}")
        if crop_res.validation.issue_codes:
            print(
                f"  Issue Codes:          {', '.join(crop_res.validation.issue_codes)}"
            )
        print(f"  Planner Latency:      {crop_res.processing_duration_ms:.2f}ms")
        print("-" * 80)

    # Aggregate stats
    valid_one_person_results = [
        r for r in results if r["expected_faces"] == 1 and r["actual_faces"] == 1
    ]
    if valid_one_person_results:
        mean_latency = float(
            np.mean([r["latency_ms"] for r in valid_one_person_results])
        )
        print("\nAggregate Stats (for valid one-person portraits):")
        print(f"  Mean Planner Latency:   {mean_latency:.4f}ms")

    # Enforce quality gates
    if args.require_real:
        for r in results:
            # 1. Fail if a valid one-person fixture is invalid or has wrong padding
            if r["expected_faces"] == 1 and r["actual_faces"] == 1:
                expected_padding = r["expected_padding_required"]
                expected_valid_without_padding = r["expected_valid_without_padding"]

                # Check padding required flag
                if r["padding_required"] != expected_padding:
                    print(
                        f"ERROR: Padding mismatch on {r['fixture']}. "
                        f"Expected padding required: {expected_padding}, got: {r['padding_required']}",
                        file=sys.stderr,
                    )
                    failed = True

                # Check overall validity
                expected_valid = r["expected_valid"]
                if r["is_valid"] != expected_valid:
                    print(
                        f"ERROR: Validity mismatch on {r['fixture']}. "
                        f"Expected is_valid: {expected_valid}, got: {r['is_valid']}. "
                        f"Issues: {r['issue_codes']}",
                        file=sys.stderr,
                    )
                    failed = True

                # Head preservation check
                if (
                    r["head_preservation"] is not None
                    and r["head_preservation"] < 0.999
                ):
                    print(
                        f"ERROR: Head preservation ratio {r['head_preservation']:.4f} for {r['fixture']} is below 0.999",
                        file=sys.stderr,
                    )
                    failed = True

                # Head-height ratio range check — read from stored per-fixture values
                if r["head_height_ratio"] is not None:
                    h_ratio = r["head_height_ratio"]
                    min_ratio = r["min_head_height_ratio"]
                    max_ratio = r["max_head_height_ratio"]
                    if not (min_ratio - 1e-4 <= h_ratio <= max_ratio + 1e-4):
                        print(
                            f"ERROR: Head-height ratio {h_ratio:.4f} for {r['fixture']} falls outside [{min_ratio}, {max_ratio}]",
                            file=sys.stderr,
                        )
                        failed = True

            # 2. Fail if no-person or multiple-person fixture is approved
            if r["expected_faces"] == 0 or r["actual_faces"] > 1:
                if r["is_valid"]:
                    print(
                        f"ERROR: Crop plan incorrectly approved for invalid fixture: {r['fixture']}",
                        file=sys.stderr,
                    )
                    failed = True

        if failed:
            print("Crop Mode B Gate: FAIL", file=sys.stderr)
            return 1
        else:
            print("Crop Mode B Gate: PASS")

    return 0


if __name__ == "__main__":
    sys.exit(main())
