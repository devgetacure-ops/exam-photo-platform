"""Audit the generated catalogue for the defects the owner found by hand.

Testing note 5 (2026-09-14): BPSC listed five signatures where the notice asks
for two. The owner could not check 132 examinations by eye, so this checks all
of them, every run, for each class of defect found:

- **Duplicate requirements**: two requirements of one type whose names overlap
  enough to be the same document.
- **Scope names**: an examination named after the research brief's scope --
  "... Photograph Specification", "(current portal scope)", "fallback".
- **Duplicate examinations**: two records with the same requirements from the
  same notice.
- **Unread pixel sizes**: a pixel size written in a requirement's instructions
  that never reached its file specification.

A finding may be allowed only with a written reason in ``ALLOWED`` below. The
engine test ``test_catalogue_audit.py`` fails on anything else.

Usage::

    python scripts/audit_catalogue.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

CATALOGUE = Path(__file__).resolve().parents[1] / "examples" / "rules"

_STOP = {
    "the", "of", "and", "candidate", "s", "a", "or", "image", "scan", "copy",
    "upload", "file", "applicant", "where", "applicable",
}
_SCOPE = re.compile(
    r"photograph\s+specification|scope\)|instruction$|fallback|\bfamily\b|"
    r"\(live photograph\)|portal photograph|registration photograph|application photograph",
    re.I,
)
_PIXELS = re.compile(r"\d{2,5}\s*(?:px|pixels?)\b", re.I)

#: Findings that are correct as they stand, each with the reason. Keyed by
#: (check, exam_id, detail).
ALLOWED: dict[tuple[str, str, str], str] = {
    ("duplicate", "dsssb-recruitment-examinations", "Left thumb impression | Right thumb impression"):
        "Two different thumbs, both asked for.",
    ("duplicate", "indian-air-force-agniveervayu-recruitment", "Candidate signature | Parent/guardian signature (where applicable)"):
        "Different signatories.",
    ("duplicate", "karnataka-common-entrance-test-2026", "Candidate signature | Parent/guardian signature"):
        "Different signatories.",
    ("duplicate", "neet-ug-2026", "Candidate signature | Scribe's signature"):
        "Different signatories.",
    ("duplicate", "kerala-engineering-architecture-medical-entrance-examination", "Communal reservation supporting certificate | Special reservation supporting certificate"):
        "Two different reservation schemes.",
    ("duplicate", "neet-ug-2026", "Class X or equivalent marksheet | Class X or equivalent passing certificate"):
        "The bulletin lists the marksheet and the passing certificate as separate uploads.",
    ("duplicate", "neet-ug-2026", "NRI / OCI / Foreign national citizenship certificate or documentary proof | Citizenship certificate"):
        "The bulletin lists both: the Appendix VI/VII proof for foreign nationals and a citizenship certificate.",
    ("unread_pixels", "rrb-section-controller", "candidate_signature"):
        "'minimum 140 x 60 pixels' is a lower bound, not a size; reading it as one would invent a size the notice does not set.",
    ("unread_pixels", "rrb-technician", "candidate_signature"):
        "'minimum 140 x 60 pixels' is a lower bound, not a size.",
    ("unread_pixels", "upsc-capf-assistant-commandants-examination-2026", "triple_signature_image"):
        "'published image dimension 350-500 pixels' names no axis; choosing width or height would be an invention.",
    ("unread_pixels", "upsc-civil-services-examination-2026", "triple_signature_image"):
        "'350-500 pixels' names no axis.",
    ("unread_pixels", "upsc-combined-defence-services-examination-ii-2026", "triple_signature_image"):
        "'350-500 pixels' names no axis.",
    ("unread_pixels", "upsc-nda-na-examination-ii-2026", "triple_signature_image"):
        "'350-500 pixels' names no axis.",
}


def _words(name: str) -> set[str]:
    return {w for w in re.sub(r"[^a-z0-9 ]", " ", name.lower()).split() if w not in _STOP}


def _records() -> list[dict[str, Any]]:
    records = []
    for path in sorted(CATALOGUE.glob("exam_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not data.get("fictional_example"):
            records.append(data)
    return records


def audit() -> list[tuple[str, str, str]]:
    findings: list[tuple[str, str, str]] = []
    records = _records()
    fingerprints: dict[tuple[Any, ...], str] = {}

    for record in records:
        exam_id = record["exam"]["exam_id"]
        name = record["exam"]["exam_name"]
        requirements = record.get("requirements") or []

        if _SCOPE.search(name):
            findings.append(("scope_name", exam_id, name))

        for i, a in enumerate(requirements):
            for b in requirements[i + 1 :]:
                if a["requirement_type"] != b["requirement_type"]:
                    continue
                wa, wb = _words(a["requirement_name"]), _words(b["requirement_name"])
                if not wa or not wb:
                    continue
                if wa <= wb or wb <= wa or len(wa & wb) / len(wa | wb) >= 0.5:
                    findings.append(
                        ("duplicate", exam_id, f"{a['requirement_name']} | {b['requirement_name']}")
                    )

        for requirement in requirements:
            if requirement["requirement_type"] == "photograph":
                continue
            text = " ".join(
                str(requirement.get(k) or "") for k in ("content_instructions", "notes")
            )
            spec = requirement.get("file_spec") or {}
            if _PIXELS.search(text) and not spec.get("dimensions"):
                findings.append(("unread_pixels", exam_id, requirement["requirement_id"]))

        # One examination recorded twice: the same name once its qualifier is
        # set aside -- "(live photograph)", "- prior-cycle ..." -- with the same
        # requirements. Sister examinations from one commission share a notice
        # and a file list and are rightly separate, so the name has to agree.
        base = re.sub(r"\s*\(.*?\)\s*|\s+-\s+.*$", "", name).strip().lower()
        names = tuple(sorted(r["requirement_name"] for r in requirements))
        key = (base, names)
        if key in fingerprints and names:
            findings.append(("duplicate_exam", exam_id, fingerprints[key]))
        fingerprints.setdefault(key, exam_id)

    return findings


def unexplained(findings: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    return [f for f in findings if f not in ALLOWED]


def main() -> int:
    findings = audit()
    bad = unexplained(findings)
    for finding in findings:
        mark = "ok  " if finding in ALLOWED else "FAIL"
        reason = ALLOWED.get(finding, "")
        print(f"{mark} {finding[0]:15} {finding[1]} :: {finding[2]}" + (f"  ({reason})" if reason else ""))
    print(f"\n{len(findings)} findings, {len(bad)} unexplained")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
