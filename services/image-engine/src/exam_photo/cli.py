import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from exam_photo.input.errors import ImageInspectionError
from exam_photo.input.limits import InputLimits
from exam_photo.input.normalization import normalize_image_input
from exam_photo.providers.landmark_geometric_head_estimator import (
    LandmarkGeometricHeadEstimator,
)
from exam_photo.rule_validation import validate_exam_rule


def main(argv: Optional[List[str]] = None) -> int:
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

    args = parser.parse_args(argv)

    if args.command == "validate-rule":
        file_path = args.file_path
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            return 1

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as je:
            print(f"Error: Invalid JSON syntax in file: {je.msg}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error: Unable to read file: {str(e)}", file=sys.stderr)
            return 1

        errors = validate_exam_rule(data)

        if not errors:
            print(
                f"Success: File '{os.path.basename(file_path)}' is valid and complies with the schema."
            )
            return 0
        else:
            print(
                f"Validation failed for '{os.path.basename(file_path)}': Found {len(errors)} error(s).",
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
            print(f"Error: File not found: {input_path}", file=sys.stderr)
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
        except Exception as e:
            print(f"Error: Invalid configuration: {str(e)}", file=sys.stderr)
            return 1

        # Read file bytes securely
        try:
            with open(input_path, "rb") as f:
                data = f.read(limits.maximum_encoded_byte_size + 1)
        except Exception as e:
            print(f"Error: Unable to read file: {str(e)}", file=sys.stderr)
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
            print(
                f"Success: Image '{metadata_dict['source_basename']}' normalized successfully."
            )
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

        # 3. Locate model path relative to package location
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
