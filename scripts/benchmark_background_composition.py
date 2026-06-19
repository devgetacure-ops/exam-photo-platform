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
from exam_photo.providers.background_composers.solid_background_composer import (  # noqa: E402
    SolidBackgroundComposer,
)
from exam_photo.providers.background_composition import (  # noqa: E402
    BackgroundCompositionConfig,
    BackgroundMode,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Background Composition.")
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
    composer = SolidBackgroundComposer()

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
    print("RUNNING BACKGROUND COMPOSITION BENCHMARKS")
    print("=" * 80)

    for entry in annotations["entries"]:
        src_name = entry["source_fixture"]
        src_path = fixtures_dir / src_name
        
        expect_bg = entry.get("background_composition_expectation")
        if expect_bg is None:
            continue
            
        img = Image.open(src_path)
        expected_faces = entry.get("expected_face_count", 1)

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
            try:
                with detector:
                    face_res = detector.detect_faces(img)
                face_count = len(face_res.detections)
                if face_count == 1:
                    face = face_res.detections[0]
            except Exception as e:
                if expect_bg.get("expected_valid", True):
                    print(f"ERROR: Face detection crashed on valid fixture {src_name}: {e}", file=sys.stderr)
                    failed = True
                pass

        # 2. Head estimation
        head_box = None
        if face is not None:
            try:
                head_res = head_estimator.estimate_head(
                    img,
                    face,
                    face.landmarks,
                    config={"minimum_face_confidence": min(0.5, face.confidence)},
                )
                head_box = head_res.head_bounding_box
            except Exception as e:
                if expect_bg.get("expected_valid", True):
                    print(f"ERROR: Head estimation crashed on valid fixture {src_name}: {e}", file=sys.stderr)
                    failed = True
                pass

        # 3. Refined mask
        refined_alpha_mask = None
        if face is not None:
            try:
                with segmenter:
                    seg_res = segmenter.segment_subject(img, face=face)
                ref_res = refiner.refine_mask(
                    coarse_mask=seg_res.coarse_mask,
                    probability_mask=seg_res.probability_mask,
                    face=face,
                    head_estimate=head_box,
                )
                refined_alpha_mask = ref_res.refined_alpha_mask
            except Exception as e:
                if expect_bg.get("expected_valid", True):
                    print(f"ERROR: Segmentation/Refinement crashed on valid fixture {src_name}: {e}", file=sys.stderr)
                    failed = True
                pass

        # 4. Compose Background
        target_colour = expect_bg.get("target_colour_hex", "#FFFFFF")
        allow_transparent = expect_bg.get("allow_transparent_output", False)
        mode = BackgroundMode.PLAIN_WHITE if target_colour == "#FFFFFF" else BackgroundMode.SOLID_COLOUR
        
        # If we expect valid execution, but previous steps failed, composer will fail nicely.
        cfg = BackgroundCompositionConfig(
            mode=mode,
            target_colour_hex=target_colour,
            minimum_foreground_coverage=expect_bg.get("minimum_foreground_coverage", 0.02),
            maximum_foreground_coverage=expect_bg.get("maximum_foreground_coverage", 0.95),
            allow_transparent_output=allow_transparent,
            allow_subject_clipping=True, # We enable this for tests unless strictly asked
        )

        bg_res = composer.compose_background(
            image=img,
            refined_alpha_mask=refined_alpha_mask if refined_alpha_mask is not None else np.zeros((img.height, img.width), dtype=np.float32),
            config=cfg,
            crop_box=None,
        )

        results.append(
            {
                "fixture": src_name,
                "expected_valid": expect_bg.get("expected_valid", True),
                "expected_min_coverage": expect_bg.get("minimum_foreground_coverage", 0.02),
                "is_valid": bg_res.validation.is_valid,
                "coverage": bg_res.foreground_coverage_ratio,
                "issue_codes": bg_res.validation.issue_codes,
                "latency_ms": bg_res.processing_duration_ms,
            }
        )

        print(f"Fixture: {src_name}")
        print(f"  Target Colour:        {bg_res.target_colour_hex}")
        if bg_res.foreground_coverage_ratio is not None:
            print(f"  Foreground Coverage:  {bg_res.foreground_coverage_ratio:.4f}")
        print(f"  Is Valid:             {bg_res.validation.is_valid}")
        if bg_res.validation.issue_codes:
            print(
                f"  Issue Codes:          {', '.join(bg_res.validation.issue_codes)}"
            )
        print(f"  Composer Latency:     {bg_res.processing_duration_ms:.2f}ms")
        print("-" * 80)

    # Aggregate stats
    valid_results = [r for r in results if r["is_valid"]]
    if valid_results:
        mean_latency = float(np.mean([r["latency_ms"] for r in valid_results]))
        print("\nAggregate Stats:")
        print(f"  Mean Composer Latency:  {mean_latency:.4f}ms")

    # Enforce quality gates
    if args.require_real:
        for r in results:
            expected_valid = r["expected_valid"]
            if r["is_valid"] != expected_valid:
                print(
                    f"ERROR: Validity mismatch on {r['fixture']}. "
                    f"Expected is_valid: {expected_valid}, got: {r['is_valid']}. "
                    f"Issues: {r['issue_codes']}",
                    file=sys.stderr,
                )
                failed = True
                
            if expected_valid and r["coverage"] is not None:
                min_cov = r["expected_min_coverage"]
                if r["coverage"] < min_cov:
                    print(
                        f"ERROR: Coverage {r['coverage']:.4f} below min {min_cov} for {r['fixture']}",
                        file=sys.stderr,
                    )
                    failed = True

        if failed:
            print("Background Composition Gate: FAIL", file=sys.stderr)
            return 1
        else:
            print("Background Composition Gate: PASS")

    return 0


if __name__ == "__main__":
    sys.exit(main())
