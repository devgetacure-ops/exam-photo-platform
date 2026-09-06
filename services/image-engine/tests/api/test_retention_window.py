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
from exam_photo.api.jobs import (
    JobRegistry,
    ProcessingJobRecord,
    parse_manifest_timestamp,
)
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


# ----------------------------------------------------------------------
# Extending a live job (DEC-067)
# ----------------------------------------------------------------------


def test_the_lifetime_ceiling_is_the_ttl_the_product_used_to_give_everyone():
    """The bound is chosen so extension cannot lengthen the worst case.

    3600 was the unconditional default before DEC-066, so the longest a file
    can now live -- and only because someone asked -- is exactly what every
    file used to get without asking.
    """
    settings = ApiSettings()

    assert settings.job_max_lifetime_seconds == 3600
    assert settings.job_max_lifetime_seconds >= settings.job_ttl_seconds


def test_a_ceiling_below_the_ttl_is_refused():
    """Otherwise every job is born past its maximum and extension never works."""
    with pytest.raises(ValueError, match="at least job_ttl_seconds"):
        ApiSettings(job_ttl_seconds=1800, job_max_lifetime_seconds=600)


def test_extending_a_live_job_moves_its_deadline_forward(api):
    _finished_job(api, age_seconds=+60)
    before = api.registry.get_job("job_retention").expires_at

    response = client.post("/v1/jobs/job_retention/extend")

    assert response.status_code == 200
    assert response.json()["expires_at"] > before
    assert client.get("/v1/jobs/job_retention/output").status_code == 200


def test_the_new_window_is_measured_from_now_not_added_to_what_is_left(api):
    """A candidate asking with two minutes left wants a full window, not 32."""
    _finished_job(api, age_seconds=+120)

    granted = parse_manifest_timestamp(
        client.post("/v1/jobs/job_retention/extend").json()["expires_at"]
    )

    expected = datetime.now(timezone.utc) + timedelta(
        seconds=api.settings.job_ttl_seconds
    )
    assert abs((granted - expected).total_seconds()) < 30


def test_extension_stops_at_the_ceiling_measured_from_creation(api):
    """Otherwise repeating the request walks a file forward for ever."""
    record = _finished_job(api, age_seconds=+60)
    # Born 55 minutes ago against a 60-minute ceiling: 5 minutes of room.
    record.created_at = (datetime.now(timezone.utc) - timedelta(minutes=55)).isoformat()
    api.registry.update_job(record)

    granted = parse_manifest_timestamp(
        client.post("/v1/jobs/job_retention/extend").json()["expires_at"]
    )

    ceiling = datetime.now(timezone.utc) + timedelta(minutes=5)
    assert granted <= ceiling + timedelta(seconds=30)


def test_a_job_at_its_ceiling_is_refused_rather_than_silently_unchanged(api):
    """409, not a 200 whose deadline did not move."""
    record = _finished_job(api, age_seconds=+60)
    record.created_at = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    api.registry.update_job(record)

    response = client.post("/v1/jobs/job_retention/extend")

    assert response.status_code == 409
    assert client.get("/v1/jobs/job_retention/output").status_code == 200


def test_an_expired_job_cannot_be_extended(api):
    """There is nothing left to keep. This is why the warning must come first."""
    _finished_job(api, age_seconds=-60)

    response = client.post("/v1/jobs/job_retention/extend")

    assert response.status_code == 404
    assert not (api.settings.artifact_root / "job_retention").exists()


def test_extending_does_not_release_a_gated_job(api):
    """Retention and payment are separate gates and must stay separate."""
    record = _finished_job(api, age_seconds=+60)
    record.entitlement = JobEntitlement.PREVIEW_ONLY
    api.registry.update_job(record)

    assert client.post("/v1/jobs/job_retention/extend").status_code == 200
    assert client.get("/v1/jobs/job_retention/output").status_code == 402


def test_status_says_whether_a_further_extension_would_buy_anything(api):
    """So the interface can stop offering a button that will answer 409."""
    record = _finished_job(api, age_seconds=+60)
    assert client.get("/v1/jobs/job_retention").json()["extendable"] is True

    record.created_at = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    api.registry.update_job(record)

    assert client.get("/v1/jobs/job_retention").json()["extendable"] is False


def test_a_creation_time_nobody_can_parse_grants_no_extension(api):
    """A job whose age is unknowable has no demonstrable room left."""
    record = _finished_job(api, age_seconds=+60)
    record.created_at = "whenever"
    api.registry.update_job(record)

    assert client.post("/v1/jobs/job_retention/extend").status_code == 409


def test_extending_an_unknown_job_is_404(api):
    assert client.post("/v1/jobs/job_nonexistent/extend").status_code == 404
