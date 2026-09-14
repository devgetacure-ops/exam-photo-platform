"""The owner's research sheet: everything we could prepare with information we lack.

Item K2 (2026-09-14). One row per examination and file where a published fact
is missing, estimated, or unreadable, saying what is missing and what would
settle it, with blank columns for the owner to fill. Generated from the
records, so it is current after every encode.

Rows, by kind:

- ``not_yet_supported``: a file the examination asks for that we cannot
  prepare because no size or format was established.
- ``photograph_no_pixel_size``: a photograph whose notice gave no pixel size.
- ``estimated_value``: a size or format that is our estimate (interim_default).
- ``partially_supported``: a photograph needing a printed name or date.
- ``unread_pixel_size``: a size in the instructions we could not read safely.
- ``no_researched_fact``: an examination with nothing for "Worth knowing".
- ``not_encoded``: an examination in the research we could not encode at all.

Usage::

    python scripts/build_missing_information_sheet.py --out docs/research-requests
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "examples" / "rules"

COLUMNS = [
    "kind",
    "exam_id",
    "examination",
    "conducting_body",
    "file",
    "requirement_id",
    "what_we_hold_now",
    "what_is_missing",
    "what_would_settle_it",
    "source_we_hold",
    "YOUR_published_value",
    "YOUR_exact_passage_from_the_notice",
    "YOUR_source_url",
    "YOUR_page_or_section",
    "YOUR_date_checked",
    "YOUR_notes",
]


def _official_source(record: dict[str, Any]) -> str:
    for source in record.get("source_evidence") or []:
        if source.get("official_source") and source.get("source_url"):
            return str(source["source_url"])
    for source in record.get("source_evidence") or []:
        if source.get("source_url"):
            return str(source["source_url"])
    return ""


def _size(spec: dict[str, Any]) -> str:
    size = spec.get("file_size") or {}
    parts = []
    if size.get("minimum_bytes"):
        parts.append(f"min {size['minimum_bytes'] // 1000} KB")
    if size.get("maximum_bytes"):
        parts.append(f"max {size['maximum_bytes'] // 1000} KB")
    formats = (spec.get("formats") or {}).get("allowed_formats")
    if formats:
        parts.append("/".join(formats))
    return ", ".join(parts)


def rows() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    facts_path = RULES / "candidate_facts.json"
    facts = json.loads(facts_path.read_text(encoding="utf-8")).get("exams", {})

    for path in sorted(RULES.glob("exam_*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("fictional_example"):
            continue
        exam = record["exam"]
        base = {
            "exam_id": exam["exam_id"],
            "examination": exam["exam_name"],
            "conducting_body": exam.get("conducting_body", ""),
            "source_we_hold": _official_source(record),
        }
        provenance = record.get("provenance") or {}

        image = record.get("image_requirements") or {}
        dims = image.get("dimensions") or {}
        if image and dims.get("mode") == "unspecified" and not dims.get("preferred_width_px"):
            out.append({
                **base,
                "kind": "photograph_no_pixel_size",
                "file": "Photograph",
                "requirement_id": "candidate_photograph",
                "what_we_hold_now": _size(image),
                "what_is_missing": "Pixel width x height (and whether mandatory or preferred), any cm size, any dpi",
                "what_would_settle_it": "The photograph section of the current information bulletin or notice",
            })

        for index, requirement in enumerate(record.get("requirements") or []):
            name = requirement.get("requirement_name", "")
            rid = requirement.get("requirement_id", "")
            spec = requirement.get("file_spec") or {}
            support = requirement.get("platform_support")
            row = {**base, "file": name, "requirement_id": rid}

            if support == "not_yet_supported":
                out.append({
                    **row,
                    "kind": "not_yet_supported",
                    "what_we_hold_now": requirement.get("content_instructions") or "",
                    "what_is_missing": "The file's size limit (KB) and accepted formats, or confirmation that the portal takes it as an upload",
                    "what_would_settle_it": "The upload instructions for this file in the current notice or portal guide",
                })
            elif support == "partially_supported":
                out.append({
                    **row,
                    "kind": "partially_supported",
                    "what_we_hold_now": requirement.get("notes") or requirement.get("content_instructions") or "",
                    "what_is_missing": "Exactly what must be printed on the photograph (name, date), where, and in what style",
                    "what_would_settle_it": "The notice's wording on the printed name and date",
                })

            estimated = [
                key.split("file_spec.", 1)[1]
                for key, value in provenance.items()
                if key.startswith(f"requirements[{index}].file_spec.")
                and (value or {}).get("type") == "interim_default"
            ]
            if estimated:
                out.append({
                    **row,
                    "kind": "estimated_value",
                    "what_we_hold_now": f"{_size(spec)} (ours: {', '.join(estimated)})",
                    "what_is_missing": "The published " + " and ".join(
                        "size limit" if e.startswith("file_size") else "accepted formats" for e in sorted(set(estimated))
                    ),
                    "what_would_settle_it": "This file's upload instructions in the current notice",
                })

            text = " ".join(str(requirement.get(k) or "") for k in ("content_instructions", "notes"))
            if requirement.get("requirement_type") != "photograph" and "pixel" in text.lower() + " " and not spec.get("dimensions"):
                if any(ch.isdigit() for ch in text) and ("px" in text.lower() or "pixel" in text.lower()):
                    out.append({
                        **row,
                        "kind": "unread_pixel_size",
                        "what_we_hold_now": text[:240],
                        "what_is_missing": "Whether the size is exact, preferred, a minimum or a range, and which number is width and which height",
                        "what_would_settle_it": "The size sentence as the notice prints it",
                    })

        entry = facts.get(exam["exam_id"]) or {}
        if not any(f.get("reported_by") for f in entry.get("facts") or []):
            out.append({
                **base,
                "kind": "no_researched_fact",
                "file": "Worth knowing",
                "requirement_id": "",
                "what_we_hold_now": "Nothing shown",
                "what_is_missing": "3-6 facts about the examination itself (candidates, process, structure, history), each with its passage and publisher",
                "what_would_settle_it": "See docs/research-requests facts prompt",
            })

    unavailable_path = RULES / "unavailable_examinations.json"
    if unavailable_path.exists():
        for item in json.loads(unavailable_path.read_text(encoding="utf-8")).get("examinations", []):
            out.append({
                "kind": "not_encoded",
                "exam_id": "",
                "examination": item.get("exam_name", ""),
                "conducting_body": "",
                "file": "Whole examination",
                "requirement_id": "",
                "what_we_hold_now": item.get("detail", ""),
                "what_is_missing": item.get("reason", ""),
                "what_would_settle_it": "The examination's current application notice",
                "source_we_hold": "",
            })
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "research-requests")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    data = rows()
    sheet = args.out / "missing-information.csv"
    with sheet.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            writer.writerow({column: row.get(column, "") for column in COLUMNS})

    counts: dict[str, int] = {}
    for row in data:
        counts[row["kind"]] = counts.get(row["kind"], 0) + 1
    summary = args.out / "MISSING_INFORMATION.md"
    lines = [
        "# What we could prepare with information we do not have",
        "",
        "Generated by `scripts/build_missing_information_sheet.py` from the records "
        "(item K2, 2026-09-14). Do not edit by hand; fill the `YOUR_` columns in "
        "`missing-information.csv` and hand the file back. Every value needs its "
        "passage, source and date, the same rule the research brief sets.",
        "",
        "| Kind | Rows | What it means |",
        "|---|---|---|",
    ]
    meaning = {
        "not_yet_supported": "A file the examination asks for that we cannot prepare yet",
        "photograph_no_pixel_size": "A photograph whose notice we hold gives no pixel size",
        "estimated_value": "A size or format that is our estimate, marked est. on the site",
        "partially_supported": "A photograph needing a printed name or date",
        "unread_pixel_size": "A size written in a way we could not read safely",
        "no_researched_fact": "An examination with nothing for Worth knowing",
        "not_encoded": "An examination we could not encode at all",
    }
    for kind in meaning:
        lines.append(f"| `{kind}` | {counts.get(kind, 0)} | {meaning[kind]} |")
    lines.append("")
    lines.append(f"**{len(data)} rows in all.**")
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(data)} rows -> {sheet}")
    for kind, n in sorted(counts.items()):
        print(f"  {kind}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
