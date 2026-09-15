"""Tests for local API endpoints and job registry/lifecycle."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from exam_photo.api.app import app
from exam_photo.api.jobs import JobRegistry
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore
from exam_photo.orchestration.rule_pipeline import RulePipelineResult

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def temp_artifact_root(tmp_path):
    """Fixture providing a temporary artifact root."""
    return tmp_path / "artifacts"


@pytest.mark.mandatory_api
def test_settings_validation(temp_artifact_root):
    """Test validation of settings fields."""
    # Valid settings
    settings = ApiSettings(
        artifact_root=temp_artifact_root,
        max_upload_bytes=100,
        job_ttl_seconds=10,
    )
    assert settings.max_upload_bytes == 100

    # Invalid root path (root drive)
    with pytest.raises(ValueError, match="cannot be a filesystem root drive"):
        ApiSettings(artifact_root=Path("/"))

    # Invalid max_upload_bytes
    with pytest.raises(ValueError, match="must be greater than 0"):
        ApiSettings(max_upload_bytes=0)

    # Invalid job_ttl_seconds
    with pytest.raises(ValueError, match="must be greater than 0"):
        ApiSettings(job_ttl_seconds=-5)


@pytest.mark.mandatory_api
def test_storage_traversal_guards(temp_artifact_root):
    """Test path traversal guards in LocalArtifactStore."""
    store = LocalArtifactStore(temp_artifact_root)

    # Valid job ID & file
    job_id = "job_valid123"
    filename = "report.json"
    path = store.get_file_path(job_id, filename)
    assert path.name == filename

    # Invalid job ID format
    with pytest.raises(ValueError, match="Invalid job_id format"):
        store.get_file_path("job_../bad", filename)

    # Traversal in filename
    with pytest.raises(ValueError, match="Directory traversal detected"):
        store.get_file_path(job_id, "../other_job/report.json")


@pytest.mark.mandatory_api
def test_job_id_validation_at_endpoints():
    """Test regex validation of job_id in FastAPI endpoints."""
    # Invalid job_id format should return 400 Bad Request if it matches route, otherwise 404
    response = client.get("/v1/jobs/job_invalid/traversal")
    assert response.status_code == 404  # Route mismatch

    response = client.get("/v1/jobs/job_../bad")
    assert response.status_code == 404  # Route mismatch (multi-segment path)

    response = client.get("/v1/jobs/job_..")
    assert response.status_code == 400  # Valid route, invalid regex
    assert "Invalid job ID format" in response.json()["detail"]

    response = client.delete("/v1/jobs/job_invalid.json")
    assert response.status_code == 400


@pytest.mark.mandatory_api
def test_health_endpoint():
    """Test that the /health endpoint works."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.mandatory_api
# The pipeline is mocked, but the service still resolves a matting backend
# first, and "auto" refuses without BiRefNet weights on disk (DEC-060). Pin
# it so the test does not depend on a model this machine may not have.
@patch(
    "exam_photo.api.service.ApiProcessingService._resolve_matting_backend",
    new=lambda self: ("mediapipe", None, ""),
)
@patch("exam_photo.api.service.RuleOrchestratedPipeline")
def test_api_jobs_lifecycle(mock_pipeline_class, temp_artifact_root):
    """Test processing, status query, report, output and deletion lifecycle."""
    # Override settings in app/service for testing
    from exam_photo.api.app import service, settings

    original_settings = service.settings
    original_root = settings.artifact_root

    service.settings = ApiSettings(
        artifact_root=temp_artifact_root,
        max_upload_bytes=1000,
        job_ttl_seconds=3600,
    )
    service.store = LocalArtifactStore(temp_artifact_root)
    service.registry = JobRegistry(temp_artifact_root)

    # Mock pipeline instance
    mock_pipeline = MagicMock()
    mock_pipeline_class.return_value = mock_pipeline

    fake_result = RulePipelineResult(
        is_valid=True,
        rule_compliant=True,
        visual_quality_acceptable=True,
        stage_reports=[],
        issue_codes=[],
        selected_crop_mode="CropModeA",
        output_filename="MarieCurie_2026.jpg",
        final_width=300,
        final_height=400,
        final_format="JPEG",
        final_bytes=500,
        final_quality=95,
        processing_duration_ms=12.5,
        encoded_bytes=b"fake_jpeg_bytes",
    )
    mock_pipeline.process_rule.return_value = fake_result

    try:
        # 1. POST /v1/process
        mock_image = b"some_image_bytes"
        rule_data = {"bounds": {"aspect_ratio": "3:4"}}
        response = client.post(
            "/v1/process",
            files={"file": ("input.jpg", mock_image, "image/jpeg")},
            data={"rule": json.dumps(rule_data)},
        )
        assert response.status_code == 200
        data = response.json()
        job_id = data["job_id"]
        assert job_id.startswith("job_")
        assert data["status"] == "SUCCEEDED"
        assert "/v1/jobs/" in data["report_url"]
        assert "/v1/jobs/" in data["output_url"]
        assert data["is_valid"] is True
        assert data["output_filename"] == "MarieCurie_2026.jpg"
        assert data["issue_codes"] == []

        # Check job.json manifest was created on disk
        manifest_path = temp_artifact_root / job_id / "job.json"
        assert manifest_path.is_file()

        # 2. GET /v1/jobs/{job_id}
        response = client.get(f"/v1/jobs/{job_id}")
        assert response.status_code == 200
        job_info = response.json()
        assert job_info["status"] == "SUCCEEDED"
        assert job_info["output_filename"] == "MarieCurie_2026.jpg"

        # 3. GET /v1/jobs/{job_id}/report
        response = client.get(f"/v1/jobs/{job_id}/report")
        assert response.status_code == 200
        report = response.json()
        assert report["is_valid"] is True
        assert "encoded_bytes" not in report

        # 4. GET /v1/jobs/{job_id}/output
        response = client.get(f"/v1/jobs/{job_id}/output")
        assert response.status_code == 200
        assert response.content == b"fake_jpeg_bytes"

        # 5. DELETE /v1/jobs/{job_id}
        response = client.delete(f"/v1/jobs/{job_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["detail"]

        # Verify disk files are gone
        assert not (temp_artifact_root / job_id).exists()

        # In-memory status should still be DELETED
        response = client.get(f"/v1/jobs/{job_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "DELETED"

        # Retrieving output or report for deleted job should be 404
        response = client.get(f"/v1/jobs/{job_id}/output")
        assert response.status_code == 404

    finally:
        # Restore settings
        service.settings = original_settings
        service.store = LocalArtifactStore(original_root)
        service.registry = JobRegistry(original_root)


@pytest.mark.mandatory_api
def test_upload_too_large(temp_artifact_root):
    """Test file size limit rejection."""
    from exam_photo.api.app import service

    original_settings = service.settings

    # Set max limit to 10 bytes
    service.settings = ApiSettings(
        artifact_root=temp_artifact_root,
        max_upload_bytes=10,
        job_ttl_seconds=3600,
    )

    try:
        response = client.post(
            "/v1/process",
            files={"file": ("input.jpg", b"0123456789_too_large_bytes", "image/jpeg")},
            data={"rule": json.dumps({})},
        )
        assert response.status_code == 413
        assert "exceeds maximum limit" in response.json()["detail"]
    finally:
        service.settings = original_settings


@pytest.mark.mandatory_api
def test_cors_headers_enabled():
    """Test CORS headers are returned for allowed origins when enabled."""
    import importlib
    import sys

    from exam_photo.api.settings import ApiSettings

    # Create fake settings with local_cors_enabled=True
    fake_settings = ApiSettings(
        artifact_root=Path("./test_artifacts_cors"),
        local_cors_enabled=True,
    )

    with patch("exam_photo.api.settings.get_settings", return_value=fake_settings):
        app_module = sys.modules["exam_photo.api.app"]
        importlib.reload(app_module)
        test_client = TestClient(app_module.app)

        # 1. Allowed origin http://localhost:3000
        response = test_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert (
            response.headers.get("access-control-allow-origin")
            == "http://localhost:3000"
        )

        # 2. Allowed origin http://127.0.0.1:3000
        response = test_client.options(
            "/health",
            headers={
                "Origin": "http://127.0.0.1:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert (
            response.headers.get("access-control-allow-origin")
            == "http://127.0.0.1:3000"
        )

        # 3. Disallowed origin
        response = test_client.options(
            "/health",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert "access-control-allow-origin" not in response.headers

    # Reload again to restore default (CORS disabled)
    importlib.reload(sys.modules["exam_photo.api.app"])
