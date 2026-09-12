"""Generate the per-examination facts sidecar from the encoded rule records.

DEC-077. Facts are **derived, never authored** -- see
`exam_photo.orchestration.exam_facts` for why, and for the two rules that
bind what may be emitted. This script is the same shape as the rest of the
catalogue's generation: it reads `examples/rules/exam_*.json` and rewrites
`examples/rules/exam_facts.json` wholesale, so a hand edit is discarded on the
next run rather than surviving as an unsourced claim.

    python scripts/generate_exam_facts.py

Re-run it after `encode_exam_rules.py`, because it reads that script's output.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "services" / "image-engine" / "src"))

from exam_photo.orchestration.exam_facts import (  # noqa: E402
    derive_facts,
    merge_researched,
)

#: Deliberately outside the `exam_*` namespace: `encode_exam_rules.py`
#: deletes every `exam_*.json` before regenerating, so a sidecar named
#: `exam_facts.json` would be silently removed by the next encode and the
#: facts would vanish with no error anywhere.
SIDECAR_NAME = "candidate_facts.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rules", type=Path, default=REPO_ROOT / "examples" / "rules")
    parser.add_argument(
        "--trivia",
        type=Path,
        default=REPO_ROOT / "packages" / "exam-rules" / "research"
        / "exam_trivia_2026.json",
        help="Researched trivia to fold in, if it exists (DEC-078).",
    )
    parser.add_argument("--check", action="store_true",
                        help="Fail if the sidecar is out of date, for CI.")
    args = parser.parse_args()

    trivia: Dict[str, Any] = {}
    if args.trivia.is_file():
        try:
            document = json.loads(args.trivia.read_text(encoding="utf-8"))
            trivia = document.get("exams") or {}
            print(f"folding in researched trivia for {len(trivia)} examinations")
        except json.JSONDecodeError:
            print(f"  could not read {args.trivia}; ignoring it")

    unmatched = set(trivia)
    payload: Dict[str, Any] = {}
    kinds: Counter = Counter()
    empty: List[str] = []

    for path in sorted(args.rules.glob("exam_*.json")):
        try:
            rule = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"  skipped unreadable {path.name}")
            continue
        facts = derive_facts(rule)
        if not facts.exam_id:
            continue
        # Research keys by exam id where it knows one and by name otherwise,
        # because a researcher is given names and not our identifiers.
        entries = trivia.get(facts.exam_id) or trivia.get(facts.exam_name)
        unmatched.discard(facts.exam_id)
        unmatched.discard(facts.exam_name)
        facts = merge_researched(facts, entries)
        payload[facts.exam_id] = json.loads(facts.model_dump_json())
        for fact in facts.facts:
            kinds[fact.kind] += 1
        if not facts.facts:
            empty.append(facts.exam_name)

    document = {
        "_generated_by": "scripts/generate_exam_facts.py",
        "_note": (
            "Derived from the rule records, never hand-written (DEC-077), "
            "plus researched facts from exam_trivia_2026.json, each checked "
            "against its source page and naming its publisher (DEC-082). "
            "Re-running replaces this file, so an edit here is lost."
        ),
        "exams": payload,
    }

    target = args.rules / SIDECAR_NAME
    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        current = target.read_text(encoding="utf-8") if target.is_file() else ""
        if current != rendered:
            print(f"{SIDECAR_NAME} is out of date; re-run scripts/generate_exam_facts.py")
            return 1
        print(f"{SIDECAR_NAME} is up to date")
        return 0

    target.write_text(rendered, encoding="utf-8")
    total = sum(kinds.values())
    print(f"written {target.relative_to(REPO_ROOT)}")
    print(f"  examinations : {len(payload)}")
    print(f"  facts        : {total}")
    for kind, count in kinds.most_common():
        print(f"     {kind:14s} {count}")
    if unmatched:
        # Loud, because a trivia entry that matches no examination is research
        # that was paid for and is not being shown.
        print(f"  UNMATCHED trivia keys: {len(unmatched)}")
        for key in sorted(unmatched):
            print(f"     {key}")
    if empty:
        # Not a failure. An examination whose every value is a platform
        # estimate has nothing it can truthfully say, and saying nothing is
        # the correct outcome.
        print(f"  no facts     : {len(empty)}")
        for name in empty:
            print(f"     {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
