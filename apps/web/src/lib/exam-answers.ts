import { isOurs } from "./kit-pricing";
import { photographSpecRows, requirementSpecRows } from "./spec-format";
import type { ExamDetail, RequirementSummary } from "./types";

/**
 * The questions a candidate types into a search box, answered from the
 * examination's record and nothing else (DEC-087).
 *
 * "SSC CGL photo size" and "NEET signature KB" are how these pages are found,
 * by a search engine and by an AI answer engine alike. Both reward a page
 * that states the answer plainly near the top, so the rules page shows these
 * as a visible "In short" block, and the same text goes into its FAQ
 * structured data: structured data that says something the page does not is
 * worse than none.
 *
 * Nothing is invented. A file with no published figure gets no question, and
 * a value that is our own estimate carries "(est.)", as it does everywhere
 * else on the site.
 */

export interface ExamAnswer {
    question: string;
    answer: string;
}

type Row = { term: string; value: string; estimated: boolean };

/** The words a search uses for each file, not the schema's. */
const SEARCH_LABEL: Record<string, string> = {
    photograph: "photo",
    signature: "signature",
    thumb_impression: "thumb impression",
    handwritten_declaration: "handwritten declaration",
};

const SHOWN_TERMS = ["Dimensions", "File size", "Format", "Background"];

function rowsFor(exam: ExamDetail, requirement: RequirementSummary): Row[] {
    const requirements = exam.requirements ?? [];
    // A record may list a photograph and carry no photograph specification
    // (DEC-079); asking for its rows would throw.
    const rows =
        requirement.requirement_type === "photograph"
            ? exam.image_requirements
                ? photographSpecRows(exam)
                : []
            : requirementSpecRows(requirement, requirements.indexOf(requirement), exam.provenance);
    return rows.filter((row) => SHOWN_TERMS.includes(row.term));
}

/** A colour code is a figure for a machine; a candidate reads "white". */
function readable(value: string): string {
    return value.replace(/#fff(fff)?\b/gi, "white");
}

function spell(rows: Row[]): string {
    return rows
        .map((row, i) => {
            const term = i === 0 ? row.term : row.term.toLowerCase();
            return `${term}: ${readable(row.value)}${row.estimated ? " (est.)" : ""}`;
        })
        .join("; ");
}

/** One entry per kind of file we prepare that has published figures, photograph first. */
export function examSpecs(exam: ExamDetail): { type: string; label: string; rows: Row[] }[] {
    const seen = new Set<string>();
    const out: { type: string; label: string; rows: Row[] }[] = [];
    for (const requirement of (exam.requirements ?? []).filter(isOurs)) {
        const label = SEARCH_LABEL[requirement.requirement_type];
        if (!label || seen.has(requirement.requirement_type)) continue;
        const rows = rowsFor(exam, requirement);
        if (rows.length === 0) continue;
        seen.add(requirement.requirement_type);
        out.push({ type: requirement.requirement_type, label, rows });
    }
    return out.sort((a, b) => Number(b.type === "photograph") - Number(a.type === "photograph"));
}

export function examAnswers(exam: ExamDetail): ExamAnswer[] {
    const answers: ExamAnswer[] = examSpecs(exam).map(({ label, rows }) => ({
        question: `What is the ${label} size for ${exam.exam_name}?`,
        answer:
            `${spell(rows)}.` +
            (rows.some((row) => row.estimated)
                ? " A value marked est. is our estimate, because the notice gives no figure for it."
                : ""),
    }));

    // The files every candidate needs, named; the ones that apply only to some
    // candidates (a scribe, a category, a disability) counted, because a list
    // of eighteen is not an answer anyone reads.
    const requirements = exam.requirements ?? [];
    if (requirements.length > 0) {
        const required = requirements.filter((r) => r.requirement_status === "mandatory");
        const others = requirements.length - required.length;
        const named = required.length > 0 ? required : requirements;
        answers.push({
            question: `Which files does the ${exam.exam_name} application ask you to upload?`,
            answer:
                `${named.map((r) => r.requirement_name).join(", ")}.` +
                (required.length > 0 && others > 0
                    ? ` ${others} more ${others === 1 ? "applies" : "apply"} only to some candidates, and ${others === 1 ? "is" : "are"} listed below.`
                    : ""),
        });
    }

    const notice = exam.source_evidence.find((source) => source.official_source && source.document_title);
    answers.push({
        question: `Who sets the upload rules for ${exam.exam_name}?`,
        answer: notice?.document_title
            ? `${exam.conducting_body}, in its “${notice.document_title}”.`
            : `${exam.conducting_body}.`,
    });

    return answers;
}

/**
 * A search result's title, naming only the files the record has figures for:
 * "photo and signature size" on an examination whose photograph is taken live
 * would promise a figure the page does not have.
 */
export function examTitle(exam: ExamDetail): string {
    const labels = examSpecs(exam)
        .slice(0, 2)
        .map((spec) => spec.label);
    return labels.length > 0
        ? `${exam.exam_name} ${labels.join(" and ")} size, and upload rules`
        : `${exam.exam_name} upload rules and file sizes`;
}

/**
 * A search result's description: the figures themselves, which is what makes a
 * candidate click, then who set them. Falls back to plain words when the
 * record has no published figures to quote.
 */
export function examDescription(exam: ExamDetail): string {
    const specs = examSpecs(exam).slice(0, 2);
    const tail = `Every file made to ${exam.conducting_body}’s published rules, and previewed before you pay.`;
    if (specs.length === 0) {
        return `Every file ${exam.exam_name} asks you to upload, with its size, dimensions and format. ${tail}`;
    }
    const figures = specs
        .map(({ label, rows }) => {
            const values = rows
                .filter((row) => row.term !== "Background")
                .map((row) => `${row.value}${row.estimated ? " (est.)" : ""}`)
                .join(", ");
            return `${label.charAt(0).toUpperCase()}${label.slice(1)}: ${values}.`;
        })
        .join(" ");
    return `${exam.exam_name}. ${figures} ${tail}`;
}
