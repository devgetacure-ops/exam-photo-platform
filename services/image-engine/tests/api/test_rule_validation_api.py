"""API integration tests for the rule validation endpoint."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from exam_photo.api.app import app, service
from exam_photo.api.settings import ApiSettings

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def sample_exact_rule():
    """Load sample exact dimension rule from examples."""
    base_path = Path(__file__).resolve().parents[4]
    rule_path = (
        base_path / "examples" / "rules" / "sample_exact_300x400_50kb_white_bg.json"
    )
    with open(rule_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def temp_artifact_root(tmp_path):
    """Fixture providing a temporary artifact root."""
    return tmp_path / "artifacts"


@pytest.mark.mandatory_rule_admin
def test_valid_rule_validation(sample_exact_rule):
    """Assert a valid rule dictionary returns is_valid=True and no errors."""
    response = client.post("/v1/rules/validate", json={"rule": sample_exact_rule})
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["error_count"] == 0
    assert data["errors"] == []


@pytest.mark.mandatory_rule_admin
def test_invalid_rule_validation(sample_exact_rule):
    """Assert an invalid rule dictionary returns is_valid=False and error details."""
    invalid_rule = dict(sample_exact_rule)
    # Violate dimensions criteria - e.g. set invalid modes or remove width
    if "image_requirements" in invalid_rule:
        invalid_rule["image_requirements"]["dimensions"]["mode"] = "invalid_mode"

    response = client.post("/v1/rules/validate", json={"rule": invalid_rule})
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert data["error_count"] > 0
    assert len(data["errors"]) > 0

    first_err = data["errors"][0]
    assert "severity" in first_err
    assert "error_code" in first_err
    assert "field_path" in first_err
    assert "message" in first_err
    assert "suggested_resolution" in first_err


@pytest.mark.mandatory_rule_admin
def test_malformed_body_validation():
    """Assert a malformed request body (e.g. missing 'rule' property) returns 422."""
    # Missing 'rule' parameter
    response = client.post("/v1/rules/validate", json={"wrong_key": {}})
    assert response.status_code == 422

    # Raw string instead of object
    response = client.post("/v1/rules/validate", json={"rule": "not_an_object"})
    assert response.status_code == 422


@pytest.mark.mandatory_rule_admin
def test_no_files_written_during_validation(sample_exact_rule, temp_artifact_root):
    """Verify that absolutely no files are written to artifact store during validation."""
    temp_artifact_root.mkdir(exist_ok=True)

    # Verify directory is empty
    assert len(list(temp_artifact_root.iterdir())) == 0

    # Override settings in app/service for testing
    original_settings = service.settings
    service.settings = ApiSettings(
        artifact_root=temp_artifact_root,
        max_upload_bytes=100000,
        job_ttl_seconds=10,
    )

    try:
        response = client.post("/v1/rules/validate", json={"rule": sample_exact_rule})
        assert response.status_code == 200

        # Verify directory remains empty after validation execution
        assert len(list(temp_artifact_root.iterdir())) == 0
    finally:
        # Restore settings
        service.settings = original_settings


@pytest.mark.mandatory_rule_admin
def test_rule_validation_cors():
    """Verify that CORS options requests behave properly for rule validation route."""
    import importlib
    import sys

    # Create fake settings with local_cors_enabled=True
    fake_settings = ApiSettings(
        artifact_root=Path("./dummy_artifacts"),
        max_upload_bytes=100000,
        job_ttl_seconds=10,
        local_cors_enabled=True,
    )

    with patch("exam_photo.api.settings.get_settings", return_value=fake_settings):
        # Reload app module to apply CORS middleware
        importlib.reload(sys.modules["exam_photo.api.app"])
        test_client = TestClient(sys.modules["exam_photo.api.app"].app)

        # Preflight options request on validation route
        response = test_client.options(
            "/v1/rules/validate",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert (
            response.headers.get("access-control-allow-origin")
            == "http://localhost:3000"
        )

    # Reload again to restore default (CORS disabled)
    importlib.reload(sys.modules["exam_photo.api.app"])


@pytest.mark.mandatory_rule_admin
def test_sample_rules_frontend_sync():
    """Verify that rules duplicated in public web assets directory are in sync with backend examples."""
    base_path = Path(__file__).resolve().parents[4]
    backend_rules_dir = base_path / "examples" / "rules"
    frontend_rules_dir = base_path / "apps" / "web" / "public" / "rules"

    sync_files = [
        "sample_exact_300x400_50kb_white_bg.json",
        "sample_range_200_300_width_230_400_height_50kb_white_bg.json",
    ]

    for filename in sync_files:
        backend_file = backend_rules_dir / filename
        frontend_file = frontend_rules_dir / filename

        assert backend_file.exists(), f"Backend rule example missing: {filename}"
        assert frontend_file.exists(), f"Frontend public rule asset missing: {filename}"

        with (
            open(backend_file, "r", encoding="utf-8") as bf,
            open(frontend_file, "r", encoding="utf-8") as ff,
        ):
            backend_data = json.load(bf)
            frontend_data = json.load(ff)

        assert backend_data == frontend_data, (
            f"Rule drift detected in {filename}. Ensure web public asset matches example exactly."
        )
