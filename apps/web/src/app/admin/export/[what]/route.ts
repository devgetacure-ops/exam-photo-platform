import { operatorFromHeaders } from "../../../../lib/operator/access";
import { engineFetch, enginePost } from "../../../../lib/operator/engine";

export const runtime = "nodejs";

const EXPORTS = new Set(["orders", "customers", "uploads"]);

/** A CSV for the accountant or a mailing tool (DEC-109); every download is logged. */
export async function GET(request: Request, { params }: { params: Promise<{ what: string }> }) {
    const actor = await operatorFromHeaders(request.headers);
    const { what } = await params;
    if (!actor || !EXPORTS.has(what)) return new Response("Not found", { status: 404 });
    let upstream: Response;
    try {
        upstream = await engineFetch(`/v1/operator/export/${what}.csv`);
    } catch {
        return new Response("Engine unreachable", { status: 502 });
    }
    if (!upstream.ok) return new Response("Export failed", { status: 502 });
    await enginePost("/v1/operator/activity", { actor, action: `exported ${what}.csv` }).catch(() => null);
    const day = new Date().toISOString().slice(0, 10);
    return new Response(upstream.body, {
        headers: {
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": `attachment; filename="examuploadkit-${what}-${day}.csv"`,
            "Cache-Control": "private, no-store",
        },
    });
}
