/**
 * Who may open the operator page (DEC-108).
 *
 * Cloudflare Access stands in front of /admin and emails the owner a one-time
 * code. This checks its signed assertion again here, so a mistake in the
 * Access policy fails shut instead of open: with no audience configured, or a
 * missing or bad assertion, the page answers 404 as if it did not exist.
 */

export interface AccessConfig {
    teamDomain: string;
    audience: string;
}

interface Jwk {
    kid: string;
    kty: string;
    n: string;
    e: string;
    alg?: string;
}

export function accessConfig(
    env: Record<string, string | undefined> = process.env,
): AccessConfig | null {
    const teamDomain = (env.EUK_ACCESS_TEAM_DOMAIN ?? "").trim().replace(/\/+$/, "");
    const audience = (env.EUK_ACCESS_AUD ?? "").trim();
    if (!/^https:\/\/[a-z0-9-]+\.cloudflareaccess\.com$/.test(teamDomain) || !audience)
        return null;
    return { teamDomain, audience };
}

function base64UrlBytes(part: string): Uint8Array<ArrayBuffer> {
    const padded = part.replace(/-/g, "+").replace(/_/g, "/");
    const binary = atob(padded + "=".repeat((4 - (padded.length % 4)) % 4));
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return bytes;
}

function decodeJson(part: string): Record<string, unknown> | null {
    try {
        const value = JSON.parse(new TextDecoder().decode(base64UrlBytes(part)));
        return value && typeof value === "object" ? value : null;
    } catch {
        return null;
    }
}

let keyCache: { at: number; teamDomain: string; keys: Jwk[] } | null = null;

async function signingKeys(
    teamDomain: string,
    fetcher: typeof fetch,
    now: number,
): Promise<Jwk[]> {
    if (keyCache && keyCache.teamDomain === teamDomain && now - keyCache.at < 3600_000)
        return keyCache.keys;
    const response = await fetcher(`${teamDomain}/cdn-cgi/access/certs`, {
        cache: "no-store",
    });
    if (!response.ok) return [];
    const body = (await response.json()) as { keys?: Jwk[] };
    const keys = Array.isArray(body.keys) ? body.keys : [];
    keyCache = { at: now, teamDomain, keys };
    return keys;
}

export function resetAccessKeyCache() {
    keyCache = null;
}

/** The operator's email if the assertion is genuine and current, else null. */
export async function verifyAccessAssertion(
    token: string | null | undefined,
    config: AccessConfig | null,
    fetcher: typeof fetch = fetch,
    now: number = Date.now(),
): Promise<string | null> {
    if (!config || !token) return null;
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const header = decodeJson(parts[0]);
    const claims = decodeJson(parts[1]);
    if (!header || !claims || header.alg !== "RS256") return null;

    const audiences = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
    if (!audiences.includes(config.audience)) return null;
    if (claims.iss !== config.teamDomain) return null;
    const seconds = now / 1000;
    if (typeof claims.exp !== "number" || claims.exp <= seconds) return null;
    if (typeof claims.nbf === "number" && claims.nbf > seconds + 60) return null;

    const keys = await signingKeys(config.teamDomain, fetcher, now);
    const jwk = keys.find((key) => key.kid === header.kid);
    if (!jwk) return null;
    try {
        const key = await crypto.subtle.importKey(
            "jwk",
            { kty: jwk.kty, n: jwk.n, e: jwk.e, alg: "RS256", ext: true },
            { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
            false,
            ["verify"],
        );
        const valid = await crypto.subtle.verify(
            "RSASSA-PKCS1-v1_5",
            key,
            base64UrlBytes(parts[2]),
            new TextEncoder().encode(`${parts[0]}.${parts[1]}`),
        );
        if (!valid) return null;
    } catch {
        return null;
    }
    return typeof claims.email === "string" ? claims.email : "operator";
}

/**
 * The single gate every operator page and route calls. Outside production a
 * developer may open it locally with EUK_OPERATOR_DEV_OPEN=true; in
 * production only a verified Access assertion does.
 */
export async function operatorFromHeaders(
    headers: Headers,
    env: Record<string, string | undefined> = process.env,
    fetcher: typeof fetch = fetch,
): Promise<string | null> {
    if (env.NODE_ENV !== "production" && env.EUK_OPERATOR_DEV_OPEN === "true")
        return "local developer";
    return verifyAccessAssertion(
        headers.get("cf-access-jwt-assertion"),
        accessConfig(env),
        fetcher,
    );
}
