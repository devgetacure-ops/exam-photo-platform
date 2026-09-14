import { loadExams } from "../../lib/catalogue.server";
import { rupees, tier } from "../../lib/kit-pricing";
import { CONTACT_EMAILS, SITE_URL } from "../../lib/site";

/**
 * `/llms.txt`: the site in plain words for AI answer engines (DEC-087).
 *
 * A proposed convention rather than a standard, and cheap to serve: what the
 * service is, what it costs, the promises it makes, and a link to every
 * examination's rules. Every statement here is one the site already makes on
 * its own pages; nothing is written only for a machine.
 */

export const dynamic = "force-static";

export async function GET() {
    const exams = [...(await loadExams())].sort((a, b) => a.exam_name.localeCompare(b.exam_name));

    const lines = [
        "# examuploadkit",
        "",
        "> Prepares the files Indian examination applications ask candidates to upload (photograph, signature, thumb impression, handwritten declaration, certificates and ID documents) to each examination's published dimensions, file size and format.",
        "",
        "## What it is",
        "",
        `- Covers ${exams.length} Indian examinations, each read from the rules its conducting body published.`,
        `- Price: ${rupees(tier(1))} for one file, ${rupees(tier(2))} for two or more. No account is needed.`,
        "- Each prepared file is shown as a watermarked preview before payment.",
        "- The face is never reshaped or whitened; only exposure, contrast, colour and sharpness are adjusted.",
        "- Uploaded and prepared files are deleted 30 minutes after preparation, or within an hour if the candidate asks for more time.",
        "- Where a notice gives no figure, the site shows its own estimate and marks it est.",
        "- Independent service; not connected with any examination authority.",
        "",
        "## Pages",
        "",
        `- [All examinations](${SITE_URL}/exams): every examination covered, A to Z`,
        `- [PDF work](${SITE_URL}/pdf): merge, reorder, compress, and PDF page to image`,
        `- [Support](${SITE_URL}/support): payment, delivery and rejection problems`,
        `- [Terms](${SITE_URL}/terms), [Privacy](${SITE_URL}/privacy), [Refunds](${SITE_URL}/refund-policy)`,
        `- Contact: ${CONTACT_EMAILS.support}`,
        "",
        "## Examinations: upload rules",
        "",
        ...exams.map(
            (exam) =>
                `- [${exam.exam_name}](${SITE_URL}/exam/${encodeURIComponent(exam.exam_id)}/rules): photo, signature and document sizes, set by ${exam.conducting_body}`,
        ),
        "",
    ];

    return new Response(lines.join("\n"), {
        headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
}
