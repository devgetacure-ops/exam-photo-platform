import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { rankEntries } from "../lib/search-rank";
import type { SearchEntry } from "../lib/types";

/**
 * Every alias has to find its own examination.
 *
 * Candidates type "CGL", not "SSC Combined Graduate Level Examination 2026",
 * and for a long time that returned nothing at all: the records carried no
 * aliases, so the ranker had only the full name to match against. The short
 * forms now live in the research sidecar and are encoded into every record.
 *
 * This is the check that keeps them honest. An alias attached to the wrong
 * examination, or one the ranker cannot reach, is a candidate sent to another
 * exam's rules — which is worse than finding nothing. So each alias is searched
 * for and must bring back its own examination at the top of the list.
 */
const CATALOGUE = path.join(process.cwd(), "..", "..", "examples", "rules");

function catalogue(): SearchEntry[] {
    return readdirSync(CATALOGUE)
        .filter((name) => name.startsWith("exam_") && name.endsWith(".json"))
        .map((name) => {
            const record = JSON.parse(
                readFileSync(path.join(CATALOGUE, name), "utf8"),
            );
            const exam = record.exam;
            return {
                id: exam.exam_id,
                name: exam.exam_name,
                body: exam.conducting_body,
                year: exam.examination_year,
                aliases: exam.aliases ?? [],
                prepares: 0,
                total: 0,
            } satisfies SearchEntry;
        });
}

describe("the examination aliases", () => {
    const entries = catalogue();

    it("covers the catalogue", () => {
        expect(entries.length).toBe(132);
        const without = entries.filter((entry) => entry.aliases.length === 0);
        // One record is its own short form already: NEET-PG.
        expect(without.map((entry) => entry.name)).toEqual(["NEET-PG"]);
    });

    it("brings back its own examination for every alias", () => {
        const misses: string[] = [];
        for (const entry of entries) {
            for (const alias of entry.aliases) {
                const top = rankEntries(entries, alias).slice(0, 3);
                if (!top.some((row) => row.entry.id === entry.id)) {
                    misses.push(`${alias} → ${entry.name}`);
                }
            }
        }
        expect(misses).toEqual([]);
    });

    it("never gives two examinations the same alias for the same body", () => {
        const seen = new Map<string, string[]>();
        for (const entry of entries) {
            for (const alias of entry.aliases) {
                const key = `${entry.body}::${alias.toLowerCase()}`;
                seen.set(key, [...(seen.get(key) ?? []), entry.name]);
            }
        }
        const shared = [...seen.entries()]
            .filter(([, names]) => names.length > 1)
            .map(([key, names]) => `${key}: ${names.join(" / ")}`);
        // Two records of the *same* examination legitimately share a short
        // form — the RBI Assistant live-photograph variant, and the Army's
        // Agniveer entries, which are stages of one recruitment rather than
        // different examinations. So this asserts the known list rather than
        // zero: a new line appearing here means an alias has been hung on an
        // examination it does not belong to.
        expect(shared.sort()).toEqual(
            [
                "Indian Army::agniveer: Indian Army Agniveer CEE 2025-26 - online upload / Indian Army Agniveer Recruitment",
                "Indian Army::army agniveer: Indian Army Agniveer CEE 2025-26 - online upload / Indian Army Agniveer Recruitment",
                "Indian Army::agnipath: Indian Army Agniveer CEE 2025-26 - online upload / Indian Army Agniveer Recruitment",
                "Reserve Bank of India::rbi assistant: RBI Assistant - Panel Year 2025 / RBI Assistant - Panel Year 2025 (live photograph)",
            ].sort(),
        );
    });
});
