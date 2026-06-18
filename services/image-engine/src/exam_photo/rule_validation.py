import json
import os
from typing import Any, Dict, List

import jsonschema
from pydantic import ValidationError

from exam_photo.models.exam_rule import ExamRule
from exam_photo.models.validation_error import ErrorSeverity, ValidationErrorModel


def format_field_path(loc: tuple[Any, ...]) -> str:
    """Formats Pydantic error path location as dot-notated or list string.

    Examples:
        ('image_requirements', 'dimensions', 'width_px') -> 'image_requirements.dimensions.width_px'
        ('source_evidence', 0, 'source_url') -> 'source_evidence[0].source_url'
    """
    path = []
    for item in loc:
        if isinstance(item, int):
            path.append(f"[{item}]")
        else:
            if path and not path[-1].endswith("]"):
                path.append(f".{item}")
            else:
                path.append(str(item))
    return "".join(path)


def validate_exam_rule(rule_dict: Dict[str, Any]) -> List[ValidationErrorModel]:
    """Validates an examination rule dictionary against canonical constraints.

    Returns a list of structured ValidationErrorModel failure summaries.
    """
    errors: List[ValidationErrorModel] = []

    # 1. Validate against the canonical JSON Schema
    schema_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "..",
            "packages",
            "exam-rules",
            "schema",
            "exam-rule.schema.json",
        )
    )

    if os.path.exists(schema_path):
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
            validator = jsonschema.Draft202012Validator(
                schema_data, format_checker=jsonschema.FormatChecker()
            )
            for err in validator.iter_errors(rule_dict):
                field_path = format_field_path(tuple(err.absolute_path))
                errors.append(
                    ValidationErrorModel(
                        error_code="RULE_VALIDATION_SCHEMA_ERROR",
                        field_path=field_path,
                        message=err.message,
                        severity=ErrorSeverity.ERROR,
                        suggested_resolution="Correct the field value to match the JSON Schema specifications.",
                    )
                )
        except Exception as e:
            errors.append(
                ValidationErrorModel(
                    error_code="RULE_VALIDATION_SCHEMA_UNAVAILABLE",
                    field_path="",
                    message=f"Could not load or parse canonical JSON Schema: {str(e)}",
                    severity=ErrorSeverity.ERROR,
                    suggested_resolution="Verify the integrity of the JSON Schema file.",
                )
            )
    else:
        # If the schema file is not found, log a warning/error
        errors.append(
            ValidationErrorModel(
                error_code="RULE_VALIDATION_SCHEMA_UNAVAILABLE",
                field_path="",
                message=f"Canonical JSON Schema not found at {schema_path}",
                severity=ErrorSeverity.ERROR,
                suggested_resolution="Ensure packages/exam-rules/schema/exam-rule.schema.json exists.",
            )
        )

    # 2. Validate using Pydantic models (for strict fields, cross-field checks)
    try:
        # Load and validate with Pydantic
        ExamRule(**rule_dict)
    except ValidationError as e:
        for err in e.errors():
            loc = err.get("loc", ())
            msg = err.get("msg", "Validation failed")
            err_type = err.get("type", "value_error")
            field_path = format_field_path(loc)

            # Generate stable error code
            error_code = f"RULE_VALIDATION_{err_type.upper().replace('.', '_')}"

            errors.append(
                ValidationErrorModel(
                    error_code=error_code,
                    field_path=field_path,
                    message=msg,
                    severity=ErrorSeverity.ERROR,
                    suggested_resolution="Correct the field value in the JSON configuration document.",
                )
            )
    return errors
