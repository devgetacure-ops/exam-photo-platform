"""The four things that stood between the service and a public host (DEC-064).

Warmup and readiness, the artifact sweeper, configurable CORS, and what
protects the CPU. Each of these is invisible in local use and each is a
production incident, so each is pinned here rather than left to a deployment
to discover.
"""

import io
import threading
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from exam_photo.api.app import app
from exam_photo.api.jobs import JobRegistry
from exam_photo.api.service import ApiProcessingService, ServiceBusyError
from exam_photo.api.settings import ApiSettings, get_settings
from exam_photo.api.storage import LocalArtifactStore

client = TestClient(app, raise_server_exceptions=False)

EXAM = "ctet-september-2026"
SIGNATURE = "candidate_signature"


@pytest.fixture
def api(tmp_path):
    """The service against a temporary root, at production defaults."""
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
    buffer = io.BytesIO()
    Image.fromarray((canvas * 255).astype(np.uint8), mode="RGB").save(
        buffer, "JPEG", quality=92
    )
    return buffer.getvalue()


def _prepare(**form):
    return client.post(
        f"/v1/exams/{EXAM}/requirements/{SIGNATURE}/prepare",
        files={"file": ("upload.jpg", _signature_photo(), "image/jpeg")},
        data=form,
    )


# ----------------------------------------------------------------------
# Blocker 1: readiness is not liveness
# ----------------------------------------------------------------------


@pytest.mark.mandatory_api
def test_health_stays_liveness_only(api):
    """Unchanged contract: anything already pointing at it keeps working."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.mandatory_api
def test_a_cold_process_is_not_ready(api):
    """The defect: `/health` said healthy while the model was 100-150 s away."""
    api._warmup_state = "warming"
    api._warmup_started_at = time.monotonic()
    api._warmup_finished_at = None

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "warming"
    assert response.json()["warmup_seconds"] is not None


@pytest.mark.mandatory_api
def test_a_warm_process_is_ready(api):
    api._warmup_state = "ready"
    api._warmup_error = None

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.mandatory_api
def test_a_failed_warmup_is_503_and_names_the_cause(api):
    """DEC-060's loud failure, arriving where a deployment actually looks."""
    with patch.object(
        ApiProcessingService,
        "_get_pipeline",
        side_effect=RuntimeError("run scripts/download_birefnet.py"),
    ):
        api.warmup()

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "failed"
    assert "download_birefnet.py" in response.json()["error"]


@pytest.mark.mandatory_api
def test_warmup_runs_an_inference_not_merely_a_model_load(api):
    """DEC-054 measured the one-time cost on the first *inference*.

    Constructing the session and calling nothing would leave the whole penalty
    for the first candidate while reporting the process ready.
    """
    with patch.object(ApiProcessingService, "_get_pipeline") as get_pipeline:
        api.warmup()

    get_pipeline.return_value.warmup.assert_called_once()
    assert api.readiness()["status"] == "ready"


@pytest.mark.mandatory_api
def test_a_process_whose_hook_has_not_run_claims_nothing(api):
    """ "Not started" is not the same as "warmed"; neither is it "failed"."""
    api._warmup_state = "not_started"

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["warmup"] == "not_started"


@pytest.mark.mandatory_api
def test_a_host_that_turned_warmup_off_is_still_ready(api):
    """Otherwise `warmup_on_boot=false` is a permanent 503 and unusable.

    The operator asked for no pre-warm. That costs the first request its
    first-inference time -- the behaviour before DEC-064 -- and must not keep
    the process out of the load balancer forever.
    """
    api.settings = api.settings.model_copy(update={"warmup_on_boot": False})
    api._warmup_state = "not_started"
    api.start_background_workers()
    try:
        response = client.get("/ready")
    finally:
        api.stop_background_workers()

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["warmup"] == "skipped"


@pytest.mark.mandatory_api
def test_readiness_reports_an_unauthenticated_operator_surface(api):
    """An open operator surface in production is otherwise entirely silent."""
    assert client.get("/ready").json()["operator_surface"] == "unauthenticated"

    api.settings = api.settings.model_copy(update={"operator_token": "s3cret"})
    try:
        assert client.get("/ready").json()["operator_surface"] == "authenticated"
    finally:
        api.settings = api.settings.model_copy(update={"operator_token": ""})


# ----------------------------------------------------------------------
# Blocker 2: expired artifacts are actually deleted
# ----------------------------------------------------------------------


@pytest.mark.mandatory_api
def test_the_sweeper_deletes_an_expired_job(api):
    """`expires_at` was written on every manifest and acted on by nothing."""
    body = _prepare().json()
    record = api.registry.get_job(body["job_id"])
    record.expires_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    api.registry.update_job(record)

    assert api.cleanup_expired_jobs() == 1
    assert not (api.settings.artifact_root / body["job_id"]).exists()


@pytest.mark.mandatory_api
def test_the_sweeper_leaves_a_live_job_alone(api):
    body = _prepare().json()

    assert api.cleanup_expired_jobs() == 0
    assert client.get(body["preview_url"]).status_code == 200


@pytest.mark.mandatory_api
def test_the_sweeper_runs_on_a_timer_without_being_asked(api):
    """Nothing called `POST /v1/cleanup-expired`, which was the whole defect."""
    api.settings = api.settings.model_copy(
        update={"cleanup_interval_seconds": 1, "warmup_on_boot": False}
    )
    api._warmup_state = "not_started"
    swept = threading.Event()
    with patch.object(
        ApiProcessingService, "cleanup_expired_jobs", side_effect=lambda: swept.set()
    ):
        api.start_background_workers()
        try:
            assert swept.wait(timeout=10), "the sweeper never ran on its own"
        finally:
            api.stop_background_workers()


@pytest.mark.mandatory_api
def test_one_failed_sweep_does_not_end_retention(api):
    """A single unreadable directory must not silently stop the loop."""
    api.settings = api.settings.model_copy(
        update={"cleanup_interval_seconds": 1, "warmup_on_boot": False}
    )
    api._warmup_state = "not_started"
    calls: list[int] = []
    done = threading.Event()

    def flaky() -> int:
        calls.append(1)
        if len(calls) == 1:
            raise OSError("disk hiccup")
        done.set()
        return 0

    with patch.object(ApiProcessingService, "cleanup_expired_jobs", side_effect=flaky):
        api.start_background_workers()
        try:
            assert done.wait(timeout=10), "the sweeper stopped after one failure"
        finally:
            api.stop_background_workers()


# ----------------------------------------------------------------------
# Blocker 3: CORS origins are configured, not hardcoded
# ----------------------------------------------------------------------


@pytest.mark.mandatory_api
def test_a_deployed_origin_can_be_configured(monkeypatch):
    """Hardcoded localhost meant the first request from a real domain failed."""
    monkeypatch.setenv(
        "EXAM_PHOTO_ALLOWED_ORIGINS", "https://examupload.in, https://www.examupload.in"
    )

    settings = get_settings()

    assert settings.allowed_origins == [
        "https://examupload.in",
        "https://www.examupload.in",
    ]


@pytest.mark.mandatory_api
def test_no_configuration_means_no_cross_origin_access(monkeypatch):
    """Same-origin behind a reverse proxy is the shape that needs no CORS."""
    monkeypatch.delenv("EXAM_PHOTO_ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("EXAM_PHOTO_LOCAL_CORS_ENABLED", raising=False)

    settings = get_settings()

    assert settings.allowed_origins == []
    assert settings.local_cors_enabled is False


# ----------------------------------------------------------------------
# Blocker 4: the operator surface, and what protects the CPU
# ----------------------------------------------------------------------


@pytest.mark.mandatory_api
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/test"),
        ("post", "/v1/cleanup-expired"),
        ("post", "/v1/rules/validate"),
        ("post", "/v1/process"),
    ],
)
def test_the_operator_surface_refuses_without_the_token(api, method, path):
    api.settings = api.settings.model_copy(update={"operator_token": "s3cret"})
    try:
        response = getattr(client, method)(path)
    finally:
        api.settings = api.settings.model_copy(update={"operator_token": ""})

    assert response.status_code == 401


@pytest.mark.mandatory_api
def test_the_operator_surface_accepts_the_token(api):
    api.settings = api.settings.model_copy(update={"operator_token": "s3cret"})
    try:
        response = client.post(
            "/v1/cleanup-expired", headers={"X-Operator-Token": "s3cret"}
        )
    finally:
        api.settings = api.settings.model_copy(update={"operator_token": ""})

    assert response.status_code == 200


@pytest.mark.mandatory_api
def test_a_wrong_token_is_refused(api):
    api.settings = api.settings.model_copy(update={"operator_token": "s3cret"})
    try:
        response = client.post(
            "/v1/cleanup-expired", headers={"X-Operator-Token": "wrong"}
        )
    finally:
        api.settings = api.settings.model_copy(update={"operator_token": ""})

    assert response.status_code == 401


@pytest.mark.mandatory_api
def test_the_candidate_surface_is_never_token_gated(api):
    """A browser would have to carry the token and would leak it to anyone."""
    api.settings = api.settings.model_copy(update={"operator_token": "s3cret"})
    try:
        assert client.get("/v1/exams").status_code == 200
        assert client.get(f"/v1/exams/{EXAM}").status_code == 200
        assert _prepare().status_code == 200
    finally:
        api.settings = api.settings.model_copy(update={"operator_token": ""})


@pytest.mark.mandatory_api
def test_preparation_is_refused_when_every_slot_is_taken(api):
    """A global cap, so no candidate is punished for their carrier's NAT."""
    api._preparation_slots = threading.BoundedSemaphore(1)

    with api.preparation_slot():
        response = _prepare()

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "15"


@pytest.mark.mandatory_api
def test_a_slot_is_released_after_the_work_finishes(api):
    api._preparation_slots = threading.BoundedSemaphore(1)

    assert _prepare().status_code == 200
    assert _prepare().status_code == 200


@pytest.mark.mandatory_api
def test_a_slot_is_released_even_when_preparation_raises(api):
    with pytest.raises(ValueError):
        with api.preparation_slot():
            raise ValueError("boom")

    assert _prepare().status_code == 200


@pytest.mark.mandatory_api
def test_the_slot_limiter_refuses_rather_than_queueing(api):
    """A request held behind a hundred others is cut by the proxy anyway."""
    api._preparation_slots = threading.BoundedSemaphore(1)

    with api.preparation_slot():
        started = time.monotonic()
        with pytest.raises(ServiceBusyError):
            with api.preparation_slot():
                pass
        assert time.monotonic() - started < 1.0


@pytest.mark.mandatory_api
def test_a_document_request_cannot_carry_unlimited_files(api):
    """Each file was bounded; the count was not (DEC-064)."""
    api.settings = api.settings.model_copy(update={"max_document_files": 3})

    response = client.post(
        f"/v1/exams/{EXAM}/requirements/{SIGNATURE}/documents",
        files=[
            ("files", (f"page{index}.jpg", _signature_photo(), "image/jpeg"))
            for index in range(4)
        ],
    )

    assert response.status_code == 413
    assert "at most 3 files" in response.json()["detail"]
