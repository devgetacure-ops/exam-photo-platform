"""Emails the owner sends to customers, and the links in them (DEC-111).

Every marketing email carries a working unsubscribe: a signed link in the
footer and the `List-Unsubscribe` / `List-Unsubscribe-Post` headers Gmail and
Yahoo require of bulk senders. An address that unsubscribes is never sent a
campaign again. Sends run on a background thread, one at a time with a pause
between them, so a large list neither blocks the page nor trips Resend's rate
limit.
"""

from __future__ import annotations

import hashlib
import hmac
import threading
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional
from urllib.parse import quote

from exam_photo.api.delivery import UnconfiguredEmailSender
from exam_photo.api.ledger import normalise_email
from exam_photo.api.operator import IST, order_emails

if TYPE_CHECKING:  # pragma: no cover
    from exam_photo.api.service import ApiProcessingService as ApiService

#: Seconds between two sends. Resend allows a few a second; one is plenty.
SEND_PAUSE_SECONDS = 1.0
#: A reminder goes this many days before an examination's closing date.
REMIND_DAYS_BEFORE = 3

SEGMENTS = {
    "all": "Everyone with an address",
    "paid": "Everyone who has paid",
    "never_paid": "Everyone who has never paid",
    "checkout_failed": "Started checkout, payment failed",
    "paid_exam": "Paid for one examination",
    "asked_exam": "Asked for one examination",
}


def _secret(service: "ApiService") -> bytes:
    key = service.settings.link_secret or service.settings.operator_token
    return hashlib.sha256(f"euk-links:{key}".encode()).digest() if key else b""


def sign(service: "ApiService", purpose: str, value: str) -> Optional[str]:
    secret = _secret(service)
    if not secret:
        return None
    return hmac.new(secret, f"{purpose}:{value}".encode(), hashlib.sha256).hexdigest()[
        :32
    ]


def verify(service: "ApiService", purpose: str, value: str, token: str) -> bool:
    expected = sign(service, purpose, value)
    return bool(expected and token and hmac.compare_digest(expected, token))


def _site(service: "ApiService") -> str:
    return (service.settings.site_url or "https://examuploadkit.com").rstrip("/")


def unsubscribe_url(service: "ApiService", email: str) -> Optional[str]:
    token = sign(service, "unsubscribe", email)
    if not token:
        return None
    return f"{_site(service)}/v1/unsubscribe?e={quote(email)}&t={token}"


def feedback_urls(service: "ApiService", order_id: str) -> Optional[Dict[str, str]]:
    token = sign(service, "feedback", order_id)
    if not token:
        return None
    base = f"{_site(service)}/feedback?o={quote(order_id)}&t={token}"
    return {"yes": f"{base}&a=yes", "no": f"{base}&a=no"}


def recipients(service: "ApiService", segment: str, target: str = "") -> List[str]:
    """Addresses in a segment, minus everyone who unsubscribed."""
    ledger = service.ledger
    orders = service.orders.recent(500000)
    paid_emails = {e for o in orders if o.paid_at for e in order_emails(o)}
    wanted = target.strip().lower()
    if segment == "all":
        found = [c["email"] for c in ledger.contacts(limit=1000000)]
    elif segment == "paid":
        found = sorted(paid_emails)
    elif segment == "never_paid":
        found = [
            c["email"]
            for c in ledger.contacts(limit=1000000)
            if c["email"] not in paid_emails
        ]
    elif segment == "checkout_failed":
        found = [
            e
            for o in orders
            if not o.paid_at and o.failed_payments
            for e in order_emails(o)
        ]
    elif segment == "paid_exam":
        found = [
            e
            for o in orders
            if o.paid_at
            and any(
                wanted in {(i.exam_id or "").lower(), (i.exam_name or "").lower()}
                for i in o.items
            )
            for e in order_emails(o)
        ]
    elif segment == "asked_exam":
        found = [
            str(t["email"])
            for t in ledger.tickets(kinds=["exam"], limit=100000)
            if t.get("email") and (t.get("exam") or "").strip().lower() == wanted
        ]
    else:
        raise ValueError(f"unknown segment {segment!r}")
    blocked = ledger.suppressed()
    cleaned = [normalise_email(e) for e in found]
    return [e for e in dict.fromkeys(cleaned) if e and e not in blocked]


def render(service: "ApiService", body: str, email: str) -> tuple[str, str]:
    """Plain text and HTML, each ending with the unsubscribe line."""
    link = unsubscribe_url(service, email) or ""
    text = f"{body.rstrip()}\n\n--\nExamUploadKit · {_site(service)}\nTo stop these emails: {link}\n"
    paragraphs = "".join(
        f'<p style="margin:0 0 14px">{_escape(p).replace(chr(10), "<br>")}</p>'
        for p in body.strip().split("\n\n")
    )
    html = (
        '<div style="font-family:Arial,sans-serif;font-size:15px;line-height:1.5;color:#111;max-width:560px">'
        f"{paragraphs}"
        f'<p style="margin:28px 0 0;font-size:12px;color:#666">ExamUploadKit · <a href="{_site(service)}">{_site(service)}</a><br>'
        f'<a href="{link}">Unsubscribe</a> from these emails.</p></div>'
    )
    return text, html


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def send_one(service: "ApiService", email: str, subject: str, body: str) -> None:
    text, html = render(service, body, email)
    link = unsubscribe_url(service, email)
    headers = {"Precedence": "bulk"}
    if link:
        headers["List-Unsubscribe"] = f"<{link}>"
        headers["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    service.email_sender.send(email, subject, text, [], html=html, headers=headers)


def start_campaign(
    service: "ApiService",
    actor: str,
    segment: str,
    target: str,
    subject: str,
    body: str,
    runner: Callable[[Callable[[], None]], None] | None = None,
) -> Dict[str, Any]:
    """Queue a campaign and send it in the background. Returns its record."""
    if not subject.strip() or not body.strip():
        raise ValueError("a campaign needs a subject and a message")
    if isinstance(service.email_sender, UnconfiguredEmailSender):
        # Refuse up front rather than queue a list that can only fail.
        raise ValueError("email sending is not configured on this server")
    addresses = recipients(service, segment, target)
    if not addresses:
        raise ValueError("nobody is in that segment")
    label = f"{segment}:{target}" if target else segment
    campaign_id = service.ledger.create_campaign(
        actor, label, subject.strip(), body.strip(), addresses
    )
    service.ledger.log(
        actor, f"started campaign to {len(addresses)}", f"campaign:{campaign_id}"
    )

    def work() -> None:
        send_campaign(service, campaign_id)

    (runner or _in_thread)(work)
    return service.ledger.campaign(campaign_id) or {}


def _in_thread(work: Callable[[], None]) -> None:
    threading.Thread(target=work, name="euk-campaign", daemon=True).start()


def send_campaign(
    service: "ApiService", campaign_id: str, pause: float = SEND_PAUSE_SECONDS
) -> None:
    ledger = service.ledger
    campaign = ledger.campaign(campaign_id)
    if campaign is None:
        return
    blocked = ledger.suppressed()
    for email in ledger.queued_recipients(campaign_id):
        if email in blocked:
            ledger.campaign_result(campaign_id, email, False, "unsubscribed")
            continue
        try:
            send_one(service, email, campaign["subject"], campaign["body"])
            ledger.campaign_result(campaign_id, email, True)
        except Exception as err:  # noqa: BLE001 - one bad address is not the list
            ledger.campaign_result(campaign_id, email, False, str(err))
        if pause:
            time.sleep(pause)
    ledger.finish_campaign(campaign_id)


def send_test(service: "ApiService", to: str, subject: str, body: str) -> None:
    send_one(service, to, f"[Test] {subject}", body)


# --- The two automatic emails -------------------------------------------------


def exam_added_message(exam: str, site: str) -> tuple[str, str]:
    return (
        f"{exam} is now on ExamUploadKit",
        f"Hello,\n\nYou asked us for {exam}. It is ready now: choose it at {site} and your photograph and signature are prepared to its published rules in a couple of minutes.\n\nThank you for asking.",
    )


def deadline_message(exam: str, closes_on: str, site: str) -> tuple[str, str]:
    return (
        f"{exam} applications close on {closes_on}",
        f"Hello,\n\nApplications for {exam} close on {closes_on}. If you still need a photograph, signature or any other file for it, {site} prepares them to the published rules in a couple of minutes.\n\nAll the best.",
    )


def run_automations(service: "ApiService", now: Optional[datetime] = None) -> List[str]:
    """Deadline reminders the owner switched on, sent once, three days before.

    Called from the engine's sweeper every few minutes. Returns the campaign
    ids it started.
    """
    ledger = service.ledger
    local = (now or datetime.now(IST)).astimezone(IST)
    if local.hour < 9:
        return []
    started: List[str] = []
    for exam_id, deadline in ledger.deadlines().items():
        if not deadline["auto_remind"]:
            continue
        remind_on = (
            datetime.fromisoformat(deadline["closes_on"])
            - timedelta(days=REMIND_DAYS_BEFORE)
        ).date()
        key = f"auto-remind:{exam_id}:{deadline['closes_on']}"
        if remind_on != local.date() or ledger.alert_sent(key):
            continue
        ledger.mark_alert_sent(key)
        entry = service.catalogue.get(exam_id)
        name = entry.rule.exam.exam_name if entry is not None else exam_id
        subject, body = deadline_message(name, deadline["closes_on"], _site(service))
        try:
            campaign = start_campaign(
                service, "automatic", "paid_exam", exam_id, subject, body
            )
            started.append(str(campaign.get("id")))
        except ValueError:
            continue
    return started
