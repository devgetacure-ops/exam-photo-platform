import type { ExamFact } from "../components/exam/exam-facts";

/**
 * The kinds a researched fact can be: things about the examination itself.
 *
 * "Worth knowing" shows facts, never rules (the owner, repeatedly). The rule
 * records also yield derived facts -- a file size, a format, a rejection
 * condition, how many files the application asks for -- and every one of
 * those is already printed where the rules are. None of them reaches the card,
 * the payment wait or the phone flow. An examination with no researched fact
 * shows no card at all.
 */
export const RESEARCHED_KINDS: ReadonlySet<string> = new Set([
    "volume",
    "process",
    "exam_day",
    "structure",
    "history",
    "window",
]);

/** A fact worth showing: a researched kind, with a source and its publisher. */
export function isResearchedFact(fact: unknown): fact is ExamFact {
    if (!fact || typeof fact !== "object") return false;
    const candidate = fact as Partial<ExamFact>;
    return (
        typeof candidate.text === "string" &&
        typeof candidate.source === "string" &&
        candidate.source.length > 0 &&
        typeof candidate.kind === "string" &&
        RESEARCHED_KINDS.has(candidate.kind) &&
        typeof candidate.reported_by === "string" &&
        candidate.reported_by.trim().length > 0
    );
}
