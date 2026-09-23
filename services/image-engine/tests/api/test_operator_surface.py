"""The operator page's engine half (DEC-108).

Every route is behind the operator token; orders carry what they were for and
every delivery attempt; a live job's files are viewable without counting as a
delivery; order records keep their own retention clock.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from exam_photo.api.app import app
from exam_photo.api.contracts import ApiJobStatus, JobEntitlement
from exam_photo.api.jobs import JobRegistry
from exam_photo.api.orders import OrderItem, OrderRegistry
from exam_photo.api.razorpay_orders import CreatedOrder
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore

client = TestClient(app, raise_server_exceptions=False)
OPERATOR = "op-secret"
AUTH = {"X-Operator-Token": OPERATOR}
KIT = "kit_operator"


@pytest.fixture
def api(tmp_path):
    from exam_photo.api.app import service

    original = (
        service.settings,
        service.store,
        service.registry,
        service.orders,
        service._order_gateway,
    )
    root = tmp_path / "artifacts"
    service.settings = ApiSettings(artifact_root=root, operator_token=OPERATOR)
    service.store = LocalArtifactStore(root)
    service.registry = JobRegistry(root)
    service.orders = OrderRegistry(root)
    try:
        yield service
    finally:
        (
            service.settings,
            service.store,
            service.registry,
            service.orders,
            service._order_gateway,
        ) = original


def _job(api, job_id, released=False):
    record = api.registry.create_job(job_id, 1800)
    record.status = ApiJobStatus.SUCCEEDED
    record.kit_id = KIT
    record.exam_id = "ctet-september-2026"
    record.requirement_type = "photograph"
    record.output_filename = f"{job_id}.jpg"
    if released:
        record.entitlement = JobEntitlement.RELEASED
    api.store.write_file(job_id, "input.jpg", b"\xff\xd8source")
    api.store.write_file(job_id, f"{job_id}.jpg", b"\xff\xd8prepared")
    api.store.write_file(job_id, "report.json", b'{"stages": {"crop": 0.2}}')
    api.registry.update_job(record)
    return record


@pytest.mark.parametrize(
    "path",
    [
        "/v1/orders",
        "/v1/operator/jobs",
        "/v1/operator/jobs/job_a",
        "/v1/operator/jobs/job_a/files/input.jpg",
        "/v1/operator/health",
    ],
)
def test_every_operator_route_refuses_without_the_token(api, path):
    _job(api, "job_a")
    assert client.get(path).status_code == 401
    assert client.get(path, headers={"X-Operator-Token": "wrong"}).status_code == 401


def test_live_jobs_are_listed_with_their_names_and_files(api):
    _job(api, "job_a")
    [job] = client.get("/v1/operator/jobs", headers=AUTH).json()["jobs"]
    assert job["job_id"] == "job_a"
    assert job["exam_name"] == "CTET September 2026"
    assert job["released"] is False
    names = {item["name"] for item in job["files"]}
    assert {"input.jpg", "job_a.jpg", "report.json"} <= names
    assert "job.json" not in names


def test_an_expired_job_is_not_listed(api):
    record = _job(api, "job_old")
    record.expires_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    api.registry.update_job(record)
    assert client.get("/v1/operator/jobs", headers=AUTH).json()["jobs"] == []
    assert client.get("/v1/operator/jobs/job_old", headers=AUTH).status_code == 404


def test_the_source_photograph_is_served_uncached_and_not_counted(api):
    _job(api, "job_a")
    response = client.get("/v1/operator/jobs/job_a/files/input.jpg", headers=AUTH)
    assert response.status_code == 200
    assert response.content == b"\xff\xd8source"
    assert "no-store" in response.headers["cache-control"]
    # An unpaid output is viewable by the operator, and viewing is not delivery.
    prepared = client.get("/v1/operator/jobs/job_a/files/job_a.jpg", headers=AUTH)
    assert prepared.status_code == 200
    assert api.registry.get_job("job_a").download_count == 0


@pytest.mark.parametrize("name", ["job.json", "..%2Fjob_b%2Finput.jpg", "notes.txt"])
def test_only_media_files_of_that_job_are_served(api, name):
    _job(api, "job_a")
    _job(api, "job_b")
    response = client.get(f"/v1/operator/jobs/job_a/files/{name}", headers=AUTH)
    assert response.status_code == 404


def test_job_detail_carries_the_report(api):
    _job(api, "job_a")
    detail = client.get("/v1/operator/jobs/job_a", headers=AUTH).json()
    assert detail["report"] == {"stages": {"crop": 0.2}}


def test_an_order_names_what_it_was_for(api):
    _job(api, "job_a")

    class Gateway:
        def create_order(self, amount_paise, currency, notes, receipt):
            return CreatedOrder(
                order_id="order_OP1",
                amount_paise=amount_paise,
                currency=currency,
                key_id="k",
            )

    api.order_gateway = Gateway()
    assert client.post(f"/v1/kits/{KIT}/order").status_code == 200

    [order] = client.get("/v1/orders", headers=AUTH).json()["orders"]
    assert order["order_id"] == "order_OP1"
    [item] = order["items"]
    assert item["exam_name"] == "CTET September 2026"
    assert item["job_id"] == "job_a"


def test_every_delivery_attempt_is_kept_on_the_order(api):
    orders: OrderRegistry = api.orders
    orders.create("order_D1", KIT, ["job_a"], 300, "INR")
    orders.mark_delivery_failed("job_a", "email", "c***@example.com", "smtp down")
    orders.mark_delivered("job_a", "email", "c***@example.com")
    orders.mark_delivered("job_a", "download")

    record = orders.get("order_D1")
    assert record is not None
    assert record.delivery_method == "email"
    assert [d.succeeded for d in record.deliveries] == [False, True, True]
    assert record.deliveries[1].masked_address == "c***@example.com"


def test_orders_list_newest_first(api):
    orders: OrderRegistry = api.orders
    orders.create("order_A", KIT, [], 300, "INR", items=[OrderItem(job_id="job_x")])
    orders.create("order_B", KIT, [], 500, "INR")
    listed = client.get("/v1/orders", headers=AUTH).json()["orders"]
    assert [o["order_id"] for o in listed] == ["order_B", "order_A"]


def test_order_retention_keeps_eight_years_with_addresses(api):
    orders: OrderRegistry = api.orders
    now = datetime.now(timezone.utc)
    for order_id, days in (("order_mid", 200), ("order_old", 3000)):
        orders.create(order_id, KIT, ["job_a"], 300, "INR")
        record = orders.get(order_id)
        assert record is not None
        record.created_at = (now - timedelta(days=days)).isoformat()
        orders._path(order_id).write_text(record.model_dump_json(), encoding="utf-8")
    orders.mark_delivered("job_a", "email", "c***@example.com", "cand@example.com")

    assert orders.sweep(now) == 1
    assert orders.get("order_old") is None
    mid = orders.get("order_mid")
    assert mid is not None
    assert mid.deliveries[0].address == "cand@example.com"


def test_health_reports_readiness_and_disk(api):
    body = client.get("/v1/operator/health", headers=AUTH).json()
    assert "status" in body
    assert body["disk"]["free_bytes"] > 0
