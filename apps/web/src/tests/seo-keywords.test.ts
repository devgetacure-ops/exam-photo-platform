import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";

import { describe, expect, test } from "vitest";

import { buildKeywords, normalise, searchableName, toCsv, type RawRecord } from "../lib/seo-keywords";

/**
 * The keyword map (DEC-088).
 *
 * The refusals lead: no keyword names a file an examination does not ask for,
 * no figure appears that no record published, and nothing is pointed at a page
 * that does not exist unless it is marked as a page to build.
 */

const dir = path.join(process.cwd(), "..", "..", "examples", "rules");
const records: RawRecord[] = readdirSync(dir)
    .filter((name) => name.startsWith("exam_") && name.endsWith(".json"))
    .map((name) => JSON.parse(readFileSync(path.join(dir, name), "utf8")) as RawRecord);
const rows = buildKeywords(records);
const ids = new Set(records.map((r) => r.exam?.exam_id));
const byId = new Map(records.map((r) => [r.exam?.exam_id, r]));

describe("the keyword map", () => {
    test("every keyword is clean, lowercase and unique", () => {
        const seen = new Set<string>();
        for (const row of rows) {
            expect(row.keyword).toBe(normalise(row.keyword));
            expect(row.keyword).not.toMatch(/undefined|null|NaN|\s{2}/);
            expect(row.keyword, "a year said twice").not.toMatch(/\b((?:19|20)\d{2})\b.*\b\1\b/);
            expect(seen.has(row.keyword), row.keyword).toBe(false);
            seen.add(row.keyword);
        }
        expect(rows.length).toBeGreaterThan(10_000);
    });

    test("a page it points at exists, or the row says it is a page to build", () => {
        const live = /^\/($|pdf$|exams$|exam-request$|exam\/[^/]+(\/rules)?$)/;
        for (const row of rows) {
            if (row.coverage === "gap") continue;
            expect(row.target_url, row.keyword).toMatch(live);
            const exam = row.target_url.match(/^\/exam\/([^/]+)/)?.[1];
            if (exam) expect(ids.has(exam), row.keyword).toBe(true);
        }
    });

    test("an examination's file keywords only name files that examination asks for", () => {
        const words: Record<string, string> = { "thumb impression": "thumb_impression", declaration: "handwritten_declaration", signature: "signature" };
        for (const row of rows.filter((r) => r.cluster === "exam-file-size" || r.cluster === "exam-file-prepare")) {
            const record = byId.get(row.exam_ids.split("|")[0]);
            const types = new Set((record?.requirements ?? []).map((r) => r.requirement_type));
            for (const [word, type] of Object.entries(words)) {
                if (row.keyword.includes(` ${word} `) || row.keyword.endsWith(` ${word}`)) {
                    const shared = row.exam_ids.split("|").some((id) => (byId.get(id)?.requirements ?? []).some((r) => r.requirement_type === type));
                    expect(types.has(type) || shared, row.keyword).toBe(true);
                }
            }
        }
    });

    test("every KB figure in a spec keyword is one a record published", () => {
        const published = new Set<string>();
        for (const record of records) {
            const sizes = [record.image_requirements?.file_size, ...(record.requirements ?? []).map((r) => r.file_spec?.file_size)];
            for (const size of sizes) if (size?.published_maximum) published.add(String(size.published_maximum));
        }
        for (const row of rows.filter((r) => r.cluster === "spec-value")) {
            const figures = row.keyword.match(/\b(\d+)\s?(kb|mb)\b/g) ?? [];
            for (const figure of figures) {
                const n = figure.match(/\d+/)![0];
                expect(published.has(n), row.keyword).toBe(true);
            }
        }
    });

    test("the photograph and signature of every examination with both are first-priority searches", () => {
        for (const record of records) {
            const types = new Set((record.requirements ?? []).map((r) => r.requirement_type));
            const alias = record.exam?.aliases?.[0];
            if (!alias || !types.has("photograph") || !types.has("signature")) continue;
            const row = rows.find((r) => r.keyword === normalise(`${alias} photo size`));
            expect(row, record.exam?.exam_id).toBeDefined();
            expect(row!.priority).toBe(1);
        }
    });

    test("a record's name loses the catalogue's own qualifiers and its year", () => {
        expect(searchableName("RBI Officers in Grade B 2026 - prior-cycle official fallback")).toBe("rbi officers in grade b");
        expect(searchableName("ICAI Examination Portal Photograph (current portal scope)")).toBe("icai examination");
        expect(searchableName("NEET (UG) 2026")).toBe("neet ug");
    });

    test("a keyword with a comma or quote survives the CSV", () => {
        const csv = toCsv([{ keyword: 'a, "b"', cluster: "c", intent: "tool", language: "en", priority: 1, target_url: "/", coverage: "gap", exam_ids: "", basis: "x" }]);
        expect(csv.split("\n")[1]).toBe('"a, ""b""",c,tool,en,1,/,gap,,x');
    });
});
