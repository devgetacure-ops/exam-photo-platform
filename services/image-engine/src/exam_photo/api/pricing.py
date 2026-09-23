"""What a kit costs, decided here and never in the browser.

DEC-070. A price the browser computes is a price a candidate can edit, so the
amount that reaches Razorpay is computed from the jobs on disk and an order is
created server-side at that amount. Razorpay then guarantees that a payment
matches its order, and that guarantee becomes a guarantee about our figure --
which is the whole reason the webhook (DEC-069) could not be pointed at live
keys without this.

Pure: it reads job records and returns numbers. No I/O, no network, no service.

**The rule, in the product owner's words:** Rs 3 for any single deliverable
that is an image and needs the model to work on it. Document work -- image to
PDF, compression, rearranging, merging -- is **free**, because candidates can
already do that elsewhere for nothing and charging for it would be charging for
the one part that is not ours.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from exam_photo.api.contracts import ApiJobStatus, JobEntitlement
from exam_photo.api.jobs import ProcessingJobRecord

#: Deliverables the model actually works on, and the only ones charged for.
#: A handwritten declaration is here because it goes through the ink pipeline
#: exactly as a signature does; a certificate scan is not, because its work is
#: assembling a PDF and that is the part we do not charge for.
CHARGEABLE_REQUIREMENT_TYPES = frozenset(
    {
        "photograph",
        "signature",
        "thumb_impression",
        "handwritten_declaration",
    }
)

#: Paise. Indexed by how many chargeable deliverables are in the basket; the
#: last entry is the ceiling, so two items and six cost the same. That is
#: deliberate and it is the product's promise: **everything an examination asks
#: for, for five rupees.** Set by the owner on 2026-09-14 (DEC-070, amended).
PRICE_LADDER_PAISE: Sequence[int] = (300, 500)

#: The struck-through figure shown beside each tier. Marketing, not arithmetic,
#: so it lives beside the real price rather than being derived from it.
LIST_LADDER_PAISE: Sequence[int] = (500, 1000)

CURRENCY = "INR"


@dataclass(frozen=True)
class QuoteLine:
    """One deliverable, and whether it is being charged for."""

    job_id: str
    requirement_id: Optional[str]
    requirement_type: Optional[str]
    chargeable: bool
    reason: str


#: Razorpay will not take less than a rupee, so no discount goes below it.
MINIMUM_CHARGE_PAISE = 100


@dataclass(frozen=True)
class Discount:
    """A coupon, already found valid, as pricing needs it (DEC-111)."""

    code: str
    kind: str  # "percent" or "flat"
    value: int  # percent 1-90, or paise

    def off(self, amount_paise: int) -> int:
        if amount_paise <= 0:
            return 0
        if self.kind == "percent":
            cut = amount_paise * max(0, min(self.value, 90)) // 100
        else:
            cut = max(0, self.value)
        return max(0, min(cut, amount_paise - MINIMUM_CHARGE_PAISE))


@dataclass(frozen=True)
class Quote:
    """What a candidate owes for a kit, and why."""

    amount_paise: int
    list_amount_paise: int
    currency: str
    chargeable_count: int
    included_free_count: int
    already_released_count: int
    lines: List[QuoteLine]
    #: DEC-110: which price-test arm priced this kit ("A" is the standard).
    price_variant: str = "A"
    #: DEC-111: the coupon applied, and what it took off.
    coupon_code: Optional[str] = None
    discount_paise: int = 0

    @property
    def is_payable(self) -> bool:
        """Whether there is anything to charge for.

        A kit of nothing but certificates is genuinely free, and an order for
        zero is not something to send to a payment gateway.
        """
        return self.amount_paise > 0


def _tier(count: int, ladder: Sequence[int]) -> int:
    if count <= 0:
        return 0
    return ladder[min(count, len(ladder)) - 1]


def _classify(record: ProcessingJobRecord) -> QuoteLine:
    kind = record.requirement_type

    if record.status == ApiJobStatus.DELETED or record.is_expired():
        return QuoteLine(record.job_id, record.requirement_id, kind, False, "expired")
    if record.entitlement == JobEntitlement.RELEASED:
        # Already paid for. Charging again for a file the candidate can already
        # download is the kind of double-billing that is very hard to argue was
        # accidental, so it is excluded here rather than caught downstream.
        return QuoteLine(
            record.job_id, record.requirement_id, kind, False, "already_released"
        )
    if not record.output_filename:
        return QuoteLine(
            record.job_id, record.requirement_id, kind, False, "nothing_prepared"
        )
    if kind not in CHARGEABLE_REQUIREMENT_TYPES:
        return QuoteLine(
            record.job_id, record.requirement_id, kind, False, "document_work_is_free"
        )
    return QuoteLine(record.job_id, record.requirement_id, kind, True, "charged")


def quote_for(
    records: Iterable[ProcessingJobRecord],
    ladder: Sequence[int] = PRICE_LADDER_PAISE,
    variant: str = "A",
    discount: Optional[Discount] = None,
) -> Quote:
    """Price a kit from the jobs it holds.

    Every job is reported, charged or not, with the reason. A candidate being
    told *why* a certificate costs nothing is worth more than a total on its
    own, and an itemised quote is also what makes an argument about a charge
    settleable later.
    """
    lines = [_classify(record) for record in records]
    chargeable = [line for line in lines if line.chargeable]
    free = [
        line
        for line in lines
        if not line.chargeable and line.reason == "document_work_is_free"
    ]
    released = [line for line in lines if line.reason == "already_released"]

    count = len(chargeable)
    base = _tier(count, ladder)
    cut = discount.off(base) if discount else 0
    return Quote(
        amount_paise=base - cut,
        list_amount_paise=_tier(count, LIST_LADDER_PAISE),
        currency=CURRENCY,
        chargeable_count=count,
        included_free_count=len(free),
        already_released_count=len(released),
        lines=lines,
        price_variant=variant,
        coupon_code=discount.code if discount and cut else None,
        discount_paise=cut,
    )


def price_variant(kit_id: str, share_percent: int) -> str:
    """Which arm of a price test a kit falls in, the same every time (DEC-110).

    A hash, not a coin toss, so a candidate who reloads sees the same price,
    and the quote and the order always agree.
    """
    if share_percent <= 0:
        return "A"
    digest = hashlib.sha256(kit_id.encode("utf-8")).digest()
    return "B" if digest[0] * 100 // 256 < min(share_percent, 100) else "A"


def parse_ladder(text: str) -> Optional[List[int]]:
    """`"400,700"` → `[400, 700]`; anything unusable → `None` (test off)."""
    try:
        values = [int(part) for part in text.split(",") if part.strip()]
    except ValueError:
        return None
    if not values or any(v < MINIMUM_CHARGE_PAISE or v > 100_000 for v in values):
        return None
    return values
