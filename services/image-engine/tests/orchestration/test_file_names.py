"""Standard file names for files an examination does not name itself (owner, F).

An examination's published name always wins. Everything else is named
``<exam>_<file>``, so a candidate's downloads folder says which examination a
file is for, and two files of one kind in one application never collide.
"""

from __future__ import annotations

import json
from pathlib import Path

from exam_photo.models.exam_rule import ExamRule
from exam_photo.orchestration.filename_generation import (
    exam_file_prefix,
    generate_safe_filename,
    standard_file_stem,
    standard_file_stems,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
CATALOGUE = REPO_ROOT / "examples" / "rules"


def _rules() -> list[ExamRule]:
    rules = []
    for path in sorted(CATALOGUE.glob("exam_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not data.get("fictional_example"):
            rules.append(ExamRule.model_validate(data))
    return rules


def test_the_prefix_is_the_short_form_candidates_type() -> None:
    assert exam_file_prefix("neet-ug-2026", ["NEET UG", "NEET"]) == "neet-ug"


def test_a_long_alias_falls_back_to_a_trimmed_id() -> None:
    prefix = exam_file_prefix(
        "joint-entrance-examination-council-uttar-pradesh-polytechnic-entrance",
        ["Joint Entrance Examination Council Uttar Pradesh"],
    )
    assert len(prefix) <= 16
    assert not prefix.endswith("-")


def test_kinds_of_file_get_their_word() -> None:
    assert (
        standard_file_stem("neet-ug-2026", ["NEET UG"], "photograph") == "neet-ug_photo"
    )
    assert (
        standard_file_stem("neet-ug-2026", ["NEET UG"], "thumb_impression")
        == "neet-ug_thumb"
    )
    assert (
        standard_file_stem(
            "neet-ug-2026",
            ["NEET UG"],
            "certificate_scan",
            "class_x_or_equivalent_marksheet",
        )
        == "neet-ug_class-x-or-equivalent"
    )


def test_two_signatures_in_one_application_are_told_apart() -> None:
    english = standard_file_stem("x", ["BPSC"], "signature", "english_signature", 2)
    hindi = standard_file_stem("x", ["BPSC"], "signature", "hindi_signature", 2)
    assert english == "bpsc_english-signature"
    assert hindi == "bpsc_hindi-signature"


def test_every_catalogue_file_gets_a_safe_unique_name() -> None:
    for rule in _rules():
        requirements = rule.requirements or []
        stems = standard_file_stems(
            rule.exam.exam_id,
            rule.exam.aliases,
            [(r.requirement_type.value, r.requirement_id) for r in requirements],
        )
        names = list(stems.values())
        for stem in names:
            assert len(stem) <= 44, stem
            # Nothing the PII guard or the sanitiser would rewrite.
            assert generate_safe_filename(stem) == f"{stem}.jpg", stem
        assert len(names) == len(set(names)), (rule.exam.exam_id, names)


def test_names_that_still_meet_after_trimming_are_numbered() -> None:
    stems = standard_file_stems(
        "karnataka-psc",
        ["KPSC"],
        [
            ("certificate_scan", "claim_supporting_certificate_for_reservation"),
            ("certificate_scan", "claim_supporting_certificate_for_disability"),
        ],
    )
    first, second = stems.values()
    assert first != second
    assert second == f"{first}-2"
