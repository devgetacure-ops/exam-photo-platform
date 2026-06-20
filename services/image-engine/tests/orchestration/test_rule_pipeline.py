import io
import json
import shutil
from pathlib import Path

import pytest
from PIL import Image
from tests.helpers.fixtures import FIXTURES_DIR

from exam_photo.cli import main
from exam_photo.models.exam_rule import ExamRule
from exam_photo.orchestration.filename_generation import (
    FilenameGenerationConfig,
    generate_safe_filename,
    sanitize_filename_part,
)
from exam_photo.orchestration.final_validation import (
    validate_final_candidate,
)
from exam_photo.orchestration.rule_pipeline import (
    RuleOrchestratedPipeline,
    RulePipelineConfig,
)
from exam_photo.orchestration.rule_resolver import RuleResolutionError, resolve_rule

pytestmark = pytest.mark.mandatory_rule_pipeline

FACE_SHA = "b4578f35940bf5a1a655214a1cce5cab13eba73c1297cd78e1a04c2380b0152f"
SEG_SHA = "9ee168ec7c8f2a16c56fe8e1cfbc514974cbbb7e434051b455635f1bd1462f5c"


def find_repo_root() -> Path:
    curr = Path(__file__).resolve().parent
    for _ in range(5):
        if (curr / "AGENTS.md").exists():
            return curr
        curr = curr.parent
    return Path(__file__).resolve().parent.parent


def get_examples_dir() -> Path:
    repo_root = find_repo_root()
    candidate = repo_root / "examples" / "rules"
    if candidate.exists():
        return candidate
    raise RuntimeError("examples/rules directory not found.")


EXAMPLES_DIR = get_examples_dir()


# =====================================================================
# 1. Rule Resolver Tests
# =====================================================================


def test_rule_resolver_exact_mode():
    rule_path = EXAMPLES_DIR / "sample_exact_300x400_50kb_white_bg.json"
    with open(rule_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rule = ExamRule.model_validate(data)

    plan = resolve_rule(rule)
    assert plan.crop_mode == "a"
    assert plan.crop_config.target_width == 300
    assert plan.crop_config.target_height == 400
    assert plan.background_config.target_colour_hex == "#FFFFFF"
    assert plan.output_preparation_config.target_width == 300
    assert plan.output_preparation_config.target_height == 400
    assert plan.compression_config.maximum_bytes == 51200
    assert plan.target_filename == "exam_photo.jpg"


def test_rule_resolver_range_mode():
    rule_path = (
        EXAMPLES_DIR / "sample_range_200_300_width_230_400_height_50kb_white_bg.json"
    )
    with open(rule_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rule = ExamRule.model_validate(data)

    plan = resolve_rule(rule)
    assert plan.crop_mode == "b"
    assert plan.crop_config.min_aspect_ratio == pytest.approx(200 / 400)
    assert plan.crop_config.max_aspect_ratio == pytest.approx(300 / 230)
    assert plan.background_config.target_colour_hex == "#FFFFFF"
    assert plan.output_preparation_config.min_width == 200
    assert plan.output_preparation_config.max_width == 300
    assert plan.compression_config.maximum_bytes == 51200


def test_rule_resolver_invalid_format():
    rule_path = EXAMPLES_DIR / "sample_exact_300x400_50kb_white_bg.json"
    with open(rule_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Set preferred format to png and allowed formats to include png to pass Pydantic validation
    data["image_requirements"]["formats"]["allowed_formats"] = ["png"]
    data["image_requirements"]["formats"]["preferred_format"] = "png"
    rule = ExamRule.model_validate(data)

    with pytest.raises(RuleResolutionError) as exc:
        resolve_rule(rule)
    assert exc.value.code == "PIPELINE_FINAL_FORMAT_INVALID"


def test_rule_resolver_preserve_transparency():
    rule_path = EXAMPLES_DIR / "sample_exact_300x400_50kb_white_bg.json"
    with open(rule_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Validate first then bypass Pydantic check to test resolve_rule raises RuleResolutionError
    rule = ExamRule.model_validate(data)
    rule.image_requirements.formats.preserve_transparency = True

    with pytest.raises(RuleResolutionError) as exc:
        resolve_rule(rule)
    assert exc.value.code == "PIPELINE_FINAL_FORMAT_INVALID"


def test_rule_resolver_exact_missing_dimensions():
    rule_path = EXAMPLES_DIR / "sample_exact_300x400_50kb_white_bg.json"
    with open(rule_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rule = ExamRule.model_validate(data)
    # Set to None directly to bypass model validation
    rule.image_requirements.dimensions.width_px = None

    with pytest.raises(RuleResolutionError) as exc:
        resolve_rule(rule)
    assert exc.value.code == "PIPELINE_CROP_MODE_UNSUPPORTED"


def test_rule_resolver_range_missing_dimensions():
    rule_path = (
        EXAMPLES_DIR / "sample_range_200_300_width_230_400_height_50kb_white_bg.json"
    )
    with open(rule_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rule = ExamRule.model_validate(data)
    rule.image_requirements.dimensions.minimum_width_px = None

    with pytest.raises(RuleResolutionError) as exc:
        resolve_rule(rule)
    assert exc.value.code == "PIPELINE_CROP_MODE_UNSUPPORTED"


def test_rule_resolver_missing_required_colour():
    rule_path = EXAMPLES_DIR / "sample_exact_300x400_50kb_white_bg.json"
    with open(rule_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rule = ExamRule.model_validate(data)
    rule.image_requirements.background.required_colour = None

    with pytest.raises(RuleResolutionError) as exc:
        resolve_rule(rule)
    assert exc.value.code == "PIPELINE_BACKGROUND_FAILED"


def test_rule_resolver_traversal_filename():
    rule_path = EXAMPLES_DIR / "sample_exact_300x400_50kb_white_bg.json"
    with open(rule_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rule = ExamRule.model_validate(data)
    rule.image_requirements.filename.exact_filename = "../traversal.jpg"

    with pytest.raises(RuleResolutionError) as exc:
        resolve_rule(rule)
    assert exc.value.code == "PIPELINE_FILENAME_INVALID"


# =====================================================================
# 2. Filename Generation Tests
# =====================================================================


def test_sanitize_filename_part_valid():
    assert sanitize_filename_part("valid-name_123.jpg") == "valid-name_123.jpg"
    assert sanitize_filename_part("spaces name here") == "spaces_name_here"

    with pytest.raises(ValueError, match="Path separators or traversal sequences"):
        sanitize_filename_part("sub/dir/name.jpg")

    with pytest.raises(ValueError, match="Path separators or traversal sequences"):
        sanitize_filename_part("sub\\dir\\name.jpg")

    with pytest.raises(ValueError, match="Path separators or traversal sequences"):
        sanitize_filename_part("../traversal.jpg")


def test_generate_safe_filename_pii():
    config = FilenameGenerationConfig(base_name="safe_default", extension="jpg")

    # Email PII
    assert (
        generate_safe_filename("john.doe@gmail.com", config=config)
        == "safe_default.jpg"
    )
    # Roll number PII (6 digits with word boundaries)
    assert generate_safe_filename("roll 123456", config=config) == "safe_default.jpg"
    assert generate_safe_filename("987654321", config=config) == "safe_default.jpg"

    # Safe candidate name
    assert generate_safe_filename("john_doe_123", config=config) == "john_doe_123.jpg"


def test_generate_safe_filename_windows_reserved():
    config = FilenameGenerationConfig(base_name="safe_default", extension="jpg")
    with pytest.raises(ValueError, match="is a Windows reserved name"):
        generate_safe_filename("CON.jpg", config=config)
    with pytest.raises(ValueError, match="is a Windows reserved name"):
        generate_safe_filename("prn", config=config)


def test_generate_safe_filename_length_truncation():
    config = FilenameGenerationConfig(
        base_name="safe_default", extension="jpg", max_length=15
    )
    long_name = "verylongnameforacandidate"
    result = generate_safe_filename(long_name, config=config)
    assert result == "verylongnam.jpg"
    assert len(result) == 15


def test_generate_safe_filename_duplicates(tmp_path):
    config = FilenameGenerationConfig(base_name="exam_photo", extension="jpg")

    # First save
    f1 = generate_safe_filename(
        "candidate_photo.jpg", output_dir=tmp_path, overwrite=False, config=config
    )
    assert f1 == "candidate_photo.jpg"
    (tmp_path / f1).touch()

    # Second save (no truncation since overall base fits within 76 chars)
    f2 = generate_safe_filename(
        "candidate_photo.jpg", output_dir=tmp_path, overwrite=False, config=config
    )
    assert f2 == "candidate_photo_001.jpg"
    (tmp_path / f2).touch()

    # Third save
    f3 = generate_safe_filename(
        "candidate_photo.jpg", output_dir=tmp_path, overwrite=False, config=config
    )
    assert f3 == "candidate_photo_002.jpg"


# =====================================================================
# 3. Final Candidate Validation Tests
# =====================================================================


def test_final_validation_valid():
    from exam_photo.providers.output_compression import (
        CompressionFormat,
        OutputCompressionConfig,
    )

    config = OutputCompressionConfig(
        target_format=CompressionFormat.JPEG,
        maximum_bytes=50000,
        minimum_bytes=1000,
    )

    img = Image.new("RGB", (300, 400), "white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    report = validate_final_candidate(
        encoded_bytes=jpeg_bytes,
        expected_width=300,
        expected_height=400,
        config=config,
    )
    assert report.is_valid is True
    assert report.actual_width == 300
    assert report.actual_height == 400
    assert report.actual_format == "JPEG"
    assert report.metadata_stripped is True
    assert len(report.issue_codes) == 0


def test_final_validation_mismatch():
    from exam_photo.providers.output_compression import (
        CompressionFormat,
        OutputCompressionConfig,
    )

    config = OutputCompressionConfig(
        target_format=CompressionFormat.JPEG,
        maximum_bytes=50000,
        minimum_bytes=1000,
    )

    img = Image.new("RGB", (150, 200), "white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    report = validate_final_candidate(
        encoded_bytes=jpeg_bytes,
        expected_width=300,
        expected_height=400,
        config=config,
    )
    assert report.is_valid is False
    assert "PIPELINE_FINAL_DIMENSIONS_INVALID" in report.issue_codes


def test_final_validation_size_limit():
    from exam_photo.providers.output_compression import (
        CompressionFormat,
        OutputCompressionConfig,
    )

    config = OutputCompressionConfig(
        target_format=CompressionFormat.JPEG,
        maximum_bytes=2000,
        minimum_bytes=1000,
    )

    img = Image.new("RGB", (600, 800), "white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    jpeg_bytes = buf.getvalue()

    report = validate_final_candidate(
        encoded_bytes=jpeg_bytes,
        expected_width=600,
        expected_height=800,
        config=config,
    )
    assert report.is_valid is False
    assert "PIPELINE_FINAL_BYTE_SIZE_INVALID" in report.issue_codes


# =====================================================================
# 4. Pipeline Integration & CLI Subcommand Smoke Tests
# =====================================================================


def test_pipeline_integration_success():
    img_path = FIXTURES_DIR / "marie_curie_curly_hair.jpg"
    with open(img_path, "rb") as f:
        image_bytes = f.read()

    rule_path = EXAMPLES_DIR / "sample_exact_300x400_50kb_white_bg.json"
    with open(rule_path, "r", encoding="utf-8") as f:
        rule_dict = json.load(f)

    repo_root = find_repo_root()
    pipeline = RuleOrchestratedPipeline(
        face_model_path=repo_root / "model-assets/blaze_face_short_range.tflite",
        segmenter_model_path=repo_root / "model-assets/selfie_segmentation.tflite",
        face_expected_sha256=FACE_SHA,
        segmenter_expected_sha256=SEG_SHA,
    )

    config = RulePipelineConfig(
        save_diagnostic_artifacts=False,
        allow_invalid_output=False,
    )

    result = pipeline.process_rule(image_bytes, rule_dict, config)
    assert result.is_valid is True
    assert result.selected_crop_mode == "a"
    assert result.final_width == 300
    assert result.final_height == 400
    assert result.final_format.upper() == "JPEG"
    assert result.final_bytes is not None
    assert result.final_bytes <= 51200
    assert len(result.issue_codes) == 0


def test_pipeline_integration_range_mode():
    img_path = FIXTURES_DIR / "marie_curie_curly_hair.jpg"
    with open(img_path, "rb") as f:
        image_bytes = f.read()

    rule_path = (
        EXAMPLES_DIR / "sample_range_200_300_width_230_400_height_50kb_white_bg.json"
    )
    with open(rule_path, "r", encoding="utf-8") as f:
        rule_dict = json.load(f)

    repo_root = find_repo_root()
    pipeline = RuleOrchestratedPipeline(
        face_model_path=repo_root / "model-assets/blaze_face_short_range.tflite",
        segmenter_model_path=repo_root / "model-assets/selfie_segmentation.tflite",
        face_expected_sha256=FACE_SHA,
        segmenter_expected_sha256=SEG_SHA,
    )

    config = RulePipelineConfig(
        save_diagnostic_artifacts=False,
        allow_invalid_output=False,
    )

    result = pipeline.process_rule(image_bytes, rule_dict, config)
    assert result.is_valid is True
    assert result.selected_crop_mode == "b"
    assert 200 <= result.final_width <= 300
    assert 230 <= result.final_height <= 400
    assert result.final_format.upper() == "JPEG"
    assert result.final_bytes <= 51200
    assert len(result.issue_codes) == 0


def test_pipeline_integration_invalid_no_face():
    img_path = FIXTURES_DIR / "blank_white_600x800.jpg"
    with open(img_path, "rb") as f:
        image_bytes = f.read()

    rule_path = EXAMPLES_DIR / "sample_exact_300x400_50kb_white_bg.json"
    with open(rule_path, "r", encoding="utf-8") as f:
        rule_dict = json.load(f)

    repo_root = find_repo_root()
    pipeline = RuleOrchestratedPipeline(
        face_model_path=repo_root / "model-assets/blaze_face_short_range.tflite",
        segmenter_model_path=repo_root / "model-assets/selfie_segmentation.tflite",
        face_expected_sha256=FACE_SHA,
        segmenter_expected_sha256=SEG_SHA,
    )

    config = RulePipelineConfig(
        save_diagnostic_artifacts=False,
        allow_invalid_output=False,
    )

    result = pipeline.process_rule(image_bytes, rule_dict, config)
    assert result.is_valid is False
    assert "PIPELINE_FACE_COUNT_INVALID" in [code.value for code in result.issue_codes]


def test_cli_process_rule_valid(tmp_path):
    img_path = FIXTURES_DIR / "marie_curie_curly_hair.jpg"
    rule_path = EXAMPLES_DIR / "sample_exact_300x400_50kb_white_bg.json"

    out_dir = tmp_path / "out_dir"
    out_dir.mkdir()

    argv = [
        "process-rule",
        "--input",
        str(img_path),
        "--rule",
        str(rule_path),
        "--output-dir",
        str(out_dir),
        "--save-output",
        "--save-report",
        "--overwrite",
    ]

    exit_code = main(argv)
    assert exit_code == 0

    expected_image = out_dir / "exam_photo.jpg"
    assert expected_image.exists()
    assert expected_image.stat().st_size <= 51200

    expected_report = out_dir / "processing_report.json"
    assert expected_report.exists()
    with open(expected_report, "r", encoding="utf-8") as f:
        rep_data = json.load(f)
    assert rep_data["is_valid"] is True


def test_cli_process_rule_invalid_save(tmp_path):
    img_path = FIXTURES_DIR / "marie_curie_curly_hair.jpg"
    rule_path = EXAMPLES_DIR / "sample_exact_300x400_50kb_white_bg.json"

    # Read the base rule and modify size floor/ceiling dynamically
    with open(rule_path, "r", encoding="utf-8") as f:
        rule_dict = json.load(f)

    # We want compression to succeed (e.g. 50 KB fits under 300 KB maximum),
    # but the rule validation to fail because the size is below 200 KB.
    rule_dict["image_requirements"]["file_size"] = {
        "minimum_bytes": 200000,  # 200 KB floor
        "maximum_bytes": 300000,  # 300 KB ceiling
        "target_ceiling_ratio": 0.95,
        "safety_margin_bytes": 2048,
    }

    temp_rule_path = tmp_path / "temp_rule.json"
    with open(temp_rule_path, "w", encoding="utf-8") as f:
        json.dump(rule_dict, f)

    out_dir = tmp_path / "out_dir"
    out_dir.mkdir()

    argv = [
        "process-rule",
        "--input",
        str(img_path),
        "--rule",
        str(temp_rule_path),
        "--output-dir",
        str(out_dir),
        "--save-output",
        "--save-report",
        "--overwrite",
    ]

    # Without --allow-invalid-output, this should fail with exit code 1 and NOT save anything
    exit_code = main(argv)
    assert exit_code == 1
    assert not (out_dir / "exam_photo.jpg").exists()
    assert not (out_dir / "diagnostic_invalid_processing_report.json").exists()

    # Clean the dir to avoid report exists issues
    shutil.rmtree(out_dir)
    out_dir.mkdir()

    # With --allow-invalid-output, it should run pipeline, return exit code 1 (since invalid),
    # but save the diagnostic image and report.
    argv_allowed = argv + ["--allow-invalid-output"]
    exit_code_allowed = main(argv_allowed)
    assert exit_code_allowed == 1

    # Image should have diagnostic prefix and exist
    assert (out_dir / "diagnostic_invalid_exam_photo.jpg").exists()
    # Report should have diagnostic prefix and exist
    assert (out_dir / "diagnostic_invalid_processing_report.json").exists()
