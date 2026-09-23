"""The operator page, Release 1 (DEC-109).

The ledger keeps what the thirty-minute erasure would lose; complaints are
matched to orders; refunds are marks, never money; every change is logged;
alerts are sent once; the payer's details come from the verified webhook.
"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from exam_photo.api.app import _ledger_failed, _ledger_finished, _ledger_started, app
from exam_photo.api.contracts import ApiJobStatus
from exam_photo.api.jobs import JobRegistry
from exam_photo.api.ledger import Ledger, stage_timings
from exam_photo.api.orders import OrderItem, OrderRegistry
from exam_photo.api.protection import UsageRegistry
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore

client = TestClient(app, raise_server_exceptions=False)
OPERATOR = "op-secret"
AUTH = {"X-Operator-Token": OPERATOR}
SECRET = "webhook-secret"
KIT = "kit_release1"


@pytest.fixture
def api(tmp_path):
    from exam_photo.api.app import service

    original = (
        service.settings,
        service.store,
        service.registry,
        service.orders,
        service.usage,
    )
    root = tmp_path / "artifacts"
    service.settings = ApiSettings(
        artifact_root=root,
        operator_token=OPERATOR,
        razorpay_webhook_secret=SECRET,
    )
    service.store = LocalArtifactStore(root)
    service.registry = JobRegistry(root)
    service.orders = OrderRegistry(root)
    service.usage = UsageRegistry(root)
    try:
        yield service
    finally:
        (
            service.settings,
            service.store,
            service.registry,
            service.orders,
            service.usage,
        ) = original


def _paid_order(api, order_id="order_R1", job_ids=("job_a",), email=None):
    api.orders.create(
        order_id,
        KIT,
        list(job_ids),
        300,
        "INR",
        items=[OrderItem(job_id=j, exam_name="CTET September 2026") for j in job_ids],
    )
    api.orders.mark_paid(order_id, f"pay_{order_id}")
    if email:
        api.orders.record_payer(order_id, email, "+919999999999", "upi")


def test_the_ledger_lives_under_the_current_artifact_root(api, tmp_path):
    assert api.ledger.path == tmp_path / "artifacts" / "_ledger" / "ledger.sqlite3"


@pytest.mark.parametrize(
    "path",
    [
        "/v1/operator/overview",
        "/v1/operator/orders",
        "/v1/operator/uploads",
        "/v1/operator/customers",
        "/v1/operator/search?q=ab",
        "/v1/operator/tickets",
        "/v1/operator/activity",
        "/v1/operator/alerts",
        "/v1/operator/export/orders.csv",
    ],
)
def test_release1_routes_refuse_without_the_token(api, path):
    assert client.get(path).status_code == 401


def test_a_preparation_is_timed_and_kept_after_erasure(api):
    from exam_photo.api.app import service

    class Requirement:
        requirement_id = "candidate_photograph"
        requirement_name = "Candidate photograph"
        requirement_type = "photograph"

    _ledger_started("job_t1", KIT, "ctet-september-2026", Requirement(), 12345)
    record = api.registry.create_job("job_t1", 1800)
    record.status = ApiJobStatus.SUCCEEDED
    record.outcome = "ready"
    record.output_width, record.output_height = 413, 531
    api.registry.update_job(record)
    api.store.write_file(
        "job_t1",
        "report.json",
        json.dumps({"stages": [{"stage": "crop", "duration_ms": 12.5}]}).encode(),
    )
    _ledger_finished(record, 0.0)
    api.store.delete_job_directory("job_t1")

    row = service.ledger.upload("job_t1")
    assert row["exam_name"] == "CTET September 2026"
    assert row["status"] == "succeeded"
    assert row["input_bytes"] == 12345
    assert row["output_width"] == 413
    assert row["stage_ms"] == {"crop": 12.5}
    assert row["processing_seconds"] > 0


def test_a_refused_preparation_is_recorded_as_busy(api):
    class Requirement:
        requirement_id = "r"
        requirement_name = "R"
        requirement_type = "photograph"

    _ledger_started("job_busy", KIT, "ctet-september-2026", Requirement(), 1)
    _ledger_failed("job_busy", "busy", 0.0, "all preparation slots busy")
    [row] = client.get("/v1/operator/uploads", headers=AUTH).json()["uploads"]
    assert row["status"] == "busy"
    assert row["live"] is False


def test_stage_timings_are_found_anywhere_in_a_report():
    report = {
        "a": [
            {"stage": "crop", "duration_ms": 2},
            {"x": {"stage": "crop", "duration_ms": 3}},
        ]
    }
    assert stage_timings(report) == {"crop": 5.0}


def _webhook(event, payment):
    body = json.dumps(
        {"event": event, "payload": {"payment": {"entity": payment}}}
    ).encode()
    signature = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    return client.post(
        "/v1/payments/razorpay/webhook",
        content=body,
        headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"},
    )


def test_the_payer_is_kept_from_the_verified_webhook(api):
    api.orders.create("order_W1", KIT, [], 300, "INR")
    response = _webhook(
        "payment.captured",
        {
            "id": "pay_W1",
            "order_id": "order_W1",
            "amount": 300,
            "currency": "INR",
            "email": "Payer@Example.com",
            "contact": "+919812345678",
            "method": "upi",
            "notes": {"kit_id": KIT},
        },
    )
    assert response.status_code == 200
    order = api.orders.get("order_W1")
    assert order.payer_email == "Payer@Example.com"
    assert order.payer_contact == "+919812345678"
    assert order.payment_method == "upi"
    assert api.ledger.contact("payer@example.com")["sources"] == ["payment"]


def test_a_failed_payment_lands_on_the_follow_up_list(api):
    api.orders.create("order_F1", KIT, [], 300, "INR")
    response = _webhook(
        "payment.failed",
        {
            "id": "pay_F1",
            "order_id": "order_F1",
            "email": "tried@example.com",
            "contact": "+919800000000",
            "error_description": "Payment was cancelled",
        },
    )
    assert response.json() == {"status": "recorded"}
    overview = client.get("/v1/operator/overview", headers=AUTH).json()
    [follow] = overview["followups"]
    assert follow["order_id"] == "order_F1"
    assert follow["state"] == "payment-failed"
    assert "tried@example.com" in follow["emails"]


def test_a_complaint_is_matched_to_its_order_by_payment_reference(api):
    _paid_order(api)
    ticket = client.post(
        "/v1/operator/tickets",
        headers=AUTH,
        json={
            "kind": "complaint",
            "email": "someone@example.com",
            "message": "No file",
            "payment_reference": "pay_order_R1",
            "reference": "EUK-C1",
        },
    ).json()
    assert ticket["order_id"] == "order_R1"
    detail = client.get("/v1/operator/orders/order_R1", headers=AUTH).json()
    assert [t["reference"] for t in detail["tickets"]] == ["EUK-C1"]
    assert any("Complaint received" in e["what"] for e in detail["timeline"])


def test_a_complaint_without_reference_is_matched_by_address(api):
    _paid_order(api, email="owner.of.order@example.com")
    ticket = client.post(
        "/v1/operator/tickets",
        headers=AUTH,
        json={
            "kind": "grievance",
            "email": "Owner.Of.Order@example.com",
            "message": "x",
        },
    ).json()
    assert ticket["order_id"] == "order_R1"


def test_the_same_form_reference_is_one_ticket(api):
    body = {
        "kind": "exam",
        "email": "a@example.com",
        "exam": "Bihar Police",
        "reference": "EUK-1",
    }
    first = client.post("/v1/operator/tickets", headers=AUTH, json=body).json()
    second = client.post("/v1/operator/tickets", headers=AUTH, json=body).json()
    assert first["id"] == second["id"]


def test_ticket_changes_are_noted_and_logged(api):
    ticket = client.post(
        "/v1/operator/tickets",
        headers=AUTH,
        json={"kind": "question", "email": "q@example.com", "message": "?"},
    ).json()
    changed = client.post(
        f"/v1/operator/tickets/{ticket['id']}",
        headers=AUTH,
        json={
            "actor": "owner@example.com",
            "status": "resolved",
            "note": "Replied by email",
        },
    ).json()
    assert changed["status"] == "resolved"
    assert changed["acknowledged_at"] and changed["resolved_at"]
    detail = client.get(f"/v1/operator/tickets/{ticket['id']}", headers=AUTH).json()
    assert detail["notes"][0]["text"] == "Replied by email"
    [entry] = client.get("/v1/operator/activity", headers=AUTH).json()["activity"]
    assert entry["actor"] == "owner@example.com"
    assert "resolved" in entry["action"]


def test_a_bad_status_or_unknown_order_is_refused(api):
    ticket = api.ledger.add_ticket(kind="support", email="a@b.co", message="m")
    assert (
        client.post(
            f"/v1/operator/tickets/{ticket['id']}",
            headers=AUTH,
            json={"status": "deleted"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/v1/operator/tickets/{ticket['id']}",
            headers=AUTH,
            json={"order_id": "order_nope"},
        ).status_code
        == 422
    )


def test_an_old_unanswered_complaint_is_overdue(api):
    old = (datetime.now(timezone.utc) - timedelta(hours=49)).isoformat()
    ticket = api.ledger.add_ticket(
        kind="complaint", email="a@b.co", message="m", created_at=old
    )
    assert ticket["ack_overdue"] is True
    exam = api.ledger.add_ticket(
        kind="exam", email="a@b.co", message="", exam="X", created_at=old
    )
    assert exam["ack_overdue"] is False


def test_a_refund_is_a_mark_that_changes_state_and_money(api):
    _paid_order(api)
    assert (
        client.post(
            "/v1/operator/orders/order_R1/refund",
            headers=AUTH,
            json={"actor": "o", "reference": "rfnd_1"},
        ).status_code
        == 200
    )
    [order] = client.get("/v1/operator/orders", headers=AUTH).json()["orders"]
    assert order["state"] == "refunded"
    assert order["refund"]["reference"] == "rfnd_1"
    overview = client.get("/v1/operator/overview", headers=AUTH).json()
    assert overview["money"]["all_time_paise"] == 0
    assert overview["money"]["refunded_paise"] == 300
    client.post(
        "/v1/operator/orders/order_R1/refund", headers=AUTH, json={"undo": True}
    )
    [order] = client.get("/v1/operator/orders", headers=AUTH).json()["orders"]
    assert order["state"] == "refund-due"


def test_customers_see_everything_by_full_address(api):
    _paid_order(api, email="Buyer@Example.com")
    api.orders.mark_delivered("job_a", "email", "b***@example.com", "buyer@example.com")
    api.ledger.contact_seen("buyer@example.com", "delivery")
    [row] = client.get("/v1/operator/customers", headers=AUTH).json()["customers"]
    assert row["email"] == "buyer@example.com"
    assert row["spent_paise"] == 300
    detail = client.get("/v1/operator/customers/buyer@example.com", headers=AUTH).json()
    assert [o["order_id"] for o in detail["orders"]] == ["order_R1"]
    found = client.get("/v1/operator/search?q=buyer@", headers=AUTH).json()
    assert found["orders"][0]["order_id"] == "order_R1"
    assert found["customers"][0]["email"] == "buyer@example.com"


def test_an_undelivered_paid_order_alerts_once(api):
    _paid_order(api)
    record = api.orders.get("order_R1")
    record.paid_at = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
    api.orders._path("order_R1").write_text(record.model_dump_json(), encoding="utf-8")

    keys = [
        a["key"]
        for a in client.get("/v1/operator/alerts", headers=AUTH).json()["alerts"]
    ]
    assert "undelivered:order_R1" in keys
    client.post("/v1/operator/alerts/sent", headers=AUTH, json=keys)
    again = [
        a["key"]
        for a in client.get("/v1/operator/alerts", headers=AUTH).json()["alerts"]
    ]
    assert "undelivered:order_R1" not in again


def test_a_run_of_failures_on_one_exam_alerts(api):
    ledger: Ledger = api.ledger
    for n in range(3):
        ledger.upload_started(f"job_f{n}", exam_name="SSC CGL")
        ledger.upload_finished(
            f"job_f{n}", status="error", processing_seconds=1, error="Boom"
        )
    alerts = client.get("/v1/operator/alerts", headers=AUTH).json()["alerts"]
    assert any(a["key"].startswith("failures:SSC CGL:") for a in alerts)


def test_overview_reports_timing_and_per_exam_numbers(api):
    ledger: Ledger = api.ledger
    for n, seconds in enumerate((8.0, 10.0, 30.0)):
        ledger.upload_started(f"job_o{n}", kit_id=KIT, exam_name="CTET September 2026")
        ledger.upload_finished(
            f"job_o{n}",
            status="succeeded",
            processing_seconds=seconds,
            stage_ms={"crop": 10},
        )
    _paid_order(api)
    data = client.get("/v1/operator/overview", headers=AUTH).json()
    assert data["preparation_seconds"]["median"] == 10.0
    assert data["preparation_seconds"]["stages_median_ms"] == {"crop": 10.0}
    [exam] = data["exams"]
    assert (
        exam["uploads"] == 3 and exam["kits_paid"] == 1 and exam["revenue_paise"] == 300
    )
    assert data["refund_due"][0]["order_id"] == "order_R1"
    assert sum(data["uploads_by_hour_ist"]) == 3


def test_notes_only_attach_to_known_kinds(api):
    assert (
        client.post(
            "/v1/operator/notes/order:order_R1",
            headers=AUTH,
            json={"text": "called them"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/v1/operator/notes/elsewhere:x", headers=AUTH, json={"text": "x"}
        ).status_code
        == 422
    )


def test_exports_are_csv(api):
    _paid_order(api, email="csv@example.com")
    response = client.get("/v1/operator/export/orders.csv", headers=AUTH)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "csv@example.com" in response.text and "order_R1" in response.text
    assert (
        client.get("/v1/operator/export/secrets.csv", headers=AUTH).status_code == 404
    )


def test_health_is_sampled_into_history(api):
    api.sample_health()
    data = client.get("/v1/operator/overview", headers=AUTH).json()
    assert len(data["health"]) == 1
