import { describe, expect, it } from "vitest";
import { byUrgency, byVolume, deadlineStatus, stampText, type Deadline } from "../lib/deadlines";

/** What a deadline means on a given day (DEC-135). */

function entry(over: Partial<Deadline>): Deadline {
    return {
        examId: "x",
        examName: "Example Exam",
        shortName: null,
        conductingBody: null,
        opens: null,
        closes: null,
        extendedTo: null,
        examDate: null,
        examDateNote: null,
        sourceUrl: null,
        lastVerified: null,
        ...over,
    };
}

describe("deadline status", () => {
    const e = entry({ opens: "2026-12-01", closes: "2026-12-20", examDate: "2027-01-15" });

    it("is opening before registration opens", () => {
        expect(deadlineStatus(e, "2026-11-25")).toMatchObject({ state: "opening", days: 6 });
        expect(stampText(deadlineStatus(e, "2026-11-25"), "2026-11-25")).toBe("Opens in 6 days");
    });

    it("is open with more than a week left, closing within a week", () => {
        expect(deadlineStatus(e, "2026-12-05").state).toBe("open");
        expect(deadlineStatus(e, "2026-12-14")).toMatchObject({ state: "closing", days: 6 });
    });

    it("says last day on the last day and is still open", () => {
        const status = deadlineStatus(e, "2026-12-20");
        expect(status).toMatchObject({ state: "closing", days: 0 });
        expect(stampText(status, "2026-12-20")).toBe("Last day today");
    });

    it("counts to an extension and marks it", () => {
        const extended = { ...e, extendedTo: "2026-12-27" };
        const status = deadlineStatus(extended, "2026-12-22");
        expect(status).toMatchObject({ state: "extended", lastDate: "2026-12-27" });
        expect(stampText(status, "2026-12-22")).toMatch(/^Extended/);
    });

    it("is exam-ahead after the last date, then past after the exam", () => {
        expect(deadlineStatus(e, "2026-12-21").state).toBe("exam-ahead");
        expect(deadlineStatus(e, "2027-01-16").state).toBe("past");
    });

    it("puts the soonest last date first", () => {
        const a = entry({ examId: "a", closes: "2026-12-30" });
        const b = entry({ examId: "b", closes: "2026-12-10" });
        const c = entry({ examId: "c", opens: "2026-12-02", closes: "2026-12-31" });
        const order = [a, b, c].sort(byUrgency("2026-12-01")).map((x) => x.examId);
        expect(order).toEqual(["b", "a", "c"]);
    });

    it("puts bigger examinations first, then the soonest, then those with no count (DEC-137)", () => {
        const small = entry({ examId: "small", closes: "2026-12-05", candidates: 90000 });
        const big = entry({ examId: "big", closes: "2026-12-30", candidates: 1400000 });
        const unknownSoon = entry({ examId: "u1", closes: "2026-12-03" });
        const unknownLate = entry({ examId: "u2", closes: "2026-12-20", candidates: null });
        const order = [unknownLate, small, unknownSoon, big].sort(byVolume("2026-12-01")).map((x) => x.examId);
        expect(order).toEqual(["big", "small", "u1", "u2"]);
    });

    it("speaks Hindi", () => {
        expect(stampText(deadlineStatus(e, "2026-12-20"), "2026-12-20", "hi")).toBe("आज आख़िरी दिन");
    });
});
