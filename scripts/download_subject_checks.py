#!/usr/bin/env python
"""Download and verify the two subject-check models (DEC-133).

Usage
-----
    python scripts/download_subject_checks.py [--yes]

The YuNet face verifier and the explicit-image classifier. Both are optional
to the engine: without them the checks are skipped and every other stage runs
as before, so a machine that has not run this still works. Production must.

Behaviour mirrors the other download scripts: read the manifest, skip a file
that is already present and verified, download, verify SHA-256, and delete on
a mismatch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_MANIFESTS = ("face-verifier-yunet.json", "explicit-image-classifier.json")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--yes", action="store_true", help="Do not ask first.")
    args = parser.parse_args()
    for name in _MANIFESTS:
        manifest = json.loads((_REPO_ROOT / "model-manifests" / name).read_text(encoding="utf-8"))
        dest = _REPO_ROOT / manifest["local_model_path_default"]
        if dest.is_file() and _sha256(dest) == manifest["sha256"]:
            print(f"{manifest['name']}: present and verified.")
            continue
        print(f"{manifest['name']} ({manifest['licence']}, {manifest['size_bytes']:,} bytes)")
        if not args.yes and input("Download? [y/N] ").strip().lower() != "y":
            print("Skipped.")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(
            manifest["source_url"], headers={"User-Agent": "exam-photo-setup/1.0"}
        )
        with urllib.request.urlopen(request, timeout=600) as response:
            dest.write_bytes(response.read())
        if _sha256(dest) != manifest["sha256"]:
            dest.unlink()
            print(f"ERROR: checksum mismatch for {dest.name}; deleted.", file=sys.stderr)
            sys.exit(1)
        print(f"  -> {dest} verified.")


if __name__ == "__main__":
    main()
