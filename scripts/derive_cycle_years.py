"""Work out which cycle each examination is in now, from the owner's tracker.

The catalogue's records carry the year of the notice their rules were read
from, so in October 2026 a candidate paying for CAT was shown "Common Admission
Test 2025" (owner, 2 October: "that is a blunder"). The owner's instruction is
that every examination reads 2026 or 2027, whichever its next sitting is, taken
from the research documents where they say.

This reads the consolidated tracker pack (Tracker, Live/Upcoming, Future
watchlist, Master records) and writes ``cycle_years.json``, which the encoder
applies to what a candidate *sees*: the name's year, the year field and the
short forms. A record's id never changes, so no address moves, and its
``source_evidence`` still names the notice the rules came from.

How a year is chosen, in order:

1. Rows in the pack whose name, with its year and "next cycle" wording removed,
   is exactly the examination's name or one of its short forms.
2. If such a row is for the 2026 cycle and that cycle is not over (registration
   open, opening, or the examination still to be sat), the year is 2026.
3. Otherwise, if a row is for 2027, the year is 2027.
4. With no row at all, 2026: the cycle now running.

Usage::

    python scripts/derive_cycle_years.py --pack <dir with the CONSOLIDATED csvs> \
        --rules examples/rules --out packages/exam-rules/research/cycle_years.json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

TODAY = date(2026, 10, 2)
FILES = ("Tracker", "Live_Upcoming", "Future_Watchlist", "Master_Records")

_NOISE = re.compile(
    r"\b(20\d\d(-\d\d)?|next cycle|future cycle|next|cycle|session\s*\d*|phase\s*\d+|"
    r"january|february|march|april|may|june|july|august|september|october|"
    r"november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|"
    r"examination|exam|recruitment)\b",
    re.I,
)


def norm(text: str) -> str:
    text = re.sub(r"\(.*?\)", " ", text or "")
    text = _NOISE.sub(" ", text)
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def row_year(row: Dict[str, str]) -> Optional[int]:
    """The cycle a tracker row is about: 2026, 2027, or None if it does not say."""
    # The examination's own title outranks the tracker's cycle column: CLAT
    # sat in December 2026 is "CLAT 2027", and that is the year candidates see.
    named = set(
        re.findall(r"(20\d\d)(?!-\d\d)", str(row.get("Exam_or_Recruitment", "")))
    )
    if len(named) == 1 and named <= {"2026", "2027"}:
        return int(named.pop())
    text = f"{row.get('Cycle', '')} {row.get('Exam_or_Recruitment', '')}"
    has26 = bool(re.search(r"2026(?!-27)", text)) or "2026-27" in text
    has27 = bool(re.search(r"(?<!2026-)2027|/ ?2027|next", text, re.I))
    if "2026-27" in text and not re.search(r"2026-27 ?/ ?20|/2027|Next", text):
        return 2026
    if has27 and not re.search(r"\b2026\b(?!-27)", text):
        return 2027
    if has26:
        return 2026
    return 2027 if has27 else None


def cycle_over(row: Dict[str, str]) -> bool:
    """Whether everything this row describes is already in the past."""
    text = " ".join(
        str(row.get(k, ""))
        for k in ("Exam_or_Selection_Window", "Registration_End", "Registration_Status")
    )
    if re.search(
        r"open|opening|upcoming|expected|awaited|announced|soon|live", text, re.I
    ):
        return False
    dates = []
    for y, m, d in re.findall(r"(20\d\d)-(\d\d)-(\d\d)", text):
        try:
            dates.append(date(int(y), int(m), int(d)))
        except ValueError:
            continue
    return bool(dates) and max(dates) < TODAY


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--rules", type=Path, default=Path("examples/rules"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    by_name: Dict[str, List[Dict[str, str]]] = {}
    for name in FILES:
        path = args.pack / f"ExamUploadKit_CONSOLIDATED_{name}.csv"
        with open(path, encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                for variant in str(row.get("Exam_or_Recruitment", "")).split(" || "):
                    key = norm(variant)
                    if key:
                        by_name.setdefault(key, []).append(row)

    out: Dict[str, Any] = {}
    counts = {2026: 0, 2027: 0}
    matched = 0
    for path in sorted(args.rules.glob("exam_*.json")):
        rule = json.loads(path.read_text(encoding="utf-8"))
        if rule.get("fictional_example") is not False:
            continue
        exam = rule["exam"]
        keys = {norm(exam["exam_name"])} | {norm(a) for a in exam.get("aliases") or []}
        rows = [row for key in keys if key for row in by_name.get(key, [])]
        years = {}
        for row in rows:
            year = row_year(row)
            if year:
                years.setdefault(year, []).append(row)
        # An examination titled 2027 that is taking applications now is the
        # 2027 examination, whatever a generic row's cycle column says.
        open_2027 = [
            r
            for r in years.get(2027, [])
            if "2027" in str(r.get("Exam_or_Recruitment", ""))
            and re.search(r"open", str(r.get("Registration_Status", "")), re.I)
        ]
        if open_2027:
            year, basis = 2027, open_2027[0]
        elif 2026 in years and not all(cycle_over(r) for r in years[2026]):
            year, basis = 2026, years[2026][0]
        elif 2027 in years:
            year, basis = 2027, years[2027][0]
        elif 2026 in years:
            # The 2026 sitting is over and no 2027 row says more: the next is 2027.
            year, basis = 2027, years[2026][0]
        else:
            year, basis = 2026, None
        if basis is not None:
            matched += 1
        counts[year] += 1
        out[exam["exam_id"]] = {
            "year": year,
            "basis": (
                f"{basis.get('Exam_or_Recruitment', '')[:80]} | cycle {basis.get('Cycle', '')[:30]}"
                f" | {basis.get('Registration_Status', '')[:40]}"
                f" | {basis.get('Exam_or_Selection_Window', '')[:60]}"
                if basis is not None
                else "no tracker row; the cycle now running"
            ),
        }

    document = {
        "_note": (
            "Which cycle each examination is in now (owner, 2 October 2026). Applied "
            "by encode_exam_rules.py to the name's year, the year field and the short "
            "forms. Ids and source evidence are untouched. Written by "
            "scripts/derive_cycle_years.py from the owner's tracker pack."
        ),
        "as_of": TODAY.isoformat(),
        "exams": out,
    }
    args.out.write_text(
        json.dumps(document, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"examinations {len(out)} | matched to a tracker row {matched} | {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
