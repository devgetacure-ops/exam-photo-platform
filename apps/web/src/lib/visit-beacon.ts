/**
 * The site's own visit counter (DEC-110): which pages a session opened, how
 * long it was actually on screen, where it came from and on what device. It
 * goes to our own server only, carries no name or address, and never runs on
 * the operator page.
 */

const SESSION_KEY = "euk:visit";
const KITS_KEY = "exam-photo:kits:v1";

export interface VisitEvent {
    session_id: string;
    type: "view" | "ping" | "search_empty";
    path?: string;
    kit_id?: string;
    seconds?: number;
    referrer_host?: string;
    utm_source?: string;
    utm_medium?: string;
    utm_campaign?: string;
    device?: string;
    browser?: string;
    connection?: string;
    query?: string;
}

export function sessionId(storage: Pick<Storage, "getItem" | "setItem"> | null = safeSession()): string {
    try {
        const existing = storage?.getItem(SESSION_KEY);
        if (existing && /^[A-Za-z0-9_-]{8,64}$/.test(existing)) return existing;
        const fresh = `s_${crypto.randomUUID().replace(/-/g, "").slice(0, 20)}`;
        storage?.setItem(SESSION_KEY, fresh);
        return fresh;
    } catch {
        return `s_${Math.random().toString(36).slice(2, 14)}`;
    }
}

function safeSession(): Storage | null {
    try {
        return typeof window === "undefined" ? null : window.sessionStorage;
    } catch {
        return null;
    }
}

/** The kit this browser worked on most recently, to join a visit to its uploads. */
export function latestKit(raw: string | null): string | undefined {
    if (!raw) return undefined;
    try {
        const store = JSON.parse(raw) as Record<string, { kitId?: string; updatedAt?: string }>;
        const kits = Object.values(store).filter((kit) => kit && typeof kit.kitId === "string");
        kits.sort((a, b) => String(b.updatedAt ?? "").localeCompare(String(a.updatedAt ?? "")));
        const kit = kits[0]?.kitId;
        return kit && /^kit_[A-Za-z0-9_-]{1,64}$/.test(kit) ? kit : undefined;
    } catch {
        return undefined;
    }
}

export function deviceOf(userAgent: string, width: number): { device: string; browser: string } {
    const ua = userAgent.toLowerCase();
    const device = /ipad|tablet/.test(ua) || (/android/.test(ua) && !/mobile/.test(ua)) ? "tablet" : /mobi|iphone|android/.test(ua) || width < 700 ? "mobile" : "desktop";
    const browser = /samsungbrowser/.test(ua)
        ? "samsung"
        : /edg\//.test(ua)
          ? "edge"
          : /opr\/|opera/.test(ua)
            ? "opera"
            : /ucbrowser/.test(ua)
              ? "uc"
              : /chrome|crios/.test(ua)
                ? "chrome"
                : /firefox|fxios/.test(ua)
                  ? "firefox"
                  : /safari/.test(ua)
                    ? "safari"
                    : "other";
    return { device, browser };
}

/** Where the visit came from: another site's host, never our own. */
export function referrerHost(referrer: string, ownHost: string): string | undefined {
    try {
        const host = new URL(referrer).host;
        return host && host !== ownHost ? host : undefined;
    } catch {
        return undefined;
    }
}

export function campaignFrom(search: string): Pick<VisitEvent, "utm_source" | "utm_medium" | "utm_campaign"> {
    const params = new URLSearchParams(search);
    const pick = (name: string) => params.get(name)?.slice(0, 80) || undefined;
    return { utm_source: pick("utm_source") ?? pick("ref"), utm_medium: pick("utm_medium"), utm_campaign: pick("utm_campaign") };
}

export function tracked(path: string): boolean {
    return !path.startsWith("/admin") && !path.startsWith("/feedback");
}

export function send(events: VisitEvent[], beacon = false): void {
    if (typeof window === "undefined" || events.length === 0) return;
    const body = JSON.stringify({ events });
    try {
        if (beacon && navigator.sendBeacon) {
            navigator.sendBeacon("/api/events", new Blob([body], { type: "application/json" }));
            return;
        }
        void fetch("/api/events", { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: true }).catch(() => undefined);
    } catch {
        /* Counting a visit is never worth an error in front of a candidate. */
    }
}

export function currentKit(): string | undefined {
    try {
        return latestKit(window.localStorage.getItem(KITS_KEY));
    } catch {
        return undefined;
    }
}

let lastReported = "";

/** A search that found nothing is demand for an examination we lack. */
export function reportEmptySearch(query: string): void {
    const text = query.trim();
    if (text.length < 3 || text.toLowerCase() === lastReported) return;
    lastReported = text.toLowerCase();
    send([{ session_id: sessionId(), type: "search_empty", query: text.slice(0, 120) }]);
}
