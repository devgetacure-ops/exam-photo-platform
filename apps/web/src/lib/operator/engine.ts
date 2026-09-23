import "server-only";

/**
 * The operator page's only way to the engine (DEC-108). The token is read on
 * the server and sent inside the compose network; it is never rendered, never
 * put in a URL and never reaches a browser.
 */

export function engineBase(env: Record<string, string | undefined> = process.env) {
    return (env.EUK_ENGINE_INTERNAL_URL ?? "http://engine:8000").replace(/\/+$/, "");
}

function token(): string {
    const value = process.env.EXAM_PHOTO_OPERATOR_TOKEN ?? "";
    if (!value) throw new Error("EXAM_PHOTO_OPERATOR_TOKEN is not set for the web server");
    return value;
}

export async function engineFetch(path: string): Promise<Response> {
    return fetch(`${engineBase()}${path}`, {
        headers: { "X-Operator-Token": token() },
        cache: "no-store",
        signal: AbortSignal.timeout(20_000),
    });
}

export type Loaded<T> = { ok: true; value: T } | { ok: false; error: string };

export async function engineJson<T>(path: string): Promise<Loaded<T>> {
    try {
        const response = await engineFetch(path);
        if (!response.ok) return { ok: false, error: `engine answered ${response.status}` };
        return { ok: true, value: (await response.json()) as T };
    } catch (error) {
        return { ok: false, error: error instanceof Error ? error.message : String(error) };
    }
}

/** A write to the engine's operator surface (DEC-109). Throws on failure. */
export async function enginePost(path: string, body: unknown): Promise<Response> {
    return fetch(`${engineBase()}${path}`, {
        method: "POST",
        headers: { "X-Operator-Token": token(), "Content-Type": "application/json" },
        body: JSON.stringify(body),
        cache: "no-store",
        signal: AbortSignal.timeout(10_000),
    });
}
