"""Put real photographs through every examination's photograph rule.

Why this exists (DEC-104): on launch day every photograph for twelve
examinations failed on the live site, and no check had caught it, because the
tests asserted each rule's *configuration* rather than running a real
photograph through it. This script does what a candidate does, for all of
them: one portrait at a time, the full pipeline, the examination's own rule,
and a verdict per examination.

Portraits are public-domain official photographs already in
`tests/fixtures/engine_quality/base/` (see its `fixture_manifest.json`), so
nothing private is used and nothing is uploaded.

Run it where the models live, outside the serving container so it cannot
starve the live engine of memory:

    docker compose -f deploy/docker-compose.yml run --rm --no-deps \\
      -v "$PWD/tests:/app/tests:ro" -v "$PWD/scripts:/app/scripts:ro" \\
      -v /tmp/smoke:/out engine python /app/scripts/smoke_catalogue_photographs.py

Exit status is 1 if any examination rejected every portrait, which is what a
broken rule looks like.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import time
from collections import Counter
from pathlib import Path

from exam_photo.cli import main as cli

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "examples" / "rules"
PORTRAITS = ROOT / "tests" / "fixtures" / "engine_quality" / "base"
DEFAULT_PORTRAITS = ["portrait_murmu", "portrait_kalam", "portrait_singh", "portrait_obama"]


def photograph_rules() -> list[tuple[str, str, Path]]:
    found = []
    for path in sorted(RULES.glob("exam_*.json")):
        rule = json.loads(path.read_text(encoding="utf-8"))
        if not rule.get("image_requirements"):
            continue
        exam = rule.get("exam") or {}
        found.append((exam.get("exam_id", path.stem), exam.get("exam_name", ""), path))
    return found


def run_one(image: Path, rule: Path) -> dict:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        cli(["process-rule", "--input", str(image), "--rule", str(rule), "--json"])
    return json.loads(buffer.getvalue())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--portraits", nargs="*", default=DEFAULT_PORTRAITS)
    parser.add_argument("--out", default="/out/smoke.json")
    parser.add_argument("--only", nargs="*", default=None, help="exam ids to run")
    args = parser.parse_args()

    images = [PORTRAITS / f"{name}.jpg" for name in args.portraits]
    missing = [str(p) for p in images if not p.is_file()]
    if missing:
        print("missing portraits:", missing, file=sys.stderr)
        return 2

    rules = photograph_rules()
    if args.only:
        rules = [r for r in rules if r[0] in set(args.only)]
    results = []
    started = time.time()
    for number, (exam_id, name, path) in enumerate(rules, 1):
        runs = []
        for image in images:
            t = time.time()
            try:
                report = run_one(image, path)
                runs.append(
                    {
                        "portrait": image.stem,
                        "valid": bool(report.get("is_valid")),
                        "codes": report.get("issue_codes") or [],
                        "mode": report.get("selected_crop_mode"),
                        "size": [report.get("final_width"), report.get("final_height")],
                        "bytes": report.get("final_bytes"),
                        "seconds": round(time.time() - t, 1),
                    }
                )
            except Exception as error:  # a crash is a finding, not a stop
                runs.append({"portrait": image.stem, "valid": False, "codes": [f"CRASH: {error}"]})
        passed = sum(1 for run in runs if run["valid"])
        results.append({"exam_id": exam_id, "exam_name": name, "passed": passed, "of": len(runs), "runs": runs})
        codes = Counter(code for run in runs if not run["valid"] for code in run["codes"])
        print(
            f"[{number}/{len(rules)}] {passed}/{len(runs)} {exam_id}"
            + (f"  {dict(codes)}" if codes else ""),
            flush=True,
        )
        Path(args.out).write_text(json.dumps(results, indent=2), encoding="utf-8")

    broken = [r for r in results if r["passed"] == 0]
    partial = [r for r in results if 0 < r["passed"] < r["of"]]
    print(
        f"\n{len(results)} examinations, {len(broken)} rejected every portrait, "
        f"{len(partial)} rejected some, in {round((time.time() - started) / 60, 1)} min",
        flush=True,
    )
    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
