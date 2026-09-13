"""Creating a Razorpay order, server-side, at a price we computed.

DEC-070. This is the companion DEC-069 said the webhook could not go live
without. The webhook proves Razorpay sent an event; it cannot prove the
candidate paid the asking price, because nothing in the engine knew the price.
An order created *here*, at an amount from `pricing.py`, closes that: Razorpay
guarantees a payment matches its order, so a verified `order.paid` for an order
we created is proof of our amount.

The gateway is a protocol with two implementations -- a real HTTP one and a
fake -- for the reason the rest of this codebase uses that shape: a test that
has to reach api.razorpay.com is a test that will fail on a train, and a
payment path most needs the tests that always run.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

RAZORPAY_ORDERS_URL = "https://api.razorpay.com/v1/orders"

#: Razorpay caps `notes` values at 512 characters. A kit id is far shorter, but
#: the cap is asserted rather than assumed, because notes silently truncating
#: is how the webhook would later find an id it cannot resolve.
MAX_NOTE_LENGTH = 512


class OrderCreationError(RuntimeError):
    """Razorpay would not create the order.

    Carries a message for the operator's log. The candidate is told the
    payment could not be started, and nothing more: a gateway's own error text
    is not something to render into a page.
    """


@dataclass(frozen=True)
class CreatedOrder:
    """The order Razorpay created, as Checkout needs it."""

    order_id: str
    amount_paise: int
    currency: str
    #: The publishable key. Safe to hand to the browser -- it identifies the
    #: account and authorises nothing on its own.
    key_id: str


class OrderGateway(Protocol):
    """Creates an order and returns what Checkout needs to open."""

    def create_order(
        self, amount_paise: int, currency: str, notes: Dict[str, str], receipt: str
    ) -> CreatedOrder: ...


class UnconfiguredOrderGateway:
    """The gateway a host gets when it has set no Razorpay credentials.

    Refuses rather than pretending, following DEC-060: a deployment with no
    keys must fail loudly at the point of use instead of returning something
    that looks like an order.
    """

    def create_order(
        self, amount_paise: int, currency: str, notes: Dict[str, str], receipt: str
    ) -> CreatedOrder:
        raise OrderCreationError("Razorpay API credentials are not configured")


class HttpOrderGateway:
    """Creates orders against Razorpay's Orders API over HTTPS."""

    def __init__(self, key_id: str, key_secret: str, timeout_seconds: float = 10.0):
        self._key_id = key_id
        self._key_secret = key_secret
        self._timeout = timeout_seconds

    def create_order(
        self, amount_paise: int, currency: str, notes: Dict[str, str], receipt: str
    ) -> CreatedOrder:
        import httpx

        for key, value in notes.items():
            if len(value) > MAX_NOTE_LENGTH:
                raise OrderCreationError(f"note {key!r} is too long for Razorpay")

        payload: Dict[str, Any] = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt[:40],
            "notes": notes,
            # Capture immediately. DEC-069 releases only on capture, so leaving
            # this manual would mean a candidate pays, the payment is merely
            # authorised, and nothing is ever released.
            "payment_capture": 1,
        }

        try:
            response = httpx.post(
                RAZORPAY_ORDERS_URL,
                json=payload,
                auth=(self._key_id, self._key_secret),
                timeout=self._timeout,
                headers={"Content-Type": "application/json"},
            )
        except Exception as err:  # network, DNS, TLS, timeout
            raise OrderCreationError(f"could not reach Razorpay: {err}") from err

        if response.status_code >= 400:
            raise OrderCreationError(
                f"Razorpay refused the order: {response.status_code} "
                f"{response.text[:300]}"
            )

        try:
            body = response.json()
        except (ValueError, json.JSONDecodeError) as err:
            raise OrderCreationError("Razorpay returned a non-JSON order") from err

        order_id = body.get("id")
        if not order_id:
            raise OrderCreationError("Razorpay returned an order with no id")

        # Read the amount back from Razorpay rather than echoing what we sent.
        # If the two ever disagree, the one the candidate will actually be
        # charged is theirs, and that is the one the webhook will later verify.
        return CreatedOrder(
            order_id=str(order_id),
            amount_paise=int(body.get("amount", amount_paise)),
            currency=str(body.get("currency", currency)),
            key_id=self._key_id,
        )


#: The publishable "key" a simulated order carries. The browser reads it as
#: the signal to open the test sheet instead of Razorpay's window (DEC-089).
SIMULATOR_KEY_ID = "simulator"

#: Every simulated order id starts with this, so a real Razorpay order can
#: never be settled by the simulator.
SIMULATED_ORDER_PREFIX = "order_sim"


class SimulatedOrderGateway:
    """Creates orders that exist only in this service's own registry (DEC-089).

    For trying the whole checkout on a machine with no Razorpay account: the
    order is priced and recorded exactly as a real one is, and nothing leaves
    the process. It is settled by `ApiProcessingService.simulate_payment`,
    which releases through the same path a verified webhook does.
    """

    def create_order(
        self, amount_paise: int, currency: str, notes: Dict[str, str], receipt: str
    ) -> CreatedOrder:
        for key, value in notes.items():
            if len(value) > MAX_NOTE_LENGTH:
                raise OrderCreationError(f"note {key!r} is too long for Razorpay")
        return CreatedOrder(
            order_id=f"{SIMULATED_ORDER_PREFIX}{secrets.token_hex(7)}",
            amount_paise=amount_paise,
            currency=currency,
            key_id=SIMULATOR_KEY_ID,
        )


class ConflictingSimulatorGateway:
    """What a host gets when it asks for the simulator beside real credentials.

    Refuses, because a simulator running where real keys are configured means
    a real deployment was switched into test mode by mistake, and settling
    orders for free there would give paid files away.
    """

    def create_order(
        self, amount_paise: int, currency: str, notes: Dict[str, str], receipt: str
    ) -> CreatedOrder:
        raise OrderCreationError(
            "the payment simulator refuses to run beside Razorpay credentials"
        )


def gateway_for(
    key_id: str,
    key_secret: str,
    timeout_seconds: float = 10.0,
    simulator: bool = False,
) -> OrderGateway:
    """The gateway a host's configuration entitles it to."""
    if simulator:
        if key_id or key_secret:
            return ConflictingSimulatorGateway()
        return SimulatedOrderGateway()
    if key_id and key_secret:
        return HttpOrderGateway(key_id, key_secret, timeout_seconds)
    return UnconfiguredOrderGateway()


def order_notes(kit_id: str, job_ids: Optional[list[str]] = None) -> Dict[str, str]:
    """The notes the webhook will read back to know what to release.

    This is the one link between paying and receiving (DEC-069): an order
    without them is a payment that takes the money and delivers nothing. It is
    built here, next to the order, rather than left to a caller to remember.
    """
    notes = {"kit_id": kit_id}
    if job_ids:
        notes["job_ids"] = ",".join(job_ids)
    return notes
