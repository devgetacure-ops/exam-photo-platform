"""Extract the per-examination deliverable inventory into a machine-readable sidecar.

Input is the registration-deliverables research report, which is prose with a
regular structure: one section per examination-stage, a table of deliverables,
then a detailed block per deliverable carrying its status, submission method,
applicability and a free-text specification.

This script converts that to JSON and *nothing else*. It does not decide what
the platform supports, does not fill a missing value, and does not resolve a
conflict -- those are policy, and policy lives in ``encode_exam_rules.py`` where
it can be stated once and reviewed. The split matters: if extraction and
interpretation share a file, a judgement call gets written down as though it
were a reading of the source.

Every value parsed out of a specification sentence keeps the wording it came
from, so a reader can check the parse without reopening the report. A sentence
this script cannot parse leaves the field absent rather than guessed.

Usage::

    python scripts/extract_deliverables.py \
        --report packages/exam-rules/research/indian_exam_registration_deliverables_report_2026.md \
        --out packages/exam-rules/research/exam_deliverables_2026.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Optional

# --- Specification-sentence patterns ----------------------------------------
#
# Each pattern is anchored on wording that actually occurs in the report. The
# examples in the comments are verbatim, so a later reader can tell whether a
# new phrasing is covered or has simply gone unnoticed.

# "20-100 KB", "3-300 kB", "normally 10-20 KB"
_SIZE_RANGE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:-|to|–)\s*(\d+(?:\.\d+)?)\s*(KB|MB|kB|kb|mb)\b"
)
# "up to 50 KB", "maximum 200 KB"
_SIZE_MAX_ONLY = re.compile(
    r"(?:up to|maximum(?: of)?|max\.?|not exceeding)\s*(\d+(?:\.\d+)?)\s*(KB|MB|kB|kb|mb)\b",
    re.I,
)
# A dash or a multiplication sign that a delivery's encoding turned into the
# replacement character: "width 150\ufffd220 px", "230\ufffd75 px".
_DASH = "\-–—\ufffd"
_TIMES = "x×\ufffd"
# "about 140 x 60 pixels", "240 x 240 pixels". Not preceded by a digit and a
# separator, so "150-220-250-320 px" is never read as one size.
_DIM_EXACT = re.compile(
    rf"(?<![\d{_DASH}{_TIMES}])(\d{{2,5}})\s*[{_TIMES}]\s*(\d{{2,5}})\s*(?:pixels|px)\b",
    re.I,
)
# "width between 150-220 pixels and height between 250-320 pixels",
# "width 150\ufffd220 px; height 250\ufffd320 px"
_DIM_AXES = re.compile(
    rf"width\s*(?:between\s*)?(\d{{2,5}})\s*[{_DASH}]\s*(\d{{2,5}})\s*(?:pixels|px)?"
    rf"\s*[;,]?\s*(?:and\s*)?height\s*(?:between\s*)?(\d{{2,5}})\s*[{_DASH}]\s*(\d{{2,5}})"
    r"\s*(?:pixels|px)\b",
    re.I,
)
# "150–220×250–320 px": a width range by a height range, in that order, as
# BPSC writes it. Only with a real dash and a real multiplication sign; the
# replacement character could be either, so it is never read here.
_DIM_RANGE_BY_RANGE = re.compile(
    r"(\d{2,5})\s*[-–—]\s*(\d{2,5})\s*[x×]\s*(\d{2,5})\s*[-–—]\s*(\d{2,5})\s*(?:pixels|px)\b",
    re.I,
)
#: Words that make a stated size a preference, or a bound that is not a size.
_PREFERRED = re.compile(r"prefer", re.I)
_LOWER_BOUND = re.compile(r"(?:minimum|at least|not less than)\s*$", re.I)
# "250 x 80 to 580 x 180 pixels"
_DIM_RANGE = re.compile(
    rf"(\d{{2,5}})\s*[{_TIMES}]\s*(\d{{2,5}})\s*(?:to|[{_DASH}])\s*(\d{{2,5}})\s*[{_TIMES}]\s*(\d{{2,5}})\s*"
    r"(?:pixels|px)\b",
    re.I,
)
# "published image dimension 350-500 pixels" -- one range with no stated axis
_DIM_UNAXED = re.compile(r"(\d{2,5})\s*(?:-|to|–)\s*(\d{2,5})\s*(?:pixels|px)\b", re.I)
# "filename 'signature.jpg'", "exact filename 'photo.jpg'"
_FILENAME = re.compile(r"filenames?\s*['\"]([A-Za-z0-9_.\-]+)['\"]", re.I)
# "JPG/JPEG", "JPEG/JPG", "JPG", "JPG/JPEG/PNG/GIF/BMP/PDF"
_FORMATS = re.compile(
    r"\b((?:JPE?G|PNG|GIF|BMP|PDF|TIFF?|WEBP)(?:\s*/\s*(?:JPE?G|PNG|GIF|BMP|PDF|TIFF?|WEBP))*)\b"
)

#: Phrases the report uses to say it could not establish a value. Their presence
#: is recorded so the encoder can distinguish "no specification published" from
#: "specification present but this script failed to read it" -- two very
#: different findings that would otherwise both look like an empty parse.
_NOT_ESTABLISHED = re.compile(
    r"not (?:established|located|found|available|part of)|"
    r"exact (?:value|current value|size|specification)[^.]*not|"
    r"portal-dependent|follow the active portal|"
    r"must be (?:taken from|followed)",
    re.I,
)


def _unit_to_kb(value: float, unit: str) -> float:
    return value * 1000.0 if unit.lower().startswith("m") else value


def _parse_specification(text: str) -> dict[str, Any]:
    """Pull structured values out of one free-text specification sentence."""
    parsed: dict[str, Any] = {}
    if not text:
        return parsed

    match = _SIZE_RANGE.search(text)
    if match:
        parsed["file_size_kb"] = {
            "minimum": _unit_to_kb(float(match.group(1)), match.group(3)),
            "maximum": _unit_to_kb(float(match.group(2)), match.group(3)),
            "source_wording": match.group(0).strip(),
        }
    else:
        match = _SIZE_MAX_ONLY.search(text)
        if match:
            parsed["file_size_kb"] = {
                "maximum": _unit_to_kb(float(match.group(1)), match.group(2)),
                "source_wording": match.group(0).strip(),
            }

    # Range first: "250 x 80 to 580 x 180" also matches the exact pattern twice,
    # and reading it as a single exact size would silently discard the range.
    axes = _DIM_AXES.search(text) or _DIM_RANGE_BY_RANGE.search(text)
    match = _DIM_RANGE.search(text)
    if match and match.group(0).count("�") >= 3:
        # "150�220�250�320 px": every separator lost to encoding, so
        # which numbers are widths and which are heights cannot be read.
        match = None
    if axes:
        parsed["dimensions_px"] = {
            "mode": "range",
            "minimum_width": int(axes.group(1)),
            "maximum_width": int(axes.group(2)),
            "minimum_height": int(axes.group(3)),
            "maximum_height": int(axes.group(4)),
            "source_wording": axes.group(0).strip(),
        }
    elif match:
        parsed["dimensions_px"] = {
            "mode": "range",
            "minimum_width": int(match.group(1)),
            "minimum_height": int(match.group(2)),
            "maximum_width": int(match.group(3)),
            "maximum_height": int(match.group(4)),
            "source_wording": match.group(0).strip(),
        }
    else:
        match = _DIM_EXACT.search(text)
        if match and _LOWER_BOUND.search(text[max(0, match.start() - 20) : match.start()]):
            # "minimum 140 x 60 pixels" is a bound, not a size; reading it as
            # one would invent the size a notice declined to set.
            match = None
        if match:
            around = text[max(0, match.start() - 25) : match.end() + 25]
            parsed["dimensions_px"] = {
                "mode": "preferred" if _PREFERRED.search(around) else "exact",
                "width": int(match.group(1)),
                "height": int(match.group(2)),
                "source_wording": match.group(0).strip(),
            }
        else:
            match = _DIM_UNAXED.search(text)
            if match:
                # Deliberately not turned into width/height: the source does not
                # say which axis it constrains, and choosing one would be an
                # invention rather than a reading.
                parsed["permitted_pixel_range"] = {
                    "source_wording": match.group(0).strip(),
                }

    match = _FILENAME.search(text)
    if match:
        parsed["filename"] = {
            "value": match.group(1),
            "source_wording": match.group(0).strip(),
        }

    match = _FORMATS.search(text)
    if match:
        formats = [part.strip().lower() for part in match.group(1).split("/")]
        parsed["formats"] = {
            "values": formats,
            "source_wording": match.group(1).strip(),
        }

    if _NOT_ESTABLISHED.search(text):
        parsed["specification_not_established"] = True

    return parsed


# --- Report structure --------------------------------------------------------

_RECORD = re.compile(r"\n## (\d+)\. (.+?)\n")
_HEADER_FIELD = re.compile(r"^- \*\*(.+?):\*\* (.+)$", re.M)
_DETAIL_BLOCK = re.compile(
    r"\n#### \d+\. (.+?)\n(.*?)(?=\n#### |\n### |\n---|\Z)", re.S
)
_DETAIL_FIELD = re.compile(r"^- \*\*(.+?):\*\* (.+)$", re.M)
_TABLE_ROW = re.compile(r"^\| (.+?) \| (.+?) \| `(\w+)` \| (.+?) \|$", re.M)
_SECTION = re.compile(r"\n### (.+?)\n(.*?)(?=\n### |\n## |\n---|\Z)", re.S)

#: The submission methods the report classifies with. Table rows are checked
#: against this set because the report contains a second four-column table per
#: examination -- the photograph field-level evidence -- whose third column is
#: also a backticked word (`verified`). Without the check that table reads as
#: eleven more deliverables per exam.
_KNOWN_METHODS = frozenset(
    {
        "file_upload",
        "handwritten_then_uploaded",
        "document_scan_upload",
        "official_live_capture",
        "external_identity_verification",
        "typed_or_selected_declaration",
        "physical_stage_requirement",
    }
)


def _strip_markup(text: str) -> str:
    return re.sub(r"[`*]", "", text).strip()


def _split_stage(raw: str) -> tuple[str, Optional[str]]:
    """'application / candidate_photograph' -> ('application', 'candidate_photograph')."""
    parts = [part.strip() for part in raw.split("/", 1)]
    return parts[0], (parts[1] if len(parts) > 1 else None)


def extract(report_text: str) -> list[dict[str, Any]]:
    bounds = [
        (m.start(), m.group(1), m.group(2)) for m in _RECORD.finditer(report_text)
    ]
    records: list[dict[str, Any]] = []

    for index, (start, number, name) in enumerate(bounds):
        end = bounds[index + 1][0] if index + 1 < len(bounds) else len(report_text)
        body = report_text[start:end]

        header = {
            _strip_markup(key): _strip_markup(value)
            for key, value in _HEADER_FIELD.findall(body)
        }
        # The report opens with four numbered preamble sections that match the
        # same heading shape as an examination record. An examination always
        # names its conducting body; a preamble section never does.
        if "Conducting body" not in header:
            continue
        stage, role = _split_stage(header.get("Stage / record", "application"))

        # The table and the detailed blocks carry the same inventory. The
        # detailed blocks are richer, so they are authoritative; the table is
        # read only to catch a deliverable that has no detailed block.
        table_rows = {
            _strip_markup(row[0]): {
                "requirement_status": _strip_markup(row[1]),
                "submission_method": row[2],
                "applicability": _strip_markup(row[3]),
            }
            for row in _TABLE_ROW.findall(body)
            if not row[0].startswith("---") and row[2] in _KNOWN_METHODS
        }

        deliverables: list[dict[str, Any]] = []
        detailed_names: set[str] = set()
        for title, block in _DETAIL_BLOCK.findall(body):
            fields = {
                _strip_markup(key): _strip_markup(value)
                for key, value in _DETAIL_FIELD.findall(block)
            }
            method = fields.get("Submission method", "")
            title = _strip_markup(title)
            detailed_names.add(title)
            specification = fields.get("Specification", "")
            deliverables.append(
                {
                    "name": title,
                    "requirement_status": fields.get("Requirement status"),
                    "submission_method": method,
                    "applicability": fields.get("Applicability"),
                    "specification": specification,
                    "evidence_status": fields.get("Evidence status"),
                    "source_url": fields.get("Source"),
                    "important_note": fields.get("Important note"),
                    "parsed": _parse_specification(specification),
                }
            )

        for title, row in table_rows.items():
            if title in detailed_names or title in ("Deliverable",):
                continue
            deliverables.append(
                {
                    "name": title,
                    "requirement_status": row["requirement_status"],
                    "submission_method": row["submission_method"],
                    "applicability": row["applicability"],
                    "specification": "",
                    "evidence_status": None,
                    "source_url": None,
                    "important_note": None,
                    "parsed": {},
                }
            )

        rejection: list[str] = []
        for section_title, section_body in _SECTION.findall(body):
            if section_title.strip().startswith("Rejection"):
                rejection = [
                    _strip_markup(line[2:])
                    for line in section_body.splitlines()
                    if line.startswith("- ")
                ]

        records.append(
            {
                "record_number": int(number),
                "exam_name": name.strip(),
                "conducting_body": header.get("Conducting body"),
                "application_cycle": header.get("Cycle"),
                "application_stage": stage,
                "photo_role": role,
                "evidence_source_url": header.get(
                    "Evidence source for photograph record"
                ),
                "deliverables": deliverables,
                "rejection_conditions": rejection,
            }
        )

    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    records = extract(args.report.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(records, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    total = sum(len(record["deliverables"]) for record in records)
    specified = sum(
        1
        for record in records
        for deliverable in record["deliverables"]
        if deliverable["parsed"].get("file_size_kb")
    )
    print(f"records      : {len(records)}")
    print(f"deliverables : {total}")
    print(f"with a size  : {specified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
