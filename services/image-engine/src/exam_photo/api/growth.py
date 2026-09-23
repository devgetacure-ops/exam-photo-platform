"""Where candidates come from and where they stop (DEC-110).

Computed from the site's own visit beacon (the ledger's `visits`), joined by
kit to the preparations and orders the engine already records. No third-party
analytics: every figure here comes from this server's own records.
"""

from __future__ import annotations

import json
import statistics
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from exam_photo.api.ledger import normalise_email, parse
from exam_photo.api.operator import IST, order_emails
from exam_photo.api.razorpay_orders import fetch_payments

if TYPE_CHECKING:  # pragma: no cover
    from exam_photo.api.service import ApiProcessingService as ApiService

#: Reconciliation looks back this far, and runs at most this often.
RECONCILE_WINDOW = timedelta(hours=48)
RECONCILE_EVERY = timedelta(minutes=55)
DEVICE_KEYS = ("device", "browser", "connection")


def _row(label: str, name: str, values: Dict[str, int]) -> Dict[str, Any]:
    return {label: name, **values}


def _median(values: List[float]) -> Optional[float]:
    return round(statistics.median(values), 1) if values else None


def _kit_facts(service: "ApiService", since: str) -> Dict[str, Dict[str, Any]]:
    """Per kit: did it upload, prepare, check out, pay, receive, and for how much."""
    facts: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "uploaded": False,
            "prepared": False,
            "failed": 0,
            "checkout": False,
            "paid": False,
            "delivered": False,
            "revenue": 0,
            "paid_at": None,
        }
    )
    for row in service.ledger.uploads(since=since, limit=500000):
        if not row.get("kit_id"):
            continue
        kit = facts[row["kit_id"]]
        kit["uploaded"] = True
        if row["status"] == "succeeded":
            kit["prepared"] = True
        elif row["status"] in ("error", "failed", "busy"):
            kit["failed"] += 1
    refunds = service.ledger.refunds()
    for order in service.orders.recent(500000):
        kit = facts[order.kit_id]
        kit["checkout"] = True
        if order.paid_at and order.order_id not in refunds:
            kit["paid"] = True
            kit["revenue"] += order.amount_paise
            if not kit["paid_at"] or order.paid_at < kit["paid_at"]:
                kit["paid_at"] = order.paid_at
        if order.delivered_at:
            kit["delivered"] = True
    return facts


def _source(visit: Dict[str, Any]) -> str:
    if visit.get("utm_source"):
        return str(visit["utm_source"]).lower()
    host = (visit.get("referrer_host") or "").lower()
    if not host:
        return "direct"
    for name, marker in (
        ("google", "google."),
        ("bing", "bing."),
        ("whatsapp", "whatsapp"),
        ("youtube", "youtube"),
        ("facebook", "facebook"),
        ("instagram", "instagram"),
        ("telegram", "t.me"),
        ("chatgpt", "chatgpt"),
    ):
        if marker in host:
            return name
    return host


def growth(service: "ApiService", days: int = 30) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=days)).isoformat()
    visits = service.ledger.visits(since)
    kits = _kit_facts(service, (now - timedelta(days=days + 30)).isoformat())

    steps = [
        "visited",
        "opened an exam",
        "uploaded",
        "prepared",
        "opened checkout",
        "paid",
        "received",
    ]
    funnel = dict.fromkeys(steps, 0)
    by_source: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"visits": 0, "prepared": 0, "paid": 0, "revenue_paise": 0}
    )
    by_device: Dict[str, Dict[str, Dict[str, int]]] = {
        key: defaultdict(lambda: {"visits": 0, "uploaded": 0, "failed": 0, "paid": 0})
        for key in DEVICE_KEYS
    }
    active_all: List[float] = []
    active_paid: List[float] = []
    to_payment: List[float] = []

    for visit in visits:
        joined = [kits[k] for k in visit["kit_ids"] if k in kits]
        reached = {
            "visited": True,
            "opened an exam": visit["exam_pages"] > 0 or bool(joined),
            "uploaded": any(k["uploaded"] for k in joined),
            "prepared": any(k["prepared"] for k in joined),
            "opened checkout": any(k["checkout"] for k in joined),
            "paid": any(k["paid"] for k in joined),
            "received": any(k["delivered"] for k in joined),
        }
        for step in steps:
            if reached[step]:
                funnel[step] += 1
        source = by_source[_source(visit)]
        source["visits"] += 1
        source["prepared"] += int(reached["prepared"])
        source["paid"] += int(reached["paid"])
        source["revenue_paise"] += sum(k["revenue"] for k in joined)
        for key in DEVICE_KEYS:
            bucket = by_device[key][str(visit.get(key) or "unknown")]
            bucket["visits"] += 1
            bucket["uploaded"] += int(reached["uploaded"])
            bucket["failed"] += sum(k["failed"] for k in joined)
            bucket["paid"] += int(reached["paid"])
        active_all.append(visit["active_seconds"])
        if reached["paid"]:
            active_paid.append(visit["active_seconds"])
            first = parse(visit["first_at"])
            paid_times = [parse(k["paid_at"]) for k in joined if k["paid_at"]]
            paid = min((p for p in paid_times if p), default=None)
            if first and paid and paid >= first:
                to_payment.append((paid - first).total_seconds() / 60)

    sources = sorted(
        ({"source": name, **values} for name, values in by_source.items()),
        key=lambda row: (-row["revenue_paise"], -row["visits"]),
    )
    devices = {
        key: sorted(
            [_row("value", name, values) for name, values in groups.items()],
            key=lambda row: -int(row["visits"]),
        )
        for key, groups in by_device.items()
    }
    landing: Dict[str, int] = defaultdict(int)
    for visit in visits:
        landing[str(visit.get("landing") or "/")] += 1

    return {
        "days": days,
        "visits": len(visits),
        "funnel": [{"step": step, "sessions": funnel[step]} for step in steps],
        "time_on_site_seconds": {
            "median_all": _median(active_all),
            "median_paying": _median(active_paid),
            "median_minutes_to_payment": _median(to_payment),
        },
        "sources": sources[:30],
        "devices": devices,
        "landing_pages": [
            {"path": p, "visits": n}
            for p, n in sorted(
                landing.items(),
                key=lambda item: -item[1],
            )[:20]
        ],
        "empty_searches": service.ledger.empty_searches(since),
        "price_test": price_test_report(service, since),
        "repeat": repeat_customers(service),
    }


def price_test_report(service: "ApiService", since: str) -> Dict[str, Any]:
    """Each arm's quotes that became orders and payments (DEC-110)."""
    arms: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"orders": 0, "paid": 0, "revenue_paise": 0}
    )
    for order in service.orders.recent(500000):
        if order.created_at < since:
            continue
        arm = arms[order.price_variant or "A"]
        arm["orders"] += 1
        if order.paid_at:
            arm["paid"] += 1
            arm["revenue_paise"] += order.amount_paise
    settings = service.settings
    return {
        "running": bool(settings.price_test_ladder and settings.price_test_share > 0),
        "ladder_b": settings.price_test_ladder,
        "share_b_percent": settings.price_test_share,
        "arms": [
            {
                "arm": name,
                **values,
                "pay_rate": round(values["paid"] / values["orders"], 4)
                if values["orders"]
                else None,
            }
            for name, values in sorted(arms.items())
        ],
    }


def repeat_customers(service: "ApiService") -> Dict[str, Any]:
    """Who came back for another examination, and how long after."""
    purchases: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for order in service.orders.recent(500000):
        if not order.paid_at:
            continue
        for email in order_emails(order):
            purchases[email].append(
                {
                    "at": order.paid_at,
                    "exams": {i.exam_name for i in order.items if i.exam_name},
                }
            )
    gaps: List[float] = []
    returning = 0
    second_exam = 0
    for history in purchases.values():
        if len(history) < 2:
            continue
        returning += 1
        history.sort(key=lambda h: h["at"])
        first, second = parse(history[0]["at"]), parse(history[1]["at"])
        if first and second:
            gaps.append((second - first).total_seconds() / 86400)
        if len(set().union(*(h["exams"] for h in history))) > 1:
            second_exam += 1
    return {
        "payers": len(purchases),
        "returning": returning,
        "for_another_exam": second_exam,
        "median_days_to_return": _median(gaps),
    }


def calendar(service: "ApiService") -> List[Dict[str, Any]]:
    """Every examination, its closing date if the owner set one, and demand."""
    deadlines = service.ledger.deadlines()
    since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    uploads: Dict[str, int] = defaultdict(int)
    for row in service.ledger.uploads(since=since, limit=500000):
        if row.get("exam_id"):
            uploads[row["exam_id"]] += 1
    revenue: Dict[str, int] = defaultdict(int)
    customers: Dict[str, set[str]] = defaultdict(set)
    for order in service.orders.recent(500000):
        if not order.paid_at:
            continue
        exam_ids = {item.exam_id for item in order.items if item.exam_id}
        for exam_id in exam_ids:
            if order.created_at >= since:
                revenue[exam_id] += order.amount_paise // len(exam_ids)
            customers[exam_id].update(order_emails(order))
    today = datetime.now(IST).date()
    rows = []
    for entry in service.catalogue.listed():
        deadline = deadlines.get(entry.exam_id)
        closes = date.fromisoformat(deadline["closes_on"]) if deadline else None
        rows.append(
            {
                "exam_id": entry.exam_id,
                "exam_name": entry.rule.exam.exam_name,
                "closes_on": deadline["closes_on"] if deadline else None,
                "days_left": (closes - today).days if closes else None,
                "note": deadline["note"] if deadline else None,
                "auto_remind": bool(deadline and deadline["auto_remind"]),
                "uploads_30d": uploads.get(entry.exam_id, 0),
                "revenue_30d_paise": revenue.get(entry.exam_id, 0),
                "past_customers": len(customers.get(entry.exam_id, set())),
            }
        )

    def order_key(row: Dict[str, Any]) -> tuple[bool, int, int]:
        left = row["days_left"]
        return (
            left is None or left < 0,
            left if left is not None else 0,
            -row["uploads_30d"],
        )

    rows.sort(key=order_key)
    return rows


def exam_customers(service: "ApiService", exam_id: str) -> List[str]:
    """Everyone who paid for an examination, for a reminder."""
    found: List[str] = []
    for order in service.orders.recent(500000):
        if order.paid_at and any(item.exam_id == exam_id for item in order.items):
            found += order_emails(order)
    return list(dict.fromkeys(found))


def reconcile(service: "ApiService", force: bool = False) -> Dict[str, Any]:
    """Compare Razorpay's captured payments with the orders we released (DEC-110).

    Catches the failure the webhook cannot report about itself: money taken
    and no file released, because the webhook never arrived. Cached for an
    hour in the ledger, so a page view does not call Razorpay.
    """
    ledger = service.ledger
    now = datetime.now(timezone.utc)
    last = parse(ledger.get_value("reconcile:at"))
    cached = ledger.get_value("reconcile:result")
    if not force and last and now - last < RECONCILE_EVERY and cached:
        result: Dict[str, Any] = json.loads(cached)
        return result
    settings = service.settings
    if (
        not (settings.razorpay_key_id and settings.razorpay_key_secret)
        or settings.payment_simulator_enabled
    ):
        return {"checked_at": None, "status": "not_configured", "problems": []}
    until = int(time.time())
    try:
        payments = fetch_payments(
            settings.razorpay_key_id,
            settings.razorpay_key_secret,
            until - int(RECONCILE_WINDOW.total_seconds()),
            until,
        )
    except Exception as err:  # noqa: BLE001
        return {
            "checked_at": now.isoformat(),
            "status": "failed",
            "error": str(err)[:200],
            "problems": [],
        }
    problems = []
    captured = 0
    for payment in payments:
        if payment.get("status") != "captured":
            continue
        captured += 1
        order_id = str(payment.get("order_id") or "")
        order = service.orders.get(order_id) if order_id else None
        if order is None:
            problems.append(
                {
                    "kind": "unknown_order",
                    "payment_id": payment.get("id"),
                    "order_id": order_id or None,
                    "amount_paise": payment.get("amount"),
                    "email": normalise_email(payment.get("email")),
                }
            )
        elif not order.paid_at:
            problems.append(
                {
                    "kind": "not_released",
                    "payment_id": payment.get("id"),
                    "order_id": order_id,
                    "amount_paise": payment.get("amount"),
                    "email": normalise_email(payment.get("email")),
                }
            )
    result = {
        "checked_at": now.isoformat(),
        "status": "ok",
        "captured": captured,
        "problems": problems,
    }
    ledger.set_value("reconcile:at", now.isoformat())
    ledger.set_value("reconcile:result", json.dumps(result))
    return result
