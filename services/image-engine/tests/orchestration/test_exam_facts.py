"""Per-examination facts, and the one property that matters (DEC-077).

The owner asked for facts a student would find *genuine, trustworthy and
helpful*. Trustworthy is the whole requirement and it rules out writing them,
so these are derived from the record's own evidence.

What is pinned here is almost entirely negative: a fact is never emitted from
a number the platform invented, never paraphrased out of the authority's own
sentence, and never contradicts another fact about the same examination. The
positive cases are cheap to satisfy and were never the risk.
"""

import glob
import json
from pathlib import Path

import pytest

from exam_photo.orchestration.exam_facts import derive_facts

RULES = Path(__file__).resolve().parents[4] / "examples" / "rules"


def _rule(**overrides):
    base = {
        "exam": {"exam_id": "test-exam", "exam_name": "Test Examination"},
        "source_evidence": [
            {"official_source": True, "source_url": "https://exam.gov.in/bulletin.pdf"}
        ],
        "image_requirements": {
            "file_size": {
                "published_maximum": 50.0,
                "published_minimum": 20.0,
                "size_unit_as_published": "kb",
            },
            "formats": {"allowed_formats": ["jpg", "jpeg"]},
            "dimensions": {"mode": "exact", "width_px": 200, "height_px": 230},
            "appearance": {},
        },
        "requirements": [],
        "provenance": {
            "image_requirements.file_size": {
                "type": "official",
                "evidence_reference": "Bulletin p2",
            },
            "image_requirements.dimensions": {
                "type": "official",
                "evidence_reference": "Bulletin p2",
            },
        },
    }
    base.update(overrides)
    return base


# ----------------------------------------------------------------------
# A fact is never built on something we made up
# ----------------------------------------------------------------------


def test_an_interim_default_produces_no_fact():
    """63 values in the catalogue are numbers the platform chose. A "fact"
    resting on one is a fabrication wearing a citation."""
    rule = _rule()
    rule["provenance"]["image_requirements.file_size"] = {"type": "interim_default"}

    kinds = {fact.kind for fact in derive_facts(rule).facts}

    assert "file_size" not in kinds


@pytest.mark.parametrize(
    "provenance", ["inferred", "platform_default", "interim_default"]
)
def test_only_official_provenance_becomes_a_fact(provenance):
    rule = _rule()
    rule["provenance"]["image_requirements.file_size"] = {"type": provenance}
    rule["provenance"]["image_requirements.dimensions"] = {"type": provenance}

    kinds = {fact.kind for fact in derive_facts(rule).facts}

    assert "file_size" not in kinds
    assert "dimensions" not in kinds


def test_a_secondary_source_produces_no_format_fact():
    """Seven examinations rest on coaching sites. They may not assert."""
    rule = _rule()
    rule["source_evidence"] = [
        {"official_source": False, "source_url": "https://coaching.example"}
    ]

    assert "format" not in {fact.kind for fact in derive_facts(rule).facts}


def test_a_record_with_nothing_official_says_nothing():
    rule = _rule(provenance={}, source_evidence=[])

    assert derive_facts(rule).facts == []


# ----------------------------------------------------------------------
# The authority's own words stay its own words
# ----------------------------------------------------------------------


def test_a_rejection_condition_is_passed_through_verbatim():
    """The paraphrase is where the meaning quietly changes."""
    published = "Applications with a blurred photograph will be rejected outright."
    rule = _rule(application_rejection_conditions=[published])

    texts = [fact.text for fact in derive_facts(rule).facts]

    assert published in texts


def test_a_requirement_condition_keeps_the_requirement_it_belongs_to():
    """A signature condition shown against the photograph is a false statement."""
    rule = _rule(
        requirements=[
            {
                "requirement_id": "candidate_signature",
                "rejection_conditions": [
                    "Signature in capital letters is not accepted."
                ],
            }
        ]
    )

    fact = next(f for f in derive_facts(rule).facts if f.kind == "rejection")

    assert fact.requirement_id == "candidate_signature"


# ----------------------------------------------------------------------
# Facts about one examination must agree with each other
# ----------------------------------------------------------------------


def test_live_capture_does_not_deny_the_upload_it_sits_beside():
    """The bug this test exists for: the first version said there was no
    photograph to upload, directly above the upload's size limit. NTA, UPSC
    and IBPS all take a live photograph *and* an upload."""
    rule = _rule()
    rule["image_requirements"]["appearance"]["live_capture_required"] = True

    facts = derive_facts(rule).facts
    capture = next(f for f in facts if f.kind == "capture")

    assert "no photograph to upload" not in capture.text.lower()
    assert "also" in capture.text.lower()
    # And the upload's own limit is still stated alongside it.
    assert any(f.kind == "file_size" for f in facts)


def test_the_same_sentence_is_not_said_twice():
    repeated = "Incomplete applications are liable to be rejected."
    rule = _rule(
        application_rejection_conditions=[repeated],
        requirements=[{"requirement_id": "photo", "rejection_conditions": [repeated]}],
    )

    texts = [f.text for f in derive_facts(rule).facts]

    assert texts.count(repeated) == 1


# ----------------------------------------------------------------------
# What the facts actually say
# ----------------------------------------------------------------------


def test_a_size_is_printed_as_the_authority_printed_it():
    """A candidate comparing our figure against the bulletin sees one number."""
    fact = next(f for f in derive_facts(_rule()).facts if f.kind == "file_size")

    assert "20 KB" in fact.text and "50 KB" in fact.text
    assert "20000" not in fact.text


def test_the_deliverable_count_is_the_products_own_observation():
    rule = _rule(requirements=[{"requirement_id": f"r{i}"} for i in range(5)])

    fact = next(f for f in derive_facts(rule).facts if f.kind == "deliverables")

    assert "5 files" in fact.text
    assert "4 more" in fact.text


def test_a_single_deliverable_gets_no_count_fact():
    """ "This asks for 1 file, not only a photograph" is nonsense."""
    rule = _rule(requirements=[{"requirement_id": "photo"}])

    assert "deliverables" not in {f.kind for f in derive_facts(rule).facts}


def test_every_fact_carries_where_it_came_from():
    for fact in derive_facts(_rule(application_rejection_conditions=["X."])).facts:
        assert fact.source


# ----------------------------------------------------------------------
# Against the real catalogue
# ----------------------------------------------------------------------


def test_the_real_catalogue_produces_facts_for_almost_every_examination():
    records = sorted(glob.glob(str(RULES / "exam_*.json")))
    assert len(records) > 40

    empty = []
    for path in records:
        rule = json.loads(Path(path).read_text(encoding="utf-8"))
        if not derive_facts(rule).facts:
            empty.append(rule["exam"]["exam_name"])

    # One examination rests entirely on secondary sources and platform
    # estimates, so it has nothing it can truthfully say. That is the correct
    # outcome, not a gap to fill.
    assert len(empty) <= 2


def test_no_real_fact_is_empty_or_unattributed():
    for path in sorted(glob.glob(str(RULES / "exam_*.json"))):
        rule = json.loads(Path(path).read_text(encoding="utf-8"))
        for fact in derive_facts(rule).facts:
            assert fact.text.strip()
            assert fact.source
            assert fact.kind


def test_the_generated_sidecar_is_up_to_date():
    """A hand edit, or a rule change without a regeneration, is caught here."""
    sidecar = RULES / "candidate_facts.json"
    assert sidecar.is_file(), "run scripts/generate_exam_facts.py"

    stored = json.loads(sidecar.read_text(encoding="utf-8"))["exams"]

    for path in sorted(glob.glob(str(RULES / "exam_*.json"))):
        rule = json.loads(Path(path).read_text(encoding="utf-8"))
        derived = derive_facts(rule)
        assert derived.exam_id in stored, derived.exam_id
        assert [f["text"] for f in stored[derived.exam_id]["facts"]] == [
            f.text for f in derived.facts
        ]


# ----------------------------------------------------------------------
# Researched trivia, held to the same bar (DEC-078)
# ----------------------------------------------------------------------


def _trivia(**overrides):
    entry = {
        "kind": "volume",
        "text": "Over 2.4 million candidates registered for NEET (UG) 2025.",
        "source_url": "https://pib.gov.in/PressReleasePage.aspx?PRID=1",
        "source_title": "PIB release",
        "official_source": True,
        "as_of": "2026-09-20",
        "cycle": "2025",
    }
    entry.update(overrides)
    return entry


def _merged(**overrides):
    from exam_photo.orchestration.exam_facts import merge_researched

    return merge_researched(derive_facts(_rule()), [_trivia(**overrides)])


def test_a_properly_sourced_fact_is_folded_in():
    texts = [f.text for f in _merged().facts]

    assert "Over 2.4 million candidates registered for NEET (UG) 2025." in texts


def test_the_source_is_carried_through():
    from exam_photo.orchestration.exam_facts import merge_researched

    fact = next(
        f
        for f in merge_researched(derive_facts(_rule()), [_trivia()]).facts
        if f.kind == "volume"
    )

    assert "pib.gov.in" in fact.source
    assert "PIB release" in fact.source


@pytest.mark.parametrize(
    "broken",
    [
        {"source_url": ""},
        {"official_source": False},
        {"as_of": ""},
        {"text": "  "},
    ],
)
def test_an_unsourced_or_undated_fact_is_dropped(broken):
    """Dropped, not softened. A trivia line with no source is exactly the
    coaching-site claim this product exists to be better than."""
    assert "volume" not in {f.kind for f in _merged(**broken).facts}


def test_a_time_sensitive_fact_without_its_cycle_is_dropped():
    """A stale application window shown as current can cost a candidate the
    examination itself. It is the one fact here with that consequence."""
    assert "window" not in {f.kind for f in _merged(kind="window", cycle=None).facts}


def test_a_time_sensitive_fact_with_its_cycle_is_kept():
    assert "window" in {f.kind for f in _merged(kind="window", cycle="2025").facts}


def test_merging_nothing_changes_nothing():
    from exam_photo.orchestration.exam_facts import merge_researched

    derived = derive_facts(_rule())

    assert merge_researched(derived, None).facts == derived.facts
    assert merge_researched(derived, []).facts == derived.facts


def test_researched_trivia_never_displaces_a_derived_fact():
    from exam_photo.orchestration.exam_facts import merge_researched

    derived = derive_facts(_rule())
    merged = merge_researched(derived, [_trivia()])

    assert [f.text for f in merged.facts][: len(derived.facts)] == [
        f.text for f in derived.facts
    ]


def test_a_duplicate_of_a_derived_fact_is_not_repeated():
    from exam_photo.orchestration.exam_facts import merge_researched

    derived = derive_facts(_rule())
    existing = derived.facts[0].text
    merged = merge_researched(derived, [_trivia(text=existing)])

    assert [f.text for f in merged.facts].count(existing) == 1


def test_a_malformed_entry_does_not_break_the_merge():
    from exam_photo.orchestration.exam_facts import merge_researched

    merged = merge_researched(derive_facts(_rule()), ["not a dict", None, _trivia()])

    assert "volume" in {f.kind for f in merged.facts}
