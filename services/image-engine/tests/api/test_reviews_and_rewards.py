"""Reviews on the downloads screen and the free-files reward (DEC-112).

A review needs the paying browser's kit and a paid order; the owner approves
before anything is public; while the offer runs, a review earns one unique,
single-use code that makes a kit free, once per person, never for a free
order; a free kit is settled without Razorpay and its code cannot be used
twice.
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from exam_photo.api.app import app
from exam_photo.api.contracts import ApiJobStatus, JobEntitlement
from exam_photo.api.jobs import JobRegistry
from exam_photo.api.ledger import Ledger
from exam_photo.api.orders import OrderItem, OrderRegistry
from exam_photo.api.protection import UsageRegistry
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore

client = TestClient(app, raise_server_exceptions=False)
OPERATOR = "op-secret"
AUTH = {"X-Operator-Token": OPERATOR}
KIT = "kit_reviewer"
OTHER_KIT = "kit_next_exam"
EXAM = "ctet-september-2026"


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
    service.settings = ApiSettings(artifact_root=root, operator_token=OPERATOR)
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


def _paid(api, order_id="order_P1", kit=KIT, email="c@example.com", amount=300):
    api.orders.create(
        order_id,
        kit,
        [],
        amount,
        "INR",
        items=[OrderItem(job_id="job_x", exam_name="CTET")],
    )
    api.orders.mark_paid(order_id, f"pay_{order_id}")
    api.orders.record_payer(order_id, email, None, "upi")


def _prepared(api, job_id, kit=OTHER_KIT):
    record = api.registry.create_job(job_id, 1800)
    record.status = ApiJobStatus.SUCCEEDED
    record.kit_id = kit
    record.exam_id = EXAM
    record.requirement_type = "photograph"
    record.output_filename = f"{job_id}.jpg"
    api.store.write_file(job_id, f"{job_id}.jpg", b"\xff\xd8x")
    api.registry.update_job(record)


def _review(order_id="order_P1", kit=KIT, rating=5, **extra):
    return client.post(
        f"/v1/kits/{kit}/review",
        json={"order_id": order_id, "rating": rating, "tags": ["Fast"], **extra},
    )


def test_only_the_paying_kit_can_review_a_paid_order(api):
    _paid(api)
    api.orders.create("order_UNPAID", KIT, [], 300, "INR")
    assert _review(kit="kit_stranger").status_code == 404
    assert _review(order_id="order_UNPAID").status_code == 404
    assert (
        client.post(
            f"/v1/kits/{KIT}/review", json={"order_id": "order_P1", "rating": 9}
        ).status_code
        == 422
    )
    assert _review().status_code == 200


def test_no_reward_while_the_offer_is_off(api):
    _paid(api)
    assert _review().json()["reward_code"] is None
    assert client.get("/v1/offers").json() == {"review_reward": False}


def test_a_review_earns_one_unique_single_use_code_per_person(api):
    client.post("/v1/operator/offers/review_reward", headers=AUTH, json={"on": True})
    _paid(api, "order_P1", email="same@example.com")
    _paid(api, "order_P2", kit="kit_two", email="Same@Example.com")
    _paid(api, "order_P3", kit="kit_three", email="other@example.com")

    first = _review().json()["reward_code"]
    assert first and first.startswith("THANKS-")
    assert _review().json()["reward_code"] == first  # editing does not mint another
    assert _review("order_P2", "kit_two").json()["reward_code"] is None  # same person
    third = _review("order_P3", "kit_three").json()["reward_code"]
    assert third and third != first
    state = client.get(f"/v1/kits/{KIT}/review?order_id=order_P1").json()
    assert state["reward_code"] == first and state["offer"] is True


def test_a_free_order_never_earns_another(api):
    client.post("/v1/operator/offers/review_reward", headers=AUTH, json={"on": True})
    _paid(api, "order_free_a", amount=0)
    assert _review("order_free_a").json()["reward_code"] is None


def test_the_code_makes_the_next_kit_free_once(api):
    client.post("/v1/operator/offers/review_reward", headers=AUTH, json={"on": True})
    _paid(api)
    code = _review().json()["reward_code"]
    _prepared(api, "job_n1")

    quote = client.get(f"/v1/kits/{OTHER_KIT}/quote?coupon={code}").json()
    assert quote["amount_paise"] == 0 and quote["free_with_coupon"] is True
    assert client.post(f"/v1/kits/{OTHER_KIT}/order?coupon={code}").status_code == 409

    claimed = client.post(f"/v1/kits/{OTHER_KIT}/claim-free?coupon={code}")
    assert claimed.status_code == 200
    assert api.registry.get_job("job_n1").entitlement == JobEntitlement.RELEASED
    order = api.orders.get(claimed.json()["order_id"])
    assert order.amount_paise == 0 and order.payment_reference == f"coupon:{code}"

    _prepared(api, "job_n2", kit="kit_again")
    assert (
        client.get(f"/v1/kits/kit_again/quote?coupon={code}").json()["coupon_status"]
        == "invalid"
    )
    assert (
        client.post(f"/v1/kits/kit_again/claim-free?coupon={code}").status_code == 409
    )


def test_claiming_is_atomic(api):
    api.ledger.save_coupon("ONCEONLY", "free", 100, max_uses=1)
    assert api.ledger.claim_coupon("ONCEONLY") is True
    assert api.ledger.claim_coupon("ONCEONLY") is False


def test_a_partial_discount_cannot_be_claimed_free(api):
    api.ledger.save_coupon("TENOFF", "percent", 10)
    _prepared(api, "job_p1")
    assert (
        client.post(f"/v1/kits/{OTHER_KIT}/claim-free?coupon=TENOFF").status_code == 409
    )


def test_the_owner_can_create_a_free_code(api):
    response = client.post(
        "/v1/operator/coupons",
        headers=AUTH,
        json={"code": "friend", "kind": "free", "value": 0, "max_uses": 1},
    )
    assert response.status_code == 200
    assert api.ledger.coupon("FRIEND")["kind"] == "free"


def test_reviews_wait_for_approval_and_can_be_rejected(api):
    _paid(api)
    _review(rating=2, comment="Portal refused", may_publish=True)
    listed = client.get("/v1/operator/reviews?status=pending", headers=AUTH).json()
    assert listed["reviews"][0]["rating"] == 2
    assert (
        client.get("/v1/operator/overview", headers=AUTH).json()["low_reviews"][0][
            "order_id"
        ]
        == "order_P1"
    )
    client.post(
        "/v1/operator/reviews/order_P1/status",
        headers=AUTH,
        json={"status": "rejected"},
    )
    assert client.get("/v1/testimonials").json()["testimonials"] == []
    assert (
        client.post(
            "/v1/operator/reviews/order_P1/status",
            headers=AUTH,
            json={"status": "shown"},
        ).status_code
        == 422
    )


def test_editing_a_review_sends_it_back_for_approval(api):
    _paid(api)
    _review(may_publish=True)
    client.post(
        "/v1/operator/reviews/order_P1/status",
        headers=AUTH,
        json={"status": "approved"},
    )
    _review(comment="changed my mind", may_publish=True)
    assert api.ledger.review("order_P1")["status"] == "pending"


def test_a_ledger_from_before_reviews_is_upgraded_in_place(tmp_path):
    path = tmp_path / "_ledger"
    path.mkdir()
    db = sqlite3.connect(path / "ledger.sqlite3")
    db.executescript(
        "CREATE TABLE feedback (order_id TEXT PRIMARY KEY, at TEXT NOT NULL, worked INTEGER NOT NULL,"
        " comment TEXT, may_publish INTEGER NOT NULL DEFAULT 0, published INTEGER NOT NULL DEFAULT 0);"
        "INSERT INTO feedback VALUES ('order_OLD', '2026-09-20', 1, 'fine', 1, 1);"
        "CREATE TABLE coupons (code TEXT PRIMARY KEY, kind TEXT NOT NULL, value INTEGER NOT NULL,"
        " partner TEXT, active INTEGER NOT NULL DEFAULT 1, max_uses INTEGER, uses INTEGER NOT NULL DEFAULT 0,"
        " expires_on TEXT, created_at TEXT NOT NULL);"
    )
    db.commit()
    db.close()
    ledger = Ledger(tmp_path)
    assert ledger.review("order_OLD")["status"] == "approved"
    ledger.save_coupon("X1", "free", 100)
    assert ledger.coupon("X1")["source"] == "manual"
