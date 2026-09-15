"""Check researched facts against the pages they cite (DEC-082, DEC-095).

A researched fact is published only when its `source_quote` is on its
`source_url` and every figure in its sentence is in that quote. This is the
check the 2026-09-13 curation ran and did not keep; it is kept now so the next
delivery is checked the same way rather than trusted.

    python scripts/verify_fact_passages.py --as-of 2026-09-15 --cache <dir>

Pages are fetched with curl (several government hosts serve certificates a
strict client rejects) and PDFs are read with pypdfium2, so run it with the
image engine's interpreter. `--cache` keeps the downloads, keyed by the first
twelve hex digits of the URL's SHA-1, so a re-run reads the same bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
TRIVIA = REPO_ROOT / "packages" / "exam-rules" / "research" / "exam_trivia_2026.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126 Safari/537.36"


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def page_text(url: str, cache: Path) -> str:
    """The readable text of a page or PDF, whitespace collapsed."""
    key = hashlib.sha1(url.encode()).hexdigest()[:12]
    extracted = cache / f"{key}.txt"
    if extracted.exists():
        return extracted.read_text(encoding="utf-8")
    raw = cache / f"{key}.bin"
    if not raw.exists():
        subprocess.run(
            ["curl", "-k", "-L", "-s", "--http1.1", "--max-time", "60",
             "-A", USER_AGENT, "-o", str(raw), url],
            check=False,
        )
    data = raw.read_bytes() if raw.exists() else b""
    if data[:5] == b"%PDF-":
        import pypdfium2 as pdfium

        document = pdfium.PdfDocument(data)
        text = "\n".join(
            document[i].get_textpage().get_text_range() for i in range(len(document))
        )
    else:
        markup = data.decode("utf-8", "replace")
        markup = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", markup)
        text = html.unescape(re.sub(r"(?s)<[^>]+>", " ", markup))
    text = _normalise(text)
    extracted.write_text(text, encoding="utf-8")
    return text


def figures(sentence: str) -> list[str]:
    """Every number of two or more digits, commas removed ("5,81,305" -> "581305")."""
    found = re.findall(r"\d[\d,.]*\d", sentence)
    return [f.replace(",", "").strip(".") for f in found]


def problems(fact: dict[str, Any], cache: Path) -> list[str]:
    quote = _normalise(str(fact.get("source_quote") or ""))
    if not quote:
        return ["no source_quote"]
    text = page_text(str(fact["source_url"]), cache)
    issues = []
    if quote not in text:
        issues.append("the quote is not on the page")
    bare_quote = quote.replace(",", "")
    for figure in figures(str(fact.get("text") or "")):
        if figure not in bare_quote:
            issues.append(f"{figure} is not in the quote")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trivia", type=Path, default=TRIVIA)
    parser.add_argument("--as-of", help="Check only facts with this as_of date.")
    parser.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)

    exams = json.loads(args.trivia.read_text(encoding="utf-8"))["exams"]
    checked = failed = 0
    for exam_id, facts in exams.items():
        for fact in facts:
            if args.as_of and fact.get("as_of") != args.as_of:
                continue
            checked += 1
            issues = problems(fact, args.cache)
            if issues:
                failed += 1
                print(f"FAIL {exam_id}: {fact['text'][:70]} -- {'; '.join(issues)}")
    print(f"{checked} checked, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
