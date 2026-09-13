"""The payment simulator, for walking checkout without a Razorpay account (DEC-089).

The refusals lead, because a simulator is a way to release a paid file without
paying: it does not exist unless switched on, it will not run beside real
Razorpay credentials, and it settles only orders it created. Then that a
simulated payment releases exactly what a verified webhook would.
"""

import pytest
from fastapi.testclient import TestClient

from exam_photo.api.app import app
from exam_photo.api.contracts import ApiJobStatus, JobEntitlement
from exam_photo.api.jobs import JobRegistry
from exam_photo.api.orders import ORDER_ID_REGEX, OrderRegistry
from exam_photo.api.protection import UsageRegistry
from exam_photo.api.razorpay_orders import (
    SIMULATOR_KEY_ID,
    ConflictingSimulatorGateway,
    OrderCreationError,
    SimulatedOrderGateway,
    gateway_for,
    order_notes,
)
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore

client = TestClient(app, raise_server_exceptions=False)

KIT = "kit_simulator"


def _use(service, tmp_path, **settings):
    service.settings = ApiSettings(artifact_root=tmp_path / "artifacts", **settings)
    service.store = LocalArtifactStore(tmp_path / "artifacts")
    service.registry = JobRegistry(tmp_path / "artifacts")
    service.orders = OrderRegistry(tmp_path / "artifacts")
    service.usage = UsageRegistry(tmp_path / "artifacts")
    service._order_gateway = None


@pytest.fixture
def api(tmp_path):
    from exam_photo.api.app import service

    original = (
        service.settings,
        service.store,
        service.registry,
        service.orders,
        service.usage,
        service._order_gateway,
    )
    try:
        yield lambda **settings: _use(service, tmp_path, **settings) or service
    finally:
        (
            service.settings,
            service.store,
            service.registry,
            service.orders,
            service.usage,
            service._order_gateway,
        ) = original


def _job(service, job_id, requirement_type="photograph"):
    record = service.registry.create_job(job_id, 1800)
    record.status = ApiJobStatus.SUCCEEDED
    record.kit_id = KIT
    record.requirement_type = requirement_type
    record.requirement_id = requirement_type
    record.output_filename = "output.jpg"
    service.store.write_file(job_id, "output.jpg", b"\xff\xd8\xff\xdb-out")
    service.registry.update_job(record)
    return record


# ----------------------------------------------------------------------
# It does not exist unless it is asked for
# ----------------------------------------------------------------------


def test_the_route_does_not_exist_with_the_simulator_off(api):
    service = api()
    _job(service, "job_a")
    order = client.post(f"/v1/kits/{KIT}/order")
    assert order.status_code == 503  # no Razorpay keys: order creation refuses

    response = client.post("/v1/payments/simulator/order_simabc/pay")
    assert response.status_code == 404
    assert service.registry.get_job("job_a").entitlement != JobEntitlement.RELEASED


def test_the_quote_says_razorpay_unless_the_simulator_is_on(api):
    api()
    assert client.get(f"/v1/kits/{KIT}/quote").json()["payment_mode"] == "razorpay"
    api(payment_simulator_enabled=True)
    assert client.get(f"/v1/kits/{KIT}/quote").json()["payment_mode"] == "simulator"


def test_the_simulator_refuses_to_run_beside_razorpay_credentials(api):
    service = api(
        payment_simulator_enabled=True,
        razorpay_key_id="rzp_live_x",
        razorpay_key_secret="secret",
    )
    _job(service, "job_a")

    assert isinstance(
        gateway_for("rzp_live_x", "secret", simulator=True), ConflictingSimulatorGateway
    )
    with pytest.raises(OrderCreationError):
        ConflictingSimulatorGateway().create_order(300, "INR", order_notes(KIT), "kit")
    assert client.post(f"/v1/kits/{KIT}/order").status_code == 503
    assert client.post("/v1/payments/simulator/order_simabc/pay").status_code == 404


def test_it_settles_only_orders_it_created(api):
    service = api(payment_simulator_enabled=True)
    _job(service, "job_a")
    service.orders.create(
        order_id="order_RealRazorpay1",
        kit_id=KIT,
        job_ids=["job_a"],
        amount_paise=300,
        currency="INR",
    )

    assert (
        client.post("/v1/payments/simulator/order_RealRazorpay1/pay").status_code == 404
    )
    assert client.post("/v1/payments/simulator/order_simnothere/pay").status_code == 404
    assert service.registry.get_job("job_a").entitlement != JobEntitlement.RELEASED


# ----------------------------------------------------------------------
# What it does when it is on
# ----------------------------------------------------------------------


def test_a_simulated_order_is_priced_and_recorded_like_a_real_one(api):
    service = api(payment_simulator_enabled=True)
    _job(service, "job_a")
    _job(service, "job_b", "signature")

    body = client.post(f"/v1/kits/{KIT}/order").json()

    assert body["key_id"] == SIMULATOR_KEY_ID
    assert body["amount_paise"] == 500
    assert ORDER_ID_REGEX.match(body["order_id"])
    record = service.orders.get(body["order_id"])
    assert record is not None and sorted(record.job_ids) == ["job_a", "job_b"]
    assert isinstance(gateway_for("", "", simulator=True), SimulatedOrderGateway)


def test_paying_releases_the_order_through_the_webhook_path(api):
    service = api(payment_simulator_enabled=True)
    _job(service, "job_a")
    order_id = client.post(f"/v1/kits/{KIT}/order").json()["order_id"]

    response = client.post(f"/v1/payments/simulator/{order_id}/pay")

    assert response.status_code == 200
    assert response.json()["released"] == ["job_a"]
    record = service.registry.get_job("job_a")
    assert record.entitlement == JobEntitlement.RELEASED
    assert record.payment_reference and record.payment_reference.startswith("pay_sim")
    assert service.orders.get(order_id).paid_at is not None
    assert client.get("/v1/jobs/job_a/output").status_code == 200


def test_ready_says_payments_are_simulated(api):
    api(payment_simulator_enabled=True)
    assert client.get("/ready").json()["payments"] == "simulated"
