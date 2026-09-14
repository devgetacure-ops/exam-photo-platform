"""A photograph uploaded in a signature's place is refused, and never priced (note 23).

Negative first: a real (synthetic) signature must still be prepared. Uses the
public-domain frontal portrait fixture as the wrong upload.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from tests.api.test_kit_endpoints import EXAM, SIGNATURE, _signature_photo
from tests.helpers.fixtures import FIXTURES_DIR

from exam_photo.api.app import app
from exam_photo.api.jobs import JobRegistry
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore

client = TestClient(app, raise_server_exceptions=False)

FACE_MODEL = (
    Path(__file__).resolve().parents[4]
    / "model-assets"
    / "blaze_face_short_range.tflite"
)

pytestmark = [
    pytest.mark.mandatory_api,
    pytest.mark.skipif(not FACE_MODEL.exists(), reason="needs the face detector asset"),
]


@pytest.fixture
def api(tmp_path):
    from exam_photo.api.app import service

    original = (service.settings, service.store, service.registry)
    service.settings = ApiSettings(
        artifact_root=tmp_path / "artifacts",
        max_upload_bytes=8 * 1024 * 1024,
        job_ttl_seconds=3600,
    )
    service.store = LocalArtifactStore(tmp_path / "artifacts")
    service.registry = JobRegistry(tmp_path / "artifacts")
    try:
        yield service
    finally:
        service.settings, service.store, service.registry = original


def _prepare(content: bytes, kit_id: str):
    return client.post(
        f"/v1/exams/{EXAM}/requirements/{SIGNATURE}/prepare",
        files={"file": ("upload.jpg", content, "image/jpeg")},
        data={"kit_id": kit_id},
    )


def test_a_real_signature_is_still_prepared(api):
    body = _prepare(_signature_photo(), "kit_realsign").json()

    assert body["outcome"] in ("prepared", "prepared_with_findings")
    assert "UPLOAD_NOT_A_SIGNATURE" not in body["issue_codes"]


def test_a_portrait_uploaded_as_a_signature_is_refused_in_plain_words(api):
    portrait = (FIXTURES_DIR / "single_face_frontal.jpg").read_bytes()

    body = _prepare(portrait, "kit_portraitsign").json()

    assert body["outcome"] == "not_produced"
    assert body["issue_codes"] == ["UPLOAD_NOT_A_SIGNATURE"]
    assert body["output_url"] is None
    assert any("not a signature" in finding for finding in body["findings"])


def test_a_refused_upload_is_never_priced(api):
    portrait = (FIXTURES_DIR / "single_face_frontal.jpg").read_bytes()
    _prepare(portrait, "kit_unpriced")

    quote = client.get("/v1/kits/kit_unpriced/quote").json()

    assert quote["amount_paise"] == 0
    assert all(line["reason"] == "nothing_prepared" for line in quote["lines"])
