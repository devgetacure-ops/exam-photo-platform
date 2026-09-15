import { loadSpecTargets } from "../../lib/catalogue.server";
import { SITE_URL } from "../../lib/site";
import { EXAM_FAMILIES } from "../../lib/exam-families";

// The host the canonicals name (DEC-087), not whichever address the request
// came in on: behind a proxy that is an internal name.
export async function GET() {
    const origin = SITE_URL;
    const { exams, targets } = await loadSpecTargets();
    const routes = [
        "/",
        "/exams",
        ...EXAM_FAMILIES.map((family) => `/exams/${family.slug}`),
        "/compress-image",
        "/compress-pdf",
        ...targets.map((target) => `/resize/${target.slug}`),
        "/pdf",
        "/exam-request",
        "/support",
        "/privacy",
        "/terms",
        "/refund-policy",
        ...exams.flatMap((exam) => [
            `/exam/${encodeURIComponent(exam.exam_id)}`,
            `/exam/${encodeURIComponent(exam.exam_id)}/rules`,
        ]),
    ];
    const escape = (text: string) =>
        text
            .replaceAll("&", "&amp;")
            .replaceAll('"', "&quot;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;");
    return new Response(
        `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${routes.map((route) => `<url><loc>${escape(origin + route)}</loc></url>`).join("")}</urlset>`,
        {
            headers: {
                "Content-Type": "application/xml",
                "Cache-Control": "public, max-age=3600",
            },
        },
    );
}
