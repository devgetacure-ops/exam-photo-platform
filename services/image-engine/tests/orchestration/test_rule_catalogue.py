"""Tests for reading the encoded examination catalogue (DEC-055)."""

import json
from pathlib import Path

import pytest

from exam_photo.models.exam_rule import PlatformSupport
from exam_photo.orchestration.rule_catalogue import load_catalogue, support_counts

REPO_ROOT = Path(__file__).resolve().parents[4]
CATALOGUE_ROOT = REPO_ROOT / "examples" / "rules"


@pytest.fixture
def real_record() -> dict:
    """One real encoded record, used as the basis for temporary catalogues."""
    path = CATALOGUE_ROOT / "exam_ibps_crp_customer_service_associates_xv.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _write(root: Path, name: str, payload: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(json.dumps(payload), encoding="utf-8")


def test_loads_the_real_catalogue():
    """The shipped catalogue reads clean, with nothing unreadable."""
    catalogue = load_catalogue(CATALOGUE_ROOT)

    assert catalogue.unreadable == {}
    assert len(catalogue.entries) == 52
    entry = catalogue.get("ibps-crp-customer-service-associates-xv")
    assert entry is not None
    assert entry.rule.exam.exam_name == "IBPS CRP Customer Service Associates-XV"


def test_fictional_records_are_never_served():
    """Sample and benchmark rules are excluded by their own flag.

    They live in the same directory as the real catalogue, and a candidate must
    never be able to select one.
    """
    catalogue = load_catalogue(CATALOGUE_ROOT)

    assert all(
        entry.rule.fictional_example is False for entry in catalogue.entries.values()
    )
    assert catalogue.get("fictional-exact-300x400") is None


def test_listing_is_ordered_by_examination_name():
    catalogue = load_catalogue(CATALOGUE_ROOT)

    names = [entry.rule.exam.exam_name for entry in catalogue.listed()]
    assert names == sorted(names)


def test_a_missing_directory_is_an_empty_catalogue(tmp_path):
    catalogue = load_catalogue(tmp_path / "nothing-here")

    assert catalogue.entries == {}
    assert catalogue.unreadable == {}


def test_one_bad_record_costs_only_its_own_examination(tmp_path, real_record):
    """A malformed record must not take down the whole picker."""
    _write(tmp_path, "good.json", real_record)
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")

    invalid = json.loads(json.dumps(real_record))
    invalid["exam"]["exam_id"] = "some-other-exam"
    invalid["status"] = "verified"
    invalid["verification"]["verification_status"] = "draft"
    _write(tmp_path, "invalid.json", invalid)

    catalogue = load_catalogue(tmp_path)

    assert set(catalogue.entries) == {"ibps-crp-customer-service-associates-xv"}
    assert "broken.json" in catalogue.unreadable
    assert "invalid.json" in catalogue.unreadable
    assert "failed rule validation" in catalogue.unreadable["invalid.json"]


def test_a_duplicate_identifier_withdraws_both_records(tmp_path, real_record):
    """Serving whichever was read last would put the wrong rule at a stable URL."""
    _write(tmp_path, "first.json", real_record)
    _write(tmp_path, "second.json", real_record)

    catalogue = load_catalogue(tmp_path)

    assert catalogue.entries == {}
    assert "first.json" in catalogue.unreadable
    assert "second.json" in catalogue.unreadable


def test_a_third_claim_on_a_contested_identifier_is_also_refused(tmp_path, real_record):
    """The gap left by two colliding records is not a slot for a third."""
    _write(tmp_path, "a.json", real_record)
    _write(tmp_path, "b.json", real_record)
    _write(tmp_path, "c.json", real_record)

    catalogue = load_catalogue(tmp_path)

    assert catalogue.entries == {}
    assert set(catalogue.unreadable) == {"a.json", "b.json", "c.json"}


def test_support_counts_carry_all_five_values(real_record):
    """Zeros are present so a missing key can never be read as 'none'."""
    catalogue = load_catalogue(CATALOGUE_ROOT)
    entry = catalogue.get("ibps-crp-customer-service-associates-xv")
    assert entry is not None

    counts = support_counts(entry.rule)

    assert set(counts) == set(PlatformSupport)
    assert sum(counts.values()) == len(entry.rule.requirements or [])


def test_unavailable_examinations_are_read_from_the_encoder_sidecar():
    """KIT-002: an examination the catalogue omits is still shown, with a reason."""
    catalogue = load_catalogue(CATALOGUE_ROOT)

    names = {item.exam_name for item in catalogue.unavailable}
    assert len(catalogue.unavailable) == 83
    assert "SSC Combined Graduate Level Examination 2026" in names
    assert all(item.reason for item in catalogue.unavailable)
    assert all(item.detail for item in catalogue.unavailable)

    with_deliverables = [
        item for item in catalogue.unavailable if item.non_photograph_deliverables > 0
    ]
    # DEC-068 grew this sharply: 81 of the 83 unencodable examinations carry
    # non-photograph deliverables, 135 between them. Every one is a signature
    # or certificate the platform could prepare and cannot reach, because a
    # rule record still requires a photograph specification. That is HANDOFF's
    # open risk 4, and this assertion is the measure of how large it now is.
    assert len(with_deliverables) == 81
    assert sum(item.non_photograph_deliverables for item in with_deliverables) == 135


def test_the_sidecar_is_never_mistaken_for_a_rule_record():
    catalogue = load_catalogue(CATALOGUE_ROOT)

    assert "unavailable_examinations.json" not in catalogue.unreadable
    assert len(catalogue.entries) == 52


def test_a_catalogue_without_the_sidecar_still_serves(tmp_path, real_record):
    """Its absence is not an error; a hand-assembled directory still works."""
    _write(tmp_path, "one.json", real_record)

    catalogue = load_catalogue(tmp_path)

    assert catalogue.unavailable == []
    assert len(catalogue.entries) == 1
    assert catalogue.unreadable == {}


def test_a_broken_sidecar_is_reported_rather_than_ignored(tmp_path, real_record):
    """Present and unreadable is a real fault; silence would hide it."""
    _write(tmp_path, "one.json", real_record)
    (tmp_path / "unavailable_examinations.json").write_text(
        "{not json", encoding="utf-8"
    )

    catalogue = load_catalogue(tmp_path)

    assert catalogue.unavailable == []
    assert "unavailable_examinations.json" in catalogue.unreadable
    assert len(catalogue.entries) == 1


def test_catalogue_wide_support_totals_match_the_recorded_figures():
    """DEC-056 quotes these; if the catalogue moves, the entry must be amended."""
    catalogue = load_catalogue(CATALOGUE_ROOT)

    totals = {support: 0 for support in PlatformSupport}
    for entry in catalogue.entries.values():
        for support, count in support_counts(entry.rule).items():
            totals[support] += count

    assert sum(totals.values()) == 215
    assert totals[PlatformSupport.SUPPORTED] == 189
    assert totals[PlatformSupport.GUIDANCE_ONLY] == 16
    assert totals[PlatformSupport.PARTIALLY_SUPPORTED] == 3
    assert totals[PlatformSupport.NOT_YET_SUPPORTED] == 7
