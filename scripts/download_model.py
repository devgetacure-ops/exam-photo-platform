#!/usr/bin/env python
"""Model acquisition helper for the MediaPipe BlazeFace face-detection asset.

Usage
-----
    python scripts/download_model.py [--variant short_range|full_range] [--dest PATH]

This script is an operator-invoked tool. It never runs automatically during
normal image processing. The model file must be acquired before face detection
can be used.

Behaviour
---------
1. Reads model-manifests/face-detector.json.
2. Checks whether the model file already exists and is verified — exits
   successfully if so.
3. Prints the download URL, expected SHA-256, size, and licence notice.
4. Prompts for confirmation, then downloads via urllib.request (stdlib only).
5. Verifies SHA-256 after download; deletes the file and exits with an error
   on mismatch.
6. Updates model-manifests/face-detector.json with the selected variant and
   verified SHA-256 / size if they were marked PENDING.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Model catalogue — curated variant records
# ---------------------------------------------------------------------------
# Source: https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector
# Licence: Apache 2.0 (model files) — verify against the model card URL below
# before redistribution.

_VARIANTS: dict[str, dict[str, str]] = {
    "short_range": {
        "filename": "blaze_face_short_range.tflite",
        "url": (
            "https://storage.googleapis.com/mediapipe-models/face_detector/"
            "blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
        ),
        "model_card_url": (
            "https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector#models"
        ),
        "licence_url": "https://www.apache.org/licenses/LICENSE-2.0",
        "description": (
            "Optimised for close-range selfie-style images. "
            "Best when the face occupies a large portion of the frame."
        ),
    },
    "full_range": {
        "filename": "blaze_face_full_range.tflite",
        "url": (
            "https://storage.googleapis.com/mediapipe-models/face_detector/"
            "blaze_face_full_range/float16/1/blaze_face_full_range.tflite"
        ),
        "model_card_url": (
            "https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector#models"
        ),
        "licence_url": "https://www.apache.org/licenses/LICENSE-2.0",
        "description": (
            "Designed for faces occupying a smaller portion of the frame "
            "(half-body, group photos). Recommended for general exam-photo uploads."
        ),
    },
}

# ---------------------------------------------------------------------------
# Repository layout
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
_MANIFEST_PATH = _REPO_ROOT / "model-manifests" / "face-detector.json"
_DEFAULT_ASSET_DIR = _REPO_ROOT / "model-assets"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest() -> dict[str, object]:
    if not _MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found at {_MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)
    with _MANIFEST_PATH.open() as fh:
        return json.load(fh)  # type: ignore[no-any-return]


def _save_manifest(data: dict[str, object]) -> None:
    with _MANIFEST_PATH.open("w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


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
    print()  # newline after progress


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and verify a MediaPipe BlazeFace model asset."
    )
    parser.add_argument(
        "--variant",
        choices=list(_VARIANTS.keys()),
        default="short_range",
        help="BlazeFace model variant to download (default: short_range).",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=None,
        help=(
            "Destination directory for the model asset file. "
            f"Default: {_DEFAULT_ASSET_DIR}"
        ),
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the download confirmation prompt.",
    )
    args = parser.parse_args()

    manifest = _load_manifest()

    # Load variant configuration from manifest
    try:
        variants = manifest["variants"]
        assert isinstance(variants, dict)
        variant = variants[args.variant]
        expected_sha = variant["sha256"]
        source_url = variant["source_url"]
        filename = variant["filename"]
    except Exception as ex:
        print(
            f"ERROR: Variant '{args.variant}' not properly configured in manifest: {ex}",
            file=sys.stderr,
        )
        sys.exit(1)

    dest_dir: Path = args.dest or _DEFAULT_ASSET_DIR
    dest_file = dest_dir / filename

    # --- Already present and verified? ---
    if dest_file.exists():
        actual_sha256 = _sha256_file(dest_file)
        if actual_sha256 == expected_sha:
            print(f"OK Model already present and verified: {dest_file}")
            return
        else:
            print(
                f"WARNING: existing model file SHA-256 does not match expected variant SHA.\n"
                f"  File:     {actual_sha256}\n"
                f"  Expected: {expected_sha}\n"
                "Deleting mismatching file and re-downloading."
            )
            dest_file.unlink()

    # --- Licence notice ---
    print("\n" + "=" * 70)
    print("MediaPipe BlazeFace Model — Licence Notice")
    print("=" * 70)
    print(f"  Variant:      {args.variant}")
    print(f"  Description:  {variant.get('description', '(not recorded)')}")
    print(f"  Source URL:   {source_url}")
    print(f"  Model card:   {variant.get('model_card_url', '(not recorded)')}")
    print(
        f"  Licence:      Apache 2.0 ({variant.get('licence_url', '(not recorded)')})"
    )
    print(
        "\n  NOTE: Verify the model card independently before redistribution.\n"
        "  The model file licence must be confirmed separately from the\n"
        "  mediapipe package licence.\n"
    )
    print("=" * 70)

    if not args.yes:
        answer = input("Proceed with download? [y/N]: ").strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    _download(source_url, dest_file)

    # --- Verify ---
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

    # --- Update manifest ---
    manifest["variant"] = args.variant
    manifest["source_url"] = source_url
    manifest["sha256"] = actual_sha256
    manifest["size_bytes"] = size_bytes
    manifest["licence"] = "Apache-2.0"
    manifest["licence_url"] = variant.get(
        "licence_url", "https://www.apache.org/licenses/LICENSE-2.0"
    )
    manifest["model_card_url"] = variant.get(
        "model_card_url",
        "https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector#models",
    )
    manifest["local_model_path_default"] = f"model-assets/{filename}"
    _save_manifest(manifest)

    print(
        f"\nOK Model downloaded and manifest updated.\n"
        f"  File:     {dest_file}\n"
        f"  Manifest: {_MANIFEST_PATH}\n"
        "\nIMPORTANT: Independently verify the model licence via the model card URL\n"
        "before distributing this asset or using it in production."
    )


if __name__ == "__main__":
    main()
