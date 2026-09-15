import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, test } from "vitest";

import { RESEARCHED_KINDS, isResearchedFact } from "../lib/researched-facts";

/**
 * "Worth knowing" is facts about the examination, never its rules (the owner,
 * 2026-09-14: "this is the last time I am telling you"). Negative first: every
 * derived kind in the real sidecar must be refused.
 */

const sidecar = JSON.parse(
    readFileSync(
        path.join(process.cwd(), "../../examples/rules/candidate_facts.json"),
        "utf8",
    ),
) as { exams: Record<string, { facts: Record<string, unknown>[] }> };

const RULE_KINDS = [
    "rejection",
    "deliverables",
    "file_size",
    "format",
    "dimensions",
    "capture",
    "appearance",
];

describe("worth knowing shows researched facts only", () => {
    test("no rule-derived kind is ever a researched kind", () => {
        for (const kind of RULE_KINDS) expect(RESEARCHED_KINDS.has(kind)).toBe(false);
    });

    test("a rule fact is refused even when it carries a publisher", () => {
        expect(
            isResearchedFact({
                kind: "rejection",
                text: "Blurred photographs are rejected.",
                source: "Notice (https://example.gov.in)",
                reported_by: "The authority",
            }),
        ).toBe(false);
    });

    test("a researched kind without a publisher is refused", () => {
        const base = {
            kind: "volume",
            text: "Over 20 lakh candidates registered.",
            source: "Press note (https://example.gov.in)",
        };
        expect(isResearchedFact(base)).toBe(false);
        expect(isResearchedFact({ ...base, reported_by: "  " })).toBe(false);
        expect(isResearchedFact({ ...base, reported_by: "Press Information Bureau" })).toBe(true);
    });

    test("across the whole catalogue, nothing shown is a rule", () => {
        let shown = 0;
        let refused = 0;
        for (const exam of Object.values(sidecar.exams)) {
            for (const fact of exam.facts) {
                if (isResearchedFact(fact)) {
                    shown++;
                    expect(RULE_KINDS).not.toContain(fact.kind);
                } else if (RULE_KINDS.includes(String(fact.kind))) {
                    refused++;
                }
            }
        }
        expect(shown).toBeGreaterThan(100);
        expect(refused).toBeGreaterThan(400);
    });

    test("an examination with only rule facts shows no card", () => {
        // RRB NTPC's researched facts were all dropped on 2026-09-15: its
        // schedule PDF is not served (DEC-095). BPSC gained two that day.
        const rrb = sidecar.exams["rrb-ntpc-graduate-cen-05-2024"];
        expect(rrb).toBeDefined();
        expect(rrb.facts.length).toBeGreaterThan(0);
        expect(rrb.facts.filter(isResearchedFact)).toEqual([]);
    });

    test("an examination whose researched facts were checked shows them", () => {
        const bpsc = sidecar.exams["bpsc-online-application"];
        expect(bpsc.facts.filter(isResearchedFact).length).toBe(2);
    });
});
