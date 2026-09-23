import { operatorFromHeaders } from "../../../../lib/operator/access";
import { actionFor, postedFromHere } from "../../../../lib/operator/actions";
import { safeBack } from "../../../../lib/operator/data";
import { enginePost } from "../../../../lib/operator/engine";

export const runtime = "nodejs";

/** `/admin/actions/{note|ticket|refund}[/{id}]`, posted by operator forms. */
export async function POST(request: Request, { params }: { params: Promise<{ action: string[] }> }) {
    const actor = await operatorFromHeaders(request.headers);
    if (!actor) return new Response("Not found", { status: 404 });
    if (!postedFromHere(request.headers, request.headers.get("host")))
        return new Response("This form must be sent from the operator page.", { status: 403 });

    const [kind, id] = (await params).action;
    const form = await request.formData();
    const back = safeBack(form.get("back"));
    const planned = actionFor(kind, id, form, actor);
    if ("error" in planned) return new Response(planned.error, { status: 422 });

    try {
        const response = await enginePost(planned.path, planned.body);
        if (!response.ok) return new Response(`The engine refused: ${response.status}`, { status: 502 });
    } catch {
        return new Response("The engine could not be reached.", { status: 502 });
    }
    // A test send returns to the composer with what was typed still in it.
    let location = back;
    if (form.get("keep_draft") === "yes") {
        const subject = String(form.get("subject") ?? "");
        const text = String(form.get("body") ?? "");
        if (subject.length + text.length < 4000) {
            const url = new URL(back, "http://operator.local");
            url.searchParams.set("subject", subject);
            url.searchParams.set("body", text);
            url.searchParams.set("tested", "1");
            location = `${url.pathname}${url.search}`;
        }
    }
    return new Response(null, { status: 303, headers: { Location: location } });
}
