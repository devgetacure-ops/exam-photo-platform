import "server-only";
import { readFile } from "node:fs/promises";
import path from "node:path";
import type { ExamFact } from "../components/exam/exam-facts";

/**
 * Kinds that only restate a measurement the page already prints in full.
 *
 * "The photograph has to be between 10 KB and 200 KB" is not worth knowing
 * next to a panel that gives that figure, its source and what we do about it.
 * What belongs here is what a candidate would not otherwise find out: what
 * this examination rejects applications for, that it photographs you itself,
 * that it will take a black and white photograph, how many files it wants.
 */
const RESTATES_A_RULE = new Set(["file_size", "format", "dimensions"]);

export async function loadExamFacts(examId: string): Promise<ExamFact[]> {
    try {
        const raw = JSON.parse(
            await readFile(
                path.join(
                    process.cwd(),
                    "../../examples/rules/candidate_facts.json",
                ),
                "utf8",
            ),
        );
        const facts: unknown = raw.exams?.[examId]?.facts;
        if (!Array.isArray(facts)) return [];
        return facts.filter(
            (fact): fact is ExamFact =>
                fact &&
                typeof fact.text === "string" &&
                typeof fact.source === "string" &&
                fact.source.length > 0 &&
                !RESTATES_A_RULE.has(fact.kind),
        );
    } catch {
        return [];
    }
}
