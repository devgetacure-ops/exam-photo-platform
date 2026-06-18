import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np
from PIL import Image

from exam_photo.input.errors import ImageInspectionError
from exam_photo.input.limits import InputLimits
from exam_photo.input.normalization import normalize_image_input
from exam_photo.providers.landmark_geometric_head_estimator import (
    LandmarkGeometricHeadEstimator,
)
from exam_photo.providers.subject_segmentation import (
    SegmentationConfig,
)
from exam_photo.rule_validation import validate_exam_rule

logger = logging.getLogger("exam_photo")
if not logger.handlers:
    logger.addHandler(logging.NullHandler())


def find_repo_root() -> Path:
    # Check environment variable override
    env_val = os.environ.get("EXAM_PHOTO_REPO_ROOT")
    if env_val:
        p = Path(env_val).resolve()
        if p.exists():
            return p
    # Traversal upward up to 5 levels
    curr = Path(__file__).resolve().parent
    for _ in range(5):
        if (curr / "AGENTS.md").exists() or (curr / "model-manifests").exists():
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent
    # Fallback to CWD parent parent
    return Path(__file__).resolve().parent.parent.parent.parent


def main(argv: Optional[List[str]] = None) -> int:
    try:
        return _main_impl(argv)
    except Exception:
        logger.error("An unexpected CLI error occurred", exc_info=True)
        print("Code: CLI_EXECUTION_FAILED", file=sys.stderr)
        print(
            "Message: An unexpected error occurred during execution.", file=sys.stderr
        )
        return 1


def _main_impl(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify examination rules and candidate image inputs."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate-rule subcommand
    validate_parser = subparsers.add_parser(
        "validate-rule", help="Validate a rule file."
    )
    validate_parser.add_argument(
        "file_path", help="Path to the JSON rule file to validate."
    )

    # inspect-input subcommand
    inspect_parser = subparsers.add_parser(
        "inspect-input", help="Inspect and normalize a candidate image input."
    )
    inspect_parser.add_argument(
        "--input", required=True, help="Path to the image file to inspect."
    )
    inspect_parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format."
    )
    inspect_parser.add_argument(
        "--max-bytes", type=int, help="Maximum allowed file size in bytes."
    )
    inspect_parser.add_argument(
        "--max-width", type=int, help="Maximum allowed width in pixels."
    )
    inspect_parser.add_argument(
        "--max-height", type=int, help="Maximum allowed height in pixels."
    )
    inspect_parser.add_argument(
        "--max-pixels", type=int, help="Maximum allowed total pixel count."
    )
    inspect_parser.add_argument(
        "--strict-extension",
        action="store_true",
        help="Reject images if file extension doesn't match raw format signature.",
    )

    # estimate-head subcommand
    head_parser = subparsers.add_parser(
        "estimate-head",
        help="Run face detection and estimate complete head bounding box.",
    )
    head_parser.add_argument(
        "--input", required=True, help="Path to the image file to process."
    )
    head_parser.add_argument(
        "--model-path", help="Path to the face-detection model (.tflite)."
    )

    # segment-subject subcommand
    segment_parser = subparsers.add_parser(
        "segment-subject",
        help="Run subject segmentation and validate the coarse mask.",
    )
    segment_parser.add_argument(
        "--input", required=True, help="Path to the image file to process."
    )
    segment_parser.add_argument(
        "--face-model-path", help="Path to the face-detection model (.tflite)."
    )
    segment_parser.add_argument(
        "--segmenter-model-path", help="Path to the segmenter model (.tflite)."
    )
    segment_parser.add_argument(
        "--variant",
        choices=["selfie_multiclass_256x256", "selfie_bin_general"],
        help="Segmenter model variant to use.",
    )
    segment_parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Threshold value for the foreground probability mask.",
    )

    # refine-mask subcommand
    refine_parser = subparsers.add_parser(
        "refine-mask",
        help="Run subject segmentation and mask refinement on an image.",
    )
    refine_parser.add_argument(
        "--input", required=True, help="Path to the image file to process."
    )
    refine_parser.add_argument(
        "--face-model-path", help="Path to the face-detection model (.tflite)."
    )
    refine_parser.add_argument(
        "--segmenter-model-path", help="Path to the segmenter model (.tflite)."
    )
    refine_parser.add_argument(
        "--variant",
        choices=["selfie_multiclass_256x256", "selfie_bin_general"],
        help="Segmenter model variant to use.",
    )
    refine_parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Threshold value for the foreground probability mask.",
    )
    refine_parser.add_argument(
        "--radius",
        type=int,
        help="Optional override for the morphology radius in pixels.",
    )
    refine_parser.add_argument(
        "--save-mask",
        help="Optional path to save the refined binary mask PNG.",
    )
    refine_parser.add_argument(
        "--save-alpha",
        help="Optional path to save the refined alpha mask PNG (uint8 scaled).",
    )
    refine_parser.add_argument(
        "--save-trimap",
        help="Optional path to save the trimap PNG.",
    )
    refine_parser.add_argument(
        "--output-dir",
        help="Optional path to save all three refined mask outputs.",
    )

    args = parser.parse_args(argv)

    if args.command == "validate-rule":
        file_path = args.file_path
        if not os.path.exists(file_path):
            print("Error: Rule file not found. Code: FILE_NOT_FOUND", file=sys.stderr)
            return 1

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(
                "Error: Invalid JSON syntax in rule file. Code: INVALID_JSON",
                file=sys.stderr,
            )
            return 1
        except Exception:
            print(
                "Error: Unable to read rule file. Code: FILE_READ_FAILED",
                file=sys.stderr,
            )
            return 1

        errors = validate_exam_rule(data)

        if not errors:
            print("Success: Rule file is valid and complies with the schema.")
            return 0
        else:
            print(
                f"Validation failed: Found {len(errors)} error(s) in rule file.",
                file=sys.stderr,
            )
            for err in errors:
                print(
                    f"  [{err.severity.upper()}] Code: {err.error_code} | Path: {err.field_path}\n"
                    f"  Message: {err.message}\n"
                    f"  Resolution: {err.suggested_resolution}\n",
                    file=sys.stderr,
                )
            return 1

    elif args.command == "inspect-input":
        input_path = args.input
        if not os.path.exists(input_path):
            print("Error: Input file not found. Code: FILE_NOT_FOUND", file=sys.stderr)
            return 1

        # Configure limits from cli flags
        limit_kwargs = {}
        if args.max_bytes is not None:
            limit_kwargs["maximum_encoded_byte_size"] = args.max_bytes
        if args.max_width is not None:
            limit_kwargs["maximum_width"] = args.max_width
        if args.max_height is not None:
            limit_kwargs["maximum_height"] = args.max_height
        if args.max_pixels is not None:
            limit_kwargs["maximum_total_pixel_count"] = args.max_pixels
        if args.strict_extension:
            limit_kwargs["extension_mismatch_policy"] = "reject"

        try:
            limits = InputLimits(**limit_kwargs)
        except Exception:
            print(
                "Error: Invalid configuration. Code: CONFIGURATION_INVALID",
                file=sys.stderr,
            )
            return 1

        # Read file bytes securely
        try:
            with open(input_path, "rb") as f:
                data = f.read(limits.maximum_encoded_byte_size + 1)
        except Exception:
            print("Error: Unable to read file. Code: FILE_READ_FAILED", file=sys.stderr)
            return 1

        # Run inspection and normalization pipeline
        try:
            result = normalize_image_input(data, input_path, limits)
        except ImageInspectionError as ie:
            if args.json:
                print(json.dumps(ie.to_dict(), indent=2), file=sys.stderr)
            else:
                print(f"Inspection Failed: {ie.code.value}", file=sys.stderr)
                print(f"Message: {ie.message}", file=sys.stderr)
                print(f"Resolution: {ie.suggested_resolution}", file=sys.stderr)
            return 1
        except Exception:
            # Mask raw stack trace
            if args.json:
                print(
                    json.dumps(
                        {
                            "error_code": "INPUT_DECODE_FAILED",
                            "message": "An unexpected decoder error occurred.",
                            "suggested_resolution": "Please check image formatting integrity.",
                        }
                    ),
                    file=sys.stderr,
                )
            else:
                print("Inspection Failed: INPUT_DECODE_FAILED", file=sys.stderr)
                print(
                    "Message: An unexpected decoder error occurred.",
                    file=sys.stderr,
                )
            return 1

        # Print success outputs
        metadata_dict = result.metadata.model_dump()
        if args.json:
            print(json.dumps(metadata_dict, indent=2))
        else:
            print("Success: Image normalized successfully.")
            print(
                f"  Dimensions: {metadata_dict['original_width']}x{metadata_dict['original_height']} -> {metadata_dict['normalized_width']}x{metadata_dict['normalized_height']}"
            )
            print(
                f"  Mode: {metadata_dict['original_mode']} -> {metadata_dict['normalized_mode']}"
            )
            if metadata_dict["warnings"]:
                print("\nWarnings:")
                for warn in metadata_dict["warnings"]:
                    print(f"  - {warn}")

        return 0

    elif args.command == "estimate-head":
        input_path = args.input
        if not os.path.exists(input_path):
            print("Error: Input file not found. Code: FILE_NOT_FOUND", file=sys.stderr)
            return 1

        # 1. Normalize the image input
        limits = InputLimits()  # use defaults
        try:
            with open(input_path, "rb") as f:
                data = f.read(limits.maximum_encoded_byte_size + 1)
        except Exception:
            print(
                "Error: Unable to read input file. Code: FILE_READ_FAILED",
                file=sys.stderr,
            )
            return 1

        try:
            norm_result = normalize_image_input(data, input_path, limits)
        except Exception:
            print(
                "Error: Image normalization failed. Code: IMAGE_NORMALIZATION_FAILED",
                file=sys.stderr,
            )
            return 1

        # 2. Lazy load MediapipeFaceDetector
        try:
            from exam_photo.providers.mediapipe_face_detector import (
                MediapipeFaceDetector,
            )
        except ImportError:
            print(
                "Error: MediaPipe face detector provider dependencies are not installed. Code: DEPENDENCY_MISSING",
                file=sys.stderr,
            )
            return 1

        # 3. Locate face model path
        repo_root = find_repo_root()
        model_path_str = args.model_path
        expected_sha256 = ""

        if not model_path_str:
            model_path_str = os.environ.get("EXAM_PHOTO_FACE_MODEL_PATH")
            expected_sha256 = os.environ.get("EXAM_PHOTO_FACE_MODEL_SHA256", "")

        if not model_path_str:
            manifest_path = repo_root / "model-manifests" / "face-detector.json"
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

        model_path = Path(model_path_str)
        if not model_path.is_absolute():
            model_path = repo_root / model_path

        if not model_path.exists():
            print(
                "Error: Face detection model file not found. Code: MODEL_NOT_FOUND",
                file=sys.stderr,
            )
            return 1

        # 4. Instantiate and run face detector using context manager
        try:
            detector = MediapipeFaceDetector(
                model_path=model_path,
                expected_sha256=expected_sha256,
            )
        except Exception:
            print(
                "Error: Face detector initialization failed. Code: DETECTOR_INIT_FAILED",
                file=sys.stderr,
            )
            return 1

        try:
            with detector:
                face_result = detector.detect_faces(norm_result.image)
        except Exception:
            print(
                "Error: Face detection failed. Code: FACE_DETECTION_FAILED",
                file=sys.stderr,
            )
            return 1

        # 5. Verify exactly 1 face
        if len(face_result.detections) == 0:
            print(
                "Error: No faces detected in the image. Code: NO_FACE_DETECTED",
                file=sys.stderr,
            )
            return 1
        elif len(face_result.detections) > 1:
            print(
                f"Error: Multiple faces ({len(face_result.detections)}) detected. Code: MULTIPLE_FACES_DETECTED",
                file=sys.stderr,
            )
            return 1

        face = face_result.detections[0]

        # 6. Run head estimator
        try:
            estimator = LandmarkGeometricHeadEstimator()
            head_result = estimator.estimate_head(
                norm_result.image, face, face.landmarks
            )
        except Exception:
            print(
                "Error: Head estimation failed. Code: HEAD_ESTIMATION_FAILED",
                file=sys.stderr,
            )
            return 1

        # 7. Print results to stdout
        print(
            "Success: Provisional geometric head-box estimation finished successfully."
        )
        print(
            f"  Provider: {head_result.provider_name} v{head_result.provider_version}"
        )
        print(f"  Method: {head_result.method}")
        print(
            f"  Confidence: {head_result.confidence:.3f} (Basis: {head_result.confidence_basis})"
        )
        print(f"  Processing Duration: {head_result.processing_duration:.2f}ms")

        # Head Bounding Box
        box = head_result.head_bounding_box
        norm_box = head_result.normalized_head_bounding_box
        print("\n  Estimated Head Bounding Box:")
        print(
            f"    Pixel Space: left={box.left:.1f}, top={box.top:.1f}, right={box.right:.1f}, bottom={box.bottom:.1f}"
        )
        print(
            f"    Normalized:  left={norm_box.left:.4f}, top={norm_box.top:.4f}, right={norm_box.right:.4f}, bottom={norm_box.bottom:.4f}"
        )

        # Boundary Visibility
        print("\n  Boundary Visibility Assessments:")
        vis = head_result.boundary_visibility
        for b_name in [
            "top_hair_boundary",
            "left_head_boundary",
            "right_head_boundary",
            "chin_boundary",
            "lower_beard_boundary",
            "left_ear",
            "right_ear",
        ]:
            assessment = getattr(vis, b_name)
            print(
                f"    {b_name:22}: state={assessment.state.value:14} basis={assessment.basis}"
            )

        # Clipping Assessment
        print("\n  Clipping Assessments:")
        clip = head_result.clipping_assessment
        for field in ["top_hair", "left_side", "right_side", "chin", "lower_beard"]:
            finding = getattr(clip, field)
            edge_dist_str = (
                f"{finding.image_edge_distance:.1f}px"
                if finding.image_edge_distance is not None
                else "N/A"
            )
            print(
                f"    {field:12}: status={finding.status.value:12} confidence={finding.confidence:.2f} basis={finding.basis:20} edge_distance={edge_dist_str}"
            )

        if head_result.warnings:
            print("\n  Warnings:")
            for w in head_result.warnings:
                print(f"    - {w}")

        return 0

    elif args.command == "segment-subject":
        input_path = args.input
        if not os.path.exists(input_path):
            print("Error: Input file not found. Code: FILE_NOT_FOUND", file=sys.stderr)
            return 1

        # 1. Normalize the image input
        limits = InputLimits()  # use defaults
        try:
            with open(input_path, "rb") as f:
                data = f.read(limits.maximum_encoded_byte_size + 1)
        except Exception:
            print(
                "Error: Unable to read input file. Code: FILE_READ_FAILED",
                file=sys.stderr,
            )
            return 1

        try:
            norm_result = normalize_image_input(data, input_path, limits)
        except Exception:
            print(
                "Error: Image normalization failed. Code: IMAGE_NORMALIZATION_FAILED",
                file=sys.stderr,
            )
            return 1

        # 2. Lazy load MediapipeFaceDetector
        try:
            from exam_photo.providers.mediapipe_face_detector import (
                MediapipeFaceDetector,
            )
        except ImportError:
            print(
                "Error: MediaPipe face detector provider dependencies are not installed. Code: DEPENDENCY_MISSING",
                file=sys.stderr,
            )
            return 1

        # 3. Locate face model path
        repo_root = find_repo_root()
        face_model_path_str = args.face_model_path
        face_expected_sha256 = ""

        if not face_model_path_str:
            face_model_path_str = os.environ.get("EXAM_PHOTO_FACE_MODEL_PATH")
            face_expected_sha256 = os.environ.get("EXAM_PHOTO_FACE_MODEL_SHA256", "")

        if not face_model_path_str:
            manifest_path = repo_root / "model-manifests" / "face-detector.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as mf:
                        manifest = json.load(mf)
                    face_model_path_str = manifest.get("local_model_path_default")
                    face_expected_sha256 = manifest.get("sha256", "")
                except Exception:
                    pass
            if not face_model_path_str:
                face_model_path_str = "model-assets/blaze_face_short_range.tflite"

        face_model_path = Path(face_model_path_str)
        if not face_model_path.is_absolute():
            face_model_path = repo_root / face_model_path

        # 4. Detect Face
        face = None
        if face_model_path.exists():
            try:
                detector = MediapipeFaceDetector(
                    model_path=face_model_path,
                    expected_sha256=face_expected_sha256,
                )
                with detector:
                    face_result = detector.detect_faces(norm_result.image)
                if len(face_result.detections) == 1:
                    face = face_result.detections[0]
            except Exception:
                pass

        # 5. Estimate Head Bounding Box if exactly one face
        head_box = None
        if face is not None:
            try:
                estimator = LandmarkGeometricHeadEstimator()
                head_result = estimator.estimate_head(
                    norm_result.image, face, face.landmarks
                )
                head_box = head_result.head_bounding_box
            except Exception:
                pass

        # 6. Locate segmenter model path
        model_path_str = args.segmenter_model_path
        expected_sha256 = ""

        if not model_path_str:
            model_path_str = os.environ.get("EXAM_PHOTO_SEGMENTER_MODEL_PATH")
            expected_sha256 = os.environ.get("EXAM_PHOTO_SEGMENTER_MODEL_SHA256", "")

        if not model_path_str:
            manifest_path = repo_root / "model-manifests" / "subject-segmenter.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as mf:
                        manifest = json.load(mf)
                    variant_name = args.variant or manifest.get(
                        "selected_variant", "selfie_bin_general"
                    )
                    variants = manifest.get("variants", {})
                    variant = variants.get(variant_name)
                    if variant is None:
                        print(
                            f"Error: Selected variant '{variant_name}' not found in manifest. Code: VARIANT_NOT_FOUND",
                            file=sys.stderr,
                        )
                        return 1
                    filename = variant.get("filename")
                    if not filename:
                        print(
                            "Error: Filename not found for selected variant in manifest. Code: MANIFEST_MALFORMED",
                            file=sys.stderr,
                        )
                        return 1
                    model_path_str = "model-assets/" + filename
                    expected_sha256 = variant.get("sha256", "")
                except Exception:
                    print(
                        "Error: Model manifest is malformed or could not be loaded. Code: MANIFEST_MALFORMED",
                        file=sys.stderr,
                    )
                    return 1
            else:
                print(
                    "Error: Model manifest not found. Code: MANIFEST_NOT_FOUND",
                    file=sys.stderr,
                )
                return 1

        model_path = Path(model_path_str)
        if not model_path.is_absolute():
            model_path = repo_root / model_path

        if not model_path.exists():
            print(
                "Error: Segmenter model file not found. Code: MODEL_NOT_FOUND",
                file=sys.stderr,
            )
            return 1

        # 7. Run segmenter
        try:
            from exam_photo.providers.segmenters.mediapipe_segmenter import (
                MediapipeSubjectSegmenter,
            )
        except ImportError:
            print(
                "Error: MediaPipe subject segmenter provider dependencies are not installed. Code: DEPENDENCY_MISSING",
                file=sys.stderr,
            )
            return 1

        try:
            segmenter = MediapipeSubjectSegmenter(
                model_path=model_path,
                expected_sha256=expected_sha256,
            )
            config = SegmentationConfig(foreground_threshold=args.threshold)
            with segmenter:
                seg_result = segmenter.segment_subject(
                    norm_result.image,
                    face=face,
                    head_estimate=head_box,
                    config=config,
                )
        except Exception as e:
            from exam_photo.providers.model_errors import (
                ModelChecksumError,
                ModelNotFoundError,
            )

            if isinstance(e, ModelNotFoundError):
                print("Code: SEGMENTATION_MODEL_MISSING", file=sys.stderr)
                print("Message: Segmentation model file is missing.", file=sys.stderr)
            elif isinstance(e, ModelChecksumError):
                print("Code: SEGMENTATION_MODEL_CHECKSUM_FAILED", file=sys.stderr)
                print(
                    "Message: Segmentation model checksum verification failed.",
                    file=sys.stderr,
                )
            else:
                logger.error("Subject segmentation failed internally", exc_info=True)
                print("Code: SEGMENTATION_PROVIDER_FAILED", file=sys.stderr)
                print(
                    "Message: Subject segmentation could not be completed.",
                    file=sys.stderr,
                )
            return 1

        # 8. Print stats
        print("Success: Subject segmentation finished successfully.")
        print(f"  Provider: {seg_result.provider_name} v{seg_result.provider_version}")
        print(f"  Model: {seg_result.model_name} v{seg_result.model_version}")
        print(f"  Processing Duration: {seg_result.processing_duration:.2f}ms")
        print(f"  Mask Dimensions: {seg_result.mask_width}x{seg_result.mask_height}")
        print(f"  Foreground Coverage: {seg_result.foreground_coverage_ratio:.4f}")

        val = seg_result.mask_validation
        print("\n  Mask Validation Report:")
        print(f"    Is Valid: {val.is_valid}")
        print(f"    Uncertain Pixel Ratio: {val.uncertain_pixel_ratio:.4f}")
        print(f"    Connected Components Count: {val.connected_components_count}")
        print(f"    Largest Component Ratio: {val.largest_component_ratio:.4f}")

        print(f"    Image Edge Contact: {val.image_edge_contact}")
        print(f"    Face Contained: {val.face_contained}")
        print(
            f"    Head Region Coverage Ratio: {val.head_region_coverage_ratio if val.head_region_coverage_ratio is not None else 'N/A'}"
        )

        if val.issue_codes:
            print("\n  Issue Codes Detected:")
            for code in val.issue_codes:
                print(f"    - {code}")

        return 0

    elif args.command == "refine-mask":
        input_path = args.input
        if not os.path.exists(input_path):
            print("Error: Input file not found. Code: FILE_NOT_FOUND", file=sys.stderr)
            return 1

        # 1. Normalize the image input
        limits = InputLimits()  # use defaults
        try:
            with open(input_path, "rb") as f:
                data = f.read(limits.maximum_encoded_byte_size + 1)
        except Exception:
            print(
                "Error: Unable to read input file. Code: FILE_READ_FAILED",
                file=sys.stderr,
            )
            return 1

        try:
            norm_result = normalize_image_input(data, input_path, limits)
        except Exception:
            print(
                "Error: Image normalization failed. Code: IMAGE_NORMALIZATION_FAILED",
                file=sys.stderr,
            )
            return 1

        # 2. Lazy load MediapipeFaceDetector
        try:
            from exam_photo.providers.mediapipe_face_detector import (
                MediapipeFaceDetector,
            )
        except ImportError:
            print(
                "Error: MediaPipe face detector provider dependencies are not installed. Code: DEPENDENCY_MISSING",
                file=sys.stderr,
            )
            return 1

        # 3. Locate face model path
        repo_root = find_repo_root()
        face_model_path_str = args.face_model_path
        face_expected_sha256 = ""

        if not face_model_path_str:
            face_model_path_str = os.environ.get("EXAM_PHOTO_FACE_MODEL_PATH")
            face_expected_sha256 = os.environ.get("EXAM_PHOTO_FACE_MODEL_SHA256", "")

        if not face_model_path_str:
            manifest_path = repo_root / "model-manifests" / "face-detector.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as mf:
                        manifest = json.load(mf)
                    face_model_path_str = manifest.get("local_model_path_default")
                    face_expected_sha256 = manifest.get("sha256", "")
                except Exception:
                    pass
            if not face_model_path_str:
                face_model_path_str = "model-assets/blaze_face_short_range.tflite"

        face_model_path = Path(face_model_path_str)
        if not face_model_path.is_absolute():
            face_model_path = repo_root / face_model_path

        # 4. Detect Face
        face = None
        if face_model_path.exists():
            try:
                detector = MediapipeFaceDetector(
                    model_path=face_model_path,
                    expected_sha256=face_expected_sha256,
                )
                with detector:
                    face_result = detector.detect_faces(norm_result.image)
                if len(face_result.detections) == 1:
                    face = face_result.detections[0]
            except Exception:
                pass

        # 5. Estimate Head Bounding Box if exactly one face
        head_box = None
        if face is not None:
            try:
                estimator = LandmarkGeometricHeadEstimator()
                head_result = estimator.estimate_head(
                    norm_result.image, face, face.landmarks
                )
                head_box = head_result.head_bounding_box
            except Exception:
                pass

        # 6. Locate segmenter model path
        model_path_str = args.segmenter_model_path
        expected_sha256 = ""

        if not model_path_str:
            model_path_str = os.environ.get("EXAM_PHOTO_SEGMENTER_MODEL_PATH")
            expected_sha256 = os.environ.get("EXAM_PHOTO_SEGMENTER_MODEL_SHA256", "")

        if not model_path_str:
            manifest_path = repo_root / "model-manifests" / "subject-segmenter.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as mf:
                        manifest = json.load(mf)
                    variant_name = args.variant or manifest.get(
                        "selected_variant", "selfie_bin_general"
                    )
                    variants = manifest.get("variants", {})
                    variant = variants.get(variant_name)
                    if variant is None:
                        print(
                            f"Error: Selected variant '{variant_name}' not found in manifest. Code: VARIANT_NOT_FOUND",
                            file=sys.stderr,
                        )
                        return 1
                    filename = variant.get("filename")
                    if not filename:
                        print(
                            "Error: Filename not found for selected variant in manifest. Code: MANIFEST_MALFORMED",
                            file=sys.stderr,
                        )
                        return 1
                    model_path_str = "model-assets/" + filename
                    expected_sha256 = variant.get("sha256", "")
                except Exception:
                    print(
                        "Error: Model manifest is malformed or could not be loaded. Code: MANIFEST_MALFORMED",
                        file=sys.stderr,
                    )
                    return 1
            else:
                print(
                    "Error: Model manifest not found. Code: MANIFEST_NOT_FOUND",
                    file=sys.stderr,
                )
                return 1

        model_path = Path(model_path_str)
        if not model_path.is_absolute():
            model_path = repo_root / model_path

        if not model_path.exists():
            print(
                "Error: Segmenter model file not found. Code: MODEL_NOT_FOUND",
                file=sys.stderr,
            )
            return 1

        # 7. Run segmenter
        try:
            from exam_photo.providers.segmenters.mediapipe_segmenter import (
                MediapipeSubjectSegmenter,
            )
        except ImportError:
            print(
                "Error: MediaPipe subject segmenter provider dependencies are not installed. Code: DEPENDENCY_MISSING",
                file=sys.stderr,
            )
            return 1

        try:
            segmenter = MediapipeSubjectSegmenter(
                model_path=model_path,
                expected_sha256=expected_sha256,
            )
            config = SegmentationConfig(foreground_threshold=args.threshold)
            with segmenter:
                seg_result = segmenter.segment_subject(
                    norm_result.image,
                    face=face,
                    head_estimate=head_box,
                    config=config,
                )
        except Exception as e:
            from exam_photo.providers.model_errors import (
                ModelChecksumError,
                ModelNotFoundError,
            )

            if isinstance(e, ModelNotFoundError):
                print("Code: SEGMENTATION_MODEL_MISSING", file=sys.stderr)
                print("Message: Segmentation model file is missing.", file=sys.stderr)
            elif isinstance(e, ModelChecksumError):
                print("Code: SEGMENTATION_MODEL_CHECKSUM_FAILED", file=sys.stderr)
                print(
                    "Message: Segmentation model checksum verification failed.",
                    file=sys.stderr,
                )
            else:
                logger.error("Subject segmentation failed internally", exc_info=True)
                print("Code: SEGMENTATION_PROVIDER_FAILED", file=sys.stderr)
                print(
                    "Message: Subject segmentation could not be completed.",
                    file=sys.stderr,
                )
            return 1

        # 8. Run Refinement
        try:
            from exam_photo.providers.foreground_refinement import RefinementConfig
            from exam_photo.providers.refiners.errors import (
                RefinementInputError,
                RefinementOutputError,
            )
            from exam_photo.providers.refiners.morphological_refiner import (
                MorphologicalForegroundRefiner,
            )

            ref_config = RefinementConfig()
            if args.radius is not None:
                ref_config.morphology_radius_px = args.radius
                ref_config.morphology_radius_ratio = None

            refiner = MorphologicalForegroundRefiner()
            ref_result = refiner.refine_mask(
                coarse_mask=seg_result.coarse_mask,
                probability_mask=seg_result.probability_mask,
                face=face,
                config=ref_config,
            )
        except Exception as e:
            if isinstance(e, RefinementInputError):
                print("Code: REFINEMENT_INPUT_INVALID", file=sys.stderr)
                print("Message: Refinement input was invalid.", file=sys.stderr)
            elif isinstance(e, RefinementOutputError):
                print("Code: REFINEMENT_OUTPUT_INVALID", file=sys.stderr)
                print("Message: Refinement output was invalid.", file=sys.stderr)
            else:
                logger.error("Refinement failed internally", exc_info=True)
                print("Code: REFINEMENT_PROVIDER_UNAVAILABLE", file=sys.stderr)
                print(
                    "Message: Refinement provider failed or is unavailable.",
                    file=sys.stderr,
                )
            return 1

        # 9. Print stats
        print("Success: Foreground mask refinement finished successfully.")
        print(f"  Provider: {ref_result.provider_name} v{ref_result.provider_version}")
        print(f"  Refinement Duration: {ref_result.refinement_duration_ms:.2f}ms")
        print(f"  Effective Radius: {ref_result.effective_radius_px}px")

        ref_val = ref_result.validation
        print("\n  Refinement Validation Report:")
        print(f"    Is Valid: {ref_val.is_valid}")
        print(f"    Coarse IoU: {ref_val.coarse_iou:.4f}")
        print(f"    Foreground Coverage Ratio: {ref_val.foreground_coverage_ratio:.4f}")
        print(f"    Edge Transition Ratio: {ref_val.edge_transition_ratio:.4f}")
        print(f"    Connectivity Improvement: {ref_val.connectivity_improvement}")

        if ref_val.issue_codes:
            print("\n  Issue Codes Detected:")
            for code in ref_val.issue_codes:
                print(f"    - {code}")

        # 10. Save files if requested
        try:
            if args.save_mask:
                ref_result.refined_binary_mask.save(args.save_mask)
                print(f"  Saved refined binary mask to {args.save_mask}")

            if args.save_alpha:
                alpha_arr = (ref_result.refined_alpha_mask * 255.0).astype(np.uint8)
                alpha_img = Image.fromarray(alpha_arr, mode="L")
                alpha_img.save(args.save_alpha)
                print(f"  Saved refined alpha mask to {args.save_alpha}")

            if args.save_trimap:
                ref_result.trimap.save(args.save_trimap)
                print(f"  Saved trimap to {args.save_trimap}")

            if args.output_dir:
                out_dir = Path(args.output_dir)
                out_dir.mkdir(parents=True, exist_ok=True)
                ref_result.refined_binary_mask.save(out_dir / "refined_mask.png")

                alpha_arr = (ref_result.refined_alpha_mask * 255.0).astype(np.uint8)
                alpha_img = Image.fromarray(alpha_arr, mode="L")
                alpha_img.save(out_dir / "refined_alpha.png")

                ref_result.trimap.save(out_dir / "trimap.png")
                print(f"  Saved all refined masks to directory: {out_dir}")
        except Exception as e:
            print(f"Error: Failed to save output files: {e}", file=sys.stderr)
            return 1

        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
