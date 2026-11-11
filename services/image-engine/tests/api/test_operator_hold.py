"""The operator's 24-hour hold (DEC-122).

At the candidate's deadline their files leave every candidate route exactly as
before; the operator can still see the upload and the prepared file until the
hold, measured from the upload, runs out, and then they are erased.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from exam_photo.api.app import app
from exam_photo.api.contracts import ApiJobStatus
from exam_photo.api.jobs import JobRegistry
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore

client = TestClient(app, raise_server_exceptions=False)
OPERATOR = "op-secret"
AUTH = {"X-Operator-Token": OPERATOR}
DAY = 86400


def _install(service, tmp_path, hold):
    root = tmp_path / "artifacts"
    service.settings = ApiSettings(
        billing_enabled=True,
        artifact_root=root,
        operator_token=OPERATOR,
        operator_hold_seconds=hold,
    )
    service.store = LocalArtifactStore(root)
    service.registry = JobRegistry(root)
    return root


@pytest.fixture
def api(tmp_path):
    from exam_photo.api.app import service

    original = (service.settings, service.store, service.registry)
    service.root = _install(service, tmp_path, DAY)
    try:
        yield service
    finally:
        service.settings, service.store, service.registry = original
        del service.root


def _job(api, job_id, age_seconds=3600):
    record = api.registry.create_job(job_id, 1800)
    record.status = ApiJobStatus.SUCCEEDED
    record.output_filename = f"{job_id}.jpg"
    now = datetime.now(timezone.utc)
    record.created_at = (now - timedelta(seconds=age_seconds)).isoformat()
    record.expires_at = (now - timedelta(minutes=1)).isoformat()
    api.store.write_file(job_id, "input.jpg", b"\xff\xd8source")
    api.store.write_file(job_id, f"{job_id}.jpg", b"\xff\xd8prepared")
    api.registry.update_job(record)
    return record


def test_an_expired_job_is_gone_for_the_candidate_and_held_for_the_operator(api):
    _job(api, "job_a")
    assert client.get("/v1/jobs/job_a/output").status_code == 404
    assert client.get("/v1/jobs/job_a/preview").status_code == 404
    assert client.get("/v1/jobs/job_a").json()["status"] == ApiJobStatus.DELETED.value
    assert not (api.root / "job_a").exists()

    for name, body in (
        ("input.jpg", b"\xff\xd8source"),
        ("job_a.jpg", b"\xff\xd8prepared"),
    ):
        response = client.get(f"/v1/operator/jobs/job_a/files/{name}", headers=AUTH)
        assert response.status_code == 200
        assert response.content == body
    detail = client.get("/v1/operator/jobs/job_a", headers=AUTH).json()
    assert {"input.jpg", "job_a.jpg"} <= {item["name"] for item in detail["files"]}


def test_a_candidates_own_deletion_is_held_too(api):
    record = _job(api, "job_b")
    record.expires_at = (datetime.now(timezone.utc) + timedelta(minutes=20)).isoformat()
    api.registry.update_job(record)
    assert client.delete("/v1/jobs/job_b").status_code == 200
    assert client.get("/v1/jobs/job_b/output").status_code == 404
    assert (
        client.get("/v1/operator/jobs/job_b/files/input.jpg", headers=AUTH).status_code
        == 200
    )


def test_the_sweeper_holds_then_erases_when_the_day_is_over(api):
    _job(api, "job_c")
    api.cleanup_expired_jobs()
    held = api.root / "_held" / "job_c"
    assert held.is_dir()

    manifest = json.loads((held / "job.json").read_text(encoding="utf-8"))
    manifest["created_at"] = (
        datetime.now(timezone.utc) - timedelta(seconds=DAY + 60)
    ).isoformat()
    (held / "job.json").write_text(json.dumps(manifest), encoding="utf-8")

    # Past the day the operator is refused even before the sweeper runs.
    assert (
        client.get("/v1/operator/jobs/job_c/files/input.jpg", headers=AUTH).status_code
        == 404
    )
    api.cleanup_expired_jobs()
    assert not held.exists()


def test_a_job_older_than_the_hold_is_erased_outright(api):
    _job(api, "job_d", age_seconds=DAY + 60)
    api.cleanup_expired_jobs()
    assert not (api.root / "job_d").exists()
    assert not (api.root / "_held" / "job_d").exists()


def test_a_held_job_nobody_can_date_is_erased(api):
    _job(api, "job_e")
    api.cleanup_expired_jobs()
    held = api.root / "_held" / "job_e"
    (held / "job.json").write_text("not json", encoding="utf-8")
    api.cleanup_expired_jobs()
    assert not held.exists()


def test_a_held_file_cannot_be_reached_outside_its_job(api):
    _job(api, "job_f")
    _job(api, "job_g")
    api.cleanup_expired_jobs()
    assert api.store.held_file_path("job_f", "../job_g/input.jpg") is None
    assert api.store.held_job_directory("../_orders") is None


def test_without_a_hold_expiry_erases_as_before(api, tmp_path):
    root = _install(api, tmp_path / "off", 0)
    _job(api, "job_h")
    api.cleanup_expired_jobs()
    assert not (root / "job_h").exists()
    assert not (root / "_held").exists()
