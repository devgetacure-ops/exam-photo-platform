"""An audit overlay renames records and removes duplicates, and nothing else (DEC-093)."""

import importlib.util
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = REPO_ROOT / "scripts"


def _merge() -> Any:
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "merge_research_delivery", SCRIPTS / "merge_research_delivery.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OVERLAY = {
    "rename_records": {"Old Scope Name Photograph": {"to": "New Name", "why": "scope"}},
    "remove_records": {"Copy Record (live photograph)": "exact copy"},
    "remove_deliverables": {
        "Old Scope Name Photograph": {"English signature": "duplicate"}
    },
}


def _records() -> list[dict[str, Any]]:
    return [
        {
            "exam_name": "Old Scope Name Photograph",
            "deliverables": [
                {"name": "English signature"},
                {"name": "Candidate signature (English)"},
            ],
        },
        {"exam_name": "Copy Record (live photograph)", "deliverables": []},
        {"exam_name": "Untouched", "deliverables": [{"name": "English signature"}]},
    ]


def test_renames_removals_and_duplicate_removal_apply_together() -> None:
    merge = _merge()
    records, log = merge.merge_deliverables(_records(), [], OVERLAY)
    names = {r["exam_name"] for r in records}

    assert names == {"New Name", "Untouched"}
    renamed = next(r for r in records if r["exam_name"] == "New Name")
    assert [d["name"] for d in renamed["deliverables"]] == [
        "Candidate signature (English)"
    ]
    assert any(line.startswith("REMOVED") for line in log)


def test_a_removal_never_reaches_another_record() -> None:
    merge = _merge()
    records, _ = merge.merge_deliverables(_records(), [], OVERLAY)
    untouched = next(r for r in records if r["exam_name"] == "Untouched")
    assert [d["name"] for d in untouched["deliverables"]] == ["English signature"]


def test_a_delivery_still_using_an_old_name_joins_the_renamed_record() -> None:
    merge = _merge()
    delivery = [
        {
            "exam_name": "Old Scope Name Photograph",
            "deliverables": [{"name": "Hindi signature"}],
        }
    ]
    records, _ = merge.merge_deliverables(_records(), delivery, OVERLAY)
    renamed = [r for r in records if r["exam_name"] == "New Name"]
    assert len(renamed) == 1
    assert {d["name"] for d in renamed[0]["deliverables"]} == {
        "Candidate signature (English)",
        "Hindi signature",
    }
