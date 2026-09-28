"""Convert a tabular research delivery (exams / uploads / worth-knowing CSVs)
into the research corpus's two JSON shapes and a trivia document.

The 2026-09-27 delivery arrived as three spreadsheets covering the 636
examinations the catalogue did not list (DEC-114). The owner's instruction is to
take it as the documents say: every value is written as ``verified`` with the
delivery's own citation, and nothing is re-judged here. The standing rules still
apply downstream -- ``merge_research_delivery.py`` never lets a delivery displace
a value the repository already holds, and a photograph with no published pixel
size is given the platform's 413 x 531 estimate (DEC-095, DEC-105).

Usage::

    python scripts/import_tabular_delivery.py \
        --delivery packages/exam-rules/research/delivery_2026_09_27 \
        --out <scratch dir>                   # writes the two corpus JSONs
    python scripts/merge_research_delivery.py --delivery <scratch dir>

Worth-knowing facts go to ``exam_trivia_2026.json`` (``--trivia``), keyed by
examination name, keeping only facts: a sentence about rules, sizes, uploads,
eligibility or fees is left out, because the facts card is facts only.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

ESTIMATED_SIZE = [413, 531]

_PHOTO = re.compile(r"photo|image|picture", re.I)
_NOT_PHOTO = re.compile(r"identity|\bid\b|proof|certificate|\bdocuments?\b|\bcard\b", re.I)
# A row named for a signature or thumb is not the photograph, unless it is the
# photograph *with* a signature box (a composite the portal takes as one image).
_SIGN_ONLY = re.compile(r"^(?!.*photo).*(signature|thumb|declaration)", re.I)
_LIVE = re.compile(r"webcam|live|real-time|real time|stream", re.I)

# A worth-knowing sentence that is really a rule (DEC-082; owner: "facts only").
_RULE_LIKE = re.compile(
    r"actionable advice|\bKB\b|\bMB\b|pixel|\bdpi\b|upload|photograph size|"
    r"reject|eligib|age limit|\bfee\b|syllabus|marking|negative mark|"
    r"\bmust\b|mandatory|required to|qualif",
    re.I,
)


def _num(text: Any) -> Optional[float]:
    match = re.search(r"\d+(?:\.\d+)?", str(text or "").replace(",", ""))
    return float(match.group()) if match else None


def _range(text: Any) -> Optional[tuple[float, float]]:
    nums = re.findall(r"\d+(?:\.\d+)?", str(text or ""))
    if len(nums) >= 2 and re.search(r"\bto\b|-|–", str(text)):
        low, high = float(nums[0]), float(nums[1])
        if low < high:
            return low, high
    return None


def _field(value: Any, row: Dict[str, str], status: str = "verified") -> Dict[str, Any]:
    source_type = str(row.get("source_type") or "")
    url = str(row.get("source_url") or "")
    return {
        "status": status,
        "value": value,
        "captured_wording": (row.get("exact_passage") or "").strip().strip('"')[:1800] or None,
        "confidence": 4,
        "source_type": ("official_pdf" if url.lower().endswith(".pdf") else "official_webpage") if "official" in source_type.lower() else "secondary_reference",
        "official_source": "official" in source_type.lower(),
        "source_url": url,
        "document_title": row.get("notice_title") or None,
        "document_identifier": None,
        "page_number": None,
        "section_name": row.get("page_or_section") or None,
        "access_date": row.get("date_checked") or None,
    }


def _formats(text: str) -> List[str]:
    found = re.findall(r"jpe?g|png|gif|pdf|webp|bmp", text.lower())
    out: List[str] = []
    for fmt in found:
        if fmt not in out:
            out.append(fmt)
    return out


def _policy(text: str) -> Optional[Dict[str, str]]:
    t = (text or "").strip()
    low = t.lower()
    if not t or low.startswith(("not applicable", "n/a", "not specified")):
        return None
    if re.search(r"not (allowed|permitted)|prohibited|no ", low) and not re.search(
        r"unless|except|religious|without|only", low
    ):
        return {"policy": "prohibited", "source_wording": t}
    if re.search(r"unless|except|religious|without|only|if ", low):
        return {"policy": "conditional", "condition": t, "source_wording": t}
    if re.search(r"allowed|permitted", low):
        return {"policy": "permitted", "source_wording": t}
    return None


def _recency_days(text: str) -> Optional[int]:
    low = (text or "").lower()
    n = _num(low)
    if n is None:
        return None
    if "month" in low:
        return int(n * 30)
    if "week" in low:
        return int(n * 7)
    if "day" in low:
        return int(n)
    return None


def _category(text: str) -> str:
    low = (text or "").lower()
    if "entrance" in low or "admission" in low:
        return "entrance"
    if "eligib" in low:
        return "eligibility"
    if "professional" in low:
        return "professional_body"
    if "board" in low:
        return "board_registration"
    return "recruitment"


def _year(text: str) -> Optional[int]:
    years = [int(y) for y in re.findall(r"20\d\d", text or "")]
    return max(years) if years else None


def _spec_record(exam: Dict[str, str], photo: Dict[str, str]) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    live = bool(_LIVE.search(photo["file_name"] + " " + photo["formats"]))
    size_max = _num(photo.get("max_size"))
    if size_max is not None and not live:
        fields["file_size.published_maximum"] = _field(size_max, photo)
        size_min = _num(photo.get("min_size"))
        if size_min is not None and size_min < size_max:
            fields["file_size.published_minimum"] = _field(size_min, photo)
        unit = (photo.get("size_unit") or "KB").strip()
        fields["file_size.size_unit_as_published"] = _field(
            "MB" if unit.lower().startswith("mb") else unit, photo
        )
    fmts = [f for f in _formats(photo.get("formats") or "") if f != "pdf"]
    if fmts and not live:
        fields["formats.allowed_formats"] = _field(fmts, photo)
    if live:
        fields["appearance.live_capture_required"] = _field(True, photo)

    w_range, h_range = _range(photo.get("pixel_width")), _range(photo.get("pixel_height"))
    width, height = _num(photo.get("pixel_width")), _num(photo.get("pixel_height"))
    rule = (photo.get("pixel_rule") or "").lower()
    if w_range and h_range:
        fields["dimensions.minimum_width_px"] = _field(int(w_range[0]), photo)
        fields["dimensions.maximum_width_px"] = _field(int(w_range[1]), photo)
        fields["dimensions.minimum_height_px"] = _field(int(h_range[0]), photo)
        fields["dimensions.maximum_height_px"] = _field(int(h_range[1]), photo)
    elif width and height and not live:
        key = "" if "exact" in rule else "preferred_"
        fields[f"dimensions.{key}width_px"] = _field(int(width), photo)
        fields[f"dimensions.{key}height_px"] = _field(int(height), photo)
    else:
        est = _field(ESTIMATED_SIZE, photo, status="estimated")
        est["reasoning"] = (
            "The delivery gives no pixel size for this photograph. It is delivered "
            "at 413 x 531 px, a 3.5 x 4.5 cm passport photograph at 300 DPI; this "
            "size is our estimate, not the body's."
        )
        fields["dimensions.estimated_size"] = est
    if photo.get("pixel_rule"):
        fields["permitted_pixel_range"] = _field(photo["pixel_rule"][:300], photo)
    dpi = _num(photo.get("dpi"))
    if dpi and 72 <= dpi <= 1200:
        fields["dpi"] = _field(int(dpi), photo)

    background = (photo.get("background") or "").lower()
    if "white" in background and "light" in background:
        fields["background.required_colour"] = _field("white or light colour", photo)
    elif "white" in background:
        fields["background.required_colour"] = _field("white", photo)
    elif "light" in background or "plain" in background:
        fields["background.mode"] = _field("plain_light", photo)

    coverage = _num(photo.get("face_coverage"))
    if coverage and 20 <= coverage <= 100:
        fields["composition.face_coverage_minimum"] = _field(coverage, photo)
    if re.search(r"\bears?\b", photo.get("face_coverage") or "", re.I):
        fields["composition.ears_visible"] = _field(True, photo)
    colour = (photo.get("colour_or_bw") or "").lower()
    if colour.strip() == "colour":
        fields["appearance.monochrome_accepted"] = _field(False, photo)
    elif re.search(r"gr[ae]y|b/?w|black and white|black & white", colour):
        fields["appearance.monochrome_accepted"] = _field(True, photo)
    for key, column in (("spectacles", "spectacles"), ("headwear", "headwear"),
                        ("face_mask", "face_mask")):
        policy = _policy(photo.get(column) or "")
        if policy:
            fields[f"appearance.{key}"] = _field(policy, photo)
    days = _recency_days(photo.get("photo_recency") or "")
    if days:
        fields["appearance.recency_maximum_days"] = _field(days, photo)
    imprint = photo.get("name_date_on_photo") or ""
    if imprint.lower().startswith("mandatory"):
        parts = []
        if "name" in imprint.lower():
            parts.append("candidate_name")
        if "date" in imprint.lower():
            parts.append("photograph_date")
        if parts:
            fields["appearance.imprint.policy"] = _field("required", photo)
            fields["appearance.imprint.fields"] = _field(parts, photo)
            fields["appearance.imprint.position"] = _field("bottom", photo)
    if photo.get("file_naming") and not photo["file_naming"].lower().startswith(
        ("not ", "n/a", "no ")
    ):
        fields["filename.instructions"] = _field(photo["file_naming"][:300], photo)

    return {
        "exam_name": exam["exam_name"],
        "aliases": _aliases(exam),
        "conducting_body": exam.get("conducting_body") or "unknown",
        "examination_year": _year(exam.get("latest_cycle", "")) or 2026,
        "application_cycle": (exam.get("latest_cycle") or "current")[:80],
        "application_stage": "application",
        "photo_role": "candidate_photograph",
        "jurisdiction": exam.get("state") or "India",
        "category": _category(exam.get("category", "")),
        "primary_source_id": "delivery_2026_09_27",
        "fields": fields,
    }


def _aliases(exam: Dict[str, str]) -> List[str]:
    out: List[str] = []
    for alias in re.split(r"[,;/]", exam.get("other_names") or ""):
        alias = alias.strip()
        if alias and alias != exam["exam_name"] and alias not in out and len(alias) <= 80:
            out.append(alias)
    return out[:12]


def _url(text: str) -> str:
    text = (text or "").strip()
    if text.startswith(("http://", "https://")):
        return text
    if re.match(r"^[\w.-]+\.[a-z]{2,}(/|$)", text, re.I):
        return f"https://{text}"
    return ""


def _cite(row: Dict[str, str], exam: Dict[str, str]) -> Dict[str, str]:
    """Where an upload row names only "Official Career Portal", cite the
    examination's own notice (or website) and title from the exams sheet."""
    row = dict(row)
    url = _url(row.get("source_url", ""))
    if not url:
        url = _url(exam.get("notice_url", "")) or _url(exam.get("official_website", ""))
    row["source_url"] = url
    row["notice_title"] = exam.get("notice_title") or exam.get("exam_name", "")
    return row


def _method(row: Dict[str, str]) -> str:
    name = row["file_name"] + " " + row["formats"]
    if _LIVE.search(name):
        return "official_live_capture"
    if re.search(r"signature|thumb|declaration", row["file_name"], re.I):
        return "handwritten_then_uploaded"
    if "pdf" in row["formats"].lower() or re.search(
        r"certificate|document|proof|mark ?sheet|annexure|card", row["file_name"], re.I
    ):
        return "document_scan_upload"
    return "file_upload"


def _deliverable(row: Dict[str, str]) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {}
    size_max = _num(row.get("max_size"))
    if size_max is not None:
        size_min = _num(row.get("min_size"))
        factor = 1000.0 if (row.get("size_unit") or "").lower().startswith("mb") else 1.0
        parsed["file_size_kb"] = {
            "minimum": (size_min * factor) if size_min is not None else None,
            "maximum": size_max * factor,
            "source_wording": f"{row.get('min_size')}-{row.get('max_size')} {row.get('size_unit')}",
        }
    fmts = _formats(row.get("formats") or "")
    if fmts:
        parsed["formats"] = {"values": fmts, "source_wording": row.get("formats")}
    width, height = _num(row.get("pixel_width")), _num(row.get("pixel_height"))
    w_range, h_range = _range(row.get("pixel_width")), _range(row.get("pixel_height"))
    wording = row.get("pixel_rule") or f"{row.get('pixel_width')} x {row.get('pixel_height')}"
    if w_range and h_range:
        parsed["dimensions_px"] = {
            "mode": "range",
            "minimum_width": int(w_range[0]), "maximum_width": int(w_range[1]),
            "minimum_height": int(h_range[0]), "maximum_height": int(h_range[1]),
            "source_wording": wording,
        }
    elif width and height:
        parsed["dimensions_px"] = {
            "mode": "exact" if "exact" in wording.lower() else "preferred",
            "width": int(width), "height": int(height),
            "source_wording": wording,
        }
    spec_bits = [row.get(c) for c in ("formats", "pixel_rule", "physical_size",
                                       "background", "signature_or_thumb_rules",
                                       "other_checks")]
    status = row.get("mandatory_or_conditional") or "Mandatory"
    return {
        "name": row["file_name"],
        "requirement_status": "Mandatory" if status.lower().startswith("mandatory")
        and "conditional" not in status.lower() else "Conditional",
        "submission_method": _method(row),
        "applicability": status,
        "specification": "; ".join(b for b in spec_bits if b and b.lower() not in
                                   ("not applicable", "n/a"))[:1200],
        "evidence_status": row.get("source_type") or "Delivery 2026-09-27",
        "source_url": row.get("source_url") or None,
        "important_note": (row.get("stage") or None),
        "parsed": parsed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delivery", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--trivia", type=Path, default=None)
    args = parser.parse_args()

    def rows(name: str) -> List[Dict[str, str]]:
        with open(args.delivery / name, encoding="utf-8-sig", newline="") as handle:
            return [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(handle)]

    exams = rows("exams.csv")
    uploads = rows("uploads.csv")
    by_row: Dict[str, List[Dict[str, str]]] = {}
    for row in uploads:
        by_row.setdefault(row["row_no"], []).append(row)

    specs: List[Dict[str, Any]] = []
    deliverables: List[Dict[str, Any]] = []
    seen_names: set[str] = set()
    for exam in exams:
        name = exam["exam_name"]
        if not name or name in seen_names:
            continue
        seen_names.add(name)
        files = [_cite(f, exam) for f in by_row.get(exam["row_no"], [])]
        photos = [f for f in files if _PHOTO.search(f["file_name"])
                  and not _NOT_PHOTO.search(f["file_name"])
                  and not _SIGN_ONLY.search(f["file_name"])]
        uploaded = [p for p in photos if not _LIVE.search(p["file_name"] + p["formats"])]
        photo = (uploaded or photos or [None])[0]
        if photo:
            specs.append(_spec_record(exam, photo))
        deliverables.append({
            "record_number": len(deliverables) + 1,
            "exam_name": name,
            "conducting_body": exam.get("conducting_body") or "unknown",
            "application_cycle": (exam.get("latest_cycle") or "current")[:80],
            "application_stage": "application",
            "photo_role": "candidate_photograph",
            "evidence_source_url": exam.get("notice_url") or exam.get("official_website") or None,
            "deliverables": [_deliverable(f) for f in files],
            "rejection_conditions": [],
        })

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "exam_photo_specs_2026.json").write_text(
        json.dumps(specs, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.out / "exam_deliverables_2026.json").write_text(
        json.dumps(deliverables, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"specs records       : {len(specs)}")
    print(f"deliverable records : {len(deliverables)}")

    if args.trivia:
        document = json.loads(args.trivia.read_text(encoding="utf-8"))
        store = document.setdefault("exams", {})
        added = dropped = 0
        for fact in rows("worth_knowing.csv"):
            text, url = fact.get("fact", ""), fact.get("source_url", "")
            if not text or not url.startswith("http") or _RULE_LIKE.search(text):
                dropped += 1
                continue
            host = urlparse(url).netloc.replace("www.", "") or "source"
            entries = store.setdefault(fact["exam_name"], [])
            if any(e.get("text") == text for e in entries):
                continue
            entries.append({
                "kind": "history",
                "text": text,
                "source_url": url,
                "source_title": fact["exam_name"],
                "source_quote": text,
                "publisher": host,
                "official_source": False,
                "as_of": fact.get("date_checked") or "2026-09-27",
                "confidence": 4,
            })
            added += 1
        args.trivia.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n",
                               encoding="utf-8")
        print(f"worth-knowing facts : {added} added, {dropped} left out (rules, not facts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
