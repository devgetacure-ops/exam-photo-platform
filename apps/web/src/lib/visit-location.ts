/**
 * Where the visitor is, as Cloudflare names it (DEC-125): country always,
 * city and region once "Add visitor location headers" is on. Read here on the
 * server, so a browser cannot claim a place. No IP address is passed on.
 */
export function locationFrom(headers: Headers): { country?: string; region?: string; city?: string } {
    const read = (name: string, limit: number) => {
        const raw = headers.get(name)?.trim();
        if (!raw) return undefined;
        let value = raw;
        try {
            value = decodeURIComponent(raw);
        } catch {
            /* Not encoded. */
        }
        return value.slice(0, limit) || undefined;
    };
    const country = read("cf-ipcountry", 2)?.toUpperCase();
    return {
        ...(country && /^[A-Z]{2}$/.test(country) && country !== "XX" && country !== "T1" ? { country } : {}),
        ...(read("cf-region", 60) ? { region: read("cf-region", 60) } : {}),
        ...(read("cf-ipcity", 60) ? { city: read("cf-ipcity", 60) } : {}),
    };
}
