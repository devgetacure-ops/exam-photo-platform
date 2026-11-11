import { ADSENSE_CLIENT } from "../../lib/ads";

/**
 * `/ads.txt` (DEC-127): declares Google as the site's authorised ad seller.
 * Empty, and a 404, until the AdSense publisher id is set.
 */
export const dynamic = "force-static";

export function GET() {
    if (!ADSENSE_CLIENT.startsWith("ca-pub-")) return new Response("Not found", { status: 404 });
    const publisher = ADSENSE_CLIENT.replace(/^ca-/, "");
    return new Response(`google.com, ${publisher}, DIRECT, f08c47fec0942fa0\n`, {
        headers: { "Content-Type": "text/plain" },
    });
}
