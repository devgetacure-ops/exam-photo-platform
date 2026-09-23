"""Releases 2 and 3 of the back office (DEC-110, DEC-111).

Visits and the funnel, price tests, coupons, reconciliation with Razorpay,
the deadline calendar, campaigns with a working unsubscribe, and the
"did it work?" feedback. Nothing here reaches the network.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from exam_photo.api import growth, marketing
from exam_photo.api.app import app
from exam_photo.api.contracts import ApiJobStatus
from exam_photo.api.delivery import Delivery, build_message, compose
from exam_photo.api.jobs import JobRegistry
from exam_photo.api.orders import OrderItem, OrderRegistry
from exam_photo.api.pricing import Discount, parse_ladder, price_variant
from exam_photo.api.protection import UsageRegistry
from exam_photo.api.razorpay_orders import CreatedOrder
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore

client = TestClient(app, raise_server_exceptions=False)
OPERATOR = "op-secret"
AUTH = {"X-Operator-Token": OPERATOR}
KIT = "kit_growth"
EXAM = "ctet-september-2026"


class FakeSender:
    def __init__(self):
        self.sent = []

    def send(self, to_address, subject, body, attachments, html=None, headers=None):
        self.sent.append(
            {
                "to": to_address,
                "subject": subject,
                "body": body,
                "html": html,
                "headers": headers or {},
            }
        )


class Gateway:
    def __init__(self):
        self.amounts = []

    def create_order(self, amount_paise, currency, notes, receipt):
        self.amounts.append(amount_paise)
        return CreatedOrder(
            order_id=f"order_G{len(self.amounts)}",
            amount_paise=amount_paise,
            currency=currency,
            key_id="k",
        )


@pytest.fixture
def api(tmp_path):
    from exam_photo.api.app import service

    original = (
        service.settings,
        service.store,
        service.registry,
        service.orders,
        service.usage,
        service._email_sender,
        service._order_gateway,
    )
    root = tmp_path / "artifacts"
    service.settings = ApiSettings(
        artifact_root=root,
        operator_token=OPERATOR,
        site_url="https://examuploadkit.com",
    )
    service.store = LocalArtifactStore(root)
    service.registry = JobRegistry(root)
    service.orders = OrderRegistry(root)
    service.usage = UsageRegistry(root)
    service.email_sender = FakeSender()
    service.order_gateway = Gateway()
    try:
        yield service
    finally:
        (
            service.settings,
            service.store,
            service.registry,
            service.orders,
            service.usage,
            service._email_sender,
            service._order_gateway,
        ) = original


def _prepared(api, job_id, kit=KIT, kind="photograph"):
    record = api.registry.create_job(job_id, 1800)
    record.status = ApiJobStatus.SUCCEEDED
    record.kit_id = kit
    record.exam_id = EXAM
    record.requirement_type = kind
    record.output_filename = f"{job_id}.jpg"
    api.store.write_file(job_id, f"{job_id}.jpg", b"\xff\xd8x")
    api.registry.update_job(record)
    return record


def _paid(api, order_id, email, exam_id=EXAM, kit=KIT, amount=300):
    api.orders.create(
        order_id,
        kit,
        [],
        amount,
        "INR",
        items=[
            OrderItem(job_id="job_x", exam_id=exam_id, exam_name="CTET September 2026")
        ],
    )
    api.orders.mark_paid(order_id, f"pay_{order_id}")
    api.orders.record_payer(order_id, email, None, "upi")
    api.ledger.contact_seen(email, "payment")


# --- Release 2 ----------------------------------------------------------------


def test_the_beacon_builds_visits_and_ignores_bad_sessions(api):
    body = {
        "events": [
            {
                "session_id": "sess_abcdefgh",
                "type": "view",
                "path": "/exam/ctet",
                "referrer_host": "www.google.com",
                "device": "mobile",
                "browser": "chrome",
                "connection": "4g",
            },
            {
                "session_id": "sess_abcdefgh",
                "type": "ping",
                "seconds": 45,
                "kit_id": KIT,
            },
            {"session_id": "bad", "type": "view", "path": "/"},
            {
                "session_id": "sess_abcdefgh",
                "type": "search_empty",
                "query": "Bihar Police",
            },
            {"session_id": "sess_abcdefgh", "type": "delete_everything"},
        ]
    }
    assert client.post("/v1/operator/events", headers=AUTH, json=body).json() == {
        "accepted": 3
    }
    [visit] = api.ledger.visits("2000")
    assert (
        visit["active_seconds"] == 45
        and visit["exam_pages"] == 1
        and visit["kit_ids"] == [KIT]
    )
    assert api.ledger.empty_searches("2000")[0]["query"] == "bihar police"


def test_a_heartbeat_cannot_claim_hours(api):
    api.ledger.record_visit_event(
        {"session_id": "sess_x", "type": "ping", "seconds": 99999}
    )
    assert api.ledger.visits("2000")[0]["active_seconds"] == 120


def test_the_funnel_joins_visits_to_uploads_and_payments(api):
    api.ledger.record_visit_event(
        {
            "session_id": "s_paying1",
            "type": "view",
            "path": "/exam/ctet",
            "referrer_host": "l.wa.me.whatsapp.com",
            "device": "mobile",
        }
    )
    api.ledger.record_visit_event(
        {"session_id": "s_paying1", "type": "ping", "seconds": 60, "kit_id": KIT}
    )
    api.ledger.record_visit_event(
        {"session_id": "s_browser", "type": "view", "path": "/", "device": "desktop"}
    )
    api.ledger.upload_started("job_f1", kit_id=KIT, exam_name="CTET")
    api.ledger.upload_finished("job_f1", status="succeeded", processing_seconds=9)
    _paid(api, "order_F1", "p@example.com")
    data = client.get("/v1/operator/growth", headers=AUTH).json()
    funnel = {row["step"]: row["sessions"] for row in data["funnel"]}
    assert funnel["visited"] == 2 and funnel["prepared"] == 1 and funnel["paid"] == 1
    whatsapp = next(row for row in data["sources"] if row["source"] == "whatsapp")
    assert whatsapp["paid"] == 1 and whatsapp["revenue_paise"] == 300
    assert data["time_on_site_seconds"]["median_paying"] == 60


def test_price_test_is_off_by_default_and_stable_when_on(api):
    assert (
        parse_ladder("") is None
        and parse_ladder("50") is None
        and parse_ladder("400,700") == [400, 700]
    )
    assert price_variant("kit_a", 0) == "A"
    assert price_variant("kit_a", 100) == "B"
    assert price_variant("kit_zz", 50) == price_variant("kit_zz", 50)


def test_the_b_arm_pays_its_own_ladder_on_quote_and_order(api):
    api.settings = api.settings.model_copy(
        update={"price_test_ladder": "400,700", "price_test_share": 100}
    )
    _prepared(api, "job_p1")
    quote = client.get(f"/v1/kits/{KIT}/quote").json()
    assert quote["amount_paise"] == 400 and quote["price_variant"] == "B"
    assert client.post(f"/v1/kits/{KIT}/order").status_code == 200
    assert api.order_gateway.amounts == [400]
    assert api.orders.get("order_G1").price_variant == "B"


def test_reconciliation_finds_money_taken_and_nothing_released(api, monkeypatch):
    api.settings = api.settings.model_copy(
        update={"razorpay_key_id": "rzp_live_x", "razorpay_key_secret": "s"}
    )
    api.orders.create("order_R1", KIT, [], 300, "INR")
    _paid(api, "order_R2", "ok@example.com")
    monkeypatch.setattr(
        growth,
        "fetch_payments",
        lambda *a, **k: [
            {
                "id": "pay_1",
                "order_id": "order_R1",
                "status": "captured",
                "amount": 300,
                "email": "x@example.com",
            },
            {
                "id": "pay_2",
                "order_id": "order_R2",
                "status": "captured",
                "amount": 300,
            },
            {
                "id": "pay_3",
                "order_id": "order_ELSEWHERE",
                "status": "captured",
                "amount": 500,
            },
            {"id": "pay_4", "order_id": "order_R1", "status": "failed", "amount": 300},
        ],
    )
    result = client.get("/v1/operator/reconcile?force=true", headers=AUTH).json()
    kinds = {p["payment_id"]: p["kind"] for p in result["problems"]}
    assert kinds == {"pay_1": "not_released", "pay_3": "unknown_order"}
    keys = [
        a["key"]
        for a in client.get("/v1/operator/alerts", headers=AUTH).json()["alerts"]
    ]
    assert "reconcile:pay_1" in keys and "reconcile:pay_3" in keys


def test_reconciliation_is_cached_between_runs(api, monkeypatch):
    api.settings = api.settings.model_copy(
        update={"razorpay_key_id": "rzp_live_x", "razorpay_key_secret": "s"}
    )
    calls = []
    monkeypatch.setattr(growth, "fetch_payments", lambda *a, **k: calls.append(1) or [])
    growth.reconcile(api)
    growth.reconcile(api)
    assert len(calls) == 1


def test_deadlines_are_validated_and_listed(api):
    assert (
        client.post(
            "/v1/operator/deadlines/not-an-exam",
            headers=AUTH,
            json={"closes_on": "2026-10-01"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/v1/operator/deadlines/{EXAM}", headers=AUTH, json={"closes_on": "1 Oct"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/v1/operator/deadlines/{EXAM}",
            headers=AUTH,
            json={"closes_on": "2099-10-01", "auto_remind": True},
        ).status_code
        == 200
    )
    rows = client.get("/v1/operator/calendar", headers=AUTH).json()["exams"]
    assert rows[0]["exam_id"] == EXAM and rows[0]["auto_remind"] is True


# --- Release 3 ----------------------------------------------------------------


def test_coupons_discount_on_the_server_and_never_below_a_rupee(api):
    assert Discount("X", "percent", 50).off(300) == 150
    assert Discount("X", "percent", 99).off(1000) == 900  # capped at 90
    assert Discount("X", "flat", 1000).off(300) == 200  # leaves one rupee
    client.post(
        "/v1/operator/coupons",
        headers=AUTH,
        json={
            "code": "coach10",
            "kind": "percent",
            "value": 10,
            "partner": "Coaching A",
            "max_uses": 1,
        },
    )
    _prepared(api, "job_c1")
    quote = client.get(f"/v1/kits/{KIT}/quote?coupon=COACH10").json()
    assert quote["amount_paise"] == 270 and quote["coupon_status"] == "applied"
    assert (
        client.get(f"/v1/kits/{KIT}/quote?coupon=NOPE").json()["coupon_status"]
        == "invalid"
    )
    client.post(f"/v1/kits/{KIT}/order?coupon=coach10")
    order = api.orders.get("order_G1")
    assert (
        order.coupon_code == "COACH10"
        and order.discount_paise == 30
        and order.amount_paise == 270
    )


def test_a_coupon_is_counted_once_paid_and_then_runs_out(api):
    from exam_photo.api.payments import ReleaseInstruction

    api.ledger.save_coupon("ONCE", "flat", 100, max_uses=1)
    api.orders.create(
        "order_C1", KIT, [], 200, "INR", coupon_code="ONCE", discount_paise=100
    )
    instruction = ReleaseInstruction(
        event="order.paid",
        payment_id="pay_c",
        order_id="order_C1",
        amount=200,
        currency="INR",
        kit_ids=[KIT],
    )
    api.apply_release_instruction(instruction)
    api.apply_release_instruction(instruction)  # Razorpay retries
    assert api.ledger.coupon("ONCE")["uses"] == 1
    _prepared(api, "job_c2")
    assert (
        client.get(f"/v1/kits/{KIT}/quote?coupon=ONCE").json()["coupon_status"]
        == "invalid"
    )


@pytest.mark.parametrize(
    "bad",
    [
        {"code": "x", "kind": "percent", "value": 10},
        {"code": "OK", "kind": "percent", "value": 95},
        {"code": "OK", "kind": "flat", "value": 5},
        {"code": "OK", "kind": "free", "value": 10},
    ],
)
def test_bad_coupons_are_refused(api, bad):
    assert (
        client.post("/v1/operator/coupons", headers=AUTH, json=bad).status_code == 422
    )


def test_segments_leave_out_everyone_who_unsubscribed(api):
    _paid(api, "order_S1", "paid@example.com")
    api.ledger.contact_seen("lead@example.com", "form:exam")
    api.ledger.contact_seen("gone@example.com", "delivery")
    api.ledger.suppress("gone@example.com", "test")
    assert marketing.recipients(api, "paid") == ["paid@example.com"]
    assert marketing.recipients(api, "never_paid") == ["lead@example.com"]
    assert set(marketing.recipients(api, "all")) == {
        "paid@example.com",
        "lead@example.com",
    }
    assert marketing.recipients(api, "paid_exam", EXAM) == ["paid@example.com"]


def test_a_campaign_sends_with_a_working_one_click_unsubscribe(api):
    _paid(api, "order_M1", "reader@example.com")
    campaign = marketing.start_campaign(
        api, "owner", "paid", "", "News", "Hello there.", runner=lambda work: work()
    )
    sent = api.email_sender.sent[0]
    assert sent["to"] == "reader@example.com"
    assert sent["headers"]["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    link = sent["headers"]["List-Unsubscribe"].strip("<>")
    assert link in sent["body"] and "Unsubscribe" in sent["html"]
    assert api.ledger.campaign(campaign["id"])["sent"] == 1

    path = link.replace("https://examuploadkit.com", "")
    assert client.post(path).status_code == 200
    assert "reader@example.com" in api.ledger.suppressed()
    assert marketing.recipients(api, "paid") == []


def test_a_forged_unsubscribe_link_does_nothing(api):
    api.ledger.contact_seen("keep@example.com", "payment")
    assert (
        client.get("/v1/unsubscribe?e=keep@example.com&t=deadbeef").status_code == 400
    )
    assert api.ledger.suppressed() == set()


def test_campaign_and_unsubscribe_headers_reach_the_wire():
    message = build_message(
        from_address="f@e.com",
        from_name="E",
        reply_to="",
        to_address="t@e.com",
        subject="s",
        body="b",
        attachments=[],
        headers={"List-Unsubscribe": "<https://x>"},
    )
    assert message["List-Unsubscribe"] == "<https://x>"


def test_exam_added_emails_everyone_who_asked_and_closes_their_requests(api):
    for who in ("a", "b"):
        api.ledger.add_ticket(
            kind="exam", email=f"{who}@example.com", message="", exam="Bihar Police"
        )
    template = client.get(
        "/v1/operator/exam-requests/template?exam=Bihar Police", headers=AUTH
    ).json()
    marketing._in_thread, original = (lambda work: work()), marketing._in_thread
    try:
        response = client.post(
            "/v1/operator/exam-requests/notify",
            headers=AUTH,
            json={"segment": "asked_exam", "target": "bihar police", **template},
        )
    finally:
        marketing._in_thread = original
    assert response.status_code == 200
    assert {s["to"] for s in api.email_sender.sent} == {
        "a@example.com",
        "b@example.com",
    }
    assert all(
        t["added_at"] and t["status"] == "resolved"
        for t in api.ledger.tickets(kinds=["exam"])
    )


def test_deadline_reminders_go_once_three_days_before(api, monkeypatch):
    _paid(api, "order_D1", "past@example.com")
    closes = (
        (datetime.now(timezone.utc) + timedelta(days=3))
        .astimezone(marketing.IST)
        .date()
        .isoformat()
    )
    api.ledger.set_deadline(EXAM, closes, "", True, "owner")
    monkeypatch.setattr(marketing, "_in_thread", lambda work: work())
    at_ten = datetime.now(marketing.IST).replace(hour=10)
    assert len(marketing.run_automations(api, at_ten)) == 1
    assert marketing.run_automations(api, at_ten) == []
    assert api.email_sender.sent[0]["to"] == "past@example.com"


def test_feedback_is_signed_per_order_and_published_only_with_permission(api):
    _paid(api, "order_FB", "f@example.com")
    urls = marketing.feedback_urls(api, "order_FB")
    token = urls["yes"].split("t=")[1].split("&")[0]
    assert (
        client.post(
            "/v1/feedback",
            json={"order_id": "order_FB", "token": "forged", "worked": True},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/v1/feedback",
            json={
                "order_id": "order_FB",
                "token": token,
                "worked": True,
                "comment": "Accepted first time",
                "may_publish": False,
            },
        ).status_code
        == 200
    )
    client.post(
        "/v1/operator/feedback/order_FB/publish", headers=AUTH, json={"published": True}
    )
    assert client.get("/v1/testimonials").json()["testimonials"] == []
    client.post(
        "/v1/feedback",
        json={
            "order_id": "order_FB",
            "token": token,
            "worked": True,
            "may_publish": True,
        },
    )
    client.post(
        "/v1/operator/feedback/order_FB/publish", headers=AUTH, json={"published": True}
    )
    [shown] = client.get("/v1/testimonials").json()["testimonials"]
    assert shown["comment"] == "Accepted first time" and "f@example.com" not in str(
        shown
    )


def test_the_delivery_email_asks_whether_it_worked():
    email = compose(
        Delivery(
            exam_names=["CTET"],
            files=[],
            feedback_yes_url="https://x/yes",
            feedback_no_url="https://x/no",
        )
    )
    assert "https://x/yes" in email.text and "https://x/no" in email.html


@pytest.mark.parametrize(
    "path",
    [
        "/v1/operator/growth",
        "/v1/operator/calendar",
        "/v1/operator/reconcile",
        "/v1/operator/coupons",
        "/v1/operator/campaigns",
        "/v1/operator/feedback",
    ],
)
def test_release23_routes_refuse_without_the_token(api, path):
    assert client.get(path).status_code == 401


def test_a_campaign_will_not_start_without_email(api):
    from exam_photo.api.delivery import UnconfiguredEmailSender

    _paid(api, "order_NE", "n@example.com")
    api.email_sender = UnconfiguredEmailSender()
    with pytest.raises(ValueError, match="not configured"):
        marketing.start_campaign(api, "o", "paid", "", "s", "b", runner=lambda w: w())
    assert api.ledger.campaigns() == []
