import io
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from exam_photo.orchestration.rule_pipeline import (
    RuleOrchestratedPipeline,
    RulePipelineConfig,
)

pytestmark = pytest.mark.mandatory_rule_pipeline

FACE_SHA = "b4578f35940bf5a1a655214a1cce5cab13eba73c1297cd78e1a04c2380b0152f"
SEG_SHA = "9ee168ec7c8f2a16c56fe8e1cfbc514974cbbb7e434051b455635f1bd1462f5c"


def find_repo_root() -> Path:
    curr = Path(__file__).resolve().parent
    for _ in range(5):
        if (curr / "AGENTS.md").exists():
            return curr
        curr = curr.parent
    return Path(__file__).resolve().parent.parent.parent.parent


def test_golden_images_regression() -> None:
    repo_root = find_repo_root()
    golden_dir = repo_root / "tests" / "golden-images"
    assert golden_dir.exists(), "golden-images directory not found"

    # Find all test cases by looking for *.rule.json
    rule_files = list(golden_dir.glob("*.rule.json"))
    assert len(rule_files) > 0, (
        "No visual regression test cases found under tests/golden-images/"
    )

    pipeline = RuleOrchestratedPipeline(
        face_model_path=repo_root / "model-assets/blaze_face_short_range.tflite",
        segmenter_model_path=repo_root / "model-assets/selfie_segmentation.tflite",
        face_expected_sha256=FACE_SHA,
        segmenter_expected_sha256=SEG_SHA,
        matting_backend="mediapipe",
    )

    config = RulePipelineConfig(
        save_diagnostic_artifacts=False,
        allow_invalid_output=False,
        allow_subject_clipping=True,
    )

    for rule_path in rule_files:
        case_id = rule_path.name.replace(".rule.json", "")

        # Determine the input image file
        input_image_path = None
        for ext in [".input.jpg", ".input.png", ".input.jpeg"]:
            candidate = golden_dir / f"{case_id}{ext}"
            if candidate.exists():
                input_image_path = candidate
                break

        assert input_image_path is not None, (
            f"Input image missing for test case {case_id}"
        )

        # Determine the golden image file
        golden_image_path = None
        for ext in [".golden.jpg", ".golden.png", ".golden.jpeg"]:
            candidate = golden_dir / f"{case_id}{ext}"
            if candidate.exists():
                golden_image_path = candidate
                break

        assert golden_image_path is not None, (
            f"Golden image missing for test case {case_id}"
        )

        # Load input image
        with open(input_image_path, "rb") as f:
            image_bytes = f.read()

        # Load rule dict
        with open(rule_path, "r", encoding="utf-8") as f:
            rule_dict = json.load(f)

        # Run pipeline
        result = pipeline.process_rule(image_bytes, rule_dict, config)
        assert result.is_valid is True, (
            f"Pipeline execution failed for test case {case_id}"
        )
        assert result.encoded_bytes is not None, (
            f"Pipeline output encoded_bytes is missing for test case {case_id}"
        )

        # Compare outputs
        golden_img = Image.open(golden_image_path)
        output_img = Image.open(io.BytesIO(result.encoded_bytes))

        # Check size match
        assert golden_img.size == output_img.size, (
            f"Size mismatch for {case_id}: expected {golden_img.size}, got {output_img.size}"
        )

        # Convert to numpy and check visual similarity using Mean Absolute Error (MAE)
        golden_arr = np.array(golden_img.convert("RGB"), dtype=np.float32)
        output_arr = np.array(output_img.convert("RGB"), dtype=np.float32)

        mae = np.mean(np.abs(golden_arr - output_arr))
        # The branch intentionally changed crop geometry and matte handling while
        # keeping this legacy public-domain fixture as a smoke regression.  Do
        # not regenerate golden processed outputs during private-photo work; keep
        # the check broad enough to catch gross breakage while exact reference
        # matching is covered by scripts/benchmark_reference_pairs.py.
        assert mae <= 25.0, (
            f"Visual regression detected for {case_id}: Mean Absolute Error (MAE) "
            f"of {mae:.4f} exceeds 25.0"
        )
