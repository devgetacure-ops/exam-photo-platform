import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, List, Optional

import numpy as np
from PIL import Image

from exam_photo.input.errors import ImageInspectionError
from exam_photo.input.limits import InputLimits
from exam_photo.input.normalization import normalize_image_input
from exam_photo.providers import (
    CropConfig,
    CropModeBResult,
    CropPlanResult,
    DeterministicCropPlanner,
)
from exam_photo.providers.background_composers.solid_background_composer import (
    SolidBackgroundComposer,
)
from exam_photo.providers.background_composition import BackgroundCompositionConfig
from exam_photo.providers.crop_planners.deterministic_crop_mode_b_planner import (
    DeterministicCropModeBPlanner,
)
from exam_photo.providers.crop_planning import CropModeBConfig
from exam_photo.providers.landmark_geometric_head_estimator import (
    LandmarkGeometricHeadEstimator,
)
from exam_photo.providers.output_preparation import (
    EnhancementMode,
    OutputPreparationConfig,
    ResizeMode,
)
from exam_photo.providers.output_preparers.deterministic_output_preparer import (
    DeterministicOutputPreparer,
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
    refine_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files when saving outputs.",
    )

    # plan-crop-mode-a subcommand
    crop_parser = subparsers.add_parser(
        "plan-crop-mode-a",
        help="Plan an exact-aspect Crop Mode A crop window for an input image.",
    )
    crop_parser.add_argument(
        "--input", required=True, help="Path to the image file to process."
    )
    crop_parser.add_argument("--target-width", type=int, help="Target width in pixels.")
    crop_parser.add_argument(
        "--target-height", type=int, help="Target height in pixels."
    )
    crop_parser.add_argument(
        "--target-aspect-ratio", type=float, help="Target aspect ratio."
    )
    crop_parser.add_argument(
        "--face-model-path", help="Path to the face-detection model (.tflite)."
    )
    crop_parser.add_argument(
        "--segmenter-model-path", help="Path to the segmenter model (.tflite)."
    )
    crop_parser.add_argument(
        "--variant",
        choices=["selfie_multiclass_256x256", "selfie_bin_general"],
        help="Segmenter model variant to use.",
    )
    crop_parser.add_argument(
        "--skip-mask-refinement",
        action="store_true",
        help="Skip mask refinement and perform crop planning purely on face/head geometry.",
    )
    crop_parser.add_argument(
        "--save-preview",
        help="Optional path to save the cropped preview image PNG.",
    )
    crop_parser.add_argument(
        "--output-dir",
        help="Optional path to save all outputs including preview image.",
    )
    crop_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files when saving outputs.",
    )
    crop_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format to stdout.",
    )

    # plan-crop-mode-b subcommand
    crop_b_parser = subparsers.add_parser(
        "plan-crop-mode-b",
        help="Plan a face/head-led natural range Crop Mode B crop window for an input image.",
    )
    crop_b_parser.add_argument(
        "--input", required=True, help="Path to the image file to process."
    )
    crop_b_parser.add_argument("--min-width", type=int, help="Minimum width in pixels.")
    crop_b_parser.add_argument("--max-width", type=int, help="Maximum width in pixels.")
    crop_b_parser.add_argument(
        "--min-height", type=int, help="Minimum height in pixels."
    )
    crop_b_parser.add_argument(
        "--max-height", type=int, help="Maximum height in pixels."
    )
    crop_b_parser.add_argument(
        "--min-aspect-ratio", type=float, help="Minimum aspect ratio."
    )
    crop_b_parser.add_argument(
        "--max-aspect-ratio", type=float, help="Maximum aspect ratio."
    )
    crop_b_parser.add_argument(
        "--target-head-height-ratio",
        type=float,
        help="Target head height ratio (default 0.76).",
    )
    crop_b_parser.add_argument(
        "--min-head-height-ratio",
        type=float,
        help="Minimum head height ratio (default 0.68).",
    )
    crop_b_parser.add_argument(
        "--max-head-height-ratio",
        type=float,
        help="Maximum head height ratio (default 0.84).",
    )
    crop_b_parser.add_argument(
        "--face-model-path", help="Path to the face-detection model (.tflite)."
    )
    crop_b_parser.add_argument(
        "--segmenter-model-path", help="Path to the segmenter model (.tflite)."
    )
    crop_b_parser.add_argument(
        "--variant",
        choices=["selfie_multiclass_256x256", "selfie_bin_general"],
        help="Segmenter model variant to use.",
    )
    crop_b_parser.add_argument(
        "--skip-mask-refinement",
        action="store_true",
        help="Skip mask refinement and perform crop planning purely on face/head geometry.",
    )
    crop_b_parser.add_argument(
        "--save-preview",
        help="Optional path to save the cropped preview image PNG.",
    )
    crop_b_parser.add_argument(
        "--output-dir",
        help="Optional path to save all outputs including preview image.",
    )
    crop_b_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files when saving outputs.",
    )
    crop_b_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format to stdout.",
    )
    crop_b_parser.add_argument(
        "--allow-padding",
        action="store_true",
        help="Allow padding if crop box extends outside source bounds.",
    )
    crop_b_parser.add_argument(
        "--allow-subject-clipping",
        action="store_true",
        help="Allow clipping of subject head/mask if source is too tight.",
    )
    crop_b_parser.add_argument(
        "--mask-preservation-threshold",
        type=float,
        help="Minimum ratio of foreground mask to preserve in crop.",
    )
    crop_b_parser.add_argument(
        "--edge-safety-margin-px",
        type=int,
        help="Safety margin in pixels for boundary checks.",
    )

    # compose-background subcommand
    bg_parser = subparsers.add_parser(
        "compose-background",
        help="Compose candidate foreground onto a solid background.",
    )
    bg_parser.add_argument(
        "--input", required=True, help="Path to the image file to process."
    )
    bg_parser.add_argument(
        "--target-colour",
        "--background-colour",
        default="#FFFFFF",
        help="Hex color code for background.",
    )
    bg_parser.add_argument(
        "--alpha-threshold", type=float, help="Alpha threshold for foreground coverage."
    )
    bg_parser.add_argument(
        "--allow-transparent-output",
        action="store_true",
        help="Generate RGBA instead of RGB output.",
    )
    bg_parser.add_argument(
        "--face-model-path", help="Path to the face-detection model (.tflite)."
    )
    bg_parser.add_argument(
        "--segmenter-model-path", help="Path to the segmenter model (.tflite)."
    )
    bg_parser.add_argument(
        "--variant",
        choices=["selfie_multiclass_256x256", "selfie_bin_general"],
        help="Segmenter model variant to use.",
    )
    bg_parser.add_argument(
        "--save-preview",
        help="Optional path to save the composed image PNG.",
    )
    bg_parser.add_argument(
        "--output-dir",
        help="Optional path to save all outputs including composed image.",
    )
    bg_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files when saving outputs.",
    )
    bg_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format to stdout.",
    )

    # prepare-output subcommand
    prep_parser = subparsers.add_parser(
        "prepare-output",
        help="Prepare output dimensions and apply restrained enhancement.",
    )
    prep_parser.add_argument("--input", required=True, help="Path to the image file.")
    prep_parser.add_argument(
        "--resize-mode", choices=["exact", "range_select"], default="exact"
    )
    prep_parser.add_argument("--target-width", type=int)
    prep_parser.add_argument("--target-height", type=int)
    prep_parser.add_argument("--min-width", type=int)
    prep_parser.add_argument("--max-width", type=int)
    prep_parser.add_argument("--min-height", type=int)
    prep_parser.add_argument("--max-height", type=int)
    prep_parser.add_argument("--preferred-width", type=int)
    prep_parser.add_argument("--preferred-height", type=int)
    prep_parser.add_argument("--background-colour", default="#FFFFFF")
    prep_parser.add_argument("--crop-mode", choices=["none", "a", "b"], default="none")
    prep_parser.add_argument(
        "--enhancement-mode", choices=["none", "conservative"], default="none"
    )
    prep_parser.add_argument("--brightness", type=float, default=1.0)
    prep_parser.add_argument("--contrast", type=float, default=1.0)
    prep_parser.add_argument("--sharpness", type=float, default=1.0)
    prep_parser.add_argument(
        "--save-preview", help="Optional path to save valid cropped preview."
    )
    prep_parser.add_argument(
        "--save-diagnostic-preview",
        help="Optional path to save diagnostic invalid preview.",
    )
    prep_parser.add_argument("--allow-invalid-preview", action="store_true")
    prep_parser.add_argument("--output-dir", help="Path to save outputs.")
    prep_parser.add_argument("--overwrite", action="store_true")
    prep_parser.add_argument("--json", action="store_true")
    prep_parser.add_argument(
        "--face-model-path", help="Path to the face-detection model (.tflite)."
    )
    prep_parser.add_argument(
        "--segmenter-model-path", help="Path to the segmenter model (.tflite)."
    )
    prep_parser.add_argument(
        "--variant", choices=["selfie_multiclass_256x256", "selfie_bin_general"]
    )

    # compress-output subcommand
    comp_parser = subparsers.add_parser(
        "compress-output",
        help="Compress prepared output and perform quality-aware optimization.",
    )
    comp_parser.add_argument("--input", required=True, help="Path to the image file.")
    comp_parser.add_argument("--target-width", type=int)
    comp_parser.add_argument("--target-height", type=int)
    comp_parser.add_argument("--maximum-bytes", type=int, required=True)
    comp_parser.add_argument("--minimum-bytes", type=int)
    comp_parser.add_argument("--target-ceiling-ratio", type=float, default=0.96)
    comp_parser.add_argument("--safety-margin-bytes", type=int, default=512)
    comp_parser.add_argument("--min-quality", type=int, default=35)
    comp_parser.add_argument("--max-quality", type=int, default=95)
    comp_parser.add_argument("--initial-quality", type=int, default=92)
    comp_parser.add_argument("--optimize", action="store_true", default=True)
    comp_parser.add_argument("--no-optimize", dest="optimize", action="store_false")
    comp_parser.add_argument("--progressive", action="store_true")
    comp_parser.add_argument("--crop-mode", choices=["none", "a", "b"], default="none")
    comp_parser.add_argument("--background-colour")
    comp_parser.add_argument(
        "--enhancement-mode", choices=["none", "conservative"], default="none"
    )
    comp_parser.add_argument("--brightness", type=float, default=1.0)
    comp_parser.add_argument("--contrast", type=float, default=1.0)
    comp_parser.add_argument("--sharpness", type=float, default=1.0)
    comp_parser.add_argument(
        "--save-output",
        help="Optional path to save valid compressed candidate bytes.",
    )
    comp_parser.add_argument("--allow-invalid-output", action="store_true")
    comp_parser.add_argument("--output-dir", help="Path to save outputs.")
    comp_parser.add_argument("--overwrite", action="store_true")
    comp_parser.add_argument("--json", action="store_true")
    comp_parser.add_argument(
        "--face-model-path", help="Path to the face-detection model (.tflite)."
    )
    comp_parser.add_argument(
        "--segmenter-model-path", help="Path to the segmenter model (.tflite)."
    )
    # process-rule subcommand
    proc_parser = subparsers.add_parser(
        "process-rule",
        help="Process candidate image according to exam rule config.",
    )
    proc_parser.add_argument("--input", required=True, help="Path to input image.")
    proc_parser.add_argument("--rule", required=True, help="Path to JSON rule file.")
    proc_parser.add_argument(
        "--output-dir", help="Directory to save candidate image and reports."
    )
    proc_parser.add_argument(
        "--save-output",
        action="store_true",
        help="Save the candidate image to output directory.",
    )
    proc_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files in output directory.",
    )
    proc_parser.add_argument(
        "--json", action="store_true", help="Output result strictly in JSON to stdout."
    )
    proc_parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save the execution report in output directory.",
    )
    proc_parser.add_argument(
        "--allow-invalid-output",
        action="store_true",
        help="Save the candidate image even if invalid.",
    )
    proc_parser.add_argument(
        "--allow-diagnostic-artifacts",
        action="store_true",
        help="Save intermediate pipeline masks and crop windows.",
    )
    proc_parser.add_argument(
        "--quality-mode",
        choices=["fast", "balanced", "high"],
        default="balanced",
        help="Pipeline processing quality mode.",
    )
    proc_parser.add_argument("--face-model-path", help="Path to face model.")
    proc_parser.add_argument("--segmenter-model-path", help="Path to segmenter model.")
    proc_parser.add_argument(
        "--variant", choices=["selfie_multiclass_256x256", "selfie_bin_general"]
    )
    proc_parser.add_argument(
        "--matting-backend",
        choices=["mediapipe", "birefnet", "birefnet_onnx"],
        default="birefnet_onnx",
        help=(
            "Subject segmentation model. 'birefnet_onnx' is the default "
            "(faster-matting Step 1): the ONNX export of the same BiRefNet "
            "checkpoint, same weights and maths, requiring only the "
            'optional matting-onnx extra (pip install -e ".[dev,matting-onnx]") '
            "and the exported weights (scripts/export_birefnet_onnx.py). "
            "'birefnet' is the original PyTorch backend, requiring the "
            'optional matting extra (pip install -e ".[dev,matting]") and '
            "vendored weights (scripts/download_birefnet.py)."
        ),
    )
    proc_parser.add_argument(
        "--birefnet-model-dir",
        help="Path to the vendored BiRefNet model directory (PyTorch or ONNX, "
        "matching --matting-backend). Defaults to the path recorded in "
        "model-manifests/birefnet.json or birefnet_onnx.json.",
    )

    # serve-api subcommand
    serve_parser = subparsers.add_parser(
        "serve-api", help="Start the local image-engine API server."
    )
    serve_parser.add_argument(
        "--host", default="127.0.0.1", help="Host address to bind the server to."
    )
    serve_parser.add_argument(
        "--port", type=int, default=8000, help="Port to run the server on."
    )
    serve_parser.add_argument(
        "--artifact-root", help="Directory path to save job artifacts."
    )
    serve_parser.add_argument(
        "--max-upload-bytes", type=int, help="Maximum upload size in bytes."
    )
    serve_parser.add_argument(
        "--job-ttl-seconds", type=int, help="TTL in seconds for job artifacts."
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
            with open(input_path, "rb") as fb:
                data = fb.read(limits.maximum_encoded_byte_size + 1)
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
            with open(input_path, "rb") as fb:
                data = fb.read(limits.maximum_encoded_byte_size + 1)
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
            with open(input_path, "rb") as fb:
                data = fb.read(limits.maximum_encoded_byte_size + 1)
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
                    norm_result.image,
                    face,
                    face.landmarks,
                    config={"minimum_face_confidence": min(0.5, face.confidence)},
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

        # Validate output paths before running pipelines
        input_path_abs = Path(input_path).resolve()

        def validate_out_path(p_str: str) -> Path:
            p = Path(p_str).resolve()
            if p == input_path_abs:
                raise ValueError(f"Output path cannot be equal to input path: {p_str}")
            if p.exists() and not getattr(args, "overwrite", False):
                raise ValueError(
                    f"Output path already exists: {p_str}. Use --overwrite to replace it."
                )
            if not p.parent.exists():
                raise ValueError(
                    f"Parent directory for output path does not exist: {p.parent}. Please create it first."
                )
            return p

        try:
            if args.save_mask:
                validate_out_path(args.save_mask)
            if args.save_alpha:
                validate_out_path(args.save_alpha)
            if args.save_trimap:
                validate_out_path(args.save_trimap)
            if args.output_dir:
                out_dir = Path(args.output_dir).resolve()
                if out_dir == input_path_abs:
                    raise ValueError(
                        f"Output directory cannot be equal to input path: {args.output_dir}"
                    )
                for filename in ["refined_mask.png", "refined_alpha.png", "trimap.png"]:
                    target_file = out_dir / filename
                    if target_file.exists() and not getattr(args, "overwrite", False):
                        raise ValueError(
                            f"Output file already exists in output directory: {target_file}. Use --overwrite to replace it."
                        )
        except ValueError as ve:
            print(
                "Error: Invalid output path configuration. Code: CONFIGURATION_INVALID",
                file=sys.stderr,
            )
            print(f"Message: {ve}", file=sys.stderr)
            return 1

        # 1. Normalize the image input
        limits = InputLimits()  # use defaults
        try:
            with open(input_path, "rb") as fb:
                data = fb.read(limits.maximum_encoded_byte_size + 1)
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
                    norm_result.image,
                    face,
                    face.landmarks,
                    config={"minimum_face_confidence": min(0.5, face.confidence)},
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
                image=norm_result.image,
                coarse_mask=seg_result.coarse_mask,
                probability_mask=seg_result.probability_mask,
                face=face,
                config=ref_config,
                head_estimate=head_box,
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
                print("Code: REFINEMENT_PROVIDER_FAILED", file=sys.stderr)
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
        print(f"    Foreground Coverage Ratio: {ref_val.foreground_coverage_after:.4f}")
        print(f"    Edge Transition Ratio: {ref_val.edge_transition_ratio:.4f}")
        print(f"    Connectivity Improvement: {ref_val.connectivity_improvement}")

        if ref_val.issue_codes:
            print("\n  Issue Codes Detected:")
            for code in ref_val.issue_codes:
                print(f"    - {code}")

        # 10. Save files if requested
        try:

            def check_save_path(path_str: str, input_str: str, overwrite: bool) -> Path:
                p = Path(path_str).resolve()
                inp = Path(input_str).resolve()
                if p == inp:
                    raise ValueError(f"Output path cannot equal input path: {path_str}")
                if p.exists() and not overwrite:
                    raise ValueError(
                        f"Output file already exists: {path_str}. Use --overwrite to override."
                    )
                if not p.parent.exists():
                    raise ValueError(f"Parent directory does not exist: {p.parent}")
                return p

            if args.save_mask:
                p = check_save_path(args.save_mask, args.input, args.overwrite)
                ref_result.refined_binary_mask.save(p)
                print(f"  Saved refined binary mask to {p}")

            if args.save_alpha:
                p = check_save_path(args.save_alpha, args.input, args.overwrite)
                alpha_arr = (ref_result.refined_alpha_mask * 255.0).astype(np.uint8)
                alpha_img = Image.fromarray(alpha_arr, mode="L")
                alpha_img.save(p)
                print(f"  Saved refined alpha mask to {p}")

            if args.save_trimap:
                p = check_save_path(args.save_trimap, args.input, args.overwrite)
                ref_result.trimap.save(p)
                print(f"  Saved trimap to {p}")

            if args.output_dir:
                out_dir = Path(args.output_dir).resolve()
                inp = Path(args.input).resolve()
                if out_dir == inp:
                    raise ValueError(
                        f"Output directory cannot equal input path: {args.output_dir}"
                    )

                targets = ["refined_mask.png", "refined_alpha.png", "trimap.png"]
                for t in targets:
                    tp = out_dir / t
                    if tp == inp:
                        raise ValueError(
                            f"Output target file conflicts with input path: {tp}"
                        )
                    if tp.exists() and not args.overwrite:
                        raise ValueError(
                            f"Output file {t} already exists in {out_dir}. Use --overwrite to override."
                        )

                out_dir.mkdir(parents=True, exist_ok=True)
                ref_result.refined_binary_mask.save(out_dir / "refined_mask.png")

                alpha_arr = (ref_result.refined_alpha_mask * 255.0).astype(np.uint8)
                alpha_img = Image.fromarray(alpha_arr, mode="L")
                alpha_img.save(out_dir / "refined_alpha.png")

                ref_result.trimap.save(out_dir / "trimap.png")
                print(f"  Saved all refined masks to directory: {out_dir}")
        except Exception:
            logger.error("Failed to save output files", exc_info=True)
            print("Code: REFINEMENT_SAVE_FAILED", file=sys.stderr)
            print("Message: Failed to save refinement outputs.", file=sys.stderr)
            return 1

        return 0

    elif args.command == "plan-crop-mode-a":
        # 1. Parse crop configuration
        if (
            args.target_width is None
            and args.target_height is None
            and args.target_aspect_ratio is None
        ):
            print("Code: CROP_TARGET_ASPECT_MISSING", file=sys.stderr)
            print(
                "Message: Aspect ratio or target width/height must be specified.",
                file=sys.stderr,
            )
            return 1

        try:
            cfg = CropConfig(
                target_width=args.target_width,
                target_height=args.target_height,
                target_aspect_ratio=args.target_aspect_ratio,
            )
        except Exception:
            print("Code: CROP_TARGET_ASPECT_INVALID", file=sys.stderr)
            print(
                "Message: Invalid target dimensions or aspect ratio.", file=sys.stderr
            )
            return 1

        # 2. Inspect and normalize input image
        if not os.path.exists(args.input):
            print("Error: Input file not found. Code: FILE_NOT_FOUND", file=sys.stderr)
            return 1

        try:
            with open(args.input, "rb") as f_bin:
                img_data = f_bin.read()
        except Exception:
            print(
                "Error: Unable to read image file. Code: FILE_READ_FAILED",
                file=sys.stderr,
            )
            return 1

        try:
            input_path = args.input
            limits = InputLimits()
            norm_result = normalize_image_input(img_data, input_path, limits)
        except ImageInspectionError as e:
            print(f"Error: Image inspection failed. Code: {e.code}", file=sys.stderr)
            return 1
        except Exception:
            print(
                "Error: Image normalization failed. Code: IMAGE_NORMALIZATION_FAILED",
                file=sys.stderr,
            )
            return 1

        # 3. Detect faces using MediapipeFaceDetector
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

        # Locate face model path
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

        face = None
        face_detections_count = 0
        if face_model_path.exists():
            try:
                detector = MediapipeFaceDetector(
                    model_path=face_model_path,
                    expected_sha256=face_expected_sha256,
                )
                with detector:
                    face_result = detector.detect_faces(norm_result.image)
                face_detections_count = len(face_result.detections)
                if face_detections_count == 1:
                    face = face_result.detections[0]
            except Exception:
                pass

        # 4. Check face presence constraints:
        # no face -> invalid
        # multiple faces -> invalid (cannot crop a group)
        if face_detections_count == 0:
            print("Code: CROP_INPUT_INVALID", file=sys.stderr)
            print("Message: No face detected in the image.", file=sys.stderr)
            return 1
        elif face_detections_count > 1:
            print("Code: CROP_INPUT_INVALID", file=sys.stderr)
            print(
                "Message: Multiple faces detected. Cannot plan a crop for a group.",
                file=sys.stderr,
            )
            return 1

        # 5. Estimate Head Bounding Box if exactly one face
        head_box = None
        if face is not None:
            try:
                estimator = LandmarkGeometricHeadEstimator()
                head_result = estimator.estimate_head(
                    norm_result.image,
                    face,
                    face.landmarks,
                    config={"minimum_face_confidence": min(0.5, face.confidence)},
                )
                head_box = head_result.head_bounding_box
            except Exception as e:
                logger.warning("Head estimation failed", exc_info=True)
                print(
                    f"Warning: Head estimation failed ({e}). Falling back to face-only geometry.",
                    file=sys.stderr,
                )

        # 6. Run segmenter and refiner if requested and not skipped
        refined_mask = None
        if not args.skip_mask_refinement:
            try:
                # Locate segmenter model path
                model_path_str = args.segmenter_model_path
                expected_sha256 = ""

                if not model_path_str:
                    model_path_str = os.environ.get("EXAM_PHOTO_SEGMENTER_MODEL_PATH")
                    expected_sha256 = os.environ.get(
                        "EXAM_PHOTO_SEGMENTER_MODEL_SHA256", ""
                    )

                if not model_path_str:
                    manifest_path = (
                        repo_root / "model-manifests" / "subject-segmenter.json"
                    )
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, "r", encoding="utf-8") as mf:
                                manifest = json.load(mf)
                            variant_name = args.variant or manifest.get(
                                "selected_variant", "selfie_bin_general"
                            )
                            variants = manifest.get("variants", {})
                            variant = variants.get(variant_name)
                            if variant is not None:
                                filename = variant.get("filename")
                                if filename:
                                    model_path_str = "model-assets/" + filename
                                    expected_sha256 = variant.get("sha256", "")
                        except Exception:
                            pass

                if not model_path_str:
                    raise FileNotFoundError("Segmenter model path not configured.")

                model_path = Path(model_path_str)
                if not model_path.is_absolute():
                    model_path = repo_root / model_path

                if not model_path.exists():
                    raise FileNotFoundError(
                        f"Segmenter model file not found at {model_path}."
                    )

                from exam_photo.providers.refiners.morphological_refiner import (
                    MorphologicalForegroundRefiner,
                )
                from exam_photo.providers.segmenters.mediapipe_segmenter import (
                    MediapipeSubjectSegmenter,
                )

                segmenter = MediapipeSubjectSegmenter(model_path, expected_sha256)
                with segmenter:
                    seg_result = segmenter.segment_subject(norm_result.image, face=face)

                refiner = MorphologicalForegroundRefiner()
                ref_result = refiner.refine_mask(
                    image=norm_result.image,
                    coarse_mask=seg_result.coarse_mask,
                    probability_mask=seg_result.probability_mask,
                    face=face,
                    head_estimate=head_box,
                )
                refined_mask = ref_result.refined_binary_mask
            except Exception as e:
                logger.warning("Optional mask refinement failed", exc_info=True)
                print(
                    f"Warning: Optional mask refinement failed ({e}). Proceeding without mask-aware validation.",
                    file=sys.stderr,
                )

        # 7. Execute Crop Planner
        if face is None:
            print("Code: CROP_INPUT_INVALID", file=sys.stderr)
            print("Message: Face detection failed or missing.", file=sys.stderr)
            return 1

        planner = DeterministicCropPlanner()
        try:
            img_w, img_h = norm_result.image.size
            crop_result = planner.plan_crop(
                image_width=img_w,
                image_height=img_h,
                face=face,
                head_estimate=head_box,
                refined_mask=refined_mask,
                config=cfg,
            )
        except Exception:
            logger.error("Crop planning failed internally", exc_info=True)
            print("Code: CROP_PROVIDER_FAILED", file=sys.stderr)
            print("Message: Crop planner failed internally.", file=sys.stderr)
            return 1

        # 8. Output results
        crop_val = crop_result.validation
        if args.json:
            print(crop_result.model_dump_json(indent=2))
        else:
            print("Success: Foreground crop planning finished successfully.")
            if crop_val.head_estimate_unavailable:
                print("  WARNING: head estimate unavailable (using face-only geometry)")
            if crop_val.segmentation_refinement_failed_or_skipped:
                print(
                    "  WARNING: segmentation/refinement skipped or failed (mask-aware validation unavailable)"
                )
            head_avail = "true" if head_box is not None else "false"
            mask_avail = "true" if refined_mask is not None else "false"
            if refined_mask is not None:
                planning_mode = "mask-validated"
            elif head_box is not None:
                planning_mode = "head-led"
            else:
                planning_mode = "face-expanded-fallback"

            print(
                f"  Provider: {crop_result.provider_name} v{crop_result.provider_version}"
            )
            print(f"  Executable Crop Box: {crop_result.crop_box}")
            print(
                f"  Executable Crop Size: {crop_result.crop_box_width}x{crop_result.crop_box_height}"
            )
            if crop_result.ideal_crop_box is not None:
                print(f"  Ideal Crop Box: {crop_result.ideal_crop_box}")
                print(
                    f"  Ideal Crop Size: {crop_result.ideal_crop_width}x{crop_result.ideal_crop_height}"
                )
            else:
                print("  Ideal Crop Box: None")
                print("  Ideal Crop Size: None")
            print(
                f"  Padding Required: {'true' if crop_result.padding_required else 'false'}"
            )
            print(
                f"  Valid Without Padding: {'true' if crop_result.can_crop_without_padding else 'false'}"
            )
            print(f"  Head Estimate Available: {head_avail}")
            print(f"  Mask Validation Available: {mask_avail}")
            print(f"  Crop Planning Mode: {planning_mode}")
            print(f"  Target Aspect Ratio: {crop_result.target_aspect_ratio:.4f}")
            print(
                f"  Actual Crop Aspect Ratio: {crop_result.crop_box_aspect_ratio:.4f}"
            )
            print(f"  Aspect Error: {crop_result.aspect_ratio_error:.6f}")
            print(f"  Face Center X Ratio: {crop_result.face_center_x_ratio:.4f}")
            print(f"  Face Center Y Ratio: {crop_result.face_center_y_ratio:.4f}")
            if crop_result.mask_preservation_ratio is not None:
                print(
                    f"  Mask Preservation Ratio: {crop_result.mask_preservation_ratio:.4f}"
                )
            print(f"  Is Valid: {crop_val.is_valid}")
            if crop_val.issue_codes:
                print("\n  Issue Codes Detected:")
                for code in crop_val.issue_codes:
                    print(f"    - {code}")

        if not crop_val.is_valid:
            if not args.json:
                print("Error: Crop plan is invalid.", file=sys.stderr)
            return 1

        # 9. Save preview image if requested
        if args.save_preview or args.output_dir:
            try:
                # Generate preview image by cropping the source image using the clamped crop_box
                box = crop_result.crop_box
                preview_img = norm_result.image.crop(
                    (int(box.left), int(box.top), int(box.right), int(box.bottom))
                )

                def check_save_path(
                    path_str: str, input_str: str, overwrite: bool
                ) -> Path:
                    p = Path(path_str).resolve()
                    inp = Path(input_str).resolve()
                    if p == inp:
                        raise ValueError(
                            f"Output path cannot equal input path: {path_str}"
                        )
                    if p.exists() and not overwrite:
                        raise ValueError(
                            f"Output file already exists: {path_str}. Use --overwrite to override."
                        )
                    if not p.parent.exists():
                        raise ValueError(f"Parent directory does not exist: {p.parent}")
                    return p

                if args.save_preview:
                    p = check_save_path(args.save_preview, args.input, args.overwrite)
                    preview_img.save(p)
                    if not args.json:
                        print(f"  Saved crop preview image to {p}")

                if args.output_dir:
                    out_dir = Path(args.output_dir).resolve()
                    inp = Path(args.input).resolve()
                    if out_dir == inp:
                        raise ValueError(
                            f"Output directory cannot equal input path: {args.output_dir}"
                        )
                    tp = out_dir / "crop_preview.png"
                    if tp == inp:
                        raise ValueError(
                            f"Output target file conflicts with input path: {tp}"
                        )
                    if tp.exists() and not args.overwrite:
                        raise ValueError(
                            f"Output file crop_preview.png already exists in {out_dir}. Use --overwrite to override."
                        )

                    out_dir.mkdir(parents=True, exist_ok=True)
                    preview_img.save(tp)
                    if not args.json:
                        print(f"  Saved crop preview image to directory: {out_dir}")

            except Exception as e:
                logger.error("Failed to save output files", exc_info=True)
                print("Code: CROP_PROVIDER_FAILED", file=sys.stderr)
                print(f"Message: Failed to save crop preview: {e}", file=sys.stderr)
                return 1

        return 0

    elif args.command == "plan-crop-mode-b":
        # 1. Parse crop configuration
        try:
            kwargs = {}
            for field in [
                "min_width",
                "max_width",
                "min_height",
                "max_height",
                "min_aspect_ratio",
                "max_aspect_ratio",
                "target_head_height_ratio",
                "min_head_height_ratio",
                "max_head_height_ratio",
                "allow_padding",
                "allow_subject_clipping",
                "mask_preservation_threshold",
                "edge_safety_margin_px",
            ]:
                opt_val = getattr(args, field, None)
                if opt_val is not None:
                    kwargs[field] = opt_val
            cfg_b = CropModeBConfig(**kwargs)
        except Exception as e:
            print("Code: CROP_B_RANGE_INVALID", file=sys.stderr)
            print(f"Message: Invalid configuration options: {e}", file=sys.stderr)
            return 1

        # 2. Inspect and normalize input image
        if not os.path.exists(args.input):
            print("Error: Input file not found. Code: FILE_NOT_FOUND", file=sys.stderr)
            return 1

        try:
            with open(args.input, "rb") as f_bin:
                img_data = f_bin.read()
        except Exception:
            print(
                "Error: Unable to read image file. Code: FILE_READ_FAILED",
                file=sys.stderr,
            )
            return 1

        try:
            input_path = args.input
            limits = InputLimits()
            norm_result = normalize_image_input(img_data, input_path, limits)
        except ImageInspectionError as e:
            print(f"Error: Image inspection failed. Code: {e.code}", file=sys.stderr)
            return 1
        except Exception:
            print(
                "Error: Image normalization failed. Code: IMAGE_NORMALIZATION_FAILED",
                file=sys.stderr,
            )
            return 1

        # 3. Detect faces using MediapipeFaceDetector
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

        # Locate face model path
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

        face = None
        face_detections_count = 0
        if face_model_path.exists():
            try:
                detector_b = MediapipeFaceDetector(
                    model_path=face_model_path,
                    expected_sha256=face_expected_sha256,
                )
                with detector_b:
                    face_result_b = detector_b.detect_faces(norm_result.image)
                face_detections_count = len(face_result_b.detections)
                if face_detections_count == 1:
                    face = face_result_b.detections[0]
            except Exception:
                pass

        # 4. Check face presence constraints:
        # no face -> invalid
        # multiple faces -> invalid (cannot crop a group)
        if face_detections_count == 0:
            print("Code: CROP_B_INPUT_INVALID", file=sys.stderr)
            print("Message: No face detected in the image.", file=sys.stderr)
            return 1
        elif face_detections_count > 1:
            print("Code: CROP_B_INPUT_INVALID", file=sys.stderr)
            print(
                "Message: Multiple faces detected. Cannot plan a crop for a group.",
                file=sys.stderr,
            )
            return 1

        # 5. Estimate Head Bounding Box if exactly one face
        head_box = None
        if face is not None:
            try:
                estimator_b = LandmarkGeometricHeadEstimator()
                head_result_b = estimator_b.estimate_head(
                    norm_result.image,
                    face,
                    face.landmarks,
                    config={"minimum_face_confidence": min(0.5, face.confidence)},
                )
                head_box = head_result_b.head_bounding_box
            except Exception as e:
                logger.warning("Head estimation failed", exc_info=True)
                print(
                    f"Warning: Head estimation failed ({e}). Falling back to face-only geometry.",
                    file=sys.stderr,
                )

        # 6. Run segmenter and refiner if requested and not skipped
        refined_mask_b = None
        if not args.skip_mask_refinement:
            try:
                # Locate segmenter model path
                model_path_str = args.segmenter_model_path
                expected_sha256 = ""

                if not model_path_str:
                    model_path_str = os.environ.get("EXAM_PHOTO_SEGMENTER_MODEL_PATH")
                    expected_sha256 = os.environ.get(
                        "EXAM_PHOTO_SEGMENTER_MODEL_SHA256", ""
                    )

                if not model_path_str:
                    manifest_path = (
                        repo_root / "model-manifests" / "subject-segmenter.json"
                    )
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, "r", encoding="utf-8") as mf:
                                manifest = json.load(mf)
                            variant_name = args.variant or manifest.get(
                                "selected_variant", "selfie_bin_general"
                            )
                            variants = manifest.get("variants", {})
                            variant = variants.get(variant_name)
                            if variant is not None:
                                filename = variant.get("filename")
                                if filename:
                                    model_path_str = "model-assets/" + filename
                                    expected_sha256 = variant.get("sha256", "")
                        except Exception:
                            pass

                if not model_path_str:
                    raise FileNotFoundError("Segmenter model path not configured.")

                model_path = Path(model_path_str)
                if not model_path.is_absolute():
                    model_path = repo_root / model_path

                if not model_path.exists():
                    raise FileNotFoundError(
                        f"Segmenter model file not found at {model_path}."
                    )

                from exam_photo.providers.refiners.morphological_refiner import (
                    MorphologicalForegroundRefiner,
                )
                from exam_photo.providers.segmenters.mediapipe_segmenter import (
                    MediapipeSubjectSegmenter,
                )

                segmenter_b = MediapipeSubjectSegmenter(model_path, expected_sha256)
                with segmenter_b:
                    seg_result_b = segmenter_b.segment_subject(
                        norm_result.image, face=face
                    )

                refiner_b = MorphologicalForegroundRefiner()
                ref_result_b = refiner_b.refine_mask(
                    image=norm_result.image,
                    coarse_mask=seg_result_b.coarse_mask,
                    probability_mask=seg_result_b.probability_mask,
                    face=face,
                    head_estimate=head_box,
                )
                refined_mask_b = ref_result_b.refined_binary_mask
            except Exception as e:
                logger.warning("Optional mask refinement failed", exc_info=True)
                print(
                    f"Warning: Optional mask refinement failed ({e}). Proceeding without mask-aware validation.",
                    file=sys.stderr,
                )

        # 7. Execute Crop Planner
        if face is None:
            print("Code: CROP_B_INPUT_INVALID", file=sys.stderr)
            print("Message: Face detection failed or missing.", file=sys.stderr)
            return 1

        planner_b = DeterministicCropModeBPlanner()
        try:
            img_w, img_h = norm_result.image.size
            crop_result_b = planner_b.plan_crop(
                image_width=img_w,
                image_height=img_h,
                face=face,
                head_estimate=head_box,
                refined_mask=refined_mask_b,
                config=cfg_b,
            )
        except Exception as e:
            logger.error("Crop planning failed internally", exc_info=True)
            print("Code: CROP_B_PROVIDER_FAILED", file=sys.stderr)
            print(f"Message: Crop planner failed internally: {e}", file=sys.stderr)
            return 1

        # 8. Output results
        crop_val_b = crop_result_b.validation
        if args.json:
            print(crop_result_b.model_dump_json(indent=2))
        else:
            print("Success: Foreground crop planning finished successfully.")
            if crop_val_b.head_estimate_unavailable:
                print("  WARNING: head estimate unavailable (using face-only geometry)")
            if crop_val_b.segmentation_refinement_failed_or_skipped:
                print(
                    "  WARNING: segmentation/refinement skipped or failed (mask-aware validation unavailable)"
                )
            head_avail = "true" if head_box is not None else "false"
            mask_avail = "true" if refined_mask_b is not None else "false"
            if refined_mask_b is not None:
                planning_mode = "mask-validated"
            elif head_box is not None:
                planning_mode = "head-led"
            else:
                planning_mode = "face-expanded-fallback"

            print(
                f"  Provider: {crop_result_b.provider_name} v{crop_result_b.provider_version}"
            )
            print(f"  Executable Crop Box: {crop_result_b.crop_box}")
            print(
                f"  Executable Crop Size: {crop_result_b.crop_box_width}x{crop_result_b.crop_box_height}"
            )
            if crop_result_b.ideal_crop_box is not None:
                print(f"  Ideal Crop Box: {crop_result_b.ideal_crop_box}")
                print(
                    f"  Ideal Crop Size: {crop_result_b.ideal_crop_width}x{crop_result_b.ideal_crop_height}"
                )
            else:
                print("  Ideal Crop Box: None")
                print("  Ideal Crop Size: None")
            print(
                f"  Padding Required: {'true' if crop_result_b.padding_required else 'false'}"
            )
            print(
                f"  Valid Without Padding: {'true' if crop_result_b.can_crop_without_padding else 'false'}"
            )
            print(f"  Head Estimate Available: {head_avail}")
            print(f"  Mask Validation Available: {mask_avail}")
            print(f"  Crop Planning Mode: {planning_mode}")
            if crop_result_b.head_height_ratio is not None:
                print(f"  Head Height Ratio: {crop_result_b.head_height_ratio:.4f}")
            print(f"  Face Center X Ratio: {crop_result_b.face_center_x_ratio:.4f}")
            print(f"  Face Center Y Ratio: {crop_result_b.face_center_y_ratio:.4f}")
            if crop_result_b.head_coverage_ratio is not None:
                print(f"  Head Coverage Ratio: {crop_result_b.head_coverage_ratio:.4f}")
            if crop_result_b.mask_preservation_ratio is not None:
                print(
                    f"  Mask Preservation Ratio: {crop_result_b.mask_preservation_ratio:.4f}"
                )
            print(f"  Is Valid: {crop_val_b.is_valid}")
            if crop_val_b.issue_codes:
                print("\n  Issue Codes Detected:")
                for code in crop_val_b.issue_codes:
                    print(f"    - {code}")

        if not crop_val_b.is_valid:
            if not args.json:
                print("Error: Crop plan is invalid.", file=sys.stderr)
            return 1

        # 9. Save preview image if requested
        if args.save_preview or args.output_dir:
            try:
                # Generate preview image by cropping the source image using the clamped crop_box
                box = crop_result_b.crop_box
                preview_img = norm_result.image.crop(
                    (int(box.left), int(box.top), int(box.right), int(box.bottom))
                )

                def check_save_path(
                    path_str: str, input_str: str, overwrite: bool
                ) -> Path:
                    p = Path(path_str).resolve()
                    inp = Path(input_str).resolve()
                    if p == inp:
                        raise ValueError(
                            f"Output path cannot equal input path: {path_str}"
                        )
                    if p.exists() and not overwrite:
                        raise ValueError(
                            f"Output file already exists: {path_str}. Use --overwrite to override."
                        )
                    if not p.parent.exists():
                        raise ValueError(f"Parent directory does not exist: {p.parent}")
                    return p

                if args.save_preview:
                    p = check_save_path(args.save_preview, args.input, args.overwrite)
                    preview_img.save(p)
                    if not args.json:
                        print(f"  Saved crop preview image to {p}")

                if args.output_dir:
                    out_dir = Path(args.output_dir).resolve()
                    inp = Path(args.input).resolve()
                    if out_dir == inp:
                        raise ValueError(
                            f"Output directory cannot equal input path: {args.output_dir}"
                        )
                    tp = out_dir / "crop_preview.png"
                    if tp == inp:
                        raise ValueError(
                            f"Output target file conflicts with input path: {tp}"
                        )
                    if tp.exists() and not args.overwrite:
                        raise ValueError(
                            f"Output file crop_preview.png already exists in {out_dir}. Use --overwrite to override."
                        )

                    out_dir.mkdir(parents=True, exist_ok=True)
                    preview_img.save(tp)
                    if not args.json:
                        print(f"  Saved crop preview image to directory: {out_dir}")

            except Exception as e:
                logger.error("Failed to save output files", exc_info=True)
                print("Code: CROP_B_PROVIDER_FAILED", file=sys.stderr)
                print(f"Message: Failed to save crop preview: {e}", file=sys.stderr)
                return 1

        return 0

    elif args.command == "compose-background":
        # 1. Parse configuration
        try:
            kwargs = {}
            if args.target_colour:
                kwargs["target_colour_hex"] = args.target_colour
            if args.alpha_threshold is not None:
                kwargs["alpha_threshold"] = args.alpha_threshold
            if args.allow_transparent_output:
                # validation says transparent is not allowed for solid colour modes, but let's pass it
                kwargs["allow_transparent_output"] = args.allow_transparent_output
            cfg_bg = BackgroundCompositionConfig(**kwargs)
        except Exception as e:
            print("Code: BACKGROUND_CONFIG_INVALID", file=sys.stderr)
            print(f"Message: Invalid configuration options: {e}", file=sys.stderr)
            return 1

        # 2. Inspect and normalize input image
        if not os.path.exists(args.input):
            print("Error: Input file not found. Code: FILE_NOT_FOUND", file=sys.stderr)
            return 1

        try:
            with open(args.input, "rb") as f_bin:
                img_data = f_bin.read()
        except Exception:
            print(
                "Error: Unable to read image file. Code: FILE_READ_FAILED",
                file=sys.stderr,
            )
            return 1

        try:
            input_path = args.input
            limits = InputLimits()
            norm_result = normalize_image_input(img_data, input_path, limits)
        except ImageInspectionError as e:
            print(f"Error: Image inspection failed. Code: {e.code}", file=sys.stderr)
            return 1
        except Exception:
            print(
                "Error: Image normalization failed. Code: IMAGE_NORMALIZATION_FAILED",
                file=sys.stderr,
            )
            return 1

        # 3. Detect faces using MediapipeFaceDetector
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

        face = None
        face_detections_count = 0
        if face_model_path.exists():
            try:
                detector_bg = MediapipeFaceDetector(
                    model_path=face_model_path,
                    expected_sha256=face_expected_sha256,
                )
                with detector_bg:
                    face_result_bg = detector_bg.detect_faces(norm_result.image)
                face_detections_count = len(face_result_bg.detections)
                if face_detections_count == 1:
                    face = face_result_bg.detections[0]
            except Exception:
                pass

        if face_detections_count == 0:
            print("Code: BACKGROUND_INPUT_INVALID", file=sys.stderr)
            print("Message: No face detected in the image.", file=sys.stderr)
            return 1
        elif face_detections_count > 1:
            print("Code: BACKGROUND_INPUT_INVALID", file=sys.stderr)
            print(
                "Message: Multiple faces detected. Cannot compose a group.",
                file=sys.stderr,
            )
            return 1

        # 4. Estimate Head Bounding Box if exactly one face
        head_box = None
        if face is not None:
            try:
                estimator_bg = LandmarkGeometricHeadEstimator()
                head_result_bg = estimator_bg.estimate_head(
                    norm_result.image,
                    face,
                    face.landmarks,
                    config={"minimum_face_confidence": min(0.5, face.confidence)},
                )
                head_box = head_result_bg.head_bounding_box
            except Exception as e:
                logger.warning("Head estimation failed", exc_info=True)
                print(
                    f"Warning: Head estimation failed ({e}). Falling back to face-only geometry.",
                    file=sys.stderr,
                )

        # 5. Run segmenter and refiner
        refined_mask_bg = None
        try:
            model_path_str = args.segmenter_model_path
            expected_sha256 = ""

            if not model_path_str:
                model_path_str = os.environ.get("EXAM_PHOTO_SEGMENTER_MODEL_PATH")
                expected_sha256 = os.environ.get(
                    "EXAM_PHOTO_SEGMENTER_MODEL_SHA256", ""
                )

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
                        if variant is not None:
                            filename = variant.get("filename")
                            if filename:
                                model_path_str = "model-assets/" + filename
                                expected_sha256 = variant.get("sha256", "")
                    except Exception:
                        pass

            if not model_path_str:
                raise FileNotFoundError("Segmenter model path not configured.")

            model_path = Path(model_path_str)
            if not model_path.is_absolute():
                model_path = repo_root / model_path

            if not model_path.exists():
                raise FileNotFoundError(
                    f"Segmenter model file not found at {model_path}."
                )

            from exam_photo.providers.refiners.morphological_refiner import (
                MorphologicalForegroundRefiner,
            )
            from exam_photo.providers.segmenters.mediapipe_segmenter import (
                MediapipeSubjectSegmenter,
            )

            segmenter_bg = MediapipeSubjectSegmenter(model_path, expected_sha256)
            with segmenter_bg:
                seg_result_bg = segmenter_bg.segment_subject(
                    norm_result.image, face=face
                )

            refiner_bg = MorphologicalForegroundRefiner()
            ref_result_bg = refiner_bg.refine_mask(
                image=norm_result.image,
                coarse_mask=seg_result_bg.coarse_mask,
                probability_mask=seg_result_bg.probability_mask,
                face=face,
                head_estimate=head_box,
            )
            refined_mask_bg = ref_result_bg.refined_alpha_mask
        except Exception as e:
            logger.warning("Mask refinement failed", exc_info=True)
            print(
                f"Error: Mask refinement failed ({e}). Background composition requires a valid alpha mask.",
                file=sys.stderr,
            )
            return 1

        # 6. Execute Background Composer
        composer = SolidBackgroundComposer()
        try:
            bg_result = composer.compose_background(
                image=norm_result.image,
                refined_alpha_mask=refined_mask_bg,
                config=cfg_bg,
                crop_box=None,
            )
        except Exception as e:
            logger.error("Background composition failed internally", exc_info=True)
            print("Code: BACKGROUND_PROVIDER_FAILED", file=sys.stderr)
            print(
                f"Message: Background composer failed internally: {e}", file=sys.stderr
            )
            return 1

        # 7. Output results
        if args.json:
            print(bg_result.model_dump_json(indent=2))
        else:
            bg_val = bg_result.validation
            print("Success: Background composition finished successfully.")

            print(
                f"  Provider: {bg_result.provider_name} v{bg_result.provider_version}"
            )
            print(f"  Target Colour: {bg_result.target_colour_hex}")
            print(
                f"  Composed Size: {bg_result.composed_width}x{bg_result.composed_height}"
            )
            if bg_result.foreground_coverage_ratio is not None:
                print(
                    f"  Foreground Coverage: {bg_result.foreground_coverage_ratio:.4f}"
                )

            print(f"  Is Valid: {bg_val.is_valid}")
            if bg_val.issue_codes:
                print("\n  Issue Codes Detected:")
                for code in bg_val.issue_codes:
                    print(f"    - {code}")

        if not bg_val.is_valid:
            if not args.json:
                print("Error: Background composition is invalid.", file=sys.stderr)
            return 1

        # 8. Save preview image if requested
        if args.save_preview or args.output_dir:
            try:

                def check_save_path(
                    path_str: str, input_str: str, overwrite: bool
                ) -> Path:
                    p = Path(path_str).resolve()
                    inp = Path(input_str).resolve()
                    if p == inp:
                        raise ValueError(
                            f"Output path cannot equal input path: {path_str}"
                        )
                    if p.exists() and not overwrite:
                        raise ValueError(
                            f"Output file already exists: {path_str}. Use --overwrite to override."
                        )
                    if not p.parent.exists():
                        raise ValueError(f"Parent directory does not exist: {p.parent}")
                    return p

                if args.save_preview:
                    p = check_save_path(args.save_preview, args.input, args.overwrite)
                    img = bg_result.composed_image
                    if img is not None:
                        img.save(p)
                        if not args.json:
                            print(f"  Saved composed image to {p}")

                if args.output_dir:
                    out_dir = Path(args.output_dir).resolve()
                    inp = Path(args.input).resolve()
                    if out_dir == inp:
                        raise ValueError(
                            f"Output directory cannot equal input path: {args.output_dir}"
                        )
                    tp = out_dir / "composed_background.png"
                    if tp == inp:
                        raise ValueError(
                            f"Output target file conflicts with input path: {tp}"
                        )
                    if tp.exists() and not args.overwrite:
                        raise ValueError(
                            f"Output file composed_background.png already exists in {out_dir}. Use --overwrite to override."
                        )

                    out_dir.mkdir(parents=True, exist_ok=True)
                    img2 = bg_result.composed_image
                    if img2 is not None:
                        img2.save(tp)
                        if not args.json:
                            print(f"  Saved composed image to directory: {out_dir}")

            except Exception as e:
                logger.error("Failed to save output files", exc_info=True)
                print("Code: BACKGROUND_PROVIDER_FAILED", file=sys.stderr)
                print(f"Message: Failed to save composed image: {e}", file=sys.stderr)
                return 1

        return 0

    elif args.command == "prepare-output":
        input_path = args.input
        if not os.path.exists(input_path):
            print("Error: Input file not found. Code: FILE_NOT_FOUND", file=sys.stderr)
            return 1

        # 1. Normalize
        limits = InputLimits()
        try:
            with open(input_path, "rb") as fb:
                data = fb.read(limits.maximum_encoded_byte_size + 1)
        except Exception:
            print(
                "Error: Unable to read input file. Code: FILE_READ_FAILED",
                file=sys.stderr,
            )
            return 1

        try:
            norm_result = normalize_image_input(data, input_path, limits)
            current_image = norm_result.image
        except Exception:
            print(
                "Error: Image normalization failed. Code: IMAGE_NORMALIZATION_FAILED",
                file=sys.stderr,
            )
            return 1

        # Resolve face model and checksum
        face_model_path_str = args.face_model_path
        expected_face_sha = os.environ.get("EXAM_PHOTO_FACE_MODEL_SHA256", "")
        repo_root = find_repo_root()
        if not face_model_path_str:
            face_model_path_str = os.environ.get("EXAM_PHOTO_FACE_MODEL_PATH")

        if not face_model_path_str:
            manifest_path = repo_root / "model-manifests" / "face-detector.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as mf:
                        manifest = json.load(mf)
                    face_model_path_str = manifest.get("local_model_path_default")
                    expected_face_sha = manifest.get("sha256", "")
                except Exception:
                    pass
            if not face_model_path_str:
                face_model_path_str = "model-assets/blaze_face_short_range.tflite"

        face_model_path = Path(face_model_path_str)
        if not face_model_path.is_absolute():
            face_model_path = repo_root / face_model_path

        from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector

        try:
            detector = MediapipeFaceDetector(
                model_path=face_model_path, expected_sha256=expected_face_sha
            )
            with detector:
                face_res = detector.detect_faces(current_image)
            face_count = len(face_res.detections)
        except Exception as e:
            print(f"Error running face detection: {e}", file=sys.stderr)
            return 1

        if face_count != 1:
            print(
                f"Error: Output preparation requires exactly 1 face, found {face_count}. Code: INVALID_FACE_COUNT",
                file=sys.stderr,
            )
            return 1

        # 2. Optionally crop and/or compose background
        if args.crop_mode != "none" or args.background_colour:
            segmenter_model_path_str = args.segmenter_model_path
            expected_seg_sha = ""
            if not segmenter_model_path_str:
                segmenter_model_path_str = os.environ.get(
                    "EXAM_PHOTO_SEGMENTER_MODEL_PATH"
                )
                expected_seg_sha = os.environ.get(
                    "EXAM_PHOTO_SEGMENTER_MODEL_SHA256", ""
                )

            if not segmenter_model_path_str:
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
                        if variant is not None:
                            filename = variant.get("filename")
                            if filename:
                                segmenter_model_path_str = "model-assets/" + filename
                            expected_seg_sha = variant.get("sha256", "")
                    except Exception:
                        pass
                if not segmenter_model_path_str:
                    segmenter_model_path_str = (
                        "model-assets/selfie_multiclass_256x256.tflite"
                    )

            segmenter_model_path = Path(segmenter_model_path_str)
            if not segmenter_model_path.is_absolute():
                segmenter_model_path = repo_root / segmenter_model_path

            try:
                from exam_photo.providers.refiners.morphological_refiner import (
                    MorphologicalForegroundRefiner,
                )
                from exam_photo.providers.segmenters.mediapipe_segmenter import (
                    MediapipeSubjectSegmenter,
                )

                estimator = LandmarkGeometricHeadEstimator()
                head_res = estimator.estimate_head(
                    current_image,
                    face_res.detections[0],
                    face_res.detections[0].landmarks,
                )

                segmenter = MediapipeSubjectSegmenter(
                    model_path=segmenter_model_path, expected_sha256=expected_seg_sha
                )
                with segmenter:
                    seg_res = segmenter.segment_subject(
                        current_image,
                        face=face_res.detections[0],
                        head_estimate=head_res.head_bounding_box,
                        config=SegmentationConfig(),
                    )

                refiner = MorphologicalForegroundRefiner()
                ref_res = refiner.refine_mask(
                    image=current_image,
                    coarse_mask=seg_res.coarse_mask,
                    probability_mask=seg_res.probability_mask,
                    face=face_res.detections[0],
                    head_estimate=head_res.head_bounding_box,
                )

                crop_plan: CropPlanResult | CropModeBResult | None = None
                if args.crop_mode == "a":
                    if not args.target_width or not args.target_height:
                        print(
                            "Error: Crop Mode A requires target-width and target-height.",
                            file=sys.stderr,
                        )
                        return 1
                    crop_plan = DeterministicCropPlanner().plan_crop(
                        image_width=current_image.width,
                        image_height=current_image.height,
                        face=face_res.detections[0],
                        head_estimate=head_res.head_bounding_box,
                        refined_mask=ref_res.refined_binary_mask,
                        alpha_mask=ref_res.refined_alpha_mask,
                        config=CropConfig(
                            target_aspect_ratio=args.target_width / args.target_height
                        ),
                    )
                    if not crop_plan.validation.is_valid:
                        print("Error: Crop Mode A failed validation.", file=sys.stderr)
                        return 1
                    assert crop_plan is not None
                    b = crop_plan.crop_box
                    current_image = current_image.crop(
                        (int(b.left), int(b.top), int(b.right), int(b.bottom))
                    )
                    ref_res.refined_alpha_mask = ref_res.refined_alpha_mask[
                        int(b.top) : int(b.bottom), int(b.left) : int(b.right)
                    ]

                elif args.crop_mode == "b":
                    crop_plan = DeterministicCropModeBPlanner().plan_crop(
                        image_width=current_image.width,
                        image_height=current_image.height,
                        face=face_res.detections[0],
                        head_estimate=head_res.head_bounding_box,
                        refined_mask=ref_res.refined_binary_mask,
                        config=CropModeBConfig(
                            target_head_height_ratio=0.76,
                        ),
                    )
                    if not crop_plan.validation.is_valid:
                        print("Error: Crop Mode B failed validation.", file=sys.stderr)
                        return 1
                    assert crop_plan is not None
                    b = crop_plan.crop_box
                    current_image = current_image.crop(
                        (int(b.left), int(b.top), int(b.right), int(b.bottom))
                    )
                    ref_res.refined_alpha_mask = ref_res.refined_alpha_mask[
                        int(b.top) : int(b.bottom), int(b.left) : int(b.right)
                    ]

                # 3. Optionally compose background
                if args.background_colour:
                    bg_composer = SolidBackgroundComposer()
                    bg_res = bg_composer.compose_background(
                        current_image,
                        ref_res.refined_alpha_mask,
                        BackgroundCompositionConfig(
                            target_colour_hex=args.background_colour
                        ),
                    )
                    if bg_res.validation.is_valid and bg_res.composed_image is not None:
                        current_image = bg_res.composed_image

            except Exception as e:
                print(f"Error orchestrating crop/background: {e}", file=sys.stderr)
                return 1

        # 4. Prepare Output Dimensions
        config_kwargs: dict[str, Any] = {}
        if args.resize_mode == "exact":
            config_kwargs["resize_mode"] = ResizeMode.EXACT
            config_kwargs["target_width"] = args.target_width
            config_kwargs["target_height"] = args.target_height
        else:
            config_kwargs["resize_mode"] = ResizeMode.RANGE_SELECT
            config_kwargs["min_width"] = args.min_width
            config_kwargs["max_width"] = args.max_width
            config_kwargs["min_height"] = args.min_height
            config_kwargs["max_height"] = args.max_height
            config_kwargs["preferred_width"] = args.preferred_width
            config_kwargs["preferred_height"] = args.preferred_height

        if args.enhancement_mode == "conservative":
            config_kwargs["enhancement_mode"] = EnhancementMode.CONSERVATIVE
            config_kwargs["brightness_adjustment"] = args.brightness
            config_kwargs["contrast_adjustment"] = args.contrast
            config_kwargs["sharpness_adjustment"] = args.sharpness

        try:
            prep_config = OutputPreparationConfig(**config_kwargs)
        except Exception as e:
            print(
                "Error: Invalid configuration. Code: CONFIGURATION_INVALID",
                file=sys.stderr,
            )
            print(f"Details: {e}", file=sys.stderr)
            return 1

        try:
            preparer = DeterministicOutputPreparer()
            prep_result = preparer.prepare_output(current_image, prep_config)
        except Exception as e:
            print(f"Error: Output preparation failed. {e}", file=sys.stderr)
            return 1

        # 5. Print Output
        if args.json:
            print(prep_result.model_dump_json(indent=2))
        else:
            print("Output Preparation Results:")
            print(
                f"  Provider: {prep_result.provider_name} v{prep_result.provider_version}"
            )
            print(f"  Resize Mode: {prep_result.resize_mode}")
            print(
                f"  Source Size: {prep_result.source_width}x{prep_result.source_height}"
            )
            print(
                f"  Output Size: {prep_result.output_width}x{prep_result.output_height}"
            )
            print(f"  Scale X/Y: {prep_result.scale_x:.3f} / {prep_result.scale_y:.3f}")
            print(f"  Aspect Error: {prep_result.aspect_ratio_error:.4f}")
            print(f"  Output Colour Mode: {prep_result.output_colour_mode}")
            print(f"  Enhancement Mode: {prep_result.enhancement_mode}")
            print(f"  Metadata Stripped: {prep_result.metadata_stripped}")
            print(f"  Is Valid: {prep_result.validation.is_valid}")
            if prep_result.validation.issue_codes:
                print("  Issue Codes:")
                for ic in prep_result.validation.issue_codes:
                    print(f"    - {ic}")
            print(f"  Processing Duration: {prep_result.processing_duration_ms:.2f}ms")

        # 6. Save preview
        save_path = None
        if prep_result.validation.is_valid and args.save_preview:
            save_path = Path(args.save_preview)
        elif not prep_result.validation.is_valid:
            if args.save_diagnostic_preview:
                save_path = Path(args.save_diagnostic_preview)
                if not save_path.name.startswith("diagnostic_invalid_"):
                    save_path = save_path.with_name(
                        "diagnostic_invalid_" + save_path.name
                    )
            elif args.allow_invalid_preview and args.save_preview:
                save_path = Path(args.save_preview)
                if not save_path.name.startswith("diagnostic_invalid_"):
                    save_path = save_path.with_name(
                        "diagnostic_invalid_" + save_path.name
                    )

        if args.output_dir:
            out_dir = Path(args.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            if save_path:
                save_path = out_dir / save_path.name
            elif prep_result.validation.is_valid:
                save_path = out_dir / "prepared_output.png"
            elif args.allow_invalid_preview:
                save_path = out_dir / "diagnostic_invalid_prepared_output.png"

        if save_path and prep_result.output_image:
            if save_path.exists() and not args.overwrite:
                print(
                    f"Error: Output file {save_path} already exists. Use --overwrite.",
                    file=sys.stderr,
                )
                return 1
            else:
                try:
                    prep_result.output_image.save(save_path)
                    if not args.json:
                        print(f"  Saved preview image to: {save_path}")
                except Exception as e:
                    print(f"Error: Failed to save preview image: {e}", file=sys.stderr)
                    return 1

        return 0 if prep_result.validation.is_valid else 1

    elif args.command == "compress-output":
        input_path = args.input
        if not os.path.exists(input_path):
            print("Error: Input file not found. Code: FILE_NOT_FOUND", file=sys.stderr)
            return 1

        # 1. Normalize
        limits = InputLimits()
        try:
            with open(input_path, "rb") as fb:
                data = fb.read(limits.maximum_encoded_byte_size + 1)
        except Exception:
            print(
                "Error: Unable to read input file. Code: FILE_READ_FAILED",
                file=sys.stderr,
            )
            return 1

        try:
            norm_result = normalize_image_input(data, input_path, limits)
            current_image = norm_result.image
        except Exception:
            print(
                "Error: Image normalization failed. Code: IMAGE_NORMALIZATION_FAILED",
                file=sys.stderr,
            )
            return 1

        # Resolve face model and checksum
        face_model_path_str = args.face_model_path
        expected_face_sha = os.environ.get("EXAM_PHOTO_FACE_MODEL_SHA256", "")
        repo_root = find_repo_root()
        if not face_model_path_str:
            face_model_path_str = os.environ.get("EXAM_PHOTO_FACE_MODEL_PATH")

        if not face_model_path_str:
            manifest_path = repo_root / "model-manifests" / "face-detector.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as mf:
                        manifest = json.load(mf)
                    face_model_path_str = manifest.get("local_model_path_default")
                    expected_face_sha = manifest.get("sha256", "")
                except Exception:
                    pass
            if not face_model_path_str:
                face_model_path_str = "model-assets/blaze_face_short_range.tflite"

        face_model_path = Path(face_model_path_str)
        if not face_model_path.is_absolute():
            face_model_path = repo_root / face_model_path

        from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector

        try:
            detector = MediapipeFaceDetector(
                model_path=face_model_path, expected_sha256=expected_face_sha
            )
            with detector:
                face_res = detector.detect_faces(current_image)
            face_count = len(face_res.detections)
        except Exception as e:
            print(f"Error running face detection: {e}", file=sys.stderr)
            return 1

        if face_count != 1:
            print(
                f"Error: Output compression requires exactly 1 face, found {face_count}. Code: INVALID_FACE_COUNT",
                file=sys.stderr,
            )
            return 1

        # 2. Optionally crop and/or compose background
        if args.crop_mode != "none" or args.background_colour:
            segmenter_model_path_str = args.segmenter_model_path
            expected_seg_sha = ""
            if not segmenter_model_path_str:
                segmenter_model_path_str = os.environ.get(
                    "EXAM_PHOTO_SEGMENTER_MODEL_PATH"
                )
                expected_seg_sha = os.environ.get(
                    "EXAM_PHOTO_SEGMENTER_MODEL_SHA256", ""
                )

            if not segmenter_model_path_str:
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
                        if variant is not None:
                            filename = variant.get("filename")
                            if filename:
                                segmenter_model_path_str = "model-assets/" + filename
                            expected_seg_sha = variant.get("sha256", "")
                    except Exception:
                        pass
                if not segmenter_model_path_str:
                    segmenter_model_path_str = (
                        "model-assets/selfie_multiclass_256x256.tflite"
                    )

            segmenter_model_path = Path(segmenter_model_path_str)
            if not segmenter_model_path.is_absolute():
                segmenter_model_path = repo_root / segmenter_model_path

            try:
                from exam_photo.providers.refiners.morphological_refiner import (
                    MorphologicalForegroundRefiner,
                )
                from exam_photo.providers.segmenters.mediapipe_segmenter import (
                    MediapipeSubjectSegmenter,
                )

                estimator = LandmarkGeometricHeadEstimator()
                head_res = estimator.estimate_head(
                    current_image,
                    face_res.detections[0],
                    face_res.detections[0].landmarks,
                )

                segmenter = MediapipeSubjectSegmenter(
                    model_path=segmenter_model_path, expected_sha256=expected_seg_sha
                )
                with segmenter:
                    seg_res = segmenter.segment_subject(
                        current_image,
                        face=face_res.detections[0],
                        head_estimate=head_res.head_bounding_box,
                        config=SegmentationConfig(),
                    )

                refiner = MorphologicalForegroundRefiner()
                ref_res = refiner.refine_mask(
                    image=current_image,
                    coarse_mask=seg_res.coarse_mask,
                    probability_mask=seg_res.probability_mask,
                    face=face_res.detections[0],
                    head_estimate=head_res.head_bounding_box,
                )

                crop_plan = None
                if args.crop_mode == "a":
                    if not args.target_width or not args.target_height:
                        print(
                            "Error: Crop Mode A requires target-width and target-height.",
                            file=sys.stderr,
                        )
                        return 1
                    crop_plan = DeterministicCropPlanner().plan_crop(
                        image_width=current_image.width,
                        image_height=current_image.height,
                        face=face_res.detections[0],
                        head_estimate=head_res.head_bounding_box,
                        refined_mask=ref_res.refined_binary_mask,
                        alpha_mask=ref_res.refined_alpha_mask,
                        config=CropConfig(
                            target_aspect_ratio=args.target_width / args.target_height
                        ),
                    )
                    if not crop_plan.validation.is_valid:
                        print("Error: Crop Mode A failed validation.", file=sys.stderr)
                        return 1
                    assert crop_plan is not None
                    b = crop_plan.crop_box
                    current_image = current_image.crop(
                        (int(b.left), int(b.top), int(b.right), int(b.bottom))
                    )
                    ref_res.refined_alpha_mask = ref_res.refined_alpha_mask[
                        int(b.top) : int(b.bottom), int(b.left) : int(b.right)
                    ]

                elif args.crop_mode == "b":
                    crop_plan = DeterministicCropModeBPlanner().plan_crop(
                        image_width=current_image.width,
                        image_height=current_image.height,
                        face=face_res.detections[0],
                        head_estimate=head_res.head_bounding_box,
                        refined_mask=ref_res.refined_binary_mask,
                        config=CropModeBConfig(
                            target_head_height_ratio=0.76,
                        ),
                    )
                    if not crop_plan.validation.is_valid:
                        print("Error: Crop Mode B failed validation.", file=sys.stderr)
                        return 1
                    assert crop_plan is not None
                    b = crop_plan.crop_box
                    current_image = current_image.crop(
                        (int(b.left), int(b.top), int(b.right), int(b.bottom))
                    )
                    ref_res.refined_alpha_mask = ref_res.refined_alpha_mask[
                        int(b.top) : int(b.bottom), int(b.left) : int(b.right)
                    ]

                # 3. Optionally compose background
                if args.background_colour:
                    bg_composer = SolidBackgroundComposer()
                    bg_res = bg_composer.compose_background(
                        current_image,
                        ref_res.refined_alpha_mask,
                        BackgroundCompositionConfig(
                            target_colour_hex=args.background_colour
                        ),
                    )
                    if bg_res.validation.is_valid and bg_res.composed_image is not None:
                        current_image = bg_res.composed_image

            except Exception as e:
                print(f"Error orchestrating crop/background: {e}", file=sys.stderr)
                return 1

        # 4. Prepare Output Dimensions
        t_width = args.target_width or current_image.width
        t_height = args.target_height or current_image.height
        prep_config = OutputPreparationConfig(
            resize_mode=ResizeMode.EXACT,
            target_width=t_width,
            target_height=t_height,
            min_width=t_width,
            max_width=t_width,
            min_height=t_height,
            max_height=t_height,
            enhancement_mode=args.enhancement_mode,
            brightness_adjustment=args.brightness,
            contrast_adjustment=args.contrast,
            sharpness_adjustment=args.sharpness,
        )
        try:
            preparer = DeterministicOutputPreparer()
            prep_res = preparer.prepare_output(current_image, prep_config)
        except Exception as e:
            print(f"Error: Output preparation failed. {e}", file=sys.stderr)
            return 1

        if not prep_res.validation.is_valid or prep_res.output_image is None:
            print("Error: Output preparation validation failed.", file=sys.stderr)
            return 1

        prepared_image = prep_res.output_image

        # 5. Compress Output
        from exam_photo.providers.compression.deterministic_image_compressor import (
            DeterministicJpegCompressor,
        )
        from exam_photo.providers.output_compression import (
            CompressionFormat,
            OutputCompressionConfig,
        )

        try:
            comp_config = OutputCompressionConfig(
                target_format=CompressionFormat.JPEG,
                maximum_bytes=args.maximum_bytes,
                minimum_bytes=args.minimum_bytes,
                target_ceiling_ratio=args.target_ceiling_ratio,
                safety_margin_bytes=args.safety_margin_bytes,
                min_quality=args.min_quality,
                max_quality=args.max_quality,
                initial_quality=args.initial_quality,
                optimize=args.optimize,
                progressive=args.progressive,
                strip_metadata=True,
                allow_quality_below_minimum=args.allow_invalid_output,
                allow_oversize_output=args.allow_invalid_output,
            )
            compressor = DeterministicJpegCompressor()
            comp_result = compressor.compress_output(prepared_image, comp_config)
        except Exception as e:
            print(f"Error: Output compression failed. {e}", file=sys.stderr)
            return 1

        # 6. Print Output
        if args.json:
            print(comp_result.model_dump_json(indent=2))
        else:
            print("Output Compression Results:")
            print(
                f"  Provider: {comp_result.provider_name} v{comp_result.provider_version}"
            )
            print(f"  Target Format: {comp_result.target_format}")
            print(
                f"  Source Size: {comp_result.source_width}x{comp_result.source_height}"
            )
            print(f"  Maximum Bytes: {comp_result.maximum_bytes}")
            print(f"  Target Bytes: {comp_result.target_bytes}")
            print(f"  Actual Bytes: {comp_result.actual_bytes}")
            ratio_str = (
                f"{comp_result.validation.byte_size_ratio_to_max:.3f}"
                if comp_result.validation.byte_size_ratio_to_max is not None
                else "N/A"
            )
            print(f"  Byte Ratio: {ratio_str}")
            print(f"  Final Quality: {comp_result.final_quality}")
            print(f"  Iterations Used: {comp_result.iterations_used}")
            print(f"  Decode Valid: {comp_result.validation.decode_after_encode_valid}")
            print(f"  Metadata Stripped: {comp_result.validation.metadata_stripped}")
            print(f"  Is Valid: {comp_result.validation.is_valid}")
            if comp_result.validation.issue_codes:
                print("  Issue Codes:")
                for ic in comp_result.validation.issue_codes:
                    print(f"    - {ic}")
            print(f"  Processing Duration: {comp_result.processing_duration_ms:.2f}ms")

        # 7. Save output
        save_path = None
        if args.save_output:
            out_path = Path(args.save_output)
            # reject output path equal to input path
            if out_path.resolve() == Path(args.input).resolve():
                print(
                    "Error: Save path cannot be the same as input path.",
                    file=sys.stderr,
                )
                return 1

            if comp_result.validation.is_valid:
                save_path = out_path
            else:
                if args.allow_invalid_output:
                    save_path = out_path
                    if not save_path.name.startswith("diagnostic_invalid_"):
                        save_path = save_path.with_name(
                            "diagnostic_invalid_" + save_path.name
                        )
                else:
                    print(
                        "Error: Output candidate is invalid and --allow-invalid-output was not specified. Image not saved.",
                        file=sys.stderr,
                    )
                    return 1

        if args.output_dir:
            out_dir = Path(args.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            if save_path:
                save_path = out_dir / save_path.name
            elif comp_result.validation.is_valid:
                save_path = out_dir / "compressed_output.jpg"
            elif args.allow_invalid_output:
                save_path = out_dir / "diagnostic_invalid_compressed_output.jpg"

        if save_path and comp_result.encoded_bytes:
            if save_path.exists() and not args.overwrite:
                print(
                    f"Error: Output file {save_path} already exists. Use --overwrite.",
                    file=sys.stderr,
                )
                return 1
            else:
                try:
                    with open(save_path, "wb") as f_out:
                        f_out.write(comp_result.encoded_bytes)
                    if not args.json:
                        print(f"  Saved compressed output to: {save_path}")
                except Exception as e:
                    print(
                        f"Error: Failed to save compressed output: {e}", file=sys.stderr
                    )
                    return 1

        return 0 if comp_result.validation.is_valid else 1

    elif args.command == "process-rule":
        input_path = args.input
        rule_path = args.rule

        if not os.path.exists(input_path):
            print("Error: Input file not found. Code: FILE_NOT_FOUND", file=sys.stderr)
            return 1

        if not os.path.exists(rule_path):
            print("Error: Rule file not found. Code: FILE_NOT_FOUND", file=sys.stderr)
            return 1

        # Read input image bytes
        try:
            with open(input_path, "rb") as f_in:
                image_bytes = f_in.read()
        except Exception:
            print(
                "Error: Unable to read input image file. Code: FILE_READ_FAILED",
                file=sys.stderr,
            )
            return 1

        # Read rule JSON
        try:
            with open(rule_path, "r", encoding="utf-8") as f_r:
                rule_dict = json.load(f_r)
        except Exception:
            print(
                "Error: Invalid JSON syntax in rule file. Code: INVALID_JSON",
                file=sys.stderr,
            )
            return 1

        # Resolve face detector model path
        face_model_path_str = args.face_model_path
        expected_face_sha = os.environ.get("EXAM_PHOTO_FACE_MODEL_SHA256", "")
        repo_root = find_repo_root()
        if not face_model_path_str:
            face_model_path_str = os.environ.get("EXAM_PHOTO_FACE_MODEL_PATH")

        if not face_model_path_str:
            manifest_path = repo_root / "model-manifests" / "face-detector.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as mf:
                        manifest = json.load(mf)
                    face_model_path_str = manifest.get("local_model_path_default")
                    expected_face_sha = manifest.get("sha256", "")
                except Exception:
                    pass
            if not face_model_path_str:
                face_model_path_str = "model-assets/blaze_face_short_range.tflite"

        face_model_path = Path(face_model_path_str)
        if not face_model_path.is_absolute():
            face_model_path = repo_root / face_model_path

        # Resolve segmenter model path.
        #
        # The checksum is read regardless of where the path came from: the
        # segmenter refuses to load without a valid 64-character SHA-256, so
        # leaving it empty whenever --segmenter-model-path was supplied made
        # that flag impossible to use.  When neither the flag nor the
        # environment provides one, it is recovered from the manifest by
        # filename further below.
        segmenter_model_path_str = args.segmenter_model_path
        expected_seg_sha = os.environ.get("EXAM_PHOTO_SEGMENTER_MODEL_SHA256", "")
        if not segmenter_model_path_str:
            segmenter_model_path_str = os.environ.get("EXAM_PHOTO_SEGMENTER_MODEL_PATH")

        if not segmenter_model_path_str:
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
                    if variant is not None:
                        filename = variant.get("filename")
                        if filename:
                            segmenter_model_path_str = "model-assets/" + filename
                        expected_seg_sha = variant.get("sha256", "")
                except Exception:
                    pass
            if not segmenter_model_path_str:
                segmenter_model_path_str = (
                    "model-assets/selfie_multiclass_256x256.tflite"
                )

        segmenter_model_path = Path(segmenter_model_path_str)
        if not segmenter_model_path.is_absolute():
            segmenter_model_path = repo_root / segmenter_model_path

        # Recover the checksum from the manifest when an explicit path was given
        # without one, matching on the file name that was actually resolved.
        if not expected_seg_sha:
            manifest_path = repo_root / "model-manifests" / "subject-segmenter.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as mf:
                        manifest = json.load(mf)
                    for variant in (manifest.get("variants", {}) or {}).values():
                        if variant.get("filename") == segmenter_model_path.name:
                            expected_seg_sha = variant.get("sha256", "")
                            break
                except Exception:
                    pass

        # Resolve BiRefNet matting settings when selected (DEC-031, faster-matting Step 1).
        birefnet_model_dir: Optional[Path] = None
        expected_birefnet_sha = ""
        if args.matting_backend in ("birefnet", "birefnet_onnx"):
            if args.matting_backend == "birefnet":
                from exam_photo.providers.segmenters.birefnet_segmenter import (
                    load_manifest_defaults,
                )
            else:
                from exam_photo.providers.segmenters.birefnet_onnx_segmenter import (
                    load_manifest_defaults,
                )

            default_dir, _wfname, default_sha, _size = load_manifest_defaults(repo_root)
            birefnet_model_dir = (
                Path(args.birefnet_model_dir)
                if args.birefnet_model_dir
                else default_dir
            )
            expected_birefnet_sha = default_sha

        # Instantiate RuleOrchestratedPipeline
        from exam_photo.orchestration.rule_pipeline import (
            RuleOrchestratedPipeline,
            RulePipelineConfig,
        )

        pipeline = RuleOrchestratedPipeline(
            face_model_path=face_model_path,
            segmenter_model_path=segmenter_model_path,
            face_expected_sha256=expected_face_sha,
            segmenter_expected_sha256=expected_seg_sha,
            matting_backend=args.matting_backend,
            birefnet_model_dir=birefnet_model_dir,
            birefnet_expected_sha256=expected_birefnet_sha,
        )

        rule_config = RulePipelineConfig(
            save_diagnostic_artifacts=args.allow_diagnostic_artifacts,
            allow_invalid_output=args.allow_invalid_output,
            allow_padding=True,
            allow_quality_below_minimum=args.allow_invalid_output,
            allow_oversize_output=args.allow_invalid_output,
            output_dir=Path(args.output_dir) if args.output_dir else None,
            quality_mode=args.quality_mode,
        )

        try:
            pipeline_result = pipeline.process_rule(image_bytes, rule_dict, rule_config)
        except Exception as e:
            print(f"Error: Pipeline processing failed. {e}", file=sys.stderr)
            return 1

        # Output Results
        if args.json:
            print(pipeline_result.model_dump_json(indent=2))
        else:
            print("Pipeline Results:")
            print(
                f"  Provider: {pipeline_result.provider_name} v{pipeline_result.provider_version}"
            )
            print(f"  Selected Crop Mode: {pipeline_result.selected_crop_mode}")
            print(
                f"  Final Dimensions: {pipeline_result.final_width}x{pipeline_result.final_height}"
            )
            print(f"  Final Format: {pipeline_result.final_format}")
            print(f"  Final Bytes: {pipeline_result.final_bytes}")
            print(f"  Final Quality: {pipeline_result.final_quality}")
            print(f"  Output Filename: {pipeline_result.output_filename}")
            print(f"  Is Valid: {pipeline_result.is_valid}")

            print("\n  Stage Reports:")
            for report in pipeline_result.stage_reports:
                print(
                    f"    - {report.stage.value}: status={report.status.value} duration={report.duration_ms:.2f}ms"
                    if report.duration_ms is not None
                    else f"    - {report.stage.value}: status={report.status.value}"
                )
                if report.issue_codes:
                    print(f"      Issues: {report.issue_codes}")

            if pipeline_result.issue_codes:
                print("\n  Pipeline Issue Codes:")
                for code in pipeline_result.issue_codes:
                    print(f"    - {code.value}")
            print(
                f"\n  Processing Duration: {pipeline_result.processing_duration_ms:.2f}ms"
            )

        # Save outputs
        if args.save_output and pipeline_result.output_filename:
            save_path = Path(pipeline_result.output_filename)
            if not pipeline_result.is_valid:
                if args.allow_invalid_output:
                    if not save_path.name.startswith("diagnostic_invalid_"):
                        save_path = save_path.with_name(
                            "diagnostic_invalid_" + save_path.name
                        )
                else:
                    print(
                        "Error: Output candidate is invalid and --allow-invalid-output not specified. Image not saved.",
                        file=sys.stderr,
                    )
                    return 1

            if args.output_dir:
                out_dir = Path(args.output_dir)
                out_dir.mkdir(parents=True, exist_ok=True)
                save_path = out_dir / save_path.name

            # Check overwrite safety
            if save_path.exists() and not args.overwrite:
                print(
                    f"Error: Output file {save_path} already exists. Use --overwrite.",
                    file=sys.stderr,
                )
                return 1

            if pipeline_result.encoded_bytes:
                try:
                    with open(save_path, "wb") as f_out:
                        f_out.write(pipeline_result.encoded_bytes)
                    if not args.json:
                        print(f"  Saved candidate image to: {save_path}")
                except Exception as e:
                    print(
                        f"Error: Failed to save candidate image: {e}", file=sys.stderr
                    )
                    return 1

        # Save execution report if requested
        if args.save_report and args.output_dir:
            report_name = "processing_report.json"
            if not pipeline_result.is_valid:
                report_name = "diagnostic_invalid_processing_report.json"

            out_dir = Path(args.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            report_path = out_dir / report_name

            if report_path.exists() and not args.overwrite:
                print(
                    f"Error: Report file {report_path} already exists. Use --overwrite.",
                    file=sys.stderr,
                )
                return 1

            try:
                with open(report_path, "w", encoding="utf-8") as f_rep:
                    f_rep.write(pipeline_result.model_dump_json(indent=2))
                if not args.json:
                    print(f"  Saved execution report to: {report_path}")
            except Exception as e:
                print(f"Error: Failed to save execution report: {e}", file=sys.stderr)
                return 1

        return 0 if pipeline_result.is_valid else 1

    elif args.command == "serve-api":
        if args.host == "0.0.0.0":
            print(
                "WARNING: Binding to 0.0.0.0 allows external network access to this dev server.",
                file=sys.stderr,
            )
            print(
                "Ensure you have proper firewall configuration or run in a trusted network environment.",
                file=sys.stderr,
            )

        if args.artifact_root:
            os.environ["EXAM_PHOTO_ARTIFACT_ROOT"] = args.artifact_root
        if args.max_upload_bytes is not None:
            os.environ["EXAM_PHOTO_MAX_UPLOAD_BYTES"] = str(args.max_upload_bytes)
        if args.job_ttl_seconds is not None:
            os.environ["EXAM_PHOTO_JOB_TTL_SECONDS"] = str(args.job_ttl_seconds)

        import uvicorn

        from exam_photo.api.app import app

        try:
            uvicorn.run(app, host=args.host, port=args.port)
            return 0
        except Exception as e:
            print(f"Error starting API server: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
