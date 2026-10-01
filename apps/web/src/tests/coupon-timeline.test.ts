import { describe, expect, it } from "vitest";

import { couponTimeline, statusOf, type CouponRecord } from "../lib/operator/coupon-timeline";

/** A coupon's whole history is on the page, in order (DEC-120). */

function coupon(overrides: Partial<CouponRecord> = {}): CouponRecord {
    return {
        code: "FRIEND",
        kind: "free",
        value: 100,
        partner: "A friend",
        active: 1,
        max_uses: 1,
        uses: 0,
        expires_on: null,
        created_at: "2026-10-01T09:00:00+00:00",
        source: "manual",
        issued_for_order: null,
        orders: 0,
        revenue_paise: 0,
        discount_paise: 0,
        ...overrides,
    };
}

describe("a coupon's timeline", () => {
    it("starts with when it was made, and says nothing else for a new code", () => {
        const events = couponTimeline(coupon({ status: "unused" }), "2026-10-02");
        expect(events.map((e) => e.text)).toEqual(["Created for A friend"]);
    });

    it("tells created, refused, used, switched and ended in the order they happened", () => {
        const events = couponTimeline(
            coupon({
                status: "switched_off",
                active: 0,
                uses: 1,
                changes: [
                    // Logged a moment after the row was written: still the creation.
                    { at: "2026-10-01T09:00:00.4+00:00", actor: "owner", action: "saved coupon FRIEND" },
                    { at: "2026-10-01T12:00:00+00:00", actor: "owner", action: "coupon disabled" },
                ],
                redemptions: [{ order_id: "order_A", at: "2026-10-01T10:00:00+00:00", amount_paise: 0, discount_paise: 300 }],
                attempts: [{ code: "FRIEND", kit_id: "kit_b", reason: "used_up", at: "2026-10-01T11:00:00+00:00" }],
            }),
            "2026-10-02",
        );
        expect(events.map((e) => e.text)).toEqual([
            "Created for A friend",
            "Used: took ₹3 off, nothing left to pay",
            "Tried and refused: it had no uses left",
            "Switched off by owner",
        ]);
        expect(events[1].orderId).toBe("order_A");
    });

    it("says a review reward is one, and links the order that earned it", () => {
        const [created] = couponTimeline(
            coupon({ source: "reward", partner: "Review reward", issued_for_order: "order_R", status: "unused" }),
            "2026-10-02",
        );
        expect(created).toMatchObject({ text: "Created as a reward for a review", orderId: "order_R" });
    });

    it("ends a code that has run out or run past its last day", () => {
        const spent = couponTimeline(
            coupon({
                status: "used_up",
                uses: 1,
                redemptions: [{ order_id: "order_A", at: "2026-10-01T10:00:00+00:00", amount_paise: 200, discount_paise: 100 }],
            }),
            "2026-10-02",
        );
        expect(spent.map((e) => e.text).slice(-2)).toEqual([
            "Used: took ₹1 off, ₹2 paid",
            "No uses left: it can no longer be used",
        ]);
        const lapsed = couponTimeline(coupon({ status: "expired", expires_on: "2026-09-30" }), "2026-10-02");
        expect(lapsed[lapsed.length - 1].text).toBe("Expired: 2026-09-30 was its last day");
    });

    it("works out the status itself when the server sends none", () => {
        expect(statusOf(coupon({ active: 0 }), "2026-10-02")).toBe("switched_off");
        expect(statusOf(coupon({ expires_on: "2026-09-30" }), "2026-10-02")).toBe("expired");
        expect(statusOf(coupon({ uses: 1 }), "2026-10-02")).toBe("used_up");
        expect(statusOf(coupon({ uses: 1, max_uses: null }), "2026-10-02")).toBe("used");
        expect(statusOf(coupon(), "2026-10-02")).toBe("unused");
    });
});
