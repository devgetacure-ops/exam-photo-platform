"""HTTP routes that exist only while billing is switched on (DEC-127).

Moved here unchanged from ``exam_photo.api.app``. Every route answers 404
while ``billing_enabled`` is off, so a free host exposes no way to quote,
charge, refund or redeem anything.

This module reads the application's shared ``service`` from
``exam_photo.api.app`` at call time, through ``_service()``, never as a name
bound at import: reloading ``app`` (as some tests do) builds a new service,
and a binding taken once would keep answering for the old one. ``app``
includes this router at the bottom of its module, after every helper
imported here exists.
"""

from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone
from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from exam_photo.api import app as _app
from exam_photo.api import marketing
from exam_photo.api import operator as operator_views
from exam_photo.api.app import (
    _OPERATOR,
    _coupon_state,
    _selected_kit_records,
)
from exam_photo.api.billing.payments import (
    SIGNATURE_HEADER,
    ReleaseInstruction,
    WebhookRejectedError,
    read_failed_payment,
    verify_and_read,
)
from exam_photo.api.billing.pricing import (
    PRICE_LADDER_PAISE,
    Discount,
    parse_ladder,
    price_variant,
    quote_for,
)
from exam_photo.api.billing.razorpay_orders import OrderCreationError, order_notes
from exam_photo.api.contracts import (
    KitOrderResponse,
    KitQuoteResponse,
    QuoteLineResponse,
)
from exam_photo.api.jobs import KIT_ID_REGEX, ProcessingJobRecord
from exam_photo.api.ledger import REVIEW_TAGS
from exam_photo.api.service import ApiProcessingService


def _service() -> ApiProcessingService:
    """The application's current service, looked up when a route runs."""
    return _app.service


def require_billing() -> None:
    """Refuse every paid route while the site runs free (DEC-127)."""
    if not _service().settings.billing_enabled:
        raise HTTPException(status_code=404, detail="Not found")


router: APIRouter = APIRouter(dependencies=[Depends(require_billing)])

#: Routes that serve the record of past orders and stay live while free: an
#: order paid before DEC-127 may still need its refund marked.
archive_router: APIRouter = APIRouter()


@router.get("/v1/kits/{kit_id}/quote", response_model=KitQuoteResponse)
def get_kit_quote(
    kit_id: str,
    job_ids: Annotated[Optional[List[str]], Query()] = None,
    coupon: Optional[str] = None,
) -> KitQuoteResponse:
    """What this kit costs, itemised (DEC-070).

    Read-only and safe to call on every render: it creates no order and
    reserves nothing, so the interface can show a price without committing the
    candidate to anything.
    """
    if not KIT_ID_REGEX.match(kit_id):
        raise HTTPException(status_code=400, detail="Invalid kit ID format")

    quote, coupon_status = _priced(
        kit_id, _selected_kit_records(kit_id, job_ids), coupon
    )
    return KitQuoteResponse(
        kit_id=kit_id,
        amount_paise=quote.amount_paise,
        price_variant=quote.price_variant,
        coupon_code=quote.coupon_code,
        discount_paise=quote.discount_paise,
        coupon_status=coupon_status,
        free_with_coupon=bool(
            coupon_status == "applied"
            and quote.amount_paise == 0
            and quote.chargeable_count
        ),
        list_amount_paise=quote.list_amount_paise,
        currency=quote.currency,
        chargeable_count=quote.chargeable_count,
        included_free_count=quote.included_free_count,
        already_released_count=quote.already_released_count,
        is_payable=quote.is_payable,
        payment_mode=(
            "simulator" if _service().settings.payment_simulator_enabled else "razorpay"
        ),
        lines=[
            QuoteLineResponse(
                job_id=line.job_id,
                requirement_id=line.requirement_id,
                requirement_type=line.requirement_type,
                chargeable=line.chargeable,
                reason=line.reason,
            )
            for line in quote.lines
        ],
    )


def _priced(
    kit_id: str, records: List[ProcessingJobRecord], coupon: Optional[str]
) -> tuple[Any, Optional[str]]:
    """The quote with the price test and any coupon applied (DEC-110, DEC-111).

    Both the quote and the order come through here, so the amount the
    candidate saw is the amount the order is created for.
    """
    ladder = parse_ladder(_service().settings.price_test_ladder)
    variant = (
        price_variant(kit_id, _service().settings.price_test_share) if ladder else "A"
    )
    status: Optional[str] = None
    discount: Optional[Discount] = None
    if coupon:
        found = _valid_coupon(coupon)
        if found is None:
            status = "invalid"
            # DEC-120: the operator sees which codes were tried and refused.
            try:
                _service().ledger.record_coupon_attempt(
                    coupon.strip().upper(), kit_id, _coupon_refusal(coupon)
                )
            except Exception:  # noqa: BLE001 - a broken ledger never blocks a sale
                pass
        else:
            discount = Discount(found["code"], found["kind"], int(found["value"]))
            status = "applied"
    quote = quote_for(
        records,
        ladder=ladder if variant == "B" and ladder else PRICE_LADDER_PAISE,
        variant=variant,
        discount=discount,
    )
    if status == "applied" and not quote.discount_paise:
        status = "no_effect"
    return quote, status


def _coupon_refusal(code: str) -> str:
    """Why `_valid_coupon` turned this code away."""
    normalised = code.strip().upper()
    if not re.fullmatch(r"[A-Z0-9_-]{2,32}", normalised):
        return "not_a_code"
    try:
        found = _service().ledger.coupon(normalised)
    except Exception:  # noqa: BLE001
        return "unknown"
    return _coupon_state(found) if found else "unknown"


def _valid_coupon(code: str) -> Optional[dict[str, Any]]:
    normalised = code.strip().upper()
    if not re.fullmatch(r"[A-Z0-9_-]{2,32}", normalised):
        return None
    try:
        found = _service().ledger.coupon(normalised)
    except Exception:  # noqa: BLE001 - a broken ledger never blocks a sale
        return None
    if not found or not found["active"]:
        return None
    if found["max_uses"] is not None and found["uses"] >= found["max_uses"]:
        return None
    if (
        found["expires_on"]
        and found["expires_on"] < datetime.now(timezone.utc).date().isoformat()
    ):
        return None
    return found


@router.post("/v1/kits/{kit_id}/order", response_model=KitOrderResponse)
def create_kit_order(
    kit_id: str,
    job_ids: Annotated[Optional[List[str]], Query()] = None,
    coupon: Optional[str] = None,
) -> KitOrderResponse:
    """Create a Razorpay order for this kit, at a price we computed (DEC-070).

    This is what makes DEC-069's webhook safe on live keys. The amount comes
    from the jobs on disk, never from the caller, so a browser cannot ask to
    be charged less; and the order carries the kit in its `notes`, which is
    the only link between paying and receiving.
    """
    if not KIT_ID_REGEX.match(kit_id):
        raise HTTPException(status_code=400, detail="Invalid kit ID format")

    records = _selected_kit_records(kit_id, job_ids)
    quote, _coupon_status = _priced(kit_id, records, coupon)
    if not quote.is_payable and quote.discount_paise:
        raise HTTPException(
            status_code=409,
            detail="This code makes the kit free: claim it instead of paying.",
        )
    if not quote.is_payable:
        # Nothing to charge for: an empty kit, one already paid, or one that
        # holds only document work, which is free. Sending a zero-amount order
        # to a payment gateway would be asking it to take nothing.
        raise HTTPException(
            status_code=409,
            detail="There is nothing to pay for in this kit.",
        )

    try:
        order = _service().order_gateway.create_order(
            amount_paise=quote.amount_paise,
            currency=quote.currency,
            notes=order_notes(kit_id),
            receipt=f"kit-{kit_id}",
        )
    except OrderCreationError as err:
        print(f"razorpay order creation failed for {kit_id}: {err}")
        raise HTTPException(
            status_code=503,
            detail="Payment could not be started. Please try again shortly.",
        ) from None

    # DEC-071: remember exactly what was priced, so the payment releases that
    # set and not whatever the kit holds when the webhook arrives. Every live
    # job is recorded, not only the charged ones -- document work is free
    # *with* a purchase, so it is delivered by the same payment.
    priced = [line.job_id for line in quote.lines]
    try:
        _service().orders.create(
            order_id=order.order_id,
            kit_id=kit_id,
            job_ids=priced,
            amount_paise=order.amount_paise,
            currency=order.currency,
            items=_service().order_items(
                [record for record in records if record.job_id in priced]
            ),
            price_variant=quote.price_variant,
            coupon_code=quote.coupon_code,
            discount_paise=quote.discount_paise,
        )
    except (ValueError, OSError) as err:
        # The order exists at Razorpay but we could not record it. Refusing is
        # right: paying against an order we cannot resolve would release
        # nothing and take the money.
        print(f"could not record order {order.order_id} for {kit_id}: {err}")
        raise HTTPException(
            status_code=503,
            detail="Payment could not be started. Please try again shortly.",
        ) from None

    return KitOrderResponse(
        kit_id=kit_id,
        order_id=order.order_id,
        amount_paise=order.amount_paise,
        currency=order.currency,
        key_id=order.key_id,
    )


class RefundMark(BaseModel):
    actor: str = "operator"
    reference: Optional[str] = None
    undo: bool = False


@archive_router.post("/v1/operator/orders/{order_id}/refund", dependencies=_OPERATOR)
def operator_mark_refund(order_id: str, mark: RefundMark) -> dict[str, Any]:
    order = _service().orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if mark.undo:
        _service().ledger.unmark_refunded(order_id)
        _service().ledger.log(mark.actor, "refund unmarked", f"order:{order_id}")
    else:
        _service().ledger.mark_refunded(
            order_id, mark.actor, mark.reference, order.amount_paise
        )
        _service().ledger.log(mark.actor, "marked refunded", f"order:{order_id}")
    return {"ok": True}


class CouponIn(BaseModel):
    actor: str = "operator"
    code: str
    kind: str
    value: int
    partner: str = ""
    max_uses: Optional[int] = None
    expires_on: Optional[str] = None


@router.post("/v1/operator/coupons", dependencies=_OPERATOR)
def operator_save_coupon(coupon: CouponIn) -> dict[str, Any]:
    code = coupon.code.strip().upper()
    if not re.fullmatch(r"[A-Z0-9_-]{2,32}", code):
        raise HTTPException(
            status_code=422, detail="Codes are 2-32 letters, digits, - or _"
        )
    if coupon.kind == "free":
        coupon.value = 100
    if coupon.kind == "percent" and not 1 <= coupon.value <= 90:
        raise HTTPException(status_code=422, detail="A percentage is 1 to 90")
    if coupon.kind == "flat" and not 100 <= coupon.value <= 100000:
        raise HTTPException(
            status_code=422, detail="A flat discount is 100 to 100000 paise"
        )
    if coupon.kind not in ("percent", "flat", "free"):
        raise HTTPException(status_code=422, detail="kind is percent, flat or free")
    _service().ledger.save_coupon(
        code,
        coupon.kind,
        coupon.value,
        coupon.partner,
        coupon.max_uses,
        coupon.expires_on,
    )
    _service().ledger.log(coupon.actor, f"saved coupon {code}", f"coupon:{code}")
    return {"ok": True, "code": code}


class ActiveIn(BaseModel):
    actor: str = "operator"
    active: bool


@router.post("/v1/operator/coupons/{code}/active", dependencies=_OPERATOR)
def operator_coupon_active(code: str, change: ActiveIn) -> dict[str, Any]:
    if _service().ledger.coupon(code) is None:
        raise HTTPException(status_code=404, detail="Unknown coupon")
    _service().ledger.set_coupon_active(code, change.active)
    _service().ledger.log(
        change.actor,
        f"coupon {'enabled' if change.active else 'disabled'}",
        f"coupon:{code}",
    )
    return {"ok": True}


class ReviewIn(BaseModel):
    order_id: str
    rating: int = Field(ge=1, le=5)
    tags: List[str] = Field(default_factory=list)
    comment: str = ""
    name: str = ""
    may_publish: bool = False


class SignedReviewIn(ReviewIn):
    token: str


def _save_review(
    review: ReviewIn, source: str, kit_id: Optional[str]
) -> dict[str, Any]:
    """Store a review and, while the offer runs, hand back a free-files code (DEC-112)."""
    order = _service().orders.get(review.order_id)
    if order is None or not order.paid_at:
        raise HTTPException(status_code=404, detail="Paid order not found")
    saved = _service().ledger.record_review(
        order.order_id,
        rating=review.rating,
        tags=review.tags,
        comment=review.comment,
        name=review.name,
        may_publish=review.may_publish,
        source=source,
        kit_id=kit_id or order.kit_id,
    )
    reward = saved.get("reward_code")
    # A free order never earns another free order, and each person earns one.
    if (
        not reward
        and _service().ledger.offer_on("review_reward")
        and order.amount_paise > 0
    ):
        # One code per person, and a person is whoever shares an address or
        # a phone number with an earlier reward (owner, 2 October): a new
        # email on the same phone used to earn a code each time. The phone is
        # the one Razorpay collected at checkout; nothing new is asked for.
        emails = operator_views.order_emails(order)
        phones = operator_views.order_phones(order)
        known = [*emails, *(f"tel:{phone}" for phone in phones)]
        if not _service().ledger.reward_already_given(
            order.order_id, known
        ) and not _phone_already_rewarded(order.order_id, phones):
            reward = _service().ledger.issue_reward(order.order_id, known)
            _service().ledger.set_reward_code(order.order_id, reward)
    return {"ok": True, "review": saved, "reward_code": reward}


def _reward_on_offer(order: Any) -> bool:
    """Whether rating this order would earn a code, so the page may say so.

    The banner used to promise free files to anyone with a paid order while
    the offer ran, including someone who already held their one code; they
    rated and, correctly, got nothing (owner, 2 October). The promise is now
    made only where `_save_review` would keep it.
    """
    if not _service().ledger.offer_on("review_reward") or order.amount_paise <= 0:
        return False
    # The order that earned the code is still within the offer: its page shows
    # the code it was given.
    own = _service().ledger.review(order.order_id)
    if own and own.get("reward_code"):
        return True
    emails = operator_views.order_emails(order)
    phones = operator_views.order_phones(order)
    known = [*emails, *(f"tel:{phone}" for phone in phones)]
    return not _service().ledger.reward_already_given(
        order.order_id, known
    ) and not _phone_already_rewarded(order.order_id, phones)


def _phone_already_rewarded(order_id: str, phones: list[str]) -> bool:
    """Whether an earlier reward went to an order paid from one of these phones.

    Rewards issued before phones were recorded with them name only addresses,
    so the phone is read from the order each one was issued for.
    """
    if not phones:
        return False
    for coupon in _service().ledger.coupons():
        earlier = coupon.get("issued_for_order")
        if coupon.get("source") != "reward" or not earlier or earlier == order_id:
            continue
        rewarded = _service().orders.get(str(earlier))
        if rewarded and set(operator_views.order_phones(rewarded)) & set(phones):
            return True
    return False


@router.get("/v1/kits/{kit_id}/review")
def get_kit_review(kit_id: str, order_id: str) -> dict[str, Any]:
    """The review box's state for a paid order in this kit (DEC-112)."""
    if not KIT_ID_REGEX.match(kit_id):
        raise HTTPException(status_code=400, detail="Invalid kit ID format")
    order = _service().orders.get(order_id)
    if order is None or order.kit_id != kit_id or not order.paid_at:
        raise HTTPException(status_code=404, detail="Paid order not found")
    existing = _service().ledger.review(order_id)
    return {
        "review": existing,
        "reward_code": existing.get("reward_code") if existing else None,
        "offer": _reward_on_offer(order),
        "tags": REVIEW_TAGS,
    }


@router.post("/v1/kits/{kit_id}/review")
def post_kit_review(kit_id: str, review: ReviewIn) -> dict[str, Any]:
    """A review from the downloads screen. The kit id is the proof of purchase:
    only the browser that paid holds it, and the order must belong to it."""
    if not KIT_ID_REGEX.match(kit_id):
        raise HTTPException(status_code=400, detail="Invalid kit ID format")
    order = _service().orders.get(review.order_id)
    if order is None or order.kit_id != kit_id:
        raise HTTPException(status_code=404, detail="Paid order not found")
    return _save_review(review, "checkout", kit_id)


@router.post("/v1/feedback")
def record_feedback(feedback: SignedReviewIn) -> dict[str, Any]:
    """The delivery email's "did it work?" link, signed per order (DEC-111)."""
    if not marketing.verify(_service(), "feedback", feedback.order_id, feedback.token):
        raise HTTPException(status_code=403, detail="This link is not valid.")
    return _save_review(feedback, "email", None)


@router.get("/v1/feedback")
def get_feedback(order_id: str, token: str) -> dict[str, Any]:
    """What the emailed link's order has already said (owner, 1 October).

    The email asks for a rating the downloads screen may already have taken.
    The page shows that rating and its one code instead of an empty form that
    reads as a second offer; `_save_review` never issues a second code either.
    """
    if not marketing.verify(_service(), "feedback", order_id, token):
        raise HTTPException(status_code=403, detail="This link is not valid.")
    order = _service().orders.get(order_id)
    if order is None or not order.paid_at:
        raise HTTPException(status_code=404, detail="Paid order not found")
    existing = _service().ledger.review(order_id)
    return {
        "review": existing,
        "reward_code": existing.get("reward_code") if existing else None,
        "offer": _reward_on_offer(order),
        "tags": REVIEW_TAGS,
    }


class OfferIn(BaseModel):
    actor: str = "operator"
    on: bool


@router.post("/v1/operator/offers/review_reward", dependencies=_OPERATOR)
def operator_set_review_offer(change: OfferIn) -> dict[str, Any]:
    _service().ledger.set_offer("review_reward", change.on)
    _service().ledger.log(
        change.actor,
        "review reward offer " + ("started" if change.on else "stopped"),
        None,
    )
    return {"ok": True, "on": change.on}


@router.post("/v1/kits/{kit_id}/claim-free")
def claim_free_kit(
    kit_id: str,
    coupon: str,
    job_ids: Annotated[Optional[List[str]], Query()] = None,
) -> dict[str, Any]:
    """Release a kit whose code makes it free, without Razorpay (DEC-112).

    Razorpay cannot take nothing, so a free order is settled here. The code is
    taken atomically before anything is released: two tabs racing the same
    single-use code release once.
    """
    if not KIT_ID_REGEX.match(kit_id):
        raise HTTPException(status_code=400, detail="Invalid kit ID format")
    records = _selected_kit_records(kit_id, job_ids)
    quote, status = _priced(kit_id, records, coupon)
    if status != "applied" or quote.amount_paise != 0 or not quote.chargeable_count:
        raise HTTPException(
            status_code=409, detail="This code does not make this kit free."
        )
    code = str(quote.coupon_code)
    if not _service().ledger.claim_coupon(code):
        raise HTTPException(status_code=409, detail="This code has already been used.")
    order_id = f"order_free_{secrets.token_hex(8)}"
    priced = [line.job_id for line in quote.lines]
    _service().orders.create(
        order_id=order_id,
        kit_id=kit_id,
        job_ids=priced,
        amount_paise=0,
        currency=quote.currency,
        items=_service().order_items([r for r in records if r.job_id in priced]),
        price_variant=quote.price_variant,
        coupon_code=code,
        discount_paise=quote.discount_paise,
    )
    instruction = ReleaseInstruction(
        event="coupon.free",
        payment_id=f"coupon:{code}",
        order_id=order_id,
        amount=0,
        currency=quote.currency,
        kit_ids=[kit_id],
    )
    _service().orders.mark_paid(order_id, instruction.payment_id)
    _service().orders.record_payer(order_id, None, None, "coupon")
    _service().usage.record_purchase(kit_id)
    released = []
    for job_id in priced:
        try:
            _service().release_job(job_id, payment=instruction)
            released.append(job_id)
        except KeyError:
            continue
    _service().ledger.log(
        "candidate", f"claimed free kit with {code}", f"order:{order_id}"
    )
    return {"order_id": order_id, "released": released}


@router.post("/v1/payments/razorpay/webhook")
async def razorpay_webhook(request: Request) -> JSONResponse:
    """Release the files a verified Razorpay payment paid for (DEC-069).

    This is the caller DEC-063 anticipated when it left `release_job` with
    nothing calling it. What makes it acceptable where a plain release route
    was not is that the shared-secret signature is checked over the **raw
    request body, before the payload is parsed at all** -- so an unsigned
    request never reaches any code that reads what it is asking for.

    Deliberately not behind the operator token. Razorpay cannot send one, and
    the signature is a stronger proof of origin than a bearer token would be.
    """
    body = await request.body()
    signature = request.headers.get(SIGNATURE_HEADER, "")

    try:
        instruction = verify_and_read(
            body, signature, _service().settings.razorpay_webhook_secret
        )
    except WebhookRejectedError as err:
        # 400 with nothing that would help a forger narrow down which check
        # failed. The reason goes to the operator's log, not to the caller.
        print(f"razorpay webhook rejected: {err.reason}")
        raise HTTPException(status_code=400, detail="Webhook rejected") from None

    if instruction is None:
        # A real event this service does not act on. Acknowledged, because
        # Razorpay retries anything it is not told arrived. A failed payment
        # is still worth remembering: it is the follow-up list (DEC-109).
        failed = read_failed_payment(body)
        if failed and failed.get("order_id"):
            _service().orders.record_failed_payment(str(failed["order_id"]), failed)
            try:
                _service().ledger.contact_seen(
                    failed.get("email"), "checkout_failed", failed.get("contact")
                )
            except Exception as err:  # noqa: BLE001
                print(f"ledger: failed payer not recorded: {err}")
            return JSONResponse({"status": "recorded"})
        return JSONResponse({"status": "ignored"})

    if instruction.names_nothing:
        # Signed by Razorpay, so the money moved, but the order carried no
        # job or kit in its notes and nothing can be released. Acknowledged
        # rather than refused -- retrying will not add the notes -- and
        # logged loudly, because it means an order was created without them
        # and a candidate has paid for something they will not receive.
        print(
            "razorpay webhook named no job or kit: "
            f"payment={instruction.payment_id} order={instruction.order_id}"
        )
        return JSONResponse({"status": "no_targets"})

    outcome = _service().apply_release_instruction(instruction)
    if outcome["unknown"]:
        print(
            f"razorpay webhook could not release {outcome['unknown']} "
            f"for payment={instruction.payment_id}"
        )
    return JSONResponse({"status": "released", **outcome})


@router.post("/v1/payments/simulator/{order_id}/pay")
def simulate_payment(order_id: str) -> JSONResponse:
    """Settle a simulated order, for testing checkout without Razorpay (DEC-089).

    Answers 404 unless the simulator is switched on and no Razorpay credentials
    are set, so on a real deployment this route does not exist in any way a
    caller can tell. It releases through the same code a verified webhook uses.
    """
    try:
        outcome = _service().simulate_payment(order_id)
    except (PermissionError, KeyError):
        raise HTTPException(status_code=404, detail="Not Found") from None
    return JSONResponse({"status": "released", **outcome})
