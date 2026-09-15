"""The purchase gate and the watermarked preview over HTTP (DEC-063).

The properties under test are the ones the product's revenue rests on: the
clean file is not served before payment, the preview that *is* served is not
the clean file, and nothing claims a watermark it did not apply.
"""

import io
import json
import zipfile
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from exam_photo.api.app import app
from exam_photo.api.jobs import JobRegistry
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore
from exam_photo.orchestration.rule_pipeline import RulePipelineResult

client = TestClient(app, raise_server_exceptions=False)

EXAM = "ctet-september-2026"
SIGNATURE = "candidate_signature"

# WBPSC replaced BPSC here when DEC-068 withdrew BPSC from the catalogue.
DOC_EXAM = "wbpsc-wbcs-online-application"
DOC_REQUIREMENT = "claim_supporting_certificates"


@pytest.fixture
def api(tmp_path):
    """The service against a temporary root, with the gate at its default."""
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


def _signature_photo() -> bytes:
    height, width = 400, 900
    canvas = np.full((height, width, 3), 0.93, dtype=np.float64)
    xs = np.arange(int(width * 0.2), int(width * 0.8))
    ys = height // 2 + height * 0.14 * np.sin(xs / (width * 0.05))
    for x, y in zip(xs, ys, strict=True):
        y0, y1 = max(0, int(y) - 4), min(height, int(y) + 4)
        canvas[y0:y1, int(x), :] = 0.08
    image = Image.fromarray((canvas * 255).astype(np.uint8), mode="RGB")
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=92)
    return buffer.getvalue()


def _page_photo(shade: int = 240) -> bytes:
    canvas = np.full((600, 420, 3), shade, dtype=np.uint8)
    canvas[120:150, 60:360] = 30
    buffer = io.BytesIO()
    Image.fromarray(canvas, mode="RGB").save(buffer, "JPEG", quality=90)
    return buffer.getvalue()


def _prepare(requirement: str = SIGNATURE, kit_id=None, exam: str = EXAM):
    data = {"kit_id": kit_id} if kit_id else {}
    return client.post(
        f"/v1/exams/{exam}/requirements/{requirement}/prepare",
        files={"file": ("upload.jpg", _signature_photo(), "image/jpeg")},
        data=data,
    )


# ----------------------------------------------------------------------
# The gate
# ----------------------------------------------------------------------


@pytest.mark.mandatory_api
def test_the_clean_file_is_not_served_before_payment(api):
    """The whole point. Before this the job id was the only thing needed."""
    body = _prepare().json()

    response = client.get(body["output_url"])

    assert response.status_code == 402
    assert body["entitlement"] == "preview_only"


@pytest.mark.mandatory_api
def test_the_refusal_names_the_preview_a_caller_may_have_instead(api):
    body = _prepare().json()

    detail = client.get(body["output_url"]).json()["detail"]

    assert body["preview_url"] in detail


@pytest.mark.mandatory_api
def test_releasing_a_job_serves_the_clean_file(api):
    """The seam a payment confirmation calls, and the only thing that opens it."""
    body = _prepare().json()

    api.release_job(body["job_id"])
    response = client.get(body["output_url"])

    assert response.status_code == 200
    assert len(response.content) == body["byte_size"]


@pytest.mark.mandatory_api
def test_no_http_route_releases_a_job(api):
    """An unauthenticated release endpoint would read as protection and be none."""
    body = _prepare().json()
    job_id = body["job_id"]

    for method, path in [
        ("post", f"/v1/jobs/{job_id}/release"),
        ("post", f"/v1/jobs/{job_id}/purchase"),
        ("post", f"/v1/jobs/{job_id}/output"),
    ]:
        assert getattr(client, method)(path).status_code in (404, 405)

    assert client.get(body["output_url"]).status_code == 402


@pytest.mark.mandatory_api
def test_the_gate_can_be_switched_off_for_engine_quality_work(api):
    """Judging a matte on a watermarked half-resolution copy is the wrong thing."""
    body = _prepare().json()

    api.settings = api.settings.model_copy(update={"purchase_gate_enabled": False})
    response = client.get(body["output_url"])

    assert response.status_code == 200


@pytest.mark.mandatory_api
# The pipeline is mocked, but the service still resolves a matting backend
# first, and "auto" refuses without BiRefNet weights on disk (DEC-060). Pin
# it so the test does not depend on a model this machine may not have.
@patch(
    "exam_photo.api.service.ApiProcessingService._resolve_matting_backend",
    new=lambda self: ("mediapipe", None, ""),
)
@patch("exam_photo.api.service.RuleOrchestratedPipeline")
def test_the_rule_admin_path_is_not_behind_the_gate(mock_pipeline_class, api):
    """`/v1/process` names no examination and never reaches a candidate."""
    mock_pipeline = MagicMock()
    mock_pipeline_class.return_value = mock_pipeline
    mock_pipeline.process_rule.return_value = RulePipelineResult(
        is_valid=True,
        rule_compliant=True,
        visual_quality_acceptable=True,
        stage_reports=[],
        issue_codes=[],
        selected_crop_mode="CropModeA",
        output_filename="admin_console.jpg",
        final_width=300,
        final_height=400,
        final_format="JPEG",
        final_bytes=500,
        final_quality=95,
        processing_duration_ms=1.0,
        encoded_bytes=_signature_photo(),
    )

    body = client.post(
        "/v1/process",
        files={"file": ("input.jpg", _signature_photo(), "image/jpeg")},
        data={"rule": json.dumps({"bounds": {"aspect_ratio": "3:4"}})},
    ).json()

    assert client.get(body["output_url"]).status_code == 200
    assert api.registry.get_job(body["job_id"]).entitlement.value == "released"

    # Everything reached through an examination is gated, by contrast.
    prepared = _prepare().json()
    assert api.registry.get_job(prepared["job_id"]).entitlement.value == "preview_only"


# ----------------------------------------------------------------------
# The preview
# ----------------------------------------------------------------------


@pytest.mark.mandatory_api
def test_the_preview_is_served_and_is_not_the_clean_file(api):
    body = _prepare().json()

    preview = client.get(body["preview_url"])
    api.release_job(body["job_id"])
    clean = client.get(body["output_url"])

    assert preview.status_code == 200
    assert preview.headers["content-type"].startswith("image/jpeg")
    assert preview.content != clean.content

    # Never the file's own pixel size (DEC-063, amended): the preview is shown
    # at a fixed display size, sharp on a phone, so it cannot meet the
    # examination's pixel specification.
    with Image.open(io.BytesIO(preview.content)) as previewed:
        with Image.open(io.BytesIO(clean.content)) as delivered:
            assert previewed.size != delivered.size
            assert max(previewed.size) in (800, 760)


@pytest.mark.mandatory_api
def test_the_preview_is_not_cached_by_anything_in_between(api):
    """A preview is one candidate's face."""
    body = _prepare().json()

    headers = client.get(body["preview_url"]).headers

    assert "no-store" in headers["cache-control"]


@pytest.mark.mandatory_api
def test_the_response_claims_a_watermark_only_where_one_was_applied(api):
    body = _prepare().json()

    assert body["preview_watermarked"] is True
    assert body["preview_url"] == f"/v1/jobs/{body['job_id']}/preview"


@pytest.mark.mandatory_api
def test_a_pdf_deliverable_gets_a_watermarked_preview_and_stays_gated(api):
    """A picture of page one to judge; the clean PDF still costs (DEC-063, amended)."""
    plan = client.post(
        f"/v1/exams/{DOC_EXAM}/requirements/{DOC_REQUIREMENT}/documents",
        files=[
            ("files", ("a.jpg", _page_photo(), "image/jpeg")),
            ("files", ("b.jpg", _page_photo(210), "image/jpeg")),
        ],
    ).json()
    body = client.post(f"/v1/documents/{plan['job_id']}/assemble", json={}).json()

    assert body["output_media_type"] == "application/pdf"
    assert body["preview_watermarked"] is True
    assert body["preview_url"] == f"/v1/jobs/{body['job_id']}/preview"
    preview = client.get(body["preview_url"])
    assert preview.status_code == 200
    assert preview.headers["content-type"].startswith("image/jpeg")
    assert not preview.content.startswith(b"%PDF")
    # Still gated: the preview is a picture; the PDF itself is what is sold.
    assert client.get(body["output_url"]).status_code == 402


@pytest.mark.mandatory_api
def test_the_job_status_reports_the_same_preview_as_the_preparation(api):
    body = _prepare().json()

    status = client.get(f"/v1/jobs/{body['job_id']}").json()

    assert status["preview_url"] == body["preview_url"]
    assert status["preview_watermarked"] is True
    assert status["entitlement"] == "preview_only"


@pytest.mark.mandatory_api
def test_a_deleted_job_serves_no_preview(api):
    body = _prepare().json()

    client.delete(f"/v1/jobs/{body['job_id']}")

    assert client.get(body["preview_url"]).status_code == 404


# ----------------------------------------------------------------------
# The package is the same hole
# ----------------------------------------------------------------------


@pytest.mark.mandatory_api
def test_the_package_download_is_refused_while_a_file_is_unpaid(api):
    kit = "kit_gate"
    _prepare(kit_id=kit)

    response = client.get(f"/v1/kits/{kit}/package/download")

    assert response.status_code == 402


@pytest.mark.mandatory_api
def test_the_checklist_stays_readable_and_says_what_is_held_back(api):
    """What an examination asks for is not something a candidate must buy."""
    kit = "kit_gate_manifest"
    _prepare(kit_id=kit)

    body = client.get(f"/v1/kits/{kit}/package").json()

    assert body["files_included"] == 0
    assert body["requirements"]
    assert body["items"][0]["awaiting_release"] is True


@pytest.mark.mandatory_api
def test_the_archive_holds_no_unreleased_file_even_when_built_directly(api):
    """Skipped in the builder as well as refused at the route."""
    kit = "kit_gate_direct"
    _prepare(kit_id=kit)

    archive, checklist = api.build_kit_package(kit)

    assert checklist["awaiting_release"] == 1
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        assert not any(name.endswith(".jpg") for name in bundle.namelist())


@pytest.mark.mandatory_api
def test_a_released_kit_packages_normally(api):
    kit = "kit_gate_released"
    body = _prepare(kit_id=kit).json()
    api.release_job(body["job_id"])

    response = client.get(f"/v1/kits/{kit}/package/download")

    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as bundle:
        assert any(name.endswith(".jpg") for name in bundle.namelist())
