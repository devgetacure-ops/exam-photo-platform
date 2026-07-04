#!/usr/bin/env python3
"""Smoke test script verifying local API processing endpoints and TTL lifecycle."""

import json
import os
import shutil
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Resolve python path to include services/image-engine/src
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "services" / "image-engine" / "src"))

from exam_photo.api.app import app, service
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore
from exam_photo.api.jobs import JobRegistry


def main() -> int:
    print("Starting API smoke test...")

    # 1. Check model presence if --require-real is set
    require_real = "--require-real" in sys.argv
    if require_real:
        face_model = repo_root / "model-assets" / "blaze_face_short_range.tflite"
        seg_model = repo_root / "model-assets" / "selfie_segmentation.tflite"

        if not face_model.exists():
            print(f"Error: Face model not found at {face_model}", file=sys.stderr)
            return 1
        if not seg_model.exists():
            print(f"Error: Segmenter model not found at {seg_model}", file=sys.stderr)
            return 1

        # Configure environment variables to use real models
        os.environ["EXAM_PHOTO_FACE_MODEL_PATH"] = str(face_model)
        os.environ["EXAM_PHOTO_FACE_MODEL_SHA256"] = (
            "b4578f35940bf5a1a655214a1cce5cab13eba73c1297cd78e1a04c2380b0152f"
        )
        os.environ["EXAM_PHOTO_SEGMENTER_MODEL_PATH"] = str(seg_model)
        os.environ["EXAM_PHOTO_SEGMENTER_MODEL_SHA256"] = (
            "9ee168ec7c8f2a16c56fe8e1cfbc514974cbbb7e434051b455635f1bd1462f5c"
        )

    # 2. Setup temp artifact root for smoke testing
    smoke_root = repo_root / ".tmp" / "smoke_api_artifacts"
    if smoke_root.exists():
        shutil.rmtree(smoke_root)
    smoke_root.mkdir(parents=True, exist_ok=True)

    # Override app settings
    service.settings = ApiSettings(
        artifact_root=smoke_root,
        max_upload_bytes=10 * 1024 * 1024,
        job_ttl_seconds=3600,
    )
    service.store = LocalArtifactStore(smoke_root)
    service.registry = JobRegistry(smoke_root)

    client = TestClient(app)

    # 3. Resolve inputs
    fixture_path = repo_root / "tests" / "fixtures" / "marie_curie_curly_hair.jpg"
    rule_path = (
        repo_root
        / "examples"
        / "rules"
        / "sample_range_200_300_width_230_400_height_50kb_white_bg.json"
    )

    if not fixture_path.exists():
        print(f"Error: Fixture not found at {fixture_path}", file=sys.stderr)
        return 1
    if not rule_path.exists():
        print(f"Error: Rule not found at {rule_path}", file=sys.stderr)
        return 1

    image_bytes = fixture_path.read_bytes()
    rule_dict = json.loads(rule_path.read_text(encoding="utf-8"))

    # 4. Trigger process request
    print("Posting image processing request...")
    response = client.post(
        "/v1/process",
        files={"file": ("marie_curie.jpg", image_bytes, "image/jpeg")},
        data={"rule": json.dumps(rule_dict)},
    )

    if response.status_code != 200:
        print(
            f"Error: Process request failed: {response.status_code}\n{response.text}",
            file=sys.stderr,
        )
        return 1

    data = response.json()
    job_id = data["job_id"]
    status = data["status"]
    report_url = data["report_url"]
    output_url = data["output_url"]

    print(f"Job created: {job_id}, initial status: {status}")
    assert job_id.startswith("job_")
    assert status == "SUCCEEDED"
    assert report_url == f"/v1/jobs/{job_id}/report"
    assert output_url == f"/v1/jobs/{job_id}/output"
    assert data["is_valid"] is True
    assert data["output_filename"] is not None
    assert data["issue_codes"] == []

    # 5. Retrieve Job Status
    response = client.get(f"/v1/jobs/{job_id}")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["status"] == "SUCCEEDED"
    assert status_data["is_valid"] is True

    # 6. Retrieve Report
    response = client.get(report_url)
    assert response.status_code == 200
    report_data = response.json()
    assert report_data["is_valid"] is True
    assert "encoded_bytes" not in report_data
    print("Report verified successfully (no binary encoded_bytes found).")

    # 7. Retrieve Output
    response = client.get(output_url)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    out_img = response.content
    assert len(out_img) > 0
    print(f"Output candidate retrieved successfully: {len(out_img)} bytes.")

    # 7b. Verify PIL decode
    from PIL import Image
    import io

    img = Image.open(io.BytesIO(out_img))
    img.load()
    assert img.format == "JPEG"
    print("Output candidate verified as valid JPEG image via PIL decode.")

    # 8. Verify TTL Cleanup
    # Manually edit the job manifest file to make it expired
    manifest_path = smoke_root / job_id / "job.json"
    assert manifest_path.is_file()

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_data["expires_at"] = "2020-01-01T00:00:00.000000+00:00"
    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    print("Triggering expired job cleanup...")
    cleanup_response = client.post("/v1/cleanup-expired")
    assert cleanup_response.status_code == 200
    assert cleanup_response.json()["cleaned_count"] == 1

    # Verify folder is deleted
    assert not (smoke_root / job_id).exists()
    print("Expired job artifacts successfully cleaned up from disk.")

    # Status check after deletion should return DELETED status
    status_response = client.get(f"/v1/jobs/{job_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "DELETED"

    # 9. Test upload limit checks
    service.settings.max_upload_bytes = 100
    response = client.post(
        "/v1/process",
        files={"file": ("marie_curie.jpg", image_bytes, "image/jpeg")},
        data={"rule": json.dumps(rule_dict)},
    )
    assert response.status_code == 413
    print("Upload size limit enforcement verified successfully.")

    # Cleanup smoke root
    if smoke_root.exists():
        shutil.rmtree(smoke_root)

    print("API smoke test completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
