#!/usr/bin/env python
"""Model acquisition helper for the MediaPipe selfie segmentation assets.

Usage
-----
    python scripts/download_segmenter.py [--variant selfie_multiclass_256x256|selfie_bin_general] [--dest PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

_VARIANTS: dict[str, dict[str, str]] = {
    "selfie_multiclass_256x256": {
        "filename": "selfie_multiclass_256x256.tflite",
        "description": "MediaPipe Selfie Multiclass model predicting background, hair, body, face, clothes, and accessories.",
        "url": "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite",
        "model_card_url": "https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Multiclass%20Segmentation.pdf",
        "licence_url": "https://www.apache.org/licenses/LICENSE-2.0"
    },
    "selfie_bin_general": {
        "filename": "selfie_segmentation.tflite",
        "description": "MediaPipe Selfie Segmentation general binary model separating background and person.",
        "url": "https://storage.googleapis.com/mediapipe-assets/selfie_segmentation.tflite",
        "model_card_url": "https://ai.google.dev/edge/mediapipe/solutions/vision/selfie_segmentation#models",
        "licence_url": "https://www.apache.org/licenses/LICENSE-2.0"
    }
}

_REPO_ROOT = Path(__file__).resolve().parent.parent
_MANIFEST_PATH = _REPO_ROOT / "model-manifests" / "subject-segmenter.json"
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
        description="Download and verify a MediaPipe Selfie Segmentation model asset."
    )
    parser.add_argument(
        "--variant",
        choices=list(_VARIANTS.keys()),
        default="selfie_multiclass_256x256",
        help="Selfie model variant to download (default: selfie_multiclass_256x256).",
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
        print(f"ERROR: Variant '{args.variant}' not properly configured in manifest: {ex}", file=sys.stderr)
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
    print("MediaPipe Selfie Segmentation Model — Licence Notice")
    print("=" * 70)
    print(f"  Variant:      {args.variant}")
    print(f"  Description:  {_VARIANTS[args.variant]['description']}")
    print(f"  Source URL:   {source_url}")
    print(f"  Model card:   {variant.get('model_card_url')}")
    print(f"  Licence:      Apache 2.0 ({variant.get('licence_url')})")
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
    manifest["selected_variant"] = args.variant
    manifest["source_url"] = source_url
    manifest["sha256"] = actual_sha256
    manifest["size_bytes"] = size_bytes
    manifest["licence"] = "Apache-2.0"
    manifest["licence_url"] = variant.get("licence_url", "https://www.apache.org/licenses/LICENSE-2.0")
    manifest["model_card_url"] = variant.get("model_card_url", "https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Multiclass%20Segmentation.pdf")
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
