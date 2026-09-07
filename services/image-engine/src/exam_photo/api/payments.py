"""Razorpay webhook verification and the release instructions it carries.

DEC-063 left `ApiProcessingService.release_job` as a seam with nothing calling
it, and said explicitly why there is no HTTP route that releases a job: an
unauthenticated one is not a weaker gate than none, it is a worse one, because
it reads as protection to anyone scanning the route list. This module is the
caller that entry anticipated, and the signature check is what makes it
different from the route DEC-063 refused to write.

Everything here is pure: it verifies bytes and reads a payload. It performs no
I/O, holds no state, and never touches a job. That is deliberate -- the parts
that can be reasoned about in a test without a service, a registry or a disk
are the parts a payment path most needs to be certain of.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

#: Razorpay signs the webhook body and sends the digest in this header.
SIGNATURE_HEADER = "X-Razorpay-Signature"

#: The events that mean money actually moved. `order.paid` fires when an order
#: is fully paid; `payment.captured` when a payment is captured. Anything else
#: -- `payment.authorized` above all -- must **not** release a file: an
#: authorised payment is a hold, not a settlement, and it can still fail.
RELEASING_EVENTS = frozenset({"payment.captured", "order.paid"})

#: A webhook body larger than this is refused unread. Razorpay's payloads are a
#: few kilobytes; anything approaching this is not one.
MAX_BODY_BYTES = 64 * 1024


class WebhookRejectedError(Exception):
    """The request is not a webhook this service will act on.

    Carries a reason for the operator's log and, deliberately, nothing that
    would help a caller work out *why* their forgery failed.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class ReleaseInstruction:
    """What a verified webhook is asking the service to release."""

    event: str
    payment_id: Optional[str]
    order_id: Optional[str]
    #: Paise, as Razorpay reports it. Recorded for reconciliation; **not** yet
    #: checked against a price, because nothing here knows what was owed. See
    #: the module note in `verify_and_read`.
    amount: Optional[int]
    currency: Optional[str]
    job_ids: List[str] = field(default_factory=list)
    kit_ids: List[str] = field(default_factory=list)

    @property
    def names_nothing(self) -> bool:
        return not self.job_ids and not self.kit_ids


def signature_matches(body: bytes, signature: str, secret: str) -> bool:
    """Whether `signature` is Razorpay's HMAC-SHA256 digest of `body`.

    Compared in constant time. The digest is taken over the **raw bytes as
    received**: re-serialising the JSON first would change the whitespace and
    the key order, and the signature would never match again.
    """
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip())


def _notes_from(entity: Dict[str, Any]) -> Dict[str, Any]:
    notes = entity.get("notes")
    return notes if isinstance(notes, dict) else {}


def _collect(notes: Dict[str, Any], key: str) -> List[str]:
    """Read one identifier, or a comma-separated list of them, from `notes`.

    A kit is bought as a bundle and a single file on its own, so both shapes
    occur. Blank entries are dropped rather than passed on as empty ids.
    """
    raw = notes.get(key)
    if raw is None:
        return []
    if isinstance(raw, list):
        candidates = [str(item) for item in raw]
    else:
        candidates = str(raw).split(",")
    return [text.strip() for text in candidates if text.strip()]


def verify_and_read(
    body: bytes, signature: str, secret: str
) -> Optional[ReleaseInstruction]:
    """Verify a webhook and read what it asks to be released.

    Returns `None` for a genuine Razorpay event this service does not act on --
    a failed payment, a refund, an authorisation. Those are acknowledged rather
    than refused, because Razorpay retries anything it is not told was received
    and a 4xx would turn one ignored event into an indefinite retry loop.

    Raises `WebhookRejectedError` when the request is not a verified webhook at all.

    **What this does not check: the amount.** `amount` is carried through for
    reconciliation, but nothing here knows what the candidate owed, so nothing
    here can tell a full payment from a rupee. Binding an amount to a job is
    the job of server-side order creation -- an order the service itself
    creates, at a price the service computes -- and until that exists this
    webhook must not be pointed at a live Razorpay account. DEC-069 records
    this as the companion piece rather than leaving it to be discovered.
    """
    if not secret:
        # Refusing here rather than reading the payload follows DEC-060: a host
        # that has not configured the secret is in exactly the state an
        # insecure default would ship, and must fail loudly rather than accept.
        raise WebhookRejectedError("no webhook secret is configured")
    if len(body) > MAX_BODY_BYTES:
        raise WebhookRejectedError("body too large")
    if not signature_matches(body, signature, secret):
        raise WebhookRejectedError("signature mismatch")

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        # Only reachable with a correctly signed body, so this is our own
        # integration breaking rather than an attacker probing.
        raise WebhookRejectedError("verified body is not JSON") from err
    if not isinstance(payload, dict):
        raise WebhookRejectedError("verified body is not a JSON object")

    event = str(payload.get("event") or "")
    if event not in RELEASING_EVENTS:
        return None

    container = payload.get("payload")
    container = container if isinstance(container, dict) else {}
    payment = ((container.get("payment") or {}).get("entity")) or {}
    order = ((container.get("order") or {}).get("entity")) or {}
    payment = payment if isinstance(payment, dict) else {}
    order = order if isinstance(order, dict) else {}

    # Notes ride on the order when one exists and on the payment otherwise.
    notes = {**_notes_from(order), **_notes_from(payment)}
    job_ids = _collect(notes, "job_id") + _collect(notes, "job_ids")
    kit_ids = _collect(notes, "kit_id") + _collect(notes, "kit_ids")

    return ReleaseInstruction(
        event=event,
        payment_id=str(payment.get("id")) if payment.get("id") else None,
        order_id=(
            str(order.get("id"))
            if order.get("id")
            else (str(payment.get("order_id")) if payment.get("order_id") else None)
        ),
        amount=payment.get("amount")
        if isinstance(payment.get("amount"), int)
        else (order.get("amount") if isinstance(order.get("amount"), int) else None),
        currency=str(payment.get("currency") or order.get("currency") or "") or None,
        job_ids=list(dict.fromkeys(job_ids)),
        kit_ids=list(dict.fromkeys(kit_ids)),
    )
