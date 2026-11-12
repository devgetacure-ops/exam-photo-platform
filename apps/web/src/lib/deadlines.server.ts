import "server-only";

import { DEADLINES, type Deadline } from "./deadlines";

/**
 * The application dates for a server-rendered page (DEC-136): the engine's
 * live list, refreshed at most once a minute, or the bundled list when the
 * engine is out of reach or has none yet (a build has no engine).
 */
export async function loadDeadlines(): Promise<readonly Deadline[]> {
    try {
        const base = (process.env.EUK_ENGINE_INTERNAL_URL ?? "http://engine:8000").replace(/\/+$/, "");
        const response = await fetch(`${base}/v1/deadlines`, {
            next: { revalidate: 60 },
            signal: AbortSignal.timeout(1500),
        });
        if (!response.ok) return DEADLINES;
        const body = (await response.json()) as { entries?: Deadline[] };
        return body.entries && body.entries.length > 0 ? body.entries : DEADLINES;
    } catch {
        return DEADLINES;
    }
}
