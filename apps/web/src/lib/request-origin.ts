/**
 * Whether a form POST came from a page on this site.
 *
 * The browser sets `Origin` itself and a page cannot forge it, so comparing it
 * with the host the browser addressed is enough to refuse a submission posted
 * from someone else's site.
 *
 * It must not be compared with `request.url`. Behind a proxy, a CDN, or even
 * `next start` bound to localhost, that URL carries the server's own idea of
 * its host, not the one in the candidate's address bar — and every genuine
 * submission was refused as foreign. Found by submitting the form at
 * 127.0.0.1 while the server called itself localhost.
 */
export function isSameOrigin(headers: Headers, siteUrl?: string): boolean {
    const origin = headers.get("origin");
    if (!origin) return false;

    let originHost: string;
    try {
        originHost = new URL(origin).host;
    } catch {
        return false;
    }

    const allowed = new Set<string>();
    const forwarded = headers.get("x-forwarded-host")?.split(",")[0]?.trim();
    if (forwarded) allowed.add(forwarded);
    const host = headers.get("host");
    if (host) allowed.add(host);
    if (siteUrl) {
        try {
            allowed.add(new URL(siteUrl).host);
        } catch {
            /* A malformed site URL adds nothing rather than allowing everything. */
        }
    }

    return allowed.has(originHost);
}
