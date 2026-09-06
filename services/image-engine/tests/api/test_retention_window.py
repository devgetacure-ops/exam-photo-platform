"""The thirty-minute retention promise, enforced rather than asserted (DEC-066).

`job_ttl_seconds` was 3600 while `docs/UI_ENGINE_HANDOFF.md` contemplated a
30-minute deletion guarantee, and the two had to be made to agree before any
public claim could be published. Settling the number surfaced the harder half:
expiry was enforced **only** by the sweeper, which runs on a timer, so an
expired file stayed downloadable in full for up to `cleanup_interval_seconds`
-- five minutes at the default. A promise measured in minutes cannot carry a
five-minute hole, so what is pinned here is that access ends at the deadline
itself and the timer is only the backstop for jobs nobody touches again.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from exam_photo.api.app import app
from exam_photo.api.contracts import ApiJobStatus, JobEntitlement
from exam_photo.api.jobs import JobRegistry, ProcessingJobRecord
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def api(tmp_path):
    """The service against a temporary root, at production defaults."""
    from exam_photo.api.app import service

    original = (service.settings, service.store, service.registry)
    service.settings = ApiSettings(artifact_root=tmp_path / "artifacts")
    service.store = LocalArtifactStore(tmp_path / "artifacts")
    service.registry = JobRegistry(tmp_path / "artifacts")
    try:
        yield service
    finally:
        service.settings, service.store, service.registry = original


def _finished_job(
    api,
    job_id: str = "job_retention",
    age_seconds: int = -60,
    kit_id: str | None = None,
) -> ProcessingJobRecord:
    """A released job with a real file on disk, expiring `age_seconds` from now.

    A negative age is a job already past its deadline. The job is *released*
    on purpose: the interesting case is a candidate who paid and came back too
    late, not one the purchase gate would have refused anyway.
    """
    record = api.registry.create_job(job_id, 1)
    record.status = ApiJobStatus.SUCCEEDED
    record.entitlement = JobEntitlement.RELEASED
    record.output_filename = "output.jpg"
    record.output_media_type = "image/jpeg"
    record.kit_id = kit_id
    record.expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=age_seconds)
    ).isoformat()
    api.store.write_file(job_id, "output.jpg", b"\xff\xd8\xff\xdb-not-really-a-jpeg")
    api.registry.update_job(record)
    return record


# ----------------------------------------------------------------------
# The number itself
# ----------------------------------------------------------------------


def test_the_default_retention_window_is_thirty_minutes():
    """The setting and the published claim must be the same number."""
    assert ApiSettings().job_ttl_seconds == 1800


# ----------------------------------------------------------------------
# Access ends at the deadline, not at the next sweep
# ----------------------------------------------------------------------


def test_an_expired_output_is_refused_before_the_sweeper_has_run(api):
    """The five-minute hole. This is the whole point of the read-path check."""
    _finished_job(api)

    response = client.get("/v1/jobs/job_retention/output")

    assert response.status_code == 404


def test_the_refusing_read_also_erases_the_job(api):
    """Refusing to serve it and leaving it on disk is not deletion."""
    _finished_job(api)

    client.get("/v1/jobs/job_retention/output")

    assert not (api.settings.artifact_root / "job_retention").exists()
    assert api.registry.get_job("job_retention").status == ApiJobStatus.DELETED


def test_an_expired_job_reports_as_deleted_and_offers_no_urls(api):
    """No new status on the wire: every caller already handles `deleted`."""
    _finished_job(api)

    body = client.get("/v1/jobs/job_retention").json()

    assert body["status"] == ApiJobStatus.DELETED.value
    assert body["output_url"] is None
    assert body["preview_url"] is None
    assert body["report_url"] is None


def test_an_expired_preview_is_refused_too(api):
    """A face at half resolution with a mark on it is still the candidate's face."""
    record = _finished_job(api)
    record.preview_filename = "preview.jpg"
    record.preview_watermarked = True
    api.store.write_file("job_retention", "preview.jpg", b"\xff\xd8\xff\xdb-preview")
    api.registry.update_job(record)

    assert client.get("/v1/jobs/job_retention/preview").status_code == 404


def test_an_expired_report_is_refused_too(api):
    """The report names findings about one candidate's file."""
    _finished_job(api)
    api.store.write_file("job_retention", "report.json", b"{}")

    assert client.get("/v1/jobs/job_retention/report").status_code == 404


def test_a_live_job_is_served_and_left_alone(api):
    """The guard must refuse the expired job and nothing else."""
    _finished_job(api, age_seconds=+600)

    response = client.get("/v1/jobs/job_retention/output")

    assert response.status_code == 200
    assert (api.settings.artifact_root / "job_retention").exists()


# ----------------------------------------------------------------------
# The predicate
# ----------------------------------------------------------------------


def test_an_expiry_nobody_can_parse_reads_as_expired():
    """A corrupt manifest must not be the one path to unlimited retention."""
    now = datetime.now(timezone.utc).isoformat()
    record = ProcessingJobRecord(
        job_id="job_corrupt",
        status=ApiJobStatus.SUCCEEDED,
        created_at=now,
        updated_at=now,
        expires_at="whenever",
    )

    assert record.is_expired()


def test_a_naive_expiry_is_read_as_utc():
    """Manifests are written with an offset; one without must not read as local."""
    now = datetime.now(timezone.utc)
    record = ProcessingJobRecord(
        job_id="job_naive",
        status=ApiJobStatus.SUCCEEDED,
        created_at=now.isoformat(),
        updated_at=now.isoformat(),
        expires_at=(now + timedelta(minutes=20)).replace(tzinfo=None).isoformat(),
    )

    assert not record.is_expired()


# ----------------------------------------------------------------------
# The kit
# ----------------------------------------------------------------------


def test_an_expired_job_leaves_its_kit(api):
    """Otherwise a package assembled in the gap returns a file said to be gone."""
    _finished_job(api, job_id="job_live", age_seconds=+600, kit_id="kit_abc")
    _finished_job(api, job_id="job_gone", age_seconds=-60, kit_id="kit_abc")

    gathered = [record.job_id for record in api.registry.jobs_in_kit("kit_abc")]

    assert gathered == ["job_live"]


# ----------------------------------------------------------------------
# The sweeper is still the backstop
# ----------------------------------------------------------------------


def test_the_sweeper_still_collects_a_job_nobody_came_back_for(api):
    """Read-path expiry only fires on a read. Most jobs never get one."""
    _finished_job(api)

    assert api.cleanup_expired_jobs() == 1
    assert not (api.settings.artifact_root / "job_retention").exists()
