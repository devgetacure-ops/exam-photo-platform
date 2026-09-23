import { engineBase } from "../../../lib/operator/engine";

export const runtime = "nodejs";

/** The feedback form's post, passed to the engine, which checks the signature (DEC-111). */
export async function POST(request: Request) {
    const site = request.headers.get("sec-fetch-site");
    if (site && site !== "same-origin") return new Response("Not allowed", { status: 403 });
    const form = await request.formData().catch(() => null);
    const orderId = String(form?.get("order_id") ?? "");
    const token = String(form?.get("token") ?? "");
    if (!/^order_[A-Za-z0-9_-]{1,64}$/.test(orderId) || !/^[a-f0-9]{32}$/.test(token))
        return new Response("This link is incomplete.", { status: 400 });
    const body = {
        order_id: orderId,
        token,
        worked: form?.get("worked") !== "no",
        comment: String(form?.get("comment") ?? "").slice(0, 1000),
        may_publish: form?.get("may_publish") === "yes",
    };
    try {
        const response = await fetch(`${engineBase()}/v1/feedback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
            signal: AbortSignal.timeout(10_000),
        });
        if (!response.ok) return new Response("We could not save that. Please reply to our email instead.", { status: 400 });
    } catch {
        return new Response("We could not save that right now. Please try again.", { status: 502 });
    }
    return new Response(null, {
        status: 303,
        headers: { Location: `/feedback?sent=1&o=${encodeURIComponent(orderId)}&t=${token}` },
    });
}
