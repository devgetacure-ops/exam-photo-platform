import "server-only";
import { readFile } from "node:fs/promises";
import path from "node:path";
import type { ExamFact } from "../components/exam/exam-facts";

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
                fact.source.length > 0,
        );
    } catch {
        return [];
    }
}
