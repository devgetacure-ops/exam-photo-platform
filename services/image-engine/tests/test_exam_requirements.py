"""The deliverable inventory and the interim-placeholder provenance state.

These two features are the data-model half of the shift from "an exam rule is a
photograph specification" to "an exam rule is everything the examination asks
for".  Both are checked here through :func:`validate_exam_rule`, which is what
the encoder, the admin console and the rule API all call, so a rule that passes
here is a rule every consumer will accept.
"""

import copy
import json
import os
import re
from typing import Any

from exam_photo.rule_validation import validate_exam_rule
from tests.helpers.fixtures import FIXTURES_DIR


def _base() -> dict[str, Any]:
    with open(os.path.join(FIXTURES_DIR, "valid_base.json"), encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return copy.deepcopy(data)


def _errors(rule: dict[str, Any]) -> list[str]:
    return [
        f"{e.field_path}: {e.message}"
        for e in validate_exam_rule(rule)
        if e.severity.value == "error"
    ]


def _photograph(**overrides: Any) -> dict[str, Any]:
    requirement = {
        "requirement_id": "candidate_photograph",
        "requirement_name": "Candidate photograph",
        "requirement_type": "photograph",
        "submission_method": "file_upload",
        "requirement_status": "mandatory",
        "platform_support": "supported",
    }
    requirement.update(overrides)
    return {k: v for k, v in requirement.items() if v is not None}


def _signature(**overrides: Any) -> dict[str, Any]:
    requirement: dict[str, Any] = {
        "requirement_id": "candidate_signature",
        "requirement_name": "Candidate signature",
        "requirement_type": "signature",
        "submission_method": "handwritten_then_uploaded",
        "requirement_status": "mandatory",
        "platform_support": "supported",
        "file_spec": {
            "file_size": {"minimum_bytes": 10000, "maximum_bytes": 20000},
            "formats": {"allowed_formats": ["jpg"], "preferred_format": "jpg"},
        },
    }
    requirement.update(overrides)
    return {k: v for k, v in requirement.items() if v is not None}


# --- The inventory ----------------------------------------------------------


def test_rule_without_requirements_stays_valid() -> None:
    """Every record written before the inventory existed must still load.

    Absence means the deliverable research has not been done, not that the
    photograph is the only requirement.
    """
    assert "requirements" not in _base()
    assert not _errors(_base())


def test_full_inventory_validates() -> None:
    rule = _base()
    rule["requirements"] = [
        _photograph(),
        _signature(),
        {
            "requirement_id": "live_photograph",
            "requirement_name": "Live photograph",
            "requirement_type": "photograph",
            "submission_method": "official_live_capture",
            "requirement_status": "mandatory",
            "platform_support": "guidance_only",
        },
        {
            "requirement_id": "disability_certificate",
            "requirement_name": "Disability certificate",
            "requirement_type": "certificate_scan",
            "submission_method": "document_scan_upload",
            "requirement_status": "conditional",
            "applicability": "Candidates claiming a PwBD concession or a scribe",
            "platform_support": "not_yet_supported",
        },
        {
            "requirement_id": "printed_photographs",
            "requirement_name": "Printed passport photographs",
            "requirement_type": "photograph",
            "submission_method": "physical_stage_requirement",
            "requirement_status": "mandatory",
            "platform_support": "physical_stage",
        },
    ]
    assert not _errors(rule)


def test_photograph_requirement_rejects_its_own_file_spec() -> None:
    """One photograph rule, in one place: ``image_requirements``."""
    rule = _base()
    rule["requirements"] = [
        _photograph(
            file_spec={
                "formats": {"allowed_formats": ["jpg"], "preferred_format": "jpg"}
            }
        )
    ]
    errors = _errors(rule)
    assert any("file_spec" in e for e in errors), errors


def test_duplicate_requirement_ids_rejected() -> None:
    rule = _base()
    # Both entries are individually valid, so the duplicate is the only defect
    # left for the rule-level validator to find. Pydantic stops at the first
    # failing sub-model, so a test that also breaks one of them would pass for
    # the wrong reason.
    rule["requirements"] = [
        _photograph(),
        _signature(requirement_id="candidate_photograph"),
    ]
    assert any("Duplicate requirement_id" in e for e in _errors(rule))


def test_two_uploaded_photographs_rejected() -> None:
    """A rule carries one photograph specification, so it can specify one."""
    rule = _base()
    rule["requirements"] = [
        _photograph(),
        _photograph(requirement_id="second_photograph"),
    ]
    assert any("one image_requirements block" in e for e in _errors(rule))


def test_two_photographs_allowed_when_one_is_live_capture() -> None:
    rule = _base()
    rule["requirements"] = [
        _photograph(),
        _photograph(
            requirement_id="live_photograph",
            submission_method="official_live_capture",
            platform_support="guidance_only",
        ),
    ]
    assert not _errors(rule)


# --- The boundary the product must not blur ---------------------------------


def test_live_capture_cannot_be_marked_supported() -> None:
    """An authority-controlled step is never an output the platform produces."""
    rule = _base()
    rule["requirements"] = [
        _photograph(
            requirement_id="live_photograph",
            submission_method="official_live_capture",
            platform_support="supported",
        )
    ]
    assert any("cannot be marked supported" in e for e in _errors(rule))


def test_external_identity_verification_cannot_be_partially_supported() -> None:
    rule = _base()
    rule["requirements"] = [
        {
            "requirement_id": "otr_identity",
            "requirement_name": "One-Time Registration identity input",
            "requirement_type": "identity_document",
            "submission_method": "external_identity_verification",
            "requirement_status": "mandatory",
            "platform_support": "partially_supported",
        }
    ]
    assert any("cannot be marked supported" in e for e in _errors(rule))


def test_physical_stage_support_requires_the_physical_stage_method() -> None:
    rule = _base()
    rule["requirements"] = [_signature(platform_support="physical_stage")]
    assert any("physical_stage_requirement" in e for e in _errors(rule))


def test_physical_stage_method_requires_the_physical_stage_support() -> None:
    rule = _base()
    rule["requirements"] = [
        _signature(
            submission_method="physical_stage_requirement",
            platform_support="guidance_only",
            file_spec=None,
        )
    ]
    assert any("physical_stage" in e for e in _errors(rule))


# --- "Supported" has to mean something --------------------------------------


def test_supported_deliverable_without_a_specification_rejected() -> None:
    rule = _base()
    rule["requirements"] = [_signature(file_spec=None)]
    errors = _errors(rule)
    assert any("no file size or format" in e for e in errors), errors


def test_dimensions_alone_do_not_make_a_deliverable_supported() -> None:
    """Without a format there is nothing to encode, and without a ceiling
    nothing to compress to."""
    rule = _base()
    rule["requirements"] = [
        _signature(
            file_spec={
                "dimensions": {
                    "mode": "exact",
                    "width_px": 140,
                    "height_px": 60,
                }
            }
        )
    ]
    assert any("no file size or format" in e for e in _errors(rule))


def test_unspecified_support_needs_no_specification() -> None:
    rule = _base()
    rule["requirements"] = [
        _signature(platform_support="not_yet_supported", file_spec=None)
    ]
    assert not _errors(rule)


def test_conditional_requirement_must_state_applicability() -> None:
    rule = _base()
    rule["requirements"] = [_signature(requirement_status="conditional")]
    assert any("applicability" in e for e in _errors(rule))


# --- Interim placeholders ---------------------------------------------------


def _interim_provenance(**overrides: Any) -> dict[str, Any]:
    entry = {
        "type": "interim_default",
        "reasoning": (
            "No published signature file size for this body. Standing in with "
            "the modal published specification across the researched set "
            "(10-20 KB) until the body's own figure is supplied."
        ),
        "confidence": 1,
        "approved": False,
    }
    entry.update(overrides)
    return entry


def test_interim_default_accepted_on_a_provisional_rule() -> None:
    rule = _base()
    assert rule["status"] == "provisional"
    rule["requirements"] = [_signature()]
    rule["provenance"]["requirements[0].file_spec.file_size.maximum_bytes"] = (
        _interim_provenance()
    )
    assert not _errors(rule)


def test_interim_default_requires_reasoning() -> None:
    rule = _base()
    rule["provenance"]["image_requirements.file_size.maximum_bytes"] = (
        _interim_provenance(reasoning=None)
    )
    assert any("Interim default" in e for e in _errors(rule))


def test_interim_default_cannot_claim_confidence() -> None:
    rule = _base()
    rule["provenance"]["image_requirements.file_size.maximum_bytes"] = (
        _interim_provenance(confidence=4)
    )
    assert any("confidence 1" in e for e in _errors(rule))


def test_interim_default_cannot_be_approved() -> None:
    rule = _base()
    rule["provenance"]["image_requirements.file_size.maximum_bytes"] = (
        _interim_provenance(approved=True)
    )
    assert any("cannot be approved" in e for e in _errors(rule))


def test_interim_default_blocks_verified_status() -> None:
    """The enforcement half: a placeholder cannot sit inside a verified rule."""
    for status in ("verified", "verified_with_ambiguity"):
        rule = _base()
        rule["status"] = status
        rule["verification"]["verification_status"] = status
        rule["fictional_example"] = False
        rule["source_evidence"][0]["official_source"] = True
        rule["provenance"]["image_requirements.file_size.maximum_bytes"] = (
            _interim_provenance()
        )
        errors = _errors(rule)
        assert any("interim placeholder values" in e for e in errors), (status, errors)


def test_interim_in_a_requirement_does_not_demote_the_photograph_rule() -> None:
    """``status`` is a statement about the photograph specification.

    A placeholder signature size says nothing about how well the exam's
    photograph rule is evidenced, so it must not drag the record to
    provisional.
    """
    rule = _base()
    rule["status"] = "verified"
    rule["verification"]["verification_status"] = "verified"
    rule["fictional_example"] = False
    rule["source_evidence"][0]["official_source"] = True
    rule["requirements"] = [_signature()]
    rule["provenance"]["requirements[0].file_spec.file_size.maximum_bytes"] = (
        _interim_provenance()
    )
    assert not _errors(rule)


def test_platform_default_is_still_allowed_on_a_verified_rule() -> None:
    """An interim placeholder is not the same thing as a settled policy choice,
    and only the first one blocks verification."""
    rule = _base()
    rule["status"] = "verified"
    rule["verification"]["verification_status"] = "verified"
    rule["fictional_example"] = False
    rule["source_evidence"][0]["official_source"] = True
    rule["provenance"]["image_requirements.file_size.maximum_bytes"] = {
        "type": "platform_default",
        "reasoning": "Decimal KB reading chosen as the safer of the two (DEC).",
        "confidence": 3,
        "approved": True,
    }
    assert not _errors(rule)


# --- The generated catalogue ------------------------------------------------
#
# These read the encoder's output rather than a hand-built fixture. The
# catalogue is generated from the research, so a defect in the mapping policy
# shows up here and nowhere else -- the unit tests above only prove the model
# rejects a bad record, not that the encoder stops writing one.

_CATALOGUE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "examples", "rules"
)


def _catalogue() -> list[tuple[str, dict[str, Any]]]:
    records = []
    for name in sorted(os.listdir(_CATALOGUE_DIR)):
        if not name.startswith("exam_") or not name.endswith(".json"):
            continue
        with open(os.path.join(_CATALOGUE_DIR, name), encoding="utf-8") as f:
            records.append((name, json.load(f)))
    return records


def test_every_encoded_examination_carries_an_inventory() -> None:
    records = _catalogue()
    assert records, "no generated rule records found"
    missing = [name for name, rule in records if not rule.get("requirements")]
    assert not missing, f"records with no deliverable inventory: {missing}"


def test_no_non_photograph_deliverable_claims_support_yet() -> None:
    """The engine that would prepare them is not built.

    Marking one supported on the strength of having a specification would
    promise an output nothing can produce.
    """
    claimed = [
        (name, requirement["requirement_id"])
        for name, rule in _catalogue()
        for requirement in rule["requirements"]
        if requirement["requirement_type"] != "photograph"
        and requirement["platform_support"] in ("supported", "partially_supported")
    ]
    assert not claimed, f"non-photograph deliverables claiming support: {claimed}"


def test_interim_provenance_paths_point_at_a_real_requirement() -> None:
    """A placeholder must be findable at the field it stands in for.

    The paths are built from a list index, so they go stale silently if the
    inventory is reordered without the provenance being rebuilt with it.
    """
    pattern = re.compile(r"^requirements\[(\d+)\]\.file_spec\.(.+)$")
    checked = 0
    for name, rule in _catalogue():
        for path, entry in rule["provenance"].items():
            if entry.get("type") != "interim_default":
                continue
            match = pattern.match(path)
            assert match, f"{name}: unexpected interim path {path}"
            index = int(match.group(1))
            assert index < len(rule["requirements"]), f"{name}: {path} out of range"
            spec = rule["requirements"][index].get("file_spec") or {}
            block = match.group(2).split(".")[0]
            assert block in spec, f"{name}: {path} names an absent block"
            checked += 1
    assert checked, "no interim placeholders found; the guard would pass vacuously"


def test_catalogue_records_no_interim_value_in_a_photograph_rule() -> None:
    offenders = [
        (name, path)
        for name, rule in _catalogue()
        for path, entry in rule["provenance"].items()
        if entry.get("type") == "interim_default"
        and path.startswith("image_requirements")
    ]
    assert not offenders, f"photograph specifications resting on a guess: {offenders}"
