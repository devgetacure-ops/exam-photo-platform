import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";

import { describe, expect, test } from "vitest";

import { EXAM_FAMILIES, UNGROUPED_CATEGORIES, familyBySlug, familyOf } from "../lib/exam-families";
import { familySlugOf, type RawRecord } from "../lib/seo-keywords";

/** The exam family hubs (DEC-096). */

const dir = path.join(process.cwd(), "..", "..", "examples", "rules");
const records: RawRecord[] = readdirSync(dir)
    .filter((name) => name.startsWith("exam_") && name.endsWith(".json"))
    .map((name) => JSON.parse(readFileSync(path.join(dir, name), "utf8")) as RawRecord);

describe("exam families", () => {
    test("every examination is in a family, or deliberately in none", () => {
        const unplaced = records
            .map((record) => record.exam?.category ?? "")
            .filter((category) => !familyOf(category) && !(category in UNGROUPED_CATEGORIES));
        expect(unplaced, "a new category must be placed in lib/exam-families.ts").toEqual([]);
    });

    test("no category is claimed by two families", () => {
        const seen = new Set<string>();
        for (const family of EXAM_FAMILIES) {
            for (const category of family.categories) {
                expect(seen.has(category), category).toBe(false);
                seen.add(category);
            }
        }
    });

    test("the eight families the owner agreed, each with examinations", () => {
        expect(EXAM_FAMILIES.map((family) => family.slug)).toEqual([
            "ssc-and-upsc",
            "banking-and-insurance",
            "railways",
            "police",
            "defence",
            "teaching",
            "state-commissions",
            "entrance-exams",
        ]);
        for (const family of EXAM_FAMILIES) {
            const members = records.filter((r) => familyOf(r.exam?.category)?.slug === family.slug);
            expect(members.length, family.slug).toBeGreaterThanOrEqual(5);
            expect(family.slug).toMatch(/^[a-z]+(-[a-z]+)*$/);
        }
        expect(familyBySlug("nope")).toBeNull();
    });

    test("the keyword map targets the same hub as the site for every examination", () => {
        for (const record of records) {
            expect(familySlugOf(record), record.exam?.exam_id).toBe(
                familyOf(record.exam?.category)?.slug ?? null,
            );
        }
    });
});
