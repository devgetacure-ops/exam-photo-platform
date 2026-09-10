import { loadExams } from "../../lib/catalogue.server";

export async function GET(request: Request) {
    const origin = new URL(process.env.NEXT_PUBLIC_SITE_URL || request.url)
        .origin;
    const exams = await loadExams();
    const routes = [
        "/",
        "/exams",
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
