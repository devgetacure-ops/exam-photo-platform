import { operatorFromHeaders } from "../../../../lib/operator/access";
import { actionFor, doneMessage, postedFromHere } from "../../../../lib/operator/actions";
import { safeBack } from "../../../../lib/operator/data";
import { enginePost } from "../../../../lib/operator/engine";

export const runtime = "nodejs";

function back(to: string, params: Record<string, string>): Response {
    const url = new URL(to, "http://operator.local");
    for (const [key, value] of Object.entries(params)) url.searchParams.set(key, value);
    return new Response(null, { status: 303, headers: { Location: `${url.pathname}${url.search}` } });
}

/**
 * `/admin/actions/{kind}[/{id}]`, posted by the console's forms (DEC-109,
 * DEC-113). Returns to the page it came from with a `done` or `failed`
 * message, which the console shows as a toast.
 */
export async function POST(request: Request, { params }: { params: Promise<{ action: string[] }> }) {
    const actor = await operatorFromHeaders(request.headers);
    if (!actor) return new Response("Not found", { status: 404 });
    if (!postedFromHere(request.headers, request.headers.get("host")))
        return new Response("This form must be sent from the operator page.", { status: 403 });

    const [kind, id] = (await params).action;
    const form = await request.formData();
    const to = safeBack(form.get("back"));
    const planned = actionFor(kind, id, form, actor);
    if ("error" in planned) return back(to, { failed: `Not saved: ${planned.error}.` });

    try {
        const response = await enginePost(planned.path, planned.body);
        if (!response.ok) {
            const detail = await response
                .json()
                .then((body: { detail?: unknown }) => (typeof body.detail === "string" ? body.detail : ""))
                .catch(() => "");
            return back(to, { failed: detail || `The engine refused (${response.status}).` });
        }
    } catch {
        return back(to, { failed: "The engine could not be reached. Nothing was changed." });
    }

    const extra: Record<string, string> = { done: doneMessage(kind, form) };
    // A test send returns to the composer with what was typed still in it.
    if (form.get("keep_draft") === "yes") {
        const subject = String(form.get("subject") ?? "");
        const text = String(form.get("body") ?? "");
        if (subject.length + text.length < 4000) Object.assign(extra, { subject, body: text });
    }
    return back(to, extra);
}
