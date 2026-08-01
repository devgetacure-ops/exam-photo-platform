#!/usr/bin/env python
"""Model acquisition helper for the MediaPipe Face Landmarker asset.

Usage
-----
    python scripts/download_face_landmarker.py [--dest PATH] [--yes]

This script is an operator-invoked tool. It never runs automatically during
normal image processing.  The landmarker refines the chin and eye line of a
face that BlazeFace has already detected (see DEC-032); it is optional, and the
pipeline falls back to the detector's own coarse points when the asset is
absent.

Behaviour mirrors scripts/download_model.py: read the manifest, skip if the
file is already present and verified, print a licence notice, download, then
verify SHA-256 and delete on mismatch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_MANIFEST_PATH = _REPO_ROOT / "model-manifests" / "face-landmarker.json"
_DEFAULT_ASSET_DIR = _REPO_ROOT / "model-assets"


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


def _download(url: str, dest: Path) -> None:
    print(f"\nDownloading:\n  {url}\n  -> {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)

    def _progress(block_num: int, block_size: int, total_size: int) -> None:
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(100.0, downloaded / total_size * 100)
            print(
                f"\r  {pct:5.1f}% ({downloaded:,} / {total_size:,} bytes)",
                end="",
                flush=True,
            )

    urllib.request.urlretrieve(url, dest, reporthook=_progress)
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and verify the MediaPipe Face Landmarker asset."
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=None,
        help=f"Destination directory for the model asset. Default: {_DEFAULT_ASSET_DIR}",
    )
    parser.add_argument(
        "--yes", action="store_true", help="Skip the download confirmation prompt."
    )
    args = parser.parse_args()

    manifest = _load_manifest()
    filename = str(manifest["filename"])
    source_url = str(manifest["source_url"])
    expected_sha = str(manifest["sha256"])
    expected_size = int(manifest["size_bytes"])  # type: ignore[arg-type]

    dest_dir: Path = args.dest or _DEFAULT_ASSET_DIR
    dest_file = dest_dir / filename

    if dest_file.exists():
        actual = _sha256_file(dest_file)
        if actual == expected_sha:
            print(f"OK Model already present and verified: {dest_file}")
            return
        print(
            f"WARNING: existing model file SHA-256 does not match the manifest.\n"
            f"  File:     {actual}\n"
            f"  Expected: {expected_sha}\n"
            "Deleting mismatching file and re-downloading."
        )
        dest_file.unlink()

    print("\n" + "=" * 70)
    print("MediaPipe Face Landmarker -- Licence Notice")
    print("=" * 70)
    print(f"  File:         {filename}")
    print(f"  Source URL:   {source_url}")
    print(f"  Size:         {expected_size:,} bytes")
    print(f"  Licence:      {manifest.get('licence', '(not recorded)')}")
    print(f"  Model card:   {manifest.get('model_card_url', '(not recorded)')}")
    print(
        "\n  NOTE: Verify the model card independently before redistribution.\n"
    )
    print("=" * 70)

    if not args.yes:
        answer = input("Proceed with download? [y/N]: ").strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    _download(source_url, dest_file)

    actual_sha256 = _sha256_file(dest_file)
    size_bytes = dest_file.stat().st_size
    print(f"\nSHA-256: {actual_sha256}")
    print(f"Size:    {size_bytes:,} bytes")

    if actual_sha256 != expected_sha:
        dest_file.unlink()
        print(
            f"\nERROR: SHA-256 mismatch!\n"
            f"  Expected: {expected_sha}\n"
            f"  Got:      {actual_sha256}\n"
            "File deleted. Re-run this script to try again.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"\nOK Model downloaded and verified.\n"
        f"  File: {dest_file}\n"
        "\nIMPORTANT: Independently verify the model licence via the model card URL\n"
        "before distributing this asset or using it in production."
    )


if __name__ == "__main__":
    main()
