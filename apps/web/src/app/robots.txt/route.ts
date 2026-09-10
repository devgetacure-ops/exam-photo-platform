export function GET(request: Request) {
    const origin = new URL(process.env.NEXT_PUBLIC_SITE_URL || request.url)
        .origin;
    return new Response(
        `User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/\nDisallow: /v1/\nSitemap: ${origin}/sitemap.xml\n`,
        { headers: { "Content-Type": "text/plain" } },
    );
}
