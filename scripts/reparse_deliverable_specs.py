"""Read pixel sizes the extractor used to miss, from the corpus's own sentences.

``extract_deliverables.py`` must not be re-run after a merge (it regenerates the
corpus from the 2026 report and discards everything merged since). But its
parser is where the sentence patterns live, and the 2026-09-14 audit found
21 signature specifications whose pixel size sat in the text and never reached
the record -- "width between 150-220 pixels and height between 250-320
pixels", "140 x 60 pixels (preferred)", sizes whose dash or multiplication
sign a delivery's encoding had turned into a replacement character.

This applies the current parser to each deliverable's ``specification`` text
and fills ``parsed.dimensions_px`` **only where it is absent**. It never
overwrites a value, never touches sizes or formats, and prints every change.

Usage::

    python scripts/reparse_deliverable_specs.py --dry-run
    python scripts/reparse_deliverable_specs.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from extract_deliverables import _parse_specification  # noqa: E402

CORPUS = Path("packages/exam-rules/research/exam_deliverables_2026.json")


def reparse(records: list[dict]) -> list[str]:
    log: list[str] = []
    for record in records:
        for deliverable in record.get("deliverables") or []:
            parsed = deliverable.setdefault("parsed", {})
            if parsed.get("dimensions_px"):
                continue
            text = str(deliverable.get("specification") or "")
            found = _parse_specification(text).get("dimensions_px")
            if not found:
                continue
            parsed["dimensions_px"] = found
            log.append(
                f"DIMS+ {record.get('exam_name')} :: {deliverable.get('name')} :: "
                f"{found['mode']} :: {found['source_wording']!r}"
            )
    return log


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=CORPUS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    records = json.loads(args.corpus.read_text(encoding="utf-8"))
    log = reparse(records)
    for line in log:
        print(line)
    print(f"\n{len(log)} dimension blocks filled")
    if not args.dry_run:
        args.corpus.write_text(
            json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"written {args.corpus}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
