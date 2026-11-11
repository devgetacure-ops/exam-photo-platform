/**
 * 32 random hex characters, in any browser.
 *
 * `crypto.randomUUID` exists only on secure pages (HTTPS or localhost). A
 * phone testing the site over Wi-Fi at `http://192.168.x.x` has no secure
 * context, and calling it there stopped every upload. `getRandomValues`
 * works everywhere, so it is the fallback; `Math.random` is the last resort
 * for an environment with no Web Crypto at all.
 */
export function randomHex(): string {
    const c = typeof crypto !== "undefined" ? crypto : undefined;
    if (c && typeof c.randomUUID === "function") return c.randomUUID().replace(/-/g, "");
    if (c && typeof c.getRandomValues === "function") {
        const bytes = c.getRandomValues(new Uint8Array(16));
        return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
    }
    let out = "";
    while (out.length < 32) out += Math.floor(Math.random() * 16).toString(16);
    return out;
}
