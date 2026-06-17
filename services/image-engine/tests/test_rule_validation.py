import json
import os

from exam_photo.rule_validation import validate_exam_rule

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
EXAMPLES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "examples", "rules"
)


from typing import Any


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        val: dict[str, Any] = json.load(f)
        return val


# --- Example Records Conformance Tests ---


def test_examples_comply_with_schema() -> None:
    for name in [
        "sample_exact_dimensions.json",
        "sample_dimension_range.json",
        "sample_unspecified_dimensions.json",
    ]:
        path = os.path.join(EXAMPLES_DIR, name)
        data = load_json(path)
        errors = validate_exam_rule(data)
        assert not errors, f"Example {name} has validation errors: {errors}"


# --- Valid Records Tests ---


def test_valid_base_fixture() -> None:
    data = load_json(os.path.join(FIXTURES_DIR, "valid_base.json"))
    errors = validate_exam_rule(data)
    assert not errors


# --- Invalid Dimensions Tests ---


def test_invalid_width_no_height() -> None:
    data = load_json(os.path.join(FIXTURES_DIR, "invalid_width_no_height.json"))
    errors = validate_exam_rule(data)
    assert len(errors) >= 1
    assert any("dimensions" in err.field_path for err in errors)


def test_invalid_min_gt_max() -> None:
    data = load_json(os.path.join(FIXTURES_DIR, "invalid_min_gt_max.json"))
    errors = validate_exam_rule(data)
    assert len(errors) >= 1
    assert any(
        "minimum_width_px" in err.field_path or "dimensions" in err.field_path
        for err in errors
    )


# --- Invalid File Sizes Tests ---


def test_invalid_safety_margin() -> None:
    data = load_json(os.path.join(FIXTURES_DIR, "invalid_safety_margin.json"))
    errors = validate_exam_rule(data)
    assert len(errors) >= 1
    assert any(
        "safety_margin_bytes" in err.field_path or "file_size" in err.field_path
        for err in errors
    )


# --- Invalid Background Rules ---


def test_invalid_hex_color() -> None:
    data = load_json(os.path.join(FIXTURES_DIR, "invalid_hex_color.json"))
    errors = validate_exam_rule(data)
    assert len(errors) >= 1
    assert any("required_colour" in err.field_path for err in errors)


# --- Invalid Filename Rules ---


def test_invalid_path_traversal() -> None:
    data = load_json(os.path.join(FIXTURES_DIR, "invalid_path_traversal.json"))
    errors = validate_exam_rule(data)
    assert len(errors) >= 1
    assert any("filename" in err.field_path for err in errors)


# --- Invalid Lifecycle and Evidence ---


def test_invalid_verified_no_evidence() -> None:
    data = load_json(os.path.join(FIXTURES_DIR, "invalid_verified_no_evidence.json"))
    errors = validate_exam_rule(data)
    assert len(errors) >= 1
    # Pydantic validates source_evidence min_length=1 first
    assert any("source_evidence" in err.field_path for err in errors)


def test_invalid_fictional_verified() -> None:
    data = load_json(os.path.join(FIXTURES_DIR, "invalid_fictional_verified.json"))
    errors = validate_exam_rule(data)
    assert len(errors) >= 1
    assert any(err.field_path == "" for err in errors)


def test_strict_extra_fields_forbidden() -> None:
    data = load_json(os.path.join(FIXTURES_DIR, "valid_base.json"))
    data["exam"]["unsupported_typo_field"] = "oops"
    errors = validate_exam_rule(data)
    assert len(errors) >= 1
    assert any("unsupported_typo_field" in err.field_path for err in errors)


def test_status_conflict_verification() -> None:
    data = load_json(os.path.join(FIXTURES_DIR, "valid_base.json"))
    data["status"] = "verified"
    data["verification"]["verification_status"] = "draft"
    errors = validate_exam_rule(data)
    assert len(errors) >= 1
    assert any("conflicts with verification status" in err.message for err in errors)


def test_verified_only_secondary_sources() -> None:
    data = load_json(os.path.join(FIXTURES_DIR, "valid_base.json"))
    data["status"] = "verified"
    data["verification"]["verification_status"] = "verified"
    data["fictional_example"] = False
    for ev in data["source_evidence"]:
        ev["official_source"] = False
        ev["source_type"] = "secondary_reference"
    errors = validate_exam_rule(data)
    assert len(errors) >= 1
    assert any(
        "supported by at least one official source" in err.message for err in errors
    )


def test_invalid_provenance_keys() -> None:
    data = load_json(os.path.join(FIXTURES_DIR, "valid_base.json"))
    data["provenance"]["image_requirements.dimensions.invalid_subfield"] = {
        "type": "official",
        "evidence_reference": "http://example.com",
        "confidence": 5,
        "approved": True,
    }
    errors = validate_exam_rule(data)
    assert len(errors) >= 1
    assert any("invalid_subfield" in err.message for err in errors)


def test_invalid_format_name() -> None:
    data = load_json(os.path.join(FIXTURES_DIR, "valid_base.json"))
    data["image_requirements"]["formats"]["allowed_formats"] = ["unsupported_format"]
    data["image_requirements"]["formats"]["preferred_format"] = "unsupported_format"
    errors = validate_exam_rule(data)
    assert len(errors) >= 1
    assert any("is not a supported format" in err.message for err in errors)


def test_invalid_date_strings() -> None:
    data = load_json(os.path.join(FIXTURES_DIR, "valid_base.json"))
    data["effective_period"] = {
        "effective_from": "2026/06/17"  # Invalid format
    }
    errors = validate_exam_rule(data)
    assert len(errors) >= 1
    assert any("YYYY-MM-DD" in err.message for err in errors)


def test_invalid_lifecycle_superseded() -> None:
    data = load_json(os.path.join(FIXTURES_DIR, "valid_base.json"))
    data["status"] = "superseded"
    data["verification"]["verification_status"] = "superseded"
    # missing superseded_by_rule_id
    errors = validate_exam_rule(data)
    assert len(errors) >= 1
    assert any("must specify the replacing rule ID" in err.message for err in errors)
