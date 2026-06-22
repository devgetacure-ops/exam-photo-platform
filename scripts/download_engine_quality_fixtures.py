import urllib.request
import re
import os
import hashlib
from PIL import Image
import io
import json
import sys
import argparse
import shutil

headers = {'User-Agent': 'ExamPhotoPlatformTest/1.0 (dmbar@gemini-developer.com)'}

def get_direct_url(page_url):
    # If the page is "local", there's no remote resolution needed
    if page_url == "local":
        return None
    try:
        req = urllib.request.Request(page_url, headers=headers)
        html = urllib.request.urlopen(req).read().decode('utf-8')
        m = re.search(r'href="(https://upload\.wikimedia\.org/wikipedia/commons/[^"]+)" class="internal"', html)
        if m:
            return m.group(1)
    except Exception as e:
        print(f"Error fetching page {page_url}: {e}", file=sys.stderr)
    return None

def verify_sha256(data: bytes, expected_sha: str) -> bool:
    h = hashlib.sha256(data).hexdigest()
    return h == expected_sha

def download_and_normalize(entry: dict, out_dir: str, require_real: bool) -> bool:
    fixture_id = entry["fixture_id"]
    filename = f"{fixture_id}.jpg"
    dest_path = os.path.join(out_dir, filename)

    # Check if already exists and matches normalized hash
    if os.path.exists(dest_path):
        with open(dest_path, "rb") as f:
            existing_data = f.read()
        if verify_sha256(existing_data, entry["normalized_sha256"]):
            print(f"{filename} already exists and is valid. Skipping download.")
            return True
        else:
            print(f"{filename} exists but has invalid hash. Re-downloading.")

    # Local sources handling
    if entry["source_page_url"] == "local":
        # Resolve source URL path relative to repo root
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Parse local path
        local_rel = entry["source_url"].replace("local://", "")
        src_path = os.path.join(repo_root, local_rel)
        if not os.path.exists(src_path):
            print(f"Error: Local fixture source {src_path} not found.", file=sys.stderr)
            if require_real:
                sys.exit(1)
            return False

        with open(src_path, "rb") as f:
            raw_data = f.read()
        
        if not verify_sha256(raw_data, entry["source_sha256"]):
            print(f"Error: Local source hash mismatch for {fixture_id}.", file=sys.stderr)
            if require_real:
                sys.exit(1)
            return False

        # Local files are copied directly or resized if needed (manifest says normalized_sha matches source_sha)
        shutil.copy2(src_path, dest_path)
        print(f"Copied local fixture {fixture_id} to {dest_path}")
        return True

    # Remote sources handling
    direct_url = get_direct_url(entry["source_page_url"])
    if not direct_url:
        print(f"Error: Could not resolve direct URL for {fixture_id}.", file=sys.stderr)
        if require_real:
            sys.exit(1)
        return False

    # Download source image
    print(f"Downloading {fixture_id} from {direct_url}...")
    try:
        req = urllib.request.Request(direct_url, headers=headers)
        raw_data = urllib.request.urlopen(req).read()
    except Exception as e:
        print(f"Error downloading {fixture_id}: {e}", file=sys.stderr)
        if require_real:
            sys.exit(1)
        return False

    # Verify source hash
    if not verify_sha256(raw_data, entry["source_sha256"]):
        print(f"Error: Downloaded source hash mismatch for {fixture_id}. Expected {entry['source_sha256']}", file=sys.stderr)
        if require_real:
            sys.exit(1)
        return False

    # Normalize source image
    try:
        img = Image.open(io.BytesIO(raw_data))
        w, h = img.size
        max_dim = entry["normalization"]["maximum_dimension"]
        if w > max_dim or h > max_dim:
            if w > h:
                new_w = max_dim
                new_h = int(round(h * (max_dim / w)))
            else:
                new_h = max_dim
                new_w = int(round(w * (max_dim / h)))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        norm_buffer = io.BytesIO()
        img.save(norm_buffer, format="JPEG", quality=entry["normalization"]["quality"])
        norm_data = norm_buffer.getvalue()

        # Verify normalized hash
        if not verify_sha256(norm_data, entry["normalized_sha256"]):
            print(f"Error: Normalized hash mismatch for {fixture_id}. Expected {entry['normalized_sha256']}", file=sys.stderr)
            if require_real:
                sys.exit(1)
            return False

        # Save locally
        with open(dest_path, "wb") as f:
            f.write(norm_data)
        print(f"Successfully processed and saved {fixture_id}")
        return True
    except Exception as e:
        print(f"Error normalizing {fixture_id}: {e}", file=sys.stderr)
        if require_real:
            sys.exit(1)
        return False

def main():
    parser = argparse.ArgumentParser(description="Download and normalize engine quality fixtures.")
    parser.add_argument("--require-real", action="store_true", help="Fail if download fails.")
    args = parser.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_path = os.path.join(repo_root, "tests", "fixtures", "engine_quality", "fixture_manifest.json")
    out_dir = os.path.join(repo_root, "tests", "fixtures", "engine_quality", "base")
    os.makedirs(out_dir, exist_ok=True)

    if not os.path.exists(manifest_path):
        print(f"Error: Manifest file {manifest_path} not found.", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    success = True
    for entry in manifest:
        if not download_and_normalize(entry, out_dir, args.require_real):
            success = False

    if not success and args.require_real:
        sys.exit(1)
    print("Fixture download and verification complete.")

if __name__ == "__main__":
    main()
