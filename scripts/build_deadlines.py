#!/usr/bin/env python
"""Application deadlines: the list the site's "hot exams" features read (DEC-135).

The master list is ``packages/exam-rules/research/deadlines.csv``. It is meant
to be edited by hand, in Excel or any spreadsheet, one row per examination:

    exam_id               the examination's id on the site (its page address)
    exam_name             for the reader of the sheet; not used by the site
    registration_opens    YYYY-MM-DD, or blank if not announced
    registration_closes   YYYY-MM-DD, the last date to apply
    extended_to           YYYY-MM-DD when the last date was extended, else blank
    exam_date             YYYY-MM-DD of the examination (first day), or blank
    exam_date_note        free text, e.g. "Prelims" or "To be announced"
    source_url            where the dates were read
    last_verified         YYYY-MM-DD the row was last checked
    candidates            how many sat it in the last cycle, digits only (DEC-137);
                          the site shows bigger examinations first

Two commands:

    python scripts/build_deadlines.py build
        Check every row and write apps/web/src/data/deadlines.json. A row
        naming an unknown examination, a date that is not a date, or an
        extension that is not after the original last date stops the build
        with the row named, so nothing wrong reaches the site.

    python scripts/build_deadlines.py seed --pack <dir with the tracker CSVs>
        Start (or add to) the sheet from the owner's tracker pack: rows whose
        last date has not passed, matched to the catalogue by name the way
        derive_cycle_years.py matches them. Existing exam_ids are kept as they
        are; the tracker never overwrites a hand-edited row.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / "packages" / "exam-rules" / "research" / "deadlines.csv"
OUT = ROOT / "apps" / "web" / "src" / "data" / "deadlines.json"
RULES = ROOT / "examples" / "rules"
COLUMNS = [
    "exam_id",
    "exam_name",
    "registration_opens",
    "registration_closes",
    "extended_to",
    "exam_date",
    "exam_date_note",
    "source_url",
    "last_verified",
    "candidates",
]
DATE_FIELDS = ("registration_opens", "registration_closes", "extended_to", "exam_date", "last_verified")

sys.path.insert(0, str(ROOT / "scripts"))
from derive_cycle_years import norm  # noqa: E402


def catalogue() -> Dict[str, dict]:
    exams: Dict[str, dict] = {}
    for path in sorted(RULES.glob("exam_*.json")):
        rule = json.loads(path.read_text(encoding="utf-8"))
        if rule.get("fictional_example") is not False:
            continue
        exams[rule["exam"]["exam_id"]] = rule["exam"]
    return exams


def parse_date(value: str) -> Optional[date]:
    value = (value or "").strip()
    if not value:
        return None
    match = re.fullmatch(r"(20\d\d)-(\d\d)-(\d\d)", value)
    if not match:
        raise ValueError(f"'{value}' is not a YYYY-MM-DD date")
    return date(int(match[1]), int(match[2]), int(match[3]))


def read_sheet() -> List[Dict[str, str]]:
    if not SHEET.exists():
        return []
    with SHEET.open(encoding="utf-8-sig", newline="") as handle:
        return [{c: (row.get(c) or "").strip() for c in COLUMNS} for row in csv.DictReader(handle)]


def write_sheet(rows: List[Dict[str, str]]) -> None:
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    with SHEET.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in sorted(rows, key=lambda r: (r["registration_closes"] or "9999", r["exam_id"])):
            writer.writerow(row)


def build() -> int:
    exams = catalogue()
    problems: List[str] = []
    entries = []
    seen = set()
    for number, row in enumerate(read_sheet(), start=2):
        where = f"deadlines.csv line {number} ({row['exam_id'] or 'no exam_id'})"
        if not row["exam_id"]:
            problems.append(f"{where}: exam_id is empty")
            continue
        if row["exam_id"] not in exams:
            problems.append(f"{where}: no examination with this id on the site")
            continue
        if row["exam_id"] in seen:
            problems.append(f"{where}: this examination already has a row")
            continue
        seen.add(row["exam_id"])
        try:
            dates = {f: parse_date(row[f]) for f in DATE_FIELDS}
        except ValueError as err:
            problems.append(f"{where}: {err}")
            continue
        if dates["registration_closes"] is None and dates["exam_date"] is None:
            problems.append(f"{where}: needs a last date to apply or an exam date")
            continue
        if dates["extended_to"] and dates["registration_closes"] and dates["extended_to"] <= dates["registration_closes"]:
            problems.append(f"{where}: extended_to must be after registration_closes")
            continue
        if dates["registration_opens"] and dates["registration_closes"] and dates["registration_opens"] > dates["registration_closes"]:
            problems.append(f"{where}: registration_opens is after registration_closes")
            continue
        candidates = row["candidates"].replace(",", "").strip()
        if candidates and not candidates.isdigit():
            problems.append(f"{where}: candidates must be a whole number")
            continue
        exam = exams[row["exam_id"]]
        entries.append(
            {
                "examId": row["exam_id"],
                "examName": exam["exam_name"],
                "shortName": (exam.get("aliases") or [None])[0],
                "conductingBody": exam.get("conducting_body"),
                "opens": row["registration_opens"] or None,
                "closes": row["registration_closes"] or None,
                "extendedTo": row["extended_to"] or None,
                "examDate": row["exam_date"] or None,
                "examDateNote": row["exam_date_note"] or None,
                "sourceUrl": row["source_url"] or None,
                "lastVerified": row["last_verified"] or None,
                "candidates": int(candidates) if candidates else None,
            }
        )
    if problems:
        print("Not written. Fix these rows first:", file=sys.stderr)
        for problem in problems:
            print("  - " + problem, file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"entries": entries}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(entries)} deadlines written to {OUT.relative_to(ROOT)}")
    return 0


def seed(pack: Path, today: date) -> int:
    exams = catalogue()
    keys: Dict[str, str] = {}
    for exam_id, exam in exams.items():
        for name in [exam["exam_name"], *(exam.get("aliases") or [])]:
            key = norm(name)
            if key:
                keys.setdefault(key, exam_id)
    rows = {row["exam_id"]: row for row in read_sheet()}
    added = 0
    for name in ("Live_Upcoming", "Tracker"):
        path = pack / f"ExamUploadKit_CONSOLIDATED_{name}.csv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for source in csv.DictReader(handle):
                closes = (source.get("Registration_End") or "")[:10]
                if not re.fullmatch(r"20\d\d-\d\d-\d\d", closes) or date.fromisoformat(closes) < today:
                    continue
                exam_id = next(
                    (
                        keys[norm(v)]
                        for v in str(source.get("Exam_or_Recruitment", "")).split(" || ")
                        if norm(v) in keys
                    ),
                    None,
                )
                if exam_id is None or exam_id in rows:
                    continue
                opens = (source.get("Registration_Start") or "")[:10]
                window = source.get("Exam_or_Selection_Window") or ""
                exam_date = re.search(r"20\d\d-\d\d-\d\d", window)
                rows[exam_id] = {
                    "exam_id": exam_id,
                    "exam_name": exams[exam_id]["exam_name"],
                    "registration_opens": opens if re.fullmatch(r"20\d\d-\d\d-\d\d", opens) else "",
                    "registration_closes": closes,
                    "extended_to": "",
                    "exam_date": exam_date[0] if exam_date else "",
                    "exam_date_note": re.sub(r"\s*20\d\d-\d\d-\d\d\s*", " ", window).strip()[:60],
                    "source_url": source.get("Source_URL") or "",
                    "last_verified": (source.get("Last_Verified") or "")[:10],
                }
                added += 1
    write_sheet(list(rows.values()))
    print(f"{added} rows added from the tracker; {len(rows)} in the sheet")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build")
    seeder = sub.add_parser("seed")
    seeder.add_argument("--pack", type=Path, required=True)
    seeder.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    if args.command == "build":
        return build()
    return seed(args.pack, args.today)


if __name__ == "__main__":
    sys.exit(main())
