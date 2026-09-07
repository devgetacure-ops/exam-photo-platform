"""What a kit costs, and the order that binds that price to a payment (DEC-070).

DEC-069 built a webhook that could prove Razorpay sent an event but not that
the candidate paid the asking price, because nothing in the engine knew the
price. These are the two halves that close it: a quote computed from the jobs
on disk, and an order created server-side at that amount.

The property that matters most is negative and is pinned first: **no amount
supplied by a caller reaches Razorpay.**
"""

import json

import pytest
from fastapi.testclient import TestClient

from exam_photo.api.app import app
from exam_photo.api.contracts import ApiJobStatus, JobEntitlement
from exam_photo.api.jobs import JobRegistry
from exam_photo.api.pricing import (
    LIST_LADDER_PAISE,
    PRICE_LADDER_PAISE,
    quote_for,
)
from exam_photo.api.razorpay_orders import (
    CreatedOrder,
    OrderCreationError,
    UnconfiguredOrderGateway,
    gateway_for,
    order_notes,
)
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore

client = TestClient(app, raise_server_exceptions=False)

KIT = "kit_pricing"


class FakeGateway:
    """Records what it was asked to charge. Never reaches the network."""

    def __init__(self, fail: bool = False):
        self.calls: list[dict] = []
        self.fail = fail

    def create_order(self, amount_paise, currency, notes, receipt):
        self.calls.append(
            {
                "amount_paise": amount_paise,
                "currency": currency,
                "notes": notes,
                "receipt": receipt,
            }
        )
        if self.fail:
            raise OrderCreationError("Razorpay said no")
        return CreatedOrder(
            order_id="order_TEST123",
            amount_paise=amount_paise,
            currency=currency,
            key_id="rzp_test_key",
        )


@pytest.fixture
def api(tmp_path):
    from exam_photo.api.app import service

    original = (
        service.settings,
        service.store,
        service.registry,
        service._order_gateway,
    )
    service.settings = ApiSettings(artifact_root=tmp_path / "artifacts")
    service.store = LocalArtifactStore(tmp_path / "artifacts")
    service.registry = JobRegistry(tmp_path / "artifacts")
    service.order_gateway = FakeGateway()
    try:
        yield service
    finally:
        (
            service.settings,
            service.store,
            service.registry,
            service._order_gateway,
        ) = original


def _job(api, job_id, requirement_type, kit_id=KIT, released=False, prepared=True):
    record = api.registry.create_job(job_id, 1800)
    record.status = ApiJobStatus.SUCCEEDED
    record.kit_id = kit_id
    record.requirement_type = requirement_type
    record.requirement_id = requirement_type
    if prepared:
        record.output_filename = "output.jpg"
        api.store.write_file(job_id, "output.jpg", b"\xff\xd8\xff\xdb-out")
    if released:
        record.entitlement = JobEntitlement.RELEASED
    api.registry.update_job(record)
    return record


# ----------------------------------------------------------------------
# The ladder
# ----------------------------------------------------------------------


def test_the_ladder_is_the_owners_prices():
    """Rs 3, Rs 5, Rs 8, struck through from Rs 4, Rs 8, Rs 10."""
    assert PRICE_LADDER_PAISE == (300, 500, 800)
    assert LIST_LADDER_PAISE == (400, 800, 1000)


def test_one_image_deliverable_costs_three_rupees(api):
    _job(api, "job_a", "photograph")

    body = client.get(f"/v1/kits/{KIT}/quote").json()

    assert body["amount_paise"] == 300
    assert body["list_amount_paise"] == 400
    assert body["chargeable_count"] == 1


def test_two_cost_five(api):
    _job(api, "job_a", "photograph")
    _job(api, "job_b", "signature")

    assert client.get(f"/v1/kits/{KIT}/quote").json()["amount_paise"] == 500


def test_three_cost_eight(api):
    _job(api, "job_a", "photograph")
    _job(api, "job_b", "signature")
    _job(api, "job_c", "thumb_impression")

    assert client.get(f"/v1/kits/{KIT}/quote").json()["amount_paise"] == 800


def test_the_top_tier_is_a_ceiling_not_a_step(api):
    """Eight rupees is the promise: everything an examination asks for."""
    for index, kind in enumerate(
        ["photograph", "signature", "thumb_impression", "handwritten_declaration"]
    ):
        _job(api, f"job_{index}", kind)

    body = client.get(f"/v1/kits/{KIT}/quote").json()

    assert body["chargeable_count"] == 4
    assert body["amount_paise"] == 800


# ----------------------------------------------------------------------
# What is free, and why
# ----------------------------------------------------------------------


def test_document_work_is_free(api):
    """The owner's rule: we do not charge for what candidates get free elsewhere."""
    _job(api, "job_cert", "certificate_scan")
    _job(api, "job_id_doc", "identity_document")

    body = client.get(f"/v1/kits/{KIT}/quote").json()

    assert body["amount_paise"] == 0
    assert body["is_payable"] is False
    assert body["included_free_count"] == 2
    assert {line["reason"] for line in body["lines"]} == {"document_work_is_free"}


def test_certificates_ride_free_alongside_charged_images(api):
    """Three rupees for the photograph; the certificates add nothing."""
    _job(api, "job_photo", "photograph")
    _job(api, "job_c1", "certificate_scan")
    _job(api, "job_c2", "certificate_scan")

    body = client.get(f"/v1/kits/{KIT}/quote").json()

    assert body["amount_paise"] == 300
    assert body["chargeable_count"] == 1
    assert body["included_free_count"] == 2


def test_an_already_paid_file_is_not_charged_twice(api):
    _job(api, "job_paid", "photograph", released=True)
    _job(api, "job_new", "signature")

    body = client.get(f"/v1/kits/{KIT}/quote").json()

    assert body["amount_paise"] == 300
    assert body["already_released_count"] == 1


def test_a_job_with_nothing_prepared_is_not_charged(api):
    _job(api, "job_empty", "photograph", prepared=False)

    assert client.get(f"/v1/kits/{KIT}/quote").json()["amount_paise"] == 0


def test_an_expired_job_is_not_charged(api):
    from datetime import datetime, timedelta, timezone

    record = _job(api, "job_gone", "photograph")
    record.expires_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    api.registry.update_job(record)

    assert quote_for([record]).amount_paise == 0


def test_every_deliverable_is_reported_with_its_reason(api):
    """An itemised quote is what makes an argument about a charge settleable."""
    _job(api, "job_photo", "photograph")
    _job(api, "job_cert", "certificate_scan")

    lines = {
        line["job_id"]: line
        for line in client.get(f"/v1/kits/{KIT}/quote").json()["lines"]
    }

    assert lines["job_photo"]["chargeable"] is True
    assert lines["job_photo"]["reason"] == "charged"
    assert lines["job_cert"]["chargeable"] is False
    assert lines["job_cert"]["reason"] == "document_work_is_free"


# ----------------------------------------------------------------------
# The order: no caller-supplied amount reaches Razorpay
# ----------------------------------------------------------------------


def test_the_order_amount_comes_from_the_jobs_not_the_caller(api):
    """The whole point of DEC-070."""
    _job(api, "job_a", "photograph")
    _job(api, "job_b", "signature")

    body = client.post(f"/v1/kits/{KIT}/order").json()

    assert body["amount_paise"] == 500
    assert api.order_gateway.calls[0]["amount_paise"] == 500


def test_an_amount_in_the_request_body_is_ignored(api):
    """A browser must not be able to ask to be charged less."""
    _job(api, "job_a", "photograph")
    _job(api, "job_b", "signature")

    response = client.post(
        f"/v1/kits/{KIT}/order",
        content=json.dumps({"amount_paise": 1, "amount": 1}),
        headers={"Content-Type": "application/json"},
    )

    assert response.json()["amount_paise"] == 500
    assert api.order_gateway.calls[0]["amount_paise"] == 500


def test_the_order_carries_the_kit_so_the_webhook_can_release_it(api):
    """Without this the payment succeeds and nothing is ever delivered."""
    _job(api, "job_a", "photograph")

    client.post(f"/v1/kits/{KIT}/order")

    assert api.order_gateway.calls[0]["notes"]["kit_id"] == KIT


def test_an_order_is_refused_when_there_is_nothing_to_pay_for(api):
    _job(api, "job_cert", "certificate_scan")

    response = client.post(f"/v1/kits/{KIT}/order")

    assert response.status_code == 409
    assert api.order_gateway.calls == []


def test_an_empty_kit_cannot_be_ordered(api):
    assert client.post(f"/v1/kits/{KIT}/order").status_code == 409


def test_a_gateway_failure_is_503_and_says_nothing_about_razorpay(api):
    """A gateway's own error text is not something to render into a page."""
    _job(api, "job_a", "photograph")
    api.order_gateway = FakeGateway(fail=True)

    response = client.post(f"/v1/kits/{KIT}/order")

    assert response.status_code == 503
    assert "Razorpay" not in response.json()["detail"]


def test_a_malformed_kit_id_is_refused(api):
    assert client.post("/v1/kits/not-a-kit/order").status_code == 400
    assert client.get("/v1/kits/not-a-kit/quote").status_code == 400


# ----------------------------------------------------------------------
# The gateway a host's configuration entitles it to
# ----------------------------------------------------------------------


def test_a_host_without_credentials_gets_a_gateway_that_refuses():
    """DEC-060: no keys must fail loudly, not fall back to something."""
    gateway = gateway_for("", "")

    assert isinstance(gateway, UnconfiguredOrderGateway)
    with pytest.raises(OrderCreationError, match="not configured"):
        gateway.create_order(300, "INR", {}, "receipt")


def test_credentials_produce_a_real_gateway():
    from exam_photo.api.razorpay_orders import HttpOrderGateway

    assert isinstance(gateway_for("rzp_test_x", "secret"), HttpOrderGateway)


def test_order_notes_always_name_the_kit():
    assert order_notes("kit_abc") == {"kit_id": "kit_abc"}
    assert order_notes("kit_abc", ["job_1", "job_2"])["job_ids"] == "job_1,job_2"


# ----------------------------------------------------------------------
# End to end, without the network: quote, order, webhook, download
# ----------------------------------------------------------------------


def test_a_paid_order_releases_exactly_what_was_quoted(api):
    """Quote, order, webhook, download -- the whole path in one test."""
    import hashlib
    import hmac

    secret = "webhook-secret"
    api.settings = api.settings.model_copy(update={"razorpay_webhook_secret": secret})
    _job(api, "job_a", "photograph")
    _job(api, "job_b", "signature")
    _job(api, "job_free", "certificate_scan")

    quote = client.get(f"/v1/kits/{KIT}/quote").json()
    assert quote["amount_paise"] == 500

    order = client.post(f"/v1/kits/{KIT}/order").json()
    assert order["amount_paise"] == 500

    body = json.dumps(
        {
            "event": "order.paid",
            "payload": {
                "order": {
                    "entity": {
                        "id": order["order_id"],
                        "amount": order["amount_paise"],
                        "currency": "INR",
                        "notes": {"kit_id": KIT},
                    }
                },
                "payment": {
                    "entity": {
                        "id": "pay_1",
                        "amount": 500,
                        "currency": "INR",
                        "notes": {},
                    }
                },
            },
        }
    ).encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    released = client.post(
        "/v1/payments/razorpay/webhook",
        content=body,
        headers={"X-Razorpay-Signature": signature},
    ).json()["released"]

    assert sorted(released) == ["job_a", "job_b", "job_free"]
    assert client.get("/v1/jobs/job_a/output").status_code == 200
    # And the kit is now settled: nothing further to charge for.
    assert client.get(f"/v1/kits/{KIT}/quote").json()["is_payable"] is False
