import { operatorFromHeaders } from "../../../../lib/operator/access";
import { engineJson } from "../../../../lib/operator/engine";

export const runtime = "nodejs";

/** What the console's Ctrl K search asks (DEC-113). Access-checked, never cached. */
export async function GET(request: Request) {
    if (!(await operatorFromHeaders(request.headers))) return new Response("Not found", { status: 404 });
    const q = (new URL(request.url).searchParams.get("q") ?? "").trim().slice(0, 120);
    if (q.length < 2) return Response.json({ orders: [], customers: [], tickets: [], uploads: [] });
    const found = await engineJson<unknown>(`/v1/operator/search?q=${encodeURIComponent(q)}`);
    if (!found.ok) return Response.json({ error: found.error }, { status: 502 });
    return Response.json(found.value, { headers: { "Cache-Control": "private, no-store" } });
}
