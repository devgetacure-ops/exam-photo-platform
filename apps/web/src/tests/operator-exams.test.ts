import { describe, expect, it } from "vitest";
import { actionFor } from "../lib/operator/actions";

/** The console's Exams page: an examination's dates, and importing a list (DEC-136). */

function form(fields: Record<string, string>): FormData {
    const data = new FormData();
    for (const [key, value] of Object.entries(fields)) data.set(key, value);
    return data;
}

describe("exam dates from the console", () => {
    it("sends every date, the source and the reminder switch", () => {
        const planned = actionFor(
            "exam-dates",
            "jee-main-2026",
            form({
                opens_on: "2026-11-01",
                closes_on: "2026-12-10",
                extended_to: "",
                exam_date: "2027-01-22",
                exam_date_note: "Session 1",
                source_url: "https://jeemain.nta.nic.in/",
                last_verified: "2026-11-12",
                auto_remind: "yes",
                candidates: "14,52,445",
            }),
            "owner",
        );
        expect(planned).toEqual({
            path: "/v1/operator/exams/jee-main-2026/dates",
            body: {
                actor: "owner",
                opens_on: "2026-11-01",
                closes_on: "2026-12-10",
                extended_to: null,
                exam_date: "2027-01-22",
                last_verified: "2026-11-12",
                exam_date_note: "Session 1",
                source_url: "https://jeemain.nta.nic.in/",
                note: "",
                auto_remind: true,
                candidates: 1452445,
            },
        });
    });

    it("refuses a bad date or examination id", () => {
        expect("error" in actionFor("exam-dates", "jee-main-2026", form({ closes_on: "10/12/2026" }), "o")).toBe(true);
        expect("error" in actionFor("exam-dates", "../etc", form({}), "o")).toBe(true);
    });

    it("imports a bundled list as given, and refuses one that is not a list", () => {
        const entries = [{ examId: "ctet-september-2026", closes: "2026-12-20" }];
        expect(actionFor("dates-import", undefined, form({ entries: JSON.stringify(entries) }), "o")).toEqual({
            path: "/v1/operator/dates/import",
            body: { actor: "o", entries },
        });
        expect("error" in actionFor("dates-import", undefined, form({ entries: "{not json" }), "o")).toBe(true);
    });
});
