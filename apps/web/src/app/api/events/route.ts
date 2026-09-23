import { enginePost } from "../../../lib/operator/engine";

export const runtime = "nodejs";

const MAX_BYTES = 8000;
/** Per session, per minute: enough for real browsing, useless for flooding. */
const PER_MINUTE = 60;
const seen = new Map<string, { minute: number; count: number }>();

/**
 * The visit beacon's way in (DEC-110). Checked and bounded here, then passed
 * to the engine with the operator token, which never reaches the browser.
 * Always answers 204: a counter that fails must not show a candidate anything.
 */
export async function POST(request: Request) {
    const done = new Response(null, { status: 204 });
    const site = request.headers.get("sec-fetch-site");
    if (site && site !== "same-origin") return done;
    if (!process.env.EXAM_PHOTO_OPERATOR_TOKEN) return done;
    const text = await request.text().catch(() => "");
    if (!text || text.length > MAX_BYTES) return done;
    let events: unknown;
    try {
        events = (JSON.parse(text) as { events?: unknown }).events;
    } catch {
        return done;
    }
    if (!Array.isArray(events) || events.length === 0) return done;
    const session = String((events[0] as { session_id?: unknown })?.session_id ?? "");
    if (!/^[A-Za-z0-9_-]{8,64}$/.test(session)) return done;
    const minute = Math.floor(Date.now() / 60000);
    const entry = seen.get(session);
    const count = entry && entry.minute === minute ? entry.count + events.length : events.length;
    seen.set(session, { minute, count });
    if (seen.size > 20000) seen.clear();
    if (count > PER_MINUTE) return done;
    await enginePost("/v1/operator/events", { events: events.slice(0, 20) }).catch(() => null);
    return done;
}
