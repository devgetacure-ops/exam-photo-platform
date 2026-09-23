"""The order we created, remembered, so a payment releases exactly what it paid for.

DEC-071. DEC-070 created the order server-side at a price computed from the
jobs on disk, but told the webhook to release *the kit* -- everything in it
when the payment landed. That is not the same set. A file prepared between the
order and the payment would have been released against an amount quoted before
it existed.

The fix is to stop describing the purchase by a container that can change.
An order records **the exact job ids it was priced from**, and the payment
releases those and nothing else. A file prepared afterwards is simply not in
the order, so there is no window to reason about and no race to lose.

It also leaves the trail a refund needs: what was ordered, for how much, when,
and which payment settled it.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

#: Razorpay order ids look like `order_MkT9r2Bx1QwPqz`. Pinned because the id
#: becomes a filename, and an id from an untrusted payload must never be able
#: to walk out of the directory it is written into.
ORDER_ID_REGEX = re.compile(r"^order_[A-Za-z0-9_-]{1,64}$")


#: How long an order record is kept (DEC-108). DEC-109: the owner keeps the
#: addresses in it for as long as the record, so they are no longer stripped.
ORDER_RETENTION = timedelta(days=8 * 365)
#: A file downloaded a hundred times is still one answer to "did it arrive".
MAX_DELIVERIES = 50


class OrderItem(BaseModel):
    """One file the order was priced from, named as the candidate saw it.

    Written when the order is created, because the job that knew these names
    is erased thirty minutes later (DEC-066) and the order is not.
    """

    job_id: str
    exam_id: Optional[str] = None
    exam_name: Optional[str] = None
    requirement_name: Optional[str] = None
    requirement_type: Optional[str] = None


class OrderDelivery(BaseModel):
    """One attempt to hand the candidate something this order covers."""

    at: str
    job_id: str
    #: `download` or `email`.
    method: str
    succeeded: bool = True
    #: Email only. The masked form is kept for display; DEC-109 keeps the
    #: address itself too, on the owner's decision.
    masked_address: Optional[str] = None
    address: Optional[str] = None
    error: Optional[str] = None


class OrderRecord(BaseModel):
    """One order, and the files it was priced from."""

    order_id: str
    kit_id: str
    #: The exact jobs quoted, captured when the order was created. This is the
    #: purchase; the kit is only where they happened to live at the time.
    job_ids: List[str] = Field(default_factory=list)
    amount_paise: int
    currency: str
    created_at: str
    #: Set when a verified payment settled this order (DEC-069).
    paid_at: Optional[str] = None
    payment_reference: Optional[str] = None
    #: When something covered by this order first reached the candidate, and
    #: how (DEC-072). This is the other half of deciding a refund: the order
    #: says money arrived, this says a file left. Deliberately carries no
    #: address -- an order record is kept long after the files are erased, and
    #: retaining a candidate's email that long serves nothing.
    delivered_at: Optional[str] = None
    delivery_method: Optional[str] = None
    #: DEC-108. Empty on orders written before these fields existed; the page
    #: says "not recorded" rather than guessing.
    items: List[OrderItem] = Field(default_factory=list)
    deliveries: List[OrderDelivery] = Field(default_factory=list)
    #: DEC-109. What Razorpay told us about the payer, from the verified
    #: webhook: the email and phone they typed into checkout, and the method.
    payer_email: Optional[str] = None
    payer_contact: Optional[str] = None
    payment_method: Optional[str] = None
    #: Attempts Razorpay reported as failed (`payment.failed`), newest last.
    failed_payments: List[Dict[str, Optional[str]]] = Field(default_factory=list)


class OrderRegistry:
    """Stores orders beside the artifacts, under a directory of their own.

    Kept out of the job directories on purpose: an order outlives the files it
    paid for. Retention erases a candidate's photograph after thirty minutes
    (DEC-066), and the record that they paid must not go with it -- that record
    is the only evidence available if they later say they were charged and
    received nothing.
    """

    def __init__(self, artifact_root: Path):
        self.root = artifact_root / "_orders"

    def _path(self, order_id: str) -> Path:
        return self.root / f"{order_id}.json"

    def create(
        self,
        order_id: str,
        kit_id: str,
        job_ids: List[str],
        amount_paise: int,
        currency: str,
        items: Optional[List[OrderItem]] = None,
    ) -> OrderRecord:
        if not ORDER_ID_REGEX.match(order_id):
            raise ValueError(f"Invalid order_id format: {order_id!r}")
        record = OrderRecord(
            order_id=order_id,
            kit_id=kit_id,
            job_ids=list(job_ids),
            amount_paise=amount_paise,
            currency=currency,
            created_at=datetime.now(timezone.utc).isoformat(),
            items=list(items or []),
        )
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(order_id).write_text(
            record.model_dump_json(indent=2), encoding="utf-8"
        )
        return record

    def get(self, order_id: str) -> Optional[OrderRecord]:
        """The order, or `None` if we did not create it.

        A `None` here is not an error: it means the payment refers to an order
        this service never made, and the webhook falls back to the identifiers
        in the notes. That path exists for an order created by hand in the
        Razorpay dashboard, which is a real thing an operator does.
        """
        if not order_id or not ORDER_ID_REGEX.match(order_id):
            return None
        path = self._path(order_id)
        if not path.is_file():
            return None
        try:
            return OrderRecord.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _all(self) -> List[tuple[Path, OrderRecord]]:
        found: List[tuple[Path, OrderRecord]] = []
        if not self.root.is_dir():
            return found
        for path in self.root.glob("order_*.json"):
            try:
                found.append(
                    (
                        path,
                        OrderRecord.model_validate_json(
                            path.read_text(encoding="utf-8")
                        ),
                    )
                )
            except Exception:
                continue
        return found

    def recent(self, limit: int = 500) -> List[OrderRecord]:
        """Every order, newest first, for the operator page (DEC-108)."""
        records = [record for _path, record in self._all()]
        records.sort(key=lambda record: record.created_at, reverse=True)
        return records[: max(0, limit)]

    def mark_delivered(
        self,
        job_id: str,
        method: str,
        masked_address: Optional[str] = None,
        address: Optional[str] = None,
    ) -> None:
        """Record a delivery of anything an order covers.

        Finds the order by the job rather than the other way round, because
        that is the direction the caller knows: a download route holds a job
        and nothing else. `delivered_at` keeps only the first -- the question a
        refund asks is whether the candidate got their file, not how many
        times -- and every attempt is kept beside it (DEC-108).
        """
        self._record(
            job_id,
            OrderDelivery(
                at=datetime.now(timezone.utc).isoformat(),
                job_id=job_id,
                method=method,
                masked_address=masked_address,
                address=address,
            ),
        )

    def mark_delivery_failed(
        self,
        job_id: str,
        method: str,
        masked_address: Optional[str],
        error: str,
        address: Optional[str] = None,
    ) -> None:
        """Record a delivery that did not happen, so a claim can be read."""
        self._record(
            job_id,
            OrderDelivery(
                at=datetime.now(timezone.utc).isoformat(),
                job_id=job_id,
                method=method,
                succeeded=False,
                masked_address=masked_address,
                address=address,
                error=error[:200],
            ),
        )

    def _record(self, job_id: str, delivery: OrderDelivery) -> None:
        first_marked = False
        for path, record in self._all():
            if job_id not in record.job_ids:
                continue
            if delivery.succeeded and not first_marked and record.delivered_at is None:
                record.delivered_at = delivery.at
                record.delivery_method = delivery.method
                first_marked = True
            if len(record.deliveries) < MAX_DELIVERIES:
                record.deliveries.append(delivery)
            path.write_text(record.model_dump_json(indent=2), encoding="utf-8")

    def sweep(self, now: Optional[datetime] = None) -> int:
        """Apply DEC-108's eight years. Returns the number removed."""
        now = now or datetime.now(timezone.utc)
        removed = 0
        for path, record in self._all():
            created = _parse(record.created_at)
            if created is not None and now - created >= ORDER_RETENTION:
                path.unlink(missing_ok=True)
                removed += 1
        return removed

    def record_payer(
        self,
        order_id: str,
        email: Optional[str],
        contact: Optional[str],
        method: Optional[str],
    ) -> None:
        """Keep who paid, as Razorpay's checkout collected it (DEC-109)."""
        record = self.get(order_id)
        if record is None:
            return
        record.payer_email = email or record.payer_email
        record.payer_contact = contact or record.payer_contact
        record.payment_method = method or record.payment_method
        self._path(order_id).write_text(
            record.model_dump_json(indent=2), encoding="utf-8"
        )

    def record_failed_payment(
        self, order_id: str, attempt: Dict[str, Optional[str]]
    ) -> None:
        """A checkout that did not go through, for the follow-up list."""
        record = self.get(order_id)
        if record is None or len(record.failed_payments) >= 20:
            return
        record.failed_payments.append(attempt)
        if attempt.get("email") and not record.payer_email:
            record.payer_email = attempt.get("email")
        if attempt.get("contact") and not record.payer_contact:
            record.payer_contact = attempt.get("contact")
        self._path(order_id).write_text(
            record.model_dump_json(indent=2), encoding="utf-8"
        )

    def paid_order_for(self, job_ids: List[str]) -> Optional[OrderRecord]:
        """The settled order that paid for any of these jobs, if there is one.

        For the receipt in the delivery email (DEC-102). The most recently paid
        wins, so a file bought twice shows the payment that released it.
        """
        if not self.root.is_dir() or not job_ids:
            return None
        wanted = set(job_ids)
        found: Optional[OrderRecord] = None
        for path in self.root.glob("order_*.json"):
            try:
                record = OrderRecord.model_validate_json(
                    path.read_text(encoding="utf-8")
                )
            except Exception:
                continue
            if record.paid_at is None or not wanted.intersection(record.job_ids):
                continue
            if found is None or (record.paid_at or "") > (found.paid_at or ""):
                found = record
        return found

    def mark_paid(self, order_id: str, payment_reference: Optional[str]) -> None:
        """Record that a verified payment settled this order.

        Idempotent: Razorpay retries, so this is called more than once for some
        payments, and the first settlement time is the one kept.
        """
        record = self.get(order_id)
        if record is None or record.paid_at is not None:
            return
        record.paid_at = datetime.now(timezone.utc).isoformat()
        record.payment_reference = payment_reference
        self._path(order_id).write_text(
            record.model_dump_json(indent=2), encoding="utf-8"
        )


def _parse(stamp: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(stamp)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
