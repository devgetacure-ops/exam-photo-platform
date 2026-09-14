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


def quote_for(records: Iterable[ProcessingJobRecord]) -> Quote:
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
    return Quote(
        amount_paise=_tier(count, PRICE_LADDER_PAISE),
        list_amount_paise=_tier(count, LIST_LADDER_PAISE),
        currency=CURRENCY,
        chargeable_count=count,
        included_free_count=len(free),
        already_released_count=len(released),
        lines=lines,
    )
