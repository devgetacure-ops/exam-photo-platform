"""Locating the canonical JSON Schema from an installed copy (DEC-065).

The schema was resolved by walking four directories up from ``__file__``,
which lands on the repository root only in a source checkout. In a container
-- or any wheel install -- it landed in the interpreter's ``lib`` grandparent,
the schema was never found, and **every rule failed validation**. Found by
building the image and running a real photograph through it.
"""

import json
import os

import pytest

from exam_photo.rule_validation import _canonical_schema_path, validate_exam_rule

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SCHEMA = os.path.join(
    REPO_ROOT, "packages", "exam-rules", "schema", "exam-rule.schema.json"
)


def test_a_checkout_finds_the_schema_without_configuration(monkeypatch):
    monkeypatch.delenv("EXAM_PHOTO_RULE_SCHEMA_PATH", raising=False)
    monkeypatch.delenv("EXAM_PHOTO_REPO_ROOT", raising=False)

    assert os.path.exists(_canonical_schema_path())


def test_the_repository_root_is_honoured(monkeypatch, tmp_path):
    """What a container sets, and what the relative walk cannot discover."""
    monkeypatch.delenv("EXAM_PHOTO_RULE_SCHEMA_PATH", raising=False)
    planted = tmp_path / "packages" / "exam-rules" / "schema"
    planted.mkdir(parents=True)
    (planted / "exam-rule.schema.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("EXAM_PHOTO_REPO_ROOT", str(tmp_path))

    assert _canonical_schema_path() == str(planted / "exam-rule.schema.json")


def test_an_explicit_path_wins(monkeypatch, tmp_path):
    target = tmp_path / "somewhere.json"
    target.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("EXAM_PHOTO_RULE_SCHEMA_PATH", str(target))

    assert _canonical_schema_path() == str(target)


def test_a_repo_root_without_the_schema_falls_back(monkeypatch, tmp_path):
    """A wrong root must not mask a checkout that does have the file."""
    monkeypatch.delenv("EXAM_PHOTO_RULE_SCHEMA_PATH", raising=False)
    monkeypatch.setenv("EXAM_PHOTO_REPO_ROOT", str(tmp_path))

    assert os.path.exists(_canonical_schema_path())


@pytest.mark.skipif(not os.path.exists(SCHEMA), reason="schema not in this checkout")
def test_a_real_catalogue_rule_validates_when_the_root_is_set(monkeypatch):
    """The end-to-end symptom: every rule failed, so every job failed."""
    monkeypatch.delenv("EXAM_PHOTO_RULE_SCHEMA_PATH", raising=False)
    monkeypatch.setenv("EXAM_PHOTO_REPO_ROOT", REPO_ROOT)
    rule_path = os.path.join(
        REPO_ROOT, "examples", "rules", "exam_ctet_september_2026.json"
    )
    with open(rule_path, "r", encoding="utf-8") as handle:
        rule = json.load(handle)

    assert validate_exam_rule(rule) == []
