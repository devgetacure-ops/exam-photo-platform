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
    return { error: "unknown action" };
}
