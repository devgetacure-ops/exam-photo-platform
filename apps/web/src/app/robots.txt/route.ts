import { SITE_URL } from "../../lib/site";

export function GET() {
    const origin = SITE_URL;
    return new Response(
        `User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/\nDisallow: /v1/\nSitemap: ${origin}/sitemap.xml\n`,
        { headers: { "Content-Type": "text/plain" } },
    );
}
