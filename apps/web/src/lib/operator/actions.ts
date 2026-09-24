/**
 * How a form on the operator page becomes a change (DEC-109).
 *
 * Every action checks, in order: that the visitor passed Cloudflare Access,
 * that the form was posted from this site (a page elsewhere cannot make the
 * owner's browser submit it), and that its fields are the expected shape.
 * Only then is the engine asked, with the owner's email as the actor.
 */

export type ActionRequest =
    | { path: string; body: Record<string, unknown> }
    | { error: string };

export function postedFromHere(headers: Headers, expectedHost: string | null): boolean {
    const origin = headers.get("origin");
    const site = headers.get("sec-fetch-site");
    if (site && site !== "same-origin") return false;
    if (!origin) return site === "same-origin";
    try {
        return new URL(origin).host === expectedHost;
    } catch {
        return false;
    }
}

function text(form: FormData, name: string, max: number): string {
    const value = form.get(name);
    return typeof value === "string" ? value.trim().slice(0, max) : "";
}

/** Turns one posted form into one engine request, or says why not. */
export function actionFor(kind: string, id: string | undefined, form: FormData, actor: string): ActionRequest {
    if (kind === "note") {
        const target = text(form, "target", 320);
        const note = text(form, "text", 4000);
        if (!/^(order|customer|ticket|upload):\S{1,300}$/.test(target) || !note) return { error: "invalid note" };
        return { path: `/v1/operator/notes/${encodeURIComponent(target)}`, body: { actor, text: note } };
    }
    if (kind === "ticket") {
        if (!id || !/^t_[a-f0-9]{12}$/.test(id)) return { error: "invalid ticket" };
        const body: Record<string, unknown> = { actor };
        const status = text(form, "status", 20);
        if (status) {
            if (!["open", "answered", "resolved"].includes(status)) return { error: "invalid status" };
            body.status = status;
        }
        const orderId = text(form, "order_id", 80);
        if (orderId) {
            if (!/^order_[A-Za-z0-9_-]{1,64}$/.test(orderId)) return { error: "invalid order" };
            body.order_id = orderId;
        }
        const added = text(form, "added", 5);
        if (added) body.added = added === "true";
        if (Object.keys(body).length === 1) return { error: "nothing to change" };
        return { path: `/v1/operator/tickets/${id}`, body };
    }
    if (kind === "refund") {
        if (!id || !/^order_[A-Za-z0-9_-]{1,64}$/.test(id)) return { error: "invalid order" };
        return {
            path: `/v1/operator/orders/${id}/refund`,
            body: { actor, reference: text(form, "reference", 80) || null, undo: text(form, "undo", 5) === "true" },
        };
    }
    // --- Releases 2 and 3 (DEC-110, DEC-111) ------------------------------
    if (kind === "deadline") {
        if (!id || !/^[a-z0-9][a-z0-9_-]{1,120}$/.test(id)) return { error: "invalid examination" };
        const closesOn = text(form, "closes_on", 10);
        if (closesOn && !/^\d{4}-\d{2}-\d{2}$/.test(closesOn)) return { error: "invalid date" };
        return {
            path: `/v1/operator/deadlines/${id}`,
            body: { actor, closes_on: closesOn || null, note: text(form, "note", 300), auto_remind: text(form, "auto_remind", 5) === "yes" },
        };
    }
    if (kind === "coupon") {
        const code = text(form, "code", 32).toUpperCase();
        const couponKind = text(form, "kind", 10);
        const raw = Number(text(form, "value", 10));
        if (!/^[A-Z0-9_-]{2,32}$/.test(code) || !["percent", "flat", "free"].includes(couponKind) || !Number.isFinite(raw))
            return { error: "invalid coupon" };
        const maxUses = text(form, "max_uses", 7);
        const expires = text(form, "expires_on", 10);
        return {
            path: "/v1/operator/coupons",
            body: {
                actor,
                code,
                kind: couponKind,
                // The form asks for rupees; the engine counts paise.
                value: couponKind === "flat" ? Math.round(raw * 100) : couponKind === "free" ? 100 : Math.round(raw),
                partner: text(form, "partner", 120),
                max_uses: maxUses ? Number(maxUses) : null,
                expires_on: /^\d{4}-\d{2}-\d{2}$/.test(expires) ? expires : null,
            },
        };
    }
    if (kind === "coupon-active") {
        if (!id || !/^[A-Z0-9_-]{2,32}$/.test(id)) return { error: "invalid coupon" };
        return { path: `/v1/operator/coupons/${id}/active`, body: { actor, active: text(form, "active", 5) === "true" } };
    }
    if (kind === "campaign" || kind === "campaign-test" || kind === "exam-added") {
        const subject = text(form, "subject", 200);
        const body = text(form, "body", 20000);
        if (!subject || !body) return { error: "a subject and a message are needed" };
        if (kind === "campaign-test") {
            const to = text(form, "to", 254);
            if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(to)) return { error: "invalid test address" };
            return { path: "/v1/operator/campaigns/test", body: { actor, to, subject, body } };
        }
        const segment = kind === "exam-added" ? "asked_exam" : text(form, "segment", 40);
        if (!["all", "paid", "never_paid", "checkout_failed", "paid_exam", "asked_exam"].includes(segment)) return { error: "invalid segment" };
        if (text(form, "confirm", 5) !== "yes") return { error: "tick the box to confirm the send" };
        return {
            path: kind === "exam-added" ? "/v1/operator/exam-requests/notify" : "/v1/operator/campaigns",
            body: { actor, segment, target: text(form, "target", 200), subject, body },
        };
    }
    if (kind === "review") {
        if (!id || !/^order_[A-Za-z0-9_-]{1,64}$/.test(id)) return { error: "invalid order" };
        const status = text(form, "status", 10);
        if (!["pending", "approved", "rejected"].includes(status)) return { error: "invalid status" };
        return { path: `/v1/operator/reviews/${id}/status`, body: { actor, status } };
    }
    if (kind === "offer") {
        return { path: "/v1/operator/offers/review_reward", body: { actor, on: text(form, "on", 5) === "true" } };
    }
    return { error: "unknown action" };
}

/** What the toast says after an action succeeds (DEC-113). */
export function doneMessage(kind: string, form: FormData): string {
    const value = (name: string) => {
        const raw = form.get(name);
        return typeof raw === "string" ? raw.trim() : "";
    };
    switch (kind) {
        case "note":
            return "Note saved.";
        case "ticket":
            if (value("status")) return `Marked ${value("status")}.`;
            if (value("order_id")) return `Linked to ${value("order_id")}.`;
            if (value("added")) return value("added") === "true" ? "Marked as added." : "No longer marked as added.";
            return "Saved.";
        case "refund":
            return value("undo") === "true" ? "Refund mark removed." : "Marked refunded.";
        case "deadline":
            return value("closes_on") ? `Closing date set to ${value("closes_on")}.` : "Closing date cleared.";
        case "coupon":
            return `Code ${value("code").toUpperCase()} saved.`;
        case "coupon-active":
            return value("active") === "true" ? "Code switched on." : "Code switched off.";
        case "campaign":
            return "Sending started. Progress shows below.";
        case "campaign-test":
            return `Test sent to ${value("to")}.`;
        case "exam-added":
            return "Everyone who asked is being emailed.";
        case "review":
            return value("status") === "approved" ? "Review approved." : value("status") === "rejected" ? "Review rejected." : "Review updated.";
        case "offer":
            return value("on") === "true" ? "Review offer started." : "Review offer stopped.";
        default:
            return "Saved.";
    }
}
