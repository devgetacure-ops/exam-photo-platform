import path from "node:path";
import { saveRequest, validateRequest } from "../../../lib/request-store";
import { isSameOrigin } from "../../../lib/request-origin";

export const runtime = "nodejs";
export async function POST(request: Request) {
    if (!isSameOrigin(request.headers, process.env.NEXT_PUBLIC_SITE_URL))
        return Response.json(
            { error: "Please submit from this website." },
            { status: 403 },
        );
    if (!request.headers.get("content-type")?.includes("application/json"))
        return Response.json(
            { error: "Unsupported request format." },
            { status: 415 },
        );
    const reader = request.body?.getReader();
    if (!reader)
        return Response.json(
            { error: "Please complete the form." },
            { status: 400 },
        );
    let length = 0;
    const chunks: Uint8Array[] = [];
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        length += value.byteLength;
        if (length > 12000) {
            await reader.cancel();
            return Response.json(
                { error: "Please keep your request under 3,000 characters." },
                { status: 413 },
            );
        }
        chunks.push(value);
    }
    let raw: unknown;
    try {
        raw = JSON.parse(Buffer.concat(chunks).toString("utf8"));
    } catch {
        return Response.json(
            { error: "Please check the form and try again." },
            { status: 400 },
        );
    }
    const value = validateRequest(raw);
    if (!value)
        return Response.json(
            { error: "Check your email, request details and consent." },
            { status: 422 },
        );
    const directory = process.env.UPLOADREADY_REQUESTS_DIR;
    if (!directory && process.env.NODE_ENV === "production")
        return Response.json(
            {
                error: "Requests are temporarily unavailable. Please try again later.",
            },
            { status: 503 },
        );
    try {
        const reference = await saveRequest(
            value,
            directory ?? path.join(process.cwd(), ".data", "requests"),
        );
        return Response.json(
            { reference },
            { status: 201, headers: { "Cache-Control": "no-store" } },
        );
    } catch {
        return Response.json(
            { error: "We couldn’t save your request. Please try again later." },
            { status: 503 },
        );
    }
}
