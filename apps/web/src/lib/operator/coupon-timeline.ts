/**
 * A coupon's whole history, in order, in words (DEC-120).
 *
 * The coupons page used to show a code and a count. The owner asked to see
 * everything that happened to each one: when it was made, each time it was
 * used and on which order, each time it was switched, each time someone tried
 * it and was turned away, and when it stopped being usable.
 */

export type CouponStatus = "unused" | "used" | "used_up" | "expired" | "switched_off";

export interface CouponRecord {
    code: string;
    kind: string;
    value: number;
    partner: string | null;
    active: number;
    max_uses: number | null;
    uses: number;
    expires_on: string | null;
    created_at: string;
    source: string;
    issued_for_order: string | null;
    orders: number;
    revenue_paise: number;
    discount_paise: number;
    status?: CouponStatus;
    redemptions?: { order_id: string; at: string; amount_paise: number; discount_paise: number }[];
    changes?: { at: string; actor: string; action: string }[];
    attempts?: { code: string; kit_id: string; reason: string; at: string }[];
}

export interface TimelineEvent {
    at: string;
    kind: "created" | "used" | "switched" | "refused" | "ended";
    text: string;
    /** An order this event points at, for a link. */
    orderId?: string;
}

export const STATUS_WORDS: Record<CouponStatus, { label: string; tone: "neutral" | "good" | "warn" | "bad" | "info" }> = {
    unused: { label: "Not used yet", tone: "info" },
    used: { label: "Used, still valid", tone: "good" },
    used_up: { label: "Used up", tone: "neutral" },
    expired: { label: "Expired", tone: "warn" },
    switched_off: { label: "Switched off", tone: "bad" },
};

const REFUSALS: Record<string, string> = {
    unknown: "no such code",
    not_a_code: "not a valid code",
    switched_off: "it was switched off",
    expired: "it had expired",
    used_up: "it had no uses left",
};

export function refusalWords(reason: string): string {
    return REFUSALS[reason] ?? "it could not be used";
}

function rupees(paise: number): string {
    return `₹${(paise / 100).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
}

/** Older ledgers may not send a status; work it out the way the server does. */
export function statusOf(coupon: CouponRecord, today: string): CouponStatus {
    if (coupon.status) return coupon.status;
    if (!coupon.active) return "switched_off";
    if (coupon.expires_on && coupon.expires_on < today) return "expired";
    if (coupon.max_uses != null && coupon.uses >= coupon.max_uses) return "used_up";
    return coupon.uses ? "used" : "unused";
}

export function couponTimeline(coupon: CouponRecord, today: string): TimelineEvent[] {
    const events: TimelineEvent[] = [];
    events.push({
        at: coupon.created_at,
        kind: "created",
        text: coupon.issued_for_order
            ? "Created as a reward for a review"
            : `Created${coupon.partner ? ` for ${coupon.partner}` : ""}`,
        orderId: coupon.issued_for_order ?? undefined,
    });
    // The first save is the creation above (logged a moment after it); only a
    // later one is an edit.
    let saves = 0;
    for (const change of coupon.changes ?? []) {
        if (change.action === "coupon disabled") {
            events.push({ at: change.at, kind: "switched", text: `Switched off by ${change.actor}` });
        } else if (change.action === "coupon enabled") {
            events.push({ at: change.at, kind: "switched", text: `Switched on by ${change.actor}` });
        } else if (change.action.startsWith("saved coupon")) {
            saves += 1;
            if (saves > 1) events.push({ at: change.at, kind: "switched", text: `Edited by ${change.actor}` });
        }
    }
    const used = coupon.redemptions ?? [];
    for (const redemption of used) {
        events.push({
            at: redemption.at,
            kind: "used",
            text:
                `Used: took ${rupees(redemption.discount_paise)} off` +
                (redemption.amount_paise > 0 ? `, ${rupees(redemption.amount_paise)} paid` : ", nothing left to pay"),
            orderId: redemption.order_id,
        });
    }
    for (const attempt of coupon.attempts ?? []) {
        events.push({ at: attempt.at, kind: "refused", text: `Tried and refused: ${refusalWords(attempt.reason)}` });
    }
    events.sort((a, b) => a.at.localeCompare(b.at));

    const status = statusOf(coupon, today);
    if (status === "used_up") {
        const last = used[used.length - 1]?.at ?? events[events.length - 1].at;
        events.push({ at: last, kind: "ended", text: "No uses left: it can no longer be used" });
    } else if (status === "expired" && coupon.expires_on) {
        events.push({
            at: `${coupon.expires_on}T23:59:59`,
            kind: "ended",
            text: `Expired: ${coupon.expires_on} was its last day`,
        });
    }
    return events;
}
