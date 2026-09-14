"""The catalogue audit finds nothing it cannot explain (testing note 5, DEC-093).

Runs ``scripts/audit_catalogue.py`` over the generated records: duplicate
requirements, examinations named after a research scope, duplicate
examinations, and pixel sizes written in instructions but never read into a
file specification. Anything correct as it stands is allowed there with a
written reason; anything else fails here.
"""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
AUDIT = REPO_ROOT / "scripts" / "audit_catalogue.py"


def _load():
    spec = importlib.util.spec_from_file_location("audit_catalogue", AUDIT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_audit_finds_nothing_unexplained() -> None:
    audit = _load()
    bad = audit.unexplained(audit.audit())
    assert bad == [], "\n".join(f"{c} {e} :: {d}" for c, e, d in bad)


def test_bpsc_asks_for_its_two_signatures_and_no_more() -> None:
    import json

    record = json.loads(
        (
            REPO_ROOT / "examples" / "rules" / "exam_bpsc-online-application.json"
        ).read_text(encoding="utf-8")
    )
    signatures = [
        r for r in record["requirements"] if r["requirement_type"] == "signature"
    ]
    assert sorted(r["requirement_name"] for r in signatures) == [
        "Candidate signature (English)",
        "Candidate signature (Hindi)",
    ]
    for signature in signatures:
        dims = signature["file_spec"]["dimensions"]
        assert dims["mode"] == "range"
        assert (dims["minimum_width_px"], dims["maximum_width_px"]) == (150, 220)
        assert (dims["minimum_height_px"], dims["maximum_height_px"]) == (250, 320)


def test_the_audit_catches_what_the_owner_found() -> None:
    """Negative: the check itself must flag a duplicate and a scope name."""
    audit = _load()
    words = audit._words
    assert words("English signature") <= words("Candidate signature (English)")
    assert audit._SCOPE.search("BPSC Current Recruitment Photograph Specification")
    assert audit._SCOPE.search(
        "ICAI Examination Portal Photograph (current portal scope)"
    )
    assert not audit._SCOPE.search("BPSC Online Application")
