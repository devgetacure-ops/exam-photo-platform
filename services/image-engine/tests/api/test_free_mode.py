"""The site running free, paid for by advertising (DEC-127).

With billing off -- the default -- a prepared file is released the moment it
exists, its preview carries no mark, and no route that quotes, charges,
refunds or redeems anything answers. The paid behaviour itself stays covered
by the other API suites, which switch billing on.
"""

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

EXAM = "ctet-september-2026"
SIGNATURE = "candidate_signature"


@pytest.fixture
def api(tmp_path):
    """The service against a temporary root, with billing at its default."""
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


def _prepare(kit_id: str = "kit_free_mode_test"):
    return client.post(
        f"/v1/exams/{EXAM}/requirements/{SIGNATURE}/prepare",
        files={"file": ("upload.jpg", _signature_photo(), "image/jpeg")},
        data={"kit_id": kit_id},
    )


def test_billing_is_off_by_default():
    assert ApiSettings().billing_enabled is False


@pytest.mark.mandatory_api
def test_a_prepared_file_downloads_without_payment(api):
    body = _prepare().json()

    response = client.get(body["output_url"])

    assert response.status_code == 200
    assert len(response.content) == body["byte_size"]
    assert body["entitlement"] == "released"


@pytest.mark.mandatory_api
def test_the_status_reports_the_file_released(api):
    body = _prepare().json()

    status = client.get(f"/v1/jobs/{body['job_id']}").json()

    assert status["entitlement"] == "released"
    assert status["output_url"]


@pytest.mark.mandatory_api
def test_the_preview_is_served_and_carries_no_mark(api):
    body = _prepare().json()

    assert body["preview_url"]
    assert body["preview_watermarked"] is False
    response = client.get(body["preview_url"])
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


@pytest.mark.mandatory_api
def test_the_kit_zip_downloads_without_payment(api):
    kit = "kit_free_zip_test"
    _prepare(kit)

    response = client.get(f"/v1/kits/{kit}/package/download")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/v1/kits/kit_abc/quote"),
        ("post", "/v1/kits/kit_abc/order"),
        ("post", "/v1/kits/kit_abc/claim-free?coupon=FREE"),
        ("post", "/v1/payments/razorpay/webhook"),
        ("post", "/v1/payments/simulator/order_x/pay"),
        ("get", "/v1/kits/kit_abc/review?order_id=order_x"),
    ],
)
def test_no_paid_route_answers_while_free(api, method, path):
    assert getattr(client, method)(path).status_code == 404


def test_readiness_says_billing_is_off(api):
    ready = api.readiness()

    assert ready["billing"] == "off"
    assert ready["payments"] == "off"
    assert ready["purchase_gate"] == "disabled"


def test_switching_billing_on_brings_the_gate_back(api):
    api.settings = api.settings.model_copy(update={"billing_enabled": True})

    assert api.gate_active is True
    assert client.get("/v1/kits/kit_abc/quote").status_code != 404
