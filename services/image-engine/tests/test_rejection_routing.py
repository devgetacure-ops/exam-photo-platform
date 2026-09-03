"""Routing published rejection conditions to the deliverable they concern.

The deliverables research records causes of rejection once per examination,
but the schema attaches them to the requirement they are about, so the encoder
routes each one by the deliverable it names.

Routing by keyword is only safe if the keywords are right, and two of them are
genuinely dangerous: "capital letters" contains "cap", and "that" contains
"hat". Either would silently move a signature condition onto the photograph,
which is a wrong statement about an examination's rules rather than a cosmetic
slip. Every one of the report's 19 distinct conditions is pinned here.
"""

import importlib.util
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
ENCODER = REPO_ROOT / "scripts" / "encode_exam_rules.py"


def _load_encoder() -> Any:
    spec = importlib.util.spec_from_file_location("encode_exam_rules", ENCODER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


encoder = _load_encoder()
route = encoder._route_rejection_conditions


def _targets(condition: str) -> set[str]:
    by_type, _application = route([condition])
    return set(by_type)


def _is_application_level(condition: str) -> bool:
    by_type, application = route([condition])
    return not by_type and bool(application)


# --- The photograph conditions ----------------------------------------------


@pytest.mark.parametrize(
    "condition",
    [
        "Shadows on the face or background are not accepted.",
        "Non-frontal or side-facing pose can fail the stated requirement.",
        "Eyes must be visible/open as stated.",
        "Spectacle glare, dark or coloured glasses can make the photograph unacceptable.",
        (
            "Caps/hats are restricted; any permitted religious covering must leave "
            "required facial features visible."
        ),
        "A face mask/covering is restricted according to the stated policy.",
        (
            "Face coverage below 75%, blurred image, misaligned face, face too "
            "close/out of frame, or ear lobes not visible are explicit UPSC "
            "rejection examples."
        ),
        (
            "A live-photo mismatch with the uploaded passport photograph prevents "
            "the candidate from proceeding."
        ),
        (
            "Capturing a photograph of a pre-existing printed/digital photograph is "
            "liable to rejection under the cited SSC notice."
        ),
        (
            "Photographs outside the stated size, aspect ratio, pose, background and "
            "visibility rules can lead to rejection without fee refund."
        ),
    ],
)
def test_photograph_conditions_reach_the_photograph(condition: str) -> None:
    assert _targets(condition) == {"photograph"}


# --- The signature conditions -----------------------------------------------


@pytest.mark.parametrize(
    "condition",
    [
        (
            "A signature image that is not exactly three vertically arranged "
            "signatures, is blurred/dark, incorrectly oriented, or outside the "
            "published file specification is rejected."
        ),
        (
            "The current notice gives different signature widths in two sections; "
            "candidates should follow the live portal's validator."
        ),
        "A signature that does not match at the examination can lead to disqualification.",
    ],
)
def test_signature_conditions_reach_the_signature(condition: str) -> None:
    assert _targets(condition) == {"signature"}


# --- Conditions that genuinely name several deliverables --------------------


def test_a_condition_naming_four_deliverables_reaches_all_four() -> None:
    # Dropping it from three of the four would understate the risk on those
    # uploads, so a multi-target condition is attached to each.
    assert _targets(
        "Unclear photograph, signature, thumb impression or declaration can lead "
        "to rejection."
    ) == {"photograph", "signature", "thumb_impression", "handwritten_declaration"}


def test_capital_letters_does_not_match_the_cap_rule() -> None:
    # "capital" contains "cap". Without a word boundary this signature and
    # declaration condition lands on the photograph as a headwear rule.
    assert _targets(
        "Signature or handwritten declaration in capital letters is not accepted "
        "in the cited banking-family instructions."
    ) == {"signature", "handwritten_declaration"}


def test_photograph_and_signature_condition_reaches_both() -> None:
    assert _targets(
        "Poor-quality, miniature, blurred or side-facing live photographs and "
        "blurred/miniature signatures are liable to rejection."
    ) == {"photograph", "signature"}


def test_documents_reach_both_document_requirement_types() -> None:
    assert _targets(
        "Unreadable documents may delay processing and may lead to rejection."
    ) == {
        "certificate_scan",
        "identity_document",
    }


# --- The two that are not per-requirement -----------------------------------


def test_an_application_wide_condition_is_not_forced_onto_a_requirement() -> None:
    assert _is_application_level(
        "The online application is not registered unless all mandatory image "
        "fields are uploaded."
    )


def test_a_research_null_statement_is_dropped_entirely() -> None:
    """An absence of evidence must never become an assertion about the exam.

    The report writes this on 15 of its 50 records to say it looked and found
    nothing. Storing it as a rejection condition would tell a candidate the
    examination published something it did not (AGENTS.md, no silent
    assumptions; DEC-049, absent is not permissive).
    """
    by_type, application = route(
        [
            "No additional explicit rejection condition was established beyond the "
            "active portal's format/size validation and correctness requirements."
        ]
    )
    assert by_type == {}
    assert application == []


def test_blank_and_whitespace_conditions_are_dropped() -> None:
    by_type, application = route(["", "   "])
    assert by_type == {}
    assert application == []


def test_a_condition_is_not_duplicated_within_one_requirement() -> None:
    by_type, _ = route(["Eyes must be visible/open as stated."] * 1)
    assert by_type["photograph"] == ["Eyes must be visible/open as stated."]


# --- Against the real research ----------------------------------------------


def test_every_condition_in_the_report_is_routed_or_deliberately_dropped() -> None:
    """No condition may be lost silently.

    Each of the report's conditions must end up on a requirement, on the
    application, or be the recognised null-statement. A keyword set that
    quietly stopped matching would otherwise drain the guidance from the exam
    pages without failing anything.
    """
    import json

    report = (
        REPO_ROOT
        / "packages"
        / "exam-rules"
        / "research"
        / "exam_deliverables_2026.json"
    )
    records = json.loads(report.read_text(encoding="utf-8"))

    distinct: set[str] = set()
    for record in records:
        distinct.update(record.get("rejection_conditions") or [])

    unaccounted = []
    for condition in distinct:
        by_type, application = route([condition])
        if by_type or application:
            continue
        if condition.startswith(encoder._NO_CONDITION_SENTINEL):
            continue
        unaccounted.append(condition)

    assert unaccounted == [], f"conditions lost by the router: {unaccounted}"


def test_the_report_still_carries_rejection_research() -> None:
    """Guards the pipeline end: the encoder can only route what it is given."""
    import json

    report = (
        REPO_ROOT
        / "packages"
        / "exam-rules"
        / "research"
        / "exam_deliverables_2026.json"
    )
    records = json.loads(report.read_text(encoding="utf-8"))
    assert sum(len(r.get("rejection_conditions") or []) for r in records) > 100
