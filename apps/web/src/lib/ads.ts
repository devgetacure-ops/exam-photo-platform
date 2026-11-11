/**
 * Advertising settings (DEC-127). Everything is off until the AdSense
 * publisher id is set at build time, so nothing ad-shaped reaches a page
 * before Google has approved the site.
 *
 * NEXT_PUBLIC_ADSENSE_CLIENT  ca-pub-…, the publisher id
 * NEXT_PUBLIC_ADSENSE_SLOTS   comma list of name=slot-id, e.g.
 *                             "exam-after-kit=1234567890,rules-mid=2345678901"
 */
export const ADSENSE_CLIENT = (process.env.NEXT_PUBLIC_ADSENSE_CLIENT ?? "").trim();

const SLOTS: Record<string, string> = Object.fromEntries(
    (process.env.NEXT_PUBLIC_ADSENSE_SLOTS ?? "")
        .split(",")
        .map((pair) => pair.split("=").map((part) => part.trim()))
        .filter((pair): pair is [string, string] => pair.length === 2 && !!pair[0] && /^\d+$/.test(pair[1])),
);

export function adSlotId(name: string): string | null {
    return ADSENSE_CLIENT.startsWith("ca-pub-") ? (SLOTS[name] ?? null) : null;
}

export function adsEnabled(): boolean {
    return ADSENSE_CLIENT.startsWith("ca-pub-");
}
