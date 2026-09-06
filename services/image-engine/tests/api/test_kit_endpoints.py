"""API tests for kit preparation, documents and packaging (DEC-055..058)."""

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

# CTET carries all three states this suite needs: a supported photograph, a
# supported signature, and a portal declaration the platform must refuse.
EXAM = "ctet-september-2026"
SIGNATURE = "candidate_signature"
PHOTOGRAPH = "candidate_photograph"
DECLARATION = "online_declaration_confirmation"

# BPSC's claim certificates are the multi-page document case, at a 400 KB
# ceiling that DEC-049 records as an interim platform estimate.
DOC_EXAM = "bpsc-current-recruitment-photograph-specification"
DOC_REQUIREMENT = "claim_supporting_certificates"

# CTET publishes its signature specification, so it carries no interim values.
# ICAI's is stood in for, which is what the package report must disclose.
ESTIMATE_EXAM = "icai-examination-portal-photograph-current-portal-scope"
ESTIMATE_SIGNATURE = "candidate_signature"


@pytest.fixture
def api(tmp_path):
    """Point the service's storage at a temporary root for one test."""
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
    """A synthetic photograph of a signature on paper."""
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
    """A synthetic photograph of a printed page."""
    canvas = np.full((600, 420, 3), shade, dtype=np.uint8)
    canvas[120:150, 60:360] = 30
    canvas[220:240, 60:300] = 40
    buffer = io.BytesIO()
    Image.fromarray(canvas, mode="RGB").save(buffer, "JPEG", quality=90)
    return buffer.getvalue()


def _blank_page() -> bytes:
    """A photograph of a sheet with nothing written on it."""
    canvas = np.full((600, 420, 3), 246, dtype=np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(canvas, mode="RGB").save(buffer, "JPEG", quality=90)
    return buffer.getvalue()


def _prepare(requirement: str, content: bytes, kit_id=None, exam: str = EXAM):
    data = {"kit_id": kit_id} if kit_id else {}
    return client.post(
        f"/v1/exams/{exam}/requirements/{requirement}/prepare",
        files={"file": ("upload.jpg", content, "image/jpeg")},
        data=data,
    )


def _release(api, job_id: str) -> None:
    """Stand in for the payment confirmation (DEC-063).

    There is deliberately no HTTP route that releases a job, so a test that
    wants the clean file calls the same seam Razorpay will.
    """
    api.release_job(job_id)


def _release_kit(api, kit_id: str) -> None:
    for record in api.registry.jobs_in_kit(kit_id):
        api.release_job(record.job_id)


# ----------------------------------------------------------------------
# The support gate (DEC-056)
# ----------------------------------------------------------------------


@pytest.mark.mandatory_api
def test_a_guidance_only_requirement_is_refused_with_409(api):
    """The platform must never appear to have completed a portal declaration."""
    response = _prepare(DECLARATION, b"anything")

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["platform_support"] == "guidance_only"
    assert detail["submission_method"] == "typed_or_selected_declaration"
    assert detail["requirement_id"] == DECLARATION


@pytest.mark.mandatory_api
def test_the_refusal_carries_what_the_candidate_must_do_instead(api):
    """A generic error would tell the candidate nothing actionable."""
    detail = _prepare(DECLARATION, b"anything").json()["detail"]

    assert detail["requirement_name"]
    assert "does not prepare" in detail["detail"]
    assert set(detail) >= {
        "exam_id",
        "requirement_id",
        "requirement_name",
        "requirement_type",
        "submission_method",
        "platform_support",
    }


@pytest.mark.mandatory_api
def test_the_gate_runs_before_the_upload_is_processed(api):
    """A refused requirement must not create a job or store bytes."""
    response = _prepare(DECLARATION, b"not even an image")

    assert response.status_code == 409
    assert "job_id" not in response.json()


@pytest.mark.mandatory_api
def test_unknown_exam_and_requirement_are_404(api):
    assert _prepare(SIGNATURE, b"x", exam="no-such-exam").status_code == 404
    assert _prepare("no_such_requirement", b"x").status_code == 404


@pytest.mark.mandatory_api
@pytest.mark.parametrize("requirement_id", ["../etc", "Upper", "has-dash"])
def test_malformed_requirement_identifiers_are_rejected(api, requirement_id):
    response = _prepare(requirement_id, b"x")

    assert response.status_code in (400, 404)


# ----------------------------------------------------------------------
# Preparation, dispatching by requirement type (DEC-055)
# ----------------------------------------------------------------------


@pytest.mark.mandatory_api
def test_a_signature_is_prepared_to_its_published_specification(api):
    response = _prepare(SIGNATURE, _signature_photo())

    assert response.status_code == 200
    body = response.json()
    assert body["requirement_type"] == "signature"
    assert body["platform_support"] == "supported"
    assert body["outcome"] in ("prepared", "prepared_with_findings")
    assert body["output_url"]
    assert body["output_filename"].endswith(".jpg")
    # CTET publishes a 30 KB ceiling for the signature.
    assert 0 < body["byte_size"] <= 30000
    assert body["ceiling_was_unpublished"] is False


@pytest.mark.mandatory_api
def test_the_prepared_file_is_downloadable_with_its_own_media_type(api):
    body = _prepare(SIGNATURE, _signature_photo()).json()
    _release(api, body["job_id"])

    output = client.get(body["output_url"])

    assert output.status_code == 200
    assert output.headers["content-type"].startswith("image/jpeg")
    assert len(output.content) == body["byte_size"]


@pytest.mark.mandatory_api
def test_a_blank_page_is_produced_and_reported_not_refused(api):
    """DEC-041: a refusal and a silent failure look the same to a candidate."""
    body = _prepare(SIGNATURE, _blank_page()).json()

    assert body["outcome"] == "prepared_with_findings"
    assert body["is_blank"] is True
    assert body["findings"]
    assert body["output_url"]


@pytest.mark.mandatory_api
def test_an_undecodable_upload_does_not_produce_a_file(api):
    body = _prepare(SIGNATURE, b"this is not an image at all").json()

    assert body["outcome"] == "not_produced"
    assert body["output_url"] is None
    assert body["findings"]


@pytest.mark.mandatory_api
@patch("exam_photo.api.service.RuleOrchestratedPipeline")
def test_a_photograph_requirement_dispatches_to_the_photograph_pipeline(
    mock_pipeline_class, api
):
    """One endpoint, two engines, chosen by requirement type."""
    mock_pipeline = MagicMock()
    mock_pipeline_class.return_value = mock_pipeline
    mock_pipeline.process_rule.return_value = RulePipelineResult(
        is_valid=True,
        rule_compliant=True,
        visual_quality_acceptable=True,
        stage_reports=[],
        issue_codes=[],
        selected_crop_mode="CropModeA",
        output_filename="candidate_2026.jpg",
        final_width=300,
        final_height=400,
        final_format="JPEG",
        final_bytes=500,
        final_quality=95,
        processing_duration_ms=1.0,
        encoded_bytes=b"fake_jpeg_bytes",
    )

    response = _prepare(PHOTOGRAPH, b"pretend photograph")

    assert response.status_code == 200
    body = response.json()
    assert body["requirement_type"] == "photograph"
    assert body["is_valid"] is True
    assert body["outcome"] == "prepared"
    assert mock_pipeline.process_rule.called


# ----------------------------------------------------------------------
# Multi-page documents (DEC-053)
# ----------------------------------------------------------------------


def _plan_document(api, uploads, kit_id=None):
    data = {"kit_id": kit_id} if kit_id else {}
    return client.post(
        f"/v1/exams/{DOC_EXAM}/requirements/{DOC_REQUIREMENT}/documents",
        files=[("files", (name, content, "image/jpeg")) for name, content in uploads],
        data=data,
    )


@pytest.mark.mandatory_api
def test_planning_returns_one_page_per_upload(api):
    response = _plan_document(
        api, [("a.jpg", _page_photo()), ("b.jpg", _page_photo(230))]
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["pages"]) == 2
    assert [p["source_index"] for p in body["pages"]] == [0, 1]
    assert all(p["origin"] == "photograph" for p in body["pages"])
    assert body["unreadable"] == {}


@pytest.mark.mandatory_api
def test_one_damaged_upload_does_not_cost_the_others(api):
    body = _plan_document(
        api, [("good.jpg", _page_photo()), ("bad.jpg", b"not an image")]
    ).json()

    assert len(body["pages"]) == 1
    assert "1" in body["unreadable"]


@pytest.mark.mandatory_api
def test_assembly_honours_the_candidates_order_and_omissions(api):
    plan = _plan_document(
        api,
        [
            ("a.jpg", _page_photo(250)),
            ("b.jpg", _page_photo(200)),
            ("c.jpg", _page_photo(150)),
        ],
    ).json()

    # Reversed, with the middle page omitted.
    order = [plan["pages"][2], plan["pages"][0]]
    response = client.post(
        f"/v1/documents/{plan['job_id']}/assemble", json={"order": order}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["output_filename"].endswith(".pdf")
    assert body["output_media_type"] == "application/pdf"

    _release(api, body["job_id"])
    output = client.get(body["output_url"])
    assert output.headers["content-type"].startswith("application/pdf")
    assert output.content.startswith(b"%PDF-")


@pytest.mark.mandatory_api
def test_assembly_without_an_order_takes_every_page(api):
    plan = _plan_document(
        api, [("a.jpg", _page_photo()), ("b.jpg", _page_photo(210))]
    ).json()

    response = client.post(f"/v1/documents/{plan['job_id']}/assemble", json={})

    assert response.status_code == 200
    assert response.json()["output_filename"].endswith(".pdf")


@pytest.mark.mandatory_api
def test_assembling_an_unknown_job_is_404(api):
    response = client.post("/v1/documents/job_nonexistent/assemble", json={})

    assert response.status_code == 404


@pytest.mark.mandatory_api
def test_assembling_a_job_that_holds_no_document_is_refused(api):
    prepared = _prepare(SIGNATURE, _signature_photo()).json()

    response = client.post(f"/v1/documents/{prepared['job_id']}/assemble", json={})

    assert response.status_code == 409


# ----------------------------------------------------------------------
# The package (DEC-055 step 4, DEC-056, DEC-057)
# ----------------------------------------------------------------------


@pytest.mark.mandatory_api
def test_the_package_gathers_a_kits_files(api):
    kit = "kit_abc123"
    _prepare(SIGNATURE, _signature_photo(), kit_id=kit)
    _release_kit(api, kit)

    response = client.get(f"/v1/kits/{kit}/package")

    assert response.status_code == 200
    body = response.json()
    assert body["kit_id"] == kit
    assert body["exam_id"] == EXAM
    assert body["files_included"] == 1


@pytest.mark.mandatory_api
def test_the_checklist_lists_every_requirement_including_refused_ones(api):
    """An omitted requirement reads as 'this exam does not ask for it'."""
    kit = "kit_checklist"
    _prepare(SIGNATURE, _signature_photo(), kit_id=kit)

    body = client.get(f"/v1/kits/{kit}/package").json()

    ids = {r["requirement_id"] for r in body["requirements"]}
    assert DECLARATION in ids
    declaration = next(
        r for r in body["requirements"] if r["requirement_id"] == DECLARATION
    )
    assert declaration["prepared_by_platform"] is False
    assert declaration["completed_by_candidate_elsewhere"] is True
    assert declaration["platform_support"] == "guidance_only"


@pytest.mark.mandatory_api
def test_the_archive_carries_the_files_the_checklist_and_the_report(api):
    kit = "kit_archive"
    _prepare(SIGNATURE, _signature_photo(), kit_id=kit)
    _release_kit(api, kit)

    response = client.get(f"/v1/kits/{kit}/package/download")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/zip")
    with zipfile.ZipFile(io.BytesIO(response.content)) as bundle:
        names = bundle.namelist()
        assert "checklist.json" in names
        assert "validation-report.json" in names
        assert any(name.endswith(".jpg") for name in names)


@pytest.mark.mandatory_api
def test_the_validation_report_names_every_platform_estimate(api):
    """DEC-057: disclosure proportionate to what the reader can do.

    Quiet in the application, explicit here -- this is the artifact somebody
    opens after a portal rejects a file.
    """
    kit = "kit_estimates"
    _prepare(ESTIMATE_SIGNATURE, _signature_photo(), kit_id=kit, exam=ESTIMATE_EXAM)
    _release_kit(api, kit)

    response = client.get(f"/v1/kits/{kit}/package/download")
    with zipfile.ZipFile(io.BytesIO(response.content)) as bundle:
        report = json.loads(bundle.read("validation-report.json"))

    assert report["estimate_count"] > 0
    assert all(entry["reasoning"] for entry in report["platform_estimates"])
    assert all(
        "platform estimate" in entry["note"] for entry in report["platform_estimates"]
    )


@pytest.mark.mandatory_api
def test_an_empty_kit_is_404(api):
    assert client.get("/v1/kits/kit_nothing/package").status_code == 404


@pytest.mark.mandatory_api
@pytest.mark.parametrize("kit_id", ["../escape", "no-prefix", "kit_"])
def test_malformed_kit_identifiers_are_rejected(api, kit_id):
    response = client.get(f"/v1/kits/{kit_id}/package")

    assert response.status_code in (400, 404)


@pytest.mark.mandatory_api
def test_a_deleted_job_leaves_the_kit(api):
    """A candidate who removed a deliverable must not find it in the package."""
    kit = "kit_deleted"
    prepared = _prepare(SIGNATURE, _signature_photo(), kit_id=kit).json()

    client.delete(f"/v1/jobs/{prepared['job_id']}")

    assert client.get(f"/v1/kits/{kit}/package").status_code == 404
