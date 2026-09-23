import { operatorFromHeaders } from "../../../../../lib/operator/access";
import { safeFileRequest } from "../../../../../lib/operator/data";
import { engineFetch } from "../../../../../lib/operator/engine";

export const runtime = "nodejs";

const NOT_FOUND = () => new Response("Not found", { status: 404 });

/**
 * A live upload's file, passed through from the engine for the operator page
 * (DEC-108). The operator token stays on this side; the browser is told never
 * to keep a copy.
 */
export async function GET(
    request: Request,
    { params }: { params: Promise<{ jobId: string; name: string }> },
) {
    if (!(await operatorFromHeaders(request.headers))) return NOT_FOUND();
    const { jobId, name } = await params;
    if (!safeFileRequest(jobId, name)) return NOT_FOUND();
    let upstream: Response;
    try {
        upstream = await engineFetch(
            `/v1/operator/jobs/${jobId}/files/${encodeURIComponent(name)}`,
        );
    } catch {
        return new Response("Engine unreachable", { status: 502 });
    }
    if (!upstream.ok) return NOT_FOUND();
    return new Response(upstream.body, {
        status: 200,
        headers: {
            "Content-Type": upstream.headers.get("content-type") ?? "application/octet-stream",
            "Cache-Control": "private, no-store, max-age=0",
            "X-Robots-Tag": "noindex",
            "Content-Disposition": "inline",
        },
    });
}
