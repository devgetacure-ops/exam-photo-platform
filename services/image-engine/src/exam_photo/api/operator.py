"""What the operator page shows, computed from the records (DEC-108, DEC-109).

Pure reading and arithmetic over the order files, the ledger and the live job
manifests. The routes in `app.py` are thin: they check the operator token and
call these. Nothing here writes except `match_ticket_order` through the
ledger, and `pending_alerts` only reads what was already sent.
"""

from __future__ import annotations

import csv
import io
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from exam_photo.api.ledger import normalise_email, parse
from exam_photo.api.orders import OrderRecord

if TYPE_CHECKING:  # pragma: no cover
    from exam_photo.api.service import ApiProcessingService as ApiService

IST = timezone(timedelta(hours=5, minutes=30))
#: A paid order with nothing delivered after this long is worth an email.
UNDELIVERED_ALERT_AFTER = timedelta(minutes=15)
#: This many failed preparations for one examination in an hour is a rule or
#: engine problem, not bad luck.
FAILURE_RUN = 3
DIGEST_HOUR_IST = 8


def _ist_day(stamp: Optional[str]) -> Optional[str]:
    moment = parse(stamp)
    return moment.astimezone(IST).date().isoformat() if moment else None


def _percentile(values: List[float], fraction: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    index = min(int(len(ordered) * fraction), len(ordered) - 1)
    return round(ordered[index], 2)


def order_emails(order: OrderRecord) -> List[str]:
    """Every address this order is known by: the payer's and each delivery's."""
    found = [normalise_email(order.payer_email)]
    found += [normalise_email(d.address) for d in order.deliveries]
    for attempt in order.failed_payments:
        found.append(normalise_email(attempt.get("email")))
    return [email for email in dict.fromkeys(found) if email]


def order_view(
    order: OrderRecord, refunds: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    view = order.model_dump(mode="json")
    refund = refunds.get(order.order_id)
    view["refund"] = refund
    view["emails"] = order_emails(order)
    view["exam_names"] = list(
        dict.fromkeys(item.exam_name for item in order.items if item.exam_name)
    )
    if refund:
        view["state"] = "refunded"
    elif order.paid_at and not order.delivered_at:
        view["state"] = "refund-due"
    elif order.delivered_at:
        view["state"] = "delivered"
    elif order.paid_at:
        view["state"] = "paid"
    elif order.failed_payments:
        view["state"] = "payment-failed"
    else:
        view["state"] = "unpaid"
    return view


def orders(
    service: "ApiService", query: str = "", limit: int = 2000
) -> List[Dict[str, Any]]:
    refunds = service.ledger.refunds()
    needle = query.strip().lower()
    views = []
    for order in service.orders.recent(limit):
        view = order_view(order, refunds)
        if needle:
            haystack = " ".join(
                [
                    order.order_id,
                    order.kit_id,
                    order.payment_reference or "",
                    order.payer_contact or "",
                    " ".join(view["emails"]),
                    " ".join(view["exam_names"]),
                    " ".join(order.job_ids),
                ]
            ).lower()
            if needle not in haystack:
                continue
        views.append(view)
    return views


def match_ticket_order(
    service: "ApiService", email: Optional[str], payment_reference: Optional[str]
) -> Optional[str]:
    """The order a complaint is about: by reference first, then by address."""
    reference = (payment_reference or "").strip().lower()
    address = normalise_email(email)
    candidates = service.orders.recent(5000)
    if reference:
        for order in candidates:
            if reference in (
                order.order_id.lower(),
                (order.payment_reference or "").lower(),
            ):
                return order.order_id
    if address:
        paid = [o for o in candidates if o.paid_at and address in order_emails(o)]
        if paid:
            return paid[0].order_id
    return None


def order_detail(service: "ApiService", order_id: str) -> Optional[Dict[str, Any]]:
    order = service.orders.get(order_id)
    if order is None:
        return None
    ledger = service.ledger
    view = order_view(order, ledger.refunds())
    uploads = {row["job_id"]: row for row in ledger.uploads(kit_ids=[order.kit_id])}
    view["uploads"] = []
    for job_id in order.job_ids:
        live = service.registry.get_job(job_id)
        row = dict(uploads.get(job_id) or {"job_id": job_id})
        row["live"] = bool(live and not live.is_expired())
        view["uploads"].append(row)
    view["kit_uploads"] = list(uploads.values())
    tickets = ledger.tickets(order_id=order_id)
    known = {t["id"] for t in tickets}
    for email in view["emails"]:
        tickets += [t for t in ledger.tickets(email=email) if t["id"] not in known]
    view["tickets"] = tickets
    view["notes"] = ledger.notes(f"order:{order_id}")
    view["timeline"] = _timeline(order, view["kit_uploads"], tickets, view["refund"])
    return view


def _timeline(
    order: OrderRecord,
    uploads: List[Dict[str, Any]],
    tickets: List[Dict[str, Any]],
    refund: Optional[Dict[str, Any]],
) -> List[Dict[str, str]]:
    events: List[Dict[str, str]] = []
    for row in uploads:
        what = row.get("requirement_name") or row.get("job_id")
        events.append({"at": row["started_at"], "what": f"Uploaded {what}"})
        if row.get("finished_at"):
            took = row.get("processing_seconds")
            events.append(
                {
                    "at": row["finished_at"],
                    "what": f"Prepared {what}: {row.get('outcome') or row.get('status')}"
                    + (f" in {took:.1f} s" if isinstance(took, (int, float)) else ""),
                }
            )
    events.append({"at": order.created_at, "what": "Checkout opened (order created)"})
    for attempt in order.failed_payments:
        events.append(
            {
                "at": attempt.get("at") or "",
                "what": f"Payment failed: {attempt.get('error') or 'no reason given'}",
            }
        )
    if order.paid_at:
        events.append(
            {
                "at": order.paid_at,
                "what": f"Paid {order.payment_reference or ''} {order.payment_method or ''}".strip(),
            }
        )
    for delivery in order.deliveries:
        target = f" to {delivery.address}" if delivery.address else ""
        state = "" if delivery.succeeded else f" FAILED ({delivery.error})"
        events.append(
            {"at": delivery.at, "what": f"{delivery.method.title()}{target}{state}"}
        )
    for ticket in tickets:
        events.append(
            {
                "at": ticket["created_at"],
                "what": f"{ticket['kind'].title()} received ({ticket.get('reference') or ticket['id']})",
            }
        )
    if refund:
        events.append(
            {
                "at": refund["at"],
                "what": f"Marked refunded {refund.get('reference') or ''}".strip(),
            }
        )
    return sorted((e for e in events if e["at"]), key=lambda e: e["at"])


def customers(service: "ApiService", query: str = "") -> List[Dict[str, Any]]:
    spend: Dict[str, int] = defaultdict(int)
    paid_orders: Dict[str, int] = defaultdict(int)
    refunds = service.ledger.refunds()
    for order in service.orders.recent(100000):
        if order.paid_at and not refunds.get(order.order_id):
            for email in order_emails(order):
                spend[email] += order.amount_paise
                paid_orders[email] += 1
    rows = service.ledger.contacts(query)
    for row in rows:
        row["spent_paise"] = spend.get(row["email"], 0)
        row["paid_orders"] = paid_orders.get(row["email"], 0)
    return rows


def customer_detail(service: "ApiService", email: str) -> Optional[Dict[str, Any]]:
    address = normalise_email(email)
    if not address:
        return None
    contact = service.ledger.contact(address)
    refunds = service.ledger.refunds()
    their_orders = [
        order_view(o, refunds)
        for o in service.orders.recent(100000)
        if address in order_emails(o)
    ]
    tickets = service.ledger.tickets(email=address)
    if contact is None and not their_orders and not tickets:
        return None
    kits = list(dict.fromkeys(o["kit_id"] for o in their_orders))
    return {
        "email": address,
        "contact": contact,
        "orders": their_orders,
        "tickets": tickets,
        "uploads": service.ledger.uploads(kit_ids=kits) if kits else [],
        "spent_paise": sum(
            o["amount_paise"] for o in their_orders if o["paid_at"] and not o["refund"]
        ),
        "notes": service.ledger.notes(f"customer:{address}"),
    }


def search(service: "ApiService", query: str) -> Dict[str, Any]:
    needle = query.strip()
    if len(needle) < 2:
        return {"orders": [], "uploads": [], "customers": [], "tickets": []}
    lowered = needle.lower()
    tickets = [
        t
        for t in service.ledger.tickets(limit=5000)
        if lowered
        in " ".join(
            str(t.get(k) or "")
            for k in (
                "id",
                "reference",
                "email",
                "exam",
                "payment_reference",
                "order_id",
                "message",
            )
        ).lower()
    ]
    return {
        "orders": orders(service, needle, limit=5000)[:50],
        "uploads": service.ledger.uploads(query=needle, limit=50),
        "customers": service.ledger.contacts(needle, limit=50),
        "tickets": tickets[:50],
    }


def overview(service: "ApiService", days: int = 30) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=days)).isoformat()
    refunds = service.ledger.refunds()
    all_orders = [order_view(o, refunds) for o in service.orders.recent(100000)]
    uploads = service.ledger.uploads(since=since, limit=200000)

    # Money, by Indian calendar day.
    today = now.astimezone(IST).date()
    series_days = [
        (today - timedelta(days=n)).isoformat() for n in range(days - 1, -1, -1)
    ]
    revenue_by_day: Dict[str, int] = {day: 0 for day in series_days}
    orders_by_day: Dict[str, int] = {day: 0 for day in series_days}
    revenue_by_exam: Dict[str, int] = defaultdict(int)
    for order in all_orders:
        if not order["paid_at"] or order["refund"]:
            continue
        day = _ist_day(order["paid_at"])
        if day in revenue_by_day:
            revenue_by_day[day] += order["amount_paise"]
            orders_by_day[day] += 1
        names = order["exam_names"] or ["Not recorded"]
        share = order["amount_paise"] // len(names)
        for name in names:
            revenue_by_exam[name] += share

    uploads_by_day: Dict[str, int] = {day: 0 for day in series_days}
    by_hour = [0] * 24
    per_exam: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "uploads": 0,
            "prepared": 0,
            "failed": 0,
            "reasons": Counter(),
            "kits": set(),
        }
    )
    times: List[float] = []
    stage_samples: Dict[str, List[float]] = defaultdict(list)
    for row in uploads:
        started = parse(row["started_at"])
        if started:
            local = started.astimezone(IST)
            if local.date().isoformat() in uploads_by_day:
                uploads_by_day[local.date().isoformat()] += 1
            by_hour[local.hour] += 1
        exam = row.get("exam_name") or row.get("exam_id") or "Unknown"
        stats = per_exam[exam]
        stats["uploads"] += 1
        if row.get("kit_id"):
            stats["kits"].add(row["kit_id"])
        if row["status"] == "succeeded":
            stats["prepared"] += 1
            if isinstance(row.get("processing_seconds"), (int, float)):
                times.append(float(row["processing_seconds"]))
            for stage, ms in (row.get("stage_ms") or {}).items():
                stage_samples[stage].append(float(ms))
        elif row["status"] in ("failed", "error", "busy"):
            stats["failed"] += 1
        for reason in (row.get("findings") or []) + (row.get("issue_codes") or []):
            stats["reasons"][reason] += 1
        if row.get("error"):
            stats["reasons"][str(row["error"]).split(":")[0]] += 1

    paid_kits = {o["kit_id"] for o in all_orders if o["paid_at"]}
    exams = []
    for name, stats in per_exam.items():
        kits = stats["kits"]
        exams.append(
            {
                "exam": name,
                "uploads": stats["uploads"],
                "prepared": stats["prepared"],
                "failed": stats["failed"],
                "kits": len(kits),
                "kits_paid": len(kits & paid_kits),
                "conversion": round(len(kits & paid_kits) / len(kits), 4)
                if kits
                else None,
                "revenue_paise": revenue_by_exam.get(name, 0),
                "top_reasons": stats["reasons"].most_common(5),
            }
        )
    exams.sort(key=lambda e: (-e["revenue_paise"], -e["uploads"]))

    # Customers who paid more than once.
    paid_by_email: Dict[str, int] = defaultdict(int)
    for order in all_orders:
        if order["paid_at"]:
            for email in order["emails"]:
                paid_by_email[email] += 1
    payers = len(paid_by_email)
    repeat = sum(1 for count in paid_by_email.values() if count > 1)

    refund_due = [o for o in all_orders if o["state"] == "refund-due"]
    tickets = service.ledger.tickets(limit=5000)
    complained = {
        t["order_id"]
        for t in tickets
        if t.get("order_id")
        and t["kind"] in ("complaint", "grievance")
        and t["status"] != "resolved"
    }
    refund_review = [
        o
        for o in all_orders
        if o["order_id"] in complained and o["state"] == "delivered"
    ]

    stuck_cutoff = (now - timedelta(minutes=10)).isoformat()
    day_ago = (now - timedelta(days=1)).isoformat()
    stuck = [
        row
        for row in uploads
        if (
            row["status"] in ("error", "busy", "failed")
            and row["started_at"] >= day_ago
        )
        or (row["status"] == "processing" and row["started_at"] < stuck_cutoff)
    ][:100]

    followups = [
        o
        for o in all_orders
        if not o["paid_at"]
        and (o["state"] == "payment-failed" or o["emails"] or o["payer_contact"])
    ][:200]
    unpaid_kits = {
        row["kit_id"]
        for row in uploads
        if row.get("kit_id")
        and row["status"] == "succeeded"
        and row["kit_id"] not in paid_kits
    }

    paid_total = sum(
        o["amount_paise"] for o in all_orders if o["paid_at"] and not o["refund"]
    )
    return {
        "days": days,
        "generated_at": now.isoformat(),
        "money": {
            "all_time_paise": paid_total,
            "period_paise": sum(revenue_by_day.values()),
            "today_paise": revenue_by_day.get(today.isoformat(), 0),
            "paid_orders": sum(1 for o in all_orders if o["paid_at"]),
            "refunded_paise": sum(
                (r.get("amount_paise") or 0) for r in refunds.values()
            ),
            "refunded_orders": len(refunds),
            "average_order_paise": round(
                paid_total
                / max(1, sum(1 for o in all_orders if o["paid_at"] and not o["refund"]))
            ),
        },
        "series": [
            {
                "day": day,
                "revenue_paise": revenue_by_day[day],
                "orders": orders_by_day[day],
                "uploads": uploads_by_day[day],
            }
            for day in series_days
        ],
        "uploads_by_hour_ist": by_hour,
        "preparation_seconds": {
            "count": len(times),
            "median": round(statistics.median(times), 2) if times else None,
            "p95": _percentile(times, 0.95),
            "max": round(max(times), 2) if times else None,
            "stages_median_ms": {
                stage: round(statistics.median(values), 1)
                for stage, values in sorted(stage_samples.items())
            },
        },
        "uploads": {
            "total": len(uploads),
            "prepared": sum(1 for r in uploads if r["status"] == "succeeded"),
            "failed": sum(1 for r in uploads if r["status"] in ("failed", "error")),
            "busy": sum(1 for r in uploads if r["status"] == "busy"),
        },
        "exams": exams,
        "customers": {
            "payers": payers,
            "repeat_payers": repeat,
            "contacts": len(service.ledger.contacts(limit=1000000)),
        },
        "refund_due": refund_due,
        "refund_review": refund_review,
        "stuck": stuck,
        "followups": followups,
        "unpaid_kits": len(unpaid_kits),
        "tickets": {
            "open": sum(
                1 for t in tickets if t["status"] != "resolved" and t["kind"] != "exam"
            ),
            "overdue": [t for t in tickets if t["ack_overdue"] or t["resolve_overdue"]],
            "exam_requests_open": sum(
                1 for t in tickets if t["kind"] == "exam" and not t.get("added_at")
            ),
        },
        "health": service.ledger.health((now - timedelta(days=7)).isoformat()),
    }


def pending_alerts(service: "ApiService") -> List[Dict[str, str]]:
    """What the watch should email now, each keyed so it is sent once."""
    now = datetime.now(timezone.utc)
    ledger = service.ledger
    alerts: List[Dict[str, str]] = []
    refunds = ledger.refunds()

    for order in service.orders.recent(5000):
        paid = parse(order.paid_at)
        if (
            paid
            and not order.delivered_at
            and order.order_id not in refunds
            and now - paid > UNDELIVERED_ALERT_AFTER
        ):
            alerts.append(
                {
                    "key": f"undelivered:{order.order_id}",
                    "subject": f"Paid but not delivered: {order.order_id}",
                    "body": f"Rs {order.amount_paise / 100:g} paid {order.paid_at} ({order.payment_reference}); nothing delivered yet.\nhttps://examuploadkit.com/admin/orders/{order.order_id}",
                }
            )

    hour_ago = (now - timedelta(hours=1)).isoformat()
    failures: Counter[str] = Counter()
    for row in ledger.uploads(since=hour_ago, limit=10000):
        if row["status"] in ("error", "failed"):
            failures[row.get("exam_name") or row.get("exam_id") or "Unknown"] += 1
    for exam, count in failures.items():
        if count >= FAILURE_RUN:
            alerts.append(
                {
                    "key": f"failures:{exam}:{now.strftime('%Y%m%d%H')}",
                    "subject": f"{count} failed preparations for {exam} in the last hour",
                    "body": f"https://examuploadkit.com/admin/uploads?q={exam}",
                }
            )

    for ticket in ledger.tickets(limit=5000):
        if ticket["ack_overdue"]:
            alerts.append(
                {
                    "key": f"ack:{ticket['id']}",
                    "subject": f"Unanswered for 48 hours: {ticket['kind']} {ticket.get('reference') or ticket['id']}",
                    "body": f"https://examuploadkit.com/admin/tickets/{ticket['id']}",
                }
            )

    from exam_photo.api.growth import reconcile

    for problem in reconcile(service).get("problems", []):
        why = (
            "we have no such order"
            if problem.get("kind") == "unknown_order"
            else "our order is not marked paid"
        )
        amount = (problem.get("amount_paise") or 0) / 100
        alerts.append(
            {
                "key": f"reconcile:{problem.get('payment_id')}",
                "subject": (
                    f"Razorpay captured {problem.get('payment_id')} "
                    "but no file was released"
                ),
                "body": (
                    f"Payment {problem.get('payment_id')} for order "
                    f"{problem.get('order_id')} (Rs {amount:g}, "
                    f"{problem.get('email') or 'no email'}) is captured at "
                    f"Razorpay; {why}.\n"
                    "https://examuploadkit.com/admin/growth#reconcile"
                ),
            }
        )

    local = now.astimezone(IST)
    if local.hour >= DIGEST_HOUR_IST:
        alerts.append({"key": f"digest:{local.date().isoformat()}", **digest(service)})

    return [alert for alert in alerts if not ledger.alert_sent(alert["key"])]


def digest(service: "ApiService") -> Dict[str, str]:
    """Yesterday, in one email, at eight in the morning (IST)."""
    data = overview(service, days=2)
    yesterday = data["series"][0]
    lines = [
        f"Yesterday: Rs {yesterday['revenue_paise'] / 100:g} from {yesterday['orders']} orders, {yesterday['uploads']} uploads.",
        f"All time: Rs {data['money']['all_time_paise'] / 100:g}.",
        f"Refund due: {len(data['refund_due'])}. Complaints to review against delivered orders: {len(data['refund_review'])}.",
        f"Open complaints and questions: {data['tickets']['open']} ({len(data['tickets']['overdue'])} overdue).",
        f"Open exam requests: {data['tickets']['exam_requests_open']}.",
        f"Failed or refused preparations in the last day: {len(data['stuck'])}.",
        f"Median preparation {data['preparation_seconds']['median']} s, p95 {data['preparation_seconds']['p95']} s.",
        "",
        "https://examuploadkit.com/admin",
    ]
    return {"subject": f"ExamUploadKit, {yesterday['day']}", "body": "\n".join(lines)}


def csv_text(rows: List[Dict[str, Any]], columns: List[str]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _flat(row.get(key)) for key in columns})
    return buffer.getvalue()


def _flat(value: Any) -> Any:
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    if isinstance(value, dict):
        return "; ".join(f"{k}={v}" for k, v in value.items())
    return value
