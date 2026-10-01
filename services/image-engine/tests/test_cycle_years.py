"""The year a candidate sees is the cycle they are applying in (DEC-119)."""

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RULES = REPO_ROOT / "examples" / "rules"


def _encoder():
    spec = importlib.util.spec_from_file_location(
        "encode_exam_rules", REPO_ROOT / "scripts" / "encode_exam_rules.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_year_moves_and_a_notice_number_does_not() -> None:
    recycle = _encoder()._recycle
    assert recycle("Common Admission Test 2025", 2026) == "Common Admission Test 2026"
    assert recycle("CBSE Classes IX/XI Registration 2025-26", 2026) == (
        "CBSE Classes IX/XI Registration 2026-27"
    )
    # A month names one sitting; once the year moves it names the wrong one.
    assert recycle("UGC-NET June 2026", 2026) == "UGC-NET 2026"
    # "CEN 05/2024" is the notice's own name, not a year.
    assert recycle("RRB NTPC Graduate - CEN 05/2024", 2026) == (
        "RRB NTPC Graduate - CEN 05/2024"
    )


def test_no_examination_shows_a_year_that_has_passed() -> None:
    """What went wrong on 2 October: "Common Admission Test 2025" at checkout."""
    import re

    stale = re.compile(r"(?<![/\d])20(1\d|2[0-5])(?![\d])")
    offenders = []
    for path in sorted(RULES.glob("exam_*.json")):
        rule = json.loads(path.read_text(encoding="utf-8"))
        if rule.get("fictional_example") is not False:
            continue
        exam = rule["exam"]
        shown = [exam["exam_name"], *exam.get("aliases", [])]
        if exam["examination_year"] not in (2026, 2027) or any(
            stale.search(text) for text in shown
        ):
            offenders.append(exam["exam_id"])
    assert offenders == []


def test_an_address_never_moves_when_the_year_does() -> None:
    cat = json.loads(
        (RULES / "exam_common_admission_test_2025.json").read_text(encoding="utf-8")
    )["exam"]
    assert cat["exam_id"] == "common-admission-test-2025"
    assert cat["exam_name"] == "Common Admission Test 2026"
