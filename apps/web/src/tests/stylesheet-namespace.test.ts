import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

/**
 * One class name, one owner.
 *
 * Every stylesheet here is global, so a class invented for one page silently
 * inherits whatever a sheet loaded elsewhere already gave that name. It has
 * cost real work: a drafting sheet picked up the phone sheet's padding, and a
 * line drawing came out as a solid orange block because `euk-mark` was already
 * the highlighter behind a headline.
 *
 * A name may be shared only on purpose, by adding it below with the reason.
 * Anything else is a collision waiting to be found in a screenshot.
 */
const SHARED: Record<string, string> = {
    "euk-chip": "the same chip appears on the landing page and an exam page",
    "euk-chips": "its row",
    "euk-exam-files": "the exam page's file list, restyled for a phone",
    "euk-exam-tip": "same, on a phone",
    "euk-kit": "the kit panel, which the phone build hides",
    "euk-label": "the small caps label, used everywhere",
    "euk-link": "the underlined link, used everywhere",
    "euk-measure": "the reading measure, shared by the exam and rules pages",
    "euk-pdfimg-caution": "the converter's caution, shown on both pages",
    "euk-section": "the section rhythm, shared by the landing and PDF pages",
};

function sheets(): { name: string; text: string }[] {
    const dir = join(process.cwd(), "src", "app");
    return readdirSync(dir)
        .filter((f) => f.endsWith(".css"))
        .map((name) => ({ name, text: readFileSync(join(dir, name), "utf8") }));
}

describe("stylesheet namespaces", () => {
    it("defines each euk- class in exactly one stylesheet", () => {
        const owners = new Map<string, Set<string>>();
        for (const sheet of sheets()) {
            for (const match of sheet.text.matchAll(/\.(euk-[a-z0-9-]+)/g)) {
                const cls = match[1];
                const set = owners.get(cls) ?? new Set<string>();
                set.add(sheet.name);
                owners.set(cls, set);
            }
        }

        const collisions = [...owners.entries()]
            .filter(([cls, files]) => files.size > 1 && !(cls in SHARED))
            .map(([cls, files]) => `${cls} in ${[...files].sort().join(", ")}`);

        expect(collisions).toEqual([]);
    });
});
