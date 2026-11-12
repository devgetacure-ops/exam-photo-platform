"""An explicit upload is refused and never stored (DEC-133)."""

import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from exam_photo.api.app import app
from exam_photo.api.jobs import JobRegistry
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore

client = TestClient(app, raise_server_exceptions=False)


class _AlwaysExplicit:
    def score(self, image: Image.Image) -> float:
        return 0.99


@pytest.fixture
def api(tmp_path):
    from exam_photo.api.app import service

    original = (
        service.settings,
        service.store,
        service.registry,
        service._explicit_classifier,
        service._explicit_unavailable,
    )
    service.settings = ApiSettings(
        artifact_root=tmp_path / "artifacts",
        max_upload_bytes=8 * 1024 * 1024,
        job_ttl_seconds=3600,
    )
    service.store = LocalArtifactStore(tmp_path / "artifacts")
    service.registry = JobRegistry(tmp_path / "artifacts")
    service._explicit_classifier = _AlwaysExplicit()  # type: ignore[assignment]
    service._explicit_unavailable = False
    try:
        yield service
    finally:
        (
            service.settings,
            service.store,
            service.registry,
            service._explicit_classifier,
            service._explicit_unavailable,
        ) = original


def _jpeg() -> bytes:
    image = Image.fromarray(np.full((300, 300, 3), 200, dtype=np.uint8))
    buffer = io.BytesIO()
    image.save(buffer, "JPEG")
    return buffer.getvalue()


@pytest.mark.parametrize("requirement", ["candidate_photograph", "candidate_signature"])
def test_an_explicit_upload_is_refused_and_nothing_is_kept(api, requirement):
    response = client.post(
        f"/v1/exams/ctet-september-2026/requirements/{requirement}/prepare",
        files={"file": ("upload.jpg", _jpeg(), "image/jpeg")},
        data={"kit_id": "kit_explicit_test"},
    )
    body = response.json()

    assert body["outcome"] == "not_produced"
    assert "CONTENT_NOT_ALLOWED" in body["issue_codes"]
    # Only the job's own record (status, issue code) remains; no image.
    job_dir = api.store.get_file_path(body["job_id"], ".")
    kept = sorted(p.name for p in job_dir.iterdir()) if job_dir.exists() else []
    assert kept in ([], ["job.json"])
