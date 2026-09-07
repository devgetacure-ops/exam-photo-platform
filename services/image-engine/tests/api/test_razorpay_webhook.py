"""The Razorpay webhook, and the gate it is allowed to open (DEC-069).

DEC-063 refused to write an HTTP route that releases a job, on the grounds
that an unauthenticated one reads as protection and is none. This is that
route, and the signature check is the entire difference. So what is pinned
here is mostly what the route *refuses*: an unsigned request, a forged one, a
body altered after signing, an authorisation that is not a payment, and a
request arriving at a host that never configured the secret.

The happy path matters too, but a payment path that only proves its happy
path has proved the wrong half.
"""

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from exam_photo.api.app import app
from exam_photo.api.contracts import ApiJobStatus, JobEntitlement
from exam_photo.api.jobs import JobRegistry
from exam_photo.api.payments import (
    SIGNATURE_HEADER,
    WebhookRejectedError,
    signature_matches,
    verify_and_read,
)
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore

client = TestClient(app, raise_server_exceptions=False)

SECRET = "a-shared-secret-only-razorpay-and-this-service-know"


@pytest.fixture
def api(tmp_path):
    """The service against a temporary root, with the webhook configured."""
    from exam_photo.api.app import service

    original = (service.settings, service.store, service.registry)
    service.settings = ApiSettings(
        artifact_root=tmp_path / "artifacts",
        razorpay_webhook_secret=SECRET,
    )
    service.store = LocalArtifactStore(tmp_path / "artifacts")
    service.registry = JobRegistry(tmp_path / "artifacts")
    try:
        yield service
    finally:
        service.settings, service.store, service.registry = original


def _sign(body: bytes, secret: str = SECRET) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _event(
    event="payment.captured",
    notes=None,
    payment_id="pay_ABC123",
    amount=400,
    order_notes=None,
):
    payload = {
        "entity": "event",
        "account_id": "acc_test",
        "event": event,
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "amount": amount,
                    "currency": "INR",
                    "status": "captured",
                    "notes": notes or {},
                }
            }
        },
    }
    if order_notes is not None:
        payload["payload"]["order"] = {
            "entity": {
                "id": "order_XYZ",
                "amount": amount,
                "currency": "INR",
                "notes": order_notes,
            }
        }
    return json.dumps(payload).encode()


def _post(body: bytes, signature: str | None = None):
    headers = {"Content-Type": "application/json"}
    if signature is not None:
        headers[SIGNATURE_HEADER] = signature
    return client.post("/v1/payments/razorpay/webhook", content=body, headers=headers)


def _prepared_job(api, job_id="job_paid", kit_id=None) -> str:
    record = api.registry.create_job(job_id, 1800)
    record.status = ApiJobStatus.SUCCEEDED
    record.output_filename = "output.jpg"
    record.output_media_type = "image/jpeg"
    record.kit_id = kit_id
    api.store.write_file(job_id, "output.jpg", b"\xff\xd8\xff\xdb-prepared")
    api.registry.update_job(record)
    assert record.entitlement == JobEntitlement.PREVIEW_ONLY
    return job_id


# ----------------------------------------------------------------------
# What the route refuses
# ----------------------------------------------------------------------


def test_an_unsigned_request_is_refused(api):
    _prepared_job(api)

    assert _post(_event(notes={"job_id": "job_paid"})).status_code == 400
    assert api.registry.get_job("job_paid").entitlement == JobEntitlement.PREVIEW_ONLY


def test_a_forged_signature_is_refused(api):
    _prepared_job(api)
    body = _event(notes={"job_id": "job_paid"})

    assert _post(body, "deadbeef" * 8).status_code == 400
    assert api.registry.get_job("job_paid").entitlement == JobEntitlement.PREVIEW_ONLY


def test_a_signature_from_the_wrong_secret_is_refused(api):
    _prepared_job(api)
    body = _event(notes={"job_id": "job_paid"})

    assert _post(body, _sign(body, "not-the-secret")).status_code == 400
    assert api.registry.get_job("job_paid").entitlement == JobEntitlement.PREVIEW_ONLY


def test_a_body_altered_after_signing_is_refused(api):
    """The whole attack: sign a 1-rupee order, then swap in someone else's job."""
    _prepared_job(api)
    honest = _event(notes={"job_id": "job_someone_else"})
    signature = _sign(honest)
    tampered = _event(notes={"job_id": "job_paid"})

    assert _post(tampered, signature).status_code == 400
    assert api.registry.get_job("job_paid").entitlement == JobEntitlement.PREVIEW_ONLY


def test_a_host_with_no_secret_configured_refuses_everything(api):
    """DEC-060 again: an unconfigured gate must fail shut, not open."""
    _prepared_job(api)
    api.settings = api.settings.model_copy(update={"razorpay_webhook_secret": ""})
    body = _event(notes={"job_id": "job_paid"})

    # Signed with the empty secret, which is what an attacker would try.
    assert _post(body, _sign(body, "")).status_code == 400
    assert api.registry.get_job("job_paid").entitlement == JobEntitlement.PREVIEW_ONLY


def test_an_oversized_body_is_refused():
    body = b"{" + b"x" * (64 * 1024 + 1)
    with pytest.raises(WebhookRejectedError, match="body too large"):
        verify_and_read(body, _sign(body), SECRET)


def test_the_refusal_says_nothing_about_which_check_failed(api):
    """A forger must not be able to bisect their way to a valid request."""
    body = _event(notes={"job_id": "job_paid"})
    unsigned = _post(body).json()["detail"]
    forged = _post(body, "00" * 32).json()["detail"]

    assert unsigned == forged == "Webhook rejected"


# ----------------------------------------------------------------------
# What it releases, and what it will not
# ----------------------------------------------------------------------


def test_a_captured_payment_releases_the_job_it_names(api):
    _prepared_job(api)
    body = _event(notes={"job_id": "job_paid"})

    response = _post(body, _sign(body))

    assert response.status_code == 200
    assert response.json()["released"] == ["job_paid"]
    assert api.registry.get_job("job_paid").entitlement == JobEntitlement.RELEASED
    assert client.get("/v1/jobs/job_paid/output").status_code == 200


def test_an_authorised_payment_releases_nothing(api):
    """An authorisation is a hold, not money. It can still fail."""
    _prepared_job(api)
    body = _event(event="payment.authorized", notes={"job_id": "job_paid"})

    response = _post(body, _sign(body))

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert api.registry.get_job("job_paid").entitlement == JobEntitlement.PREVIEW_ONLY


def test_a_refund_releases_nothing(api):
    _prepared_job(api)
    body = _event(event="refund.processed", notes={"job_id": "job_paid"})

    assert _post(body, _sign(body)).json()["status"] == "ignored"
    assert api.registry.get_job("job_paid").entitlement == JobEntitlement.PREVIEW_ONLY


def test_an_ignored_event_is_acknowledged_not_refused(api):
    """A 4xx would make Razorpay retry an event forever."""
    body = _event(event="payment.failed")

    assert _post(body, _sign(body)).status_code == 200


def test_a_paid_kit_releases_every_job_in_it(api):
    _prepared_job(api, "job_one", kit_id="kit_abc")
    _prepared_job(api, "job_two", kit_id="kit_abc")
    _prepared_job(api, "job_other", kit_id="kit_zzz")
    body = _event(notes={"kit_id": "kit_abc"})

    released = _post(body, _sign(body)).json()["released"]

    assert sorted(released) == ["job_one", "job_two"]
    assert api.registry.get_job("job_other").entitlement == JobEntitlement.PREVIEW_ONLY


def test_notes_on_the_order_are_read_too(api):
    """A bundle carries its identifiers on the order, not the payment."""
    _prepared_job(api, "job_one", kit_id="kit_abc")
    body = _event(notes={}, order_notes={"kit_id": "kit_abc"})

    assert _post(body, _sign(body)).json()["released"] == ["job_one"]


def test_a_payment_naming_nothing_is_acknowledged_and_flagged(api):
    """The money moved and no file can be released. Retrying will not help."""
    body = _event(notes={})

    response = _post(body, _sign(body))

    assert response.status_code == 200
    assert response.json()["status"] == "no_targets"


def test_an_unknown_job_does_not_stop_the_rest_of_a_bundle(api):
    _prepared_job(api, "job_real")
    body = _event(notes={"job_id": "job_real,job_never_existed"})

    outcome = _post(body, _sign(body)).json()

    assert outcome["released"] == ["job_real"]
    assert outcome["unknown"] == ["job_never_existed"]


def test_an_expired_job_cannot_be_released(api):
    """DEC-066: the file is gone, so an entitlement to it would be a lie."""
    from datetime import datetime, timedelta, timezone

    job_id = _prepared_job(api)
    record = api.registry.get_job(job_id)
    record.expires_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    api.registry.update_job(record)
    body = _event(notes={"job_id": job_id})

    outcome = _post(body, _sign(body)).json()

    assert outcome["released"] == []
    assert outcome["unknown"] == [job_id]


# ----------------------------------------------------------------------
# Razorpay retries. This must survive it.
# ----------------------------------------------------------------------


def test_the_same_webhook_delivered_twice_is_harmless(api):
    """Razorpay retries anything it was not told arrived."""
    _prepared_job(api)
    body = _event(notes={"job_id": "job_paid"})
    signature = _sign(body)

    first = _post(body, signature).json()
    second = _post(body, signature).json()

    assert first == second
    assert api.registry.get_job("job_paid").entitlement == JobEntitlement.RELEASED


# ----------------------------------------------------------------------
# The reconciliation trail
# ----------------------------------------------------------------------


def test_a_release_records_the_payment_that_caused_it(api):
    """A release with no payment reference is what an audit must be able to see."""
    _prepared_job(api)
    body = _event(notes={"job_id": "job_paid"}, payment_id="pay_TRACE", amount=400)

    _post(body, _sign(body))

    record = api.registry.get_job("job_paid")
    assert record.payment_reference == "pay_TRACE"
    assert record.payment_amount == 400
    assert record.payment_currency == "INR"
    assert record.released_at


# ----------------------------------------------------------------------
# The verifier itself
# ----------------------------------------------------------------------


def test_signature_comparison_rejects_an_empty_secret_or_signature():
    assert not signature_matches(b"{}", "", SECRET)
    assert not signature_matches(b"{}", _sign(b"{}"), "")


def test_a_verified_body_that_is_not_json_is_rejected():
    body = b"not json at all"
    with pytest.raises(WebhookRejectedError, match="not JSON"):
        verify_and_read(body, _sign(body), SECRET)


def test_a_verified_body_that_is_not_an_object_is_rejected():
    body = b"[1, 2, 3]"
    with pytest.raises(WebhookRejectedError, match="not a JSON object"):
        verify_and_read(body, _sign(body), SECRET)
