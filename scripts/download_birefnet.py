#!/usr/bin/env python
"""Model acquisition helper for the BiRefNet subject matting model.

Usage
-----
    python scripts/download_birefnet.py [--dest PATH] [--yes]

This script is an operator-invoked tool. It never runs automatically during
normal image processing.  BiRefNet is a multi-file Hugging Face Hub repository
rather than a single downloadable URL, so it is vendored with
``huggingface_hub.snapshot_download`` pinned to the exact revision recorded in
``model-manifests/birefnet.json`` (see DEC-031), and the primary weights file
is SHA-256 verified against that manifest the same way the single-file
face-detector and segmenter models are.

Behaviour
---------
1. Reads model-manifests/birefnet.json for the pinned repo_id/revision and the
   expected weights checksum.
2. Checks whether the weights file already exists locally with a matching
   checksum -- exits successfully if so.
3. Prints the source, revision, size, and licence notice.
4. Prompts for confirmation, then downloads via huggingface_hub (requires the
   `matting` extra: pip install -e ".[dev,matting]").
5. Verifies the weights SHA-256 after download; the directory is left in place
   on mismatch so the operator can inspect it, but the script exits non-zero.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_MANIFEST_PATH = _REPO_ROOT / "model-manifests" / "birefnet.json"
_DEFAULT_DEST_DIR = _REPO_ROOT / "model-assets" / "birefnet"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest() -> dict[str, object]:
    if not _MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found at {_MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)
    with _MANIFEST_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)  # type: ignore[no-any-return]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and verify the BiRefNet matting model."
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=None,
        help=f"Destination directory for the model files. Default: {_DEFAULT_DEST_DIR}",
    )
    parser.add_argument(
        "--yes", action="store_true", help="Skip the download confirmation prompt."
    )
    args = parser.parse_args()

    manifest = _load_manifest()
    repo_id = str(manifest["repo_id"])
    revision = str(manifest["revision"])
    weights_filename = str(manifest["weights_filename"])
    expected_sha = str(manifest["weights_sha256"])
    expected_size = int(manifest["weights_size_bytes"])  # type: ignore[arg-type]

    dest_dir: Path = args.dest or _DEFAULT_DEST_DIR
    weights_path = dest_dir / weights_filename

    if weights_path.exists():
        actual = _sha256_file(weights_path)
        if actual == expected_sha:
            print(f"OK Model already present and verified: {weights_path}")
            return
        print(
            f"WARNING: existing weights file SHA-256 does not match the manifest.\n"
            f"  File:     {actual}\n"
            f"  Expected: {expected_sha}\n"
            "Re-downloading."
        )

    print("\n" + "=" * 70)
    print("BiRefNet Subject Matting Model -- Licence Notice")
    print("=" * 70)
    print(f"  Repo:         {repo_id}")
    print(f"  Revision:     {revision}  (pinned; not 'main')")
    print(
        f"  Weights size: {expected_size:,} bytes (~{expected_size / (1 << 20):.0f} MiB)"
    )
    print(f"  Licence:      {manifest.get('licence', '(not recorded)')}")
    print(f"  Model card:   {manifest.get('model_card_url', '(not recorded)')}")
    print(
        "\n  NOTE: Verify the model card independently before redistribution.\n"
        "  Requires the 'matting' extra: pip install -e \".[dev,matting]\"\n"
    )
    print("=" * 70)

    if not args.yes:
        answer = input("Proceed with download? [y/N]: ").strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print(
            "ERROR: huggingface_hub is not installed. Install the 'matting' extra:\n"
            '  pip install -e ".[dev,matting]"',
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"\nDownloading {repo_id}@{revision} -> {dest_dir}")
    snapshot_download(
        repo_id=repo_id,
        revision=revision,
        local_dir=dest_dir,
        allow_patterns=["*.py", "*.json", "*.safetensors", "*.md", "LICENSE*"],
    )

    if not weights_path.exists():
        print(
            f"ERROR: expected weights file not found after download: {weights_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    actual_sha256 = _sha256_file(weights_path)
    size_bytes = weights_path.stat().st_size
    print(f"\nSHA-256: {actual_sha256}")
    print(f"Size:    {size_bytes:,} bytes")

    if actual_sha256 != expected_sha:
        print(
            f"\nERROR: SHA-256 mismatch!\n"
            f"  Expected: {expected_sha}\n"
            f"  Got:      {actual_sha256}\n"
            "The downloaded files were left in place for inspection; delete\n"
            f"{dest_dir} and re-run this script to try again.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"\nOK Model downloaded and verified.\n"
        f"  Directory: {dest_dir}\n"
        "\nIMPORTANT: Independently verify the model licence via the model card URL\n"
        "before distributing this asset or using it in production."
    )


if __name__ == "__main__":
    main()
