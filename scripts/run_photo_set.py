"""Run a folder of photographs through the rule pipeline and report on them.

Built for looking at output, not at numbers. The recurring failure mode
recorded in HANDOFF.md is that every metric which improves by removing content
reads as an improvement -- paper got whiter as a thumb impression was
destroyed, crop tightness improved while letters lost their strokes -- and in
each case the numbers stayed green and only looking at the image caught it.

So this writes the prepared files somewhere you can open them, and prints a
table beside them rather than instead of them.

    python scripts/run_photo_set.py --input-dir "C:/Users/dmbar/Pictures/new-test-images"

Add --contact-sheet to get a single image of every result, which is the
fastest way to spot the one that went wrong.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = REPO_ROOT / "services" / "image-engine" / ".venv" / "Scripts" / "python.exe"
FACE_MODEL = REPO_ROOT / "model-assets" / "blaze_face_short_range.tflite"
SEGMENTER = REPO_ROOT / "model-assets" / "selfie_multiclass_256x256.tflite"
BIREFNET_DIR = REPO_ROOT / "model-assets" / "birefnet"

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def _run_one(
    image: Path, rule: Path, out_dir: Path, backend: str, quality: str
) -> dict[str, object]:
    """Prepare one photograph, returning what the pipeline said about it."""
    job_dir = out_dir / image.stem
    job_dir.mkdir(parents=True, exist_ok=True)

    command = [
        str(PYTHON), "-m", "exam_photo", "process-rule",
        "--input", str(image),
        "--rule", str(rule),
        "--output-dir", str(job_dir),
        "--save-output", "--save-report", "--overwrite",
        "--json",
        "--quality-mode", quality,
        "--matting-backend", backend,
        "--face-model-path", str(FACE_MODEL),
        "--segmenter-model-path", str(SEGMENTER),
        # Keep going when a photograph is judged non-compliant: a rejected
        # result is exactly the one worth looking at.
        "--allow-invalid-output",
    ]
    if backend in {"birefnet", "birefnet_onnx"}:
        command += ["--birefnet-model-dir", str(BIREFNET_DIR)]

    started = time.monotonic()
    proc = subprocess.run(command, capture_output=True, text=True, cwd=REPO_ROOT)
    elapsed = time.monotonic() - started

    row: dict[str, object] = {"name": image.name, "seconds": round(elapsed, 1)}

    report = job_dir / "processing_report.json"
    if report.exists():
        data = json.loads(report.read_text(encoding="utf-8"))
        row.update(
            valid=data.get("is_valid"),
            compliant=data.get("rule_compliant"),
            quality_ok=data.get("visual_quality_acceptable"),
            issues=data.get("issue_codes") or [],
            width=data.get("final_width"),
            height=data.get("final_height"),
            bytes=data.get("final_bytes"),
        )
    else:
        # No report means the run failed before it could write one; the
        # engine's own message is more useful than a generic failure.
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        row.update(valid=None, issues=["DID_NOT_RUN"], error=tail[-1] if tail else "")
    return row


def _contact_sheet(out_dir: Path, rows: list[dict[str, object]], path: Path) -> None:
    """One image of every result, because 40 files are not 40 openings."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Pillow not available; skipping contact sheet")
        return

    tiles = []
    for row in rows:
        produced = out_dir / Path(str(row["name"])).stem / "exam_photo.jpg"
        if produced.exists():
            tiles.append((str(row["name"]), Image.open(produced).convert("RGB"), row))

    if not tiles:
        print("nothing produced; no contact sheet")
        return

    cell_w, cell_h, label_h = 200, 200, 26
    cols = 8
    rows_n = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows_n * (cell_h + label_h)), (250, 250, 250))
    draw = ImageDraw.Draw(sheet)

    for index, (name, image, row) in enumerate(tiles):
        image.thumbnail((cell_w, cell_h))
        x = (index % cols) * cell_w
        y = (index // cols) * (cell_h + label_h)
        sheet.paste(image, (x + (cell_w - image.width) // 2, y))
        # Flag anything the pipeline was unhappy about, so a bad one is
        # findable without cross-referencing the table.
        flag = "" if row.get("valid") else "  !"
        draw.text((x + 4, y + cell_h + 6), f"{name[:26]}{flag}", fill=(40, 40, 40))

    sheet.save(path)
    print(f"contact sheet: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument(
        "--rule",
        type=Path,
        default=REPO_ROOT / "examples" / "rules" / "exam_common_admission_test_2025.json",
        help="Rule to prepare against. Any file in examples/rules/ works.",
    )
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument(
        "--backend",
        default="birefnet_onnx" if BIREFNET_DIR.exists() else "mediapipe",
        choices=["mediapipe", "birefnet", "birefnet_onnx"],
        help=(
            "mediapipe is fast but its 256px mask gives visibly blocky edges; "
            "birefnet is what the product ships and what output should be "
            "judged on."
        ),
    )
    parser.add_argument("--quality-mode", default="balanced", choices=["fast", "balanced", "high"])
    parser.add_argument("--limit", type=int, default=0, help="Only the first N images.")
    parser.add_argument("--contact-sheet", action="store_true")
    args = parser.parse_args()

    images = sorted(
        p for p in args.input_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES
    )
    if args.limit:
        images = images[: args.limit]
    if not images:
        print(f"no images in {args.input_dir}")
        return 1

    out_dir = args.out_dir or (args.input_dir.parent / f"{args.input_dir.name}-output")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"{len(images)} images  ->  {out_dir}")
    print(f"rule: {args.rule.name}   backend: {args.backend}   quality: {args.quality_mode}")
    print()

    rows = []
    for index, image in enumerate(images, 1):
        print(f"[{index}/{len(images)}] {image.name} ", end="", flush=True)
        row = _run_one(image, args.rule, out_dir, args.backend, args.quality_mode)
        rows.append(row)
        mark = "ok " if row.get("valid") else "FLAG"
        issues = ",".join(str(i) for i in (row.get("issues") or [])) or "-"
        print(f"{mark} {row['seconds']}s  {issues}")

    print()
    produced = sum(1 for r in rows if r.get("width"))
    flagged = [r for r in rows if not r.get("valid")]
    total = sum(float(r["seconds"]) for r in rows)
    print(f"produced {produced}/{len(rows)}   flagged {len(flagged)}   "
          f"total {total:.0f}s   mean {total/len(rows):.1f}s")

    if flagged:
        print("\nflagged:")
        for row in flagged:
            print(f"  {row['name']}: {','.join(str(i) for i in (row.get('issues') or []))}")

    summary = out_dir / "summary.json"
    summary.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nper-image results: {summary}")

    if args.contact_sheet:
        _contact_sheet(out_dir, rows, out_dir / "contact-sheet.png")

    return 0


if __name__ == "__main__":
    sys.exit(main())
