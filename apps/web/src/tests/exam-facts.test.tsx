import { afterEach, describe, expect, test } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import {
    ExamFacts,
    factAttribution,
    factUrl,
    type ExamFact,
} from "../components/exam/exam-facts";

/**
 * Whose word a fact is (DEC-082).
 *
 * Reputable publications may now be a source as well as the authority. The
 * one thing that must never happen is a newspaper's figure reading as the
 * examination's own statement, so these start from that.
 */

afterEach(cleanup);

const reported: ExamFact = {
    kind: "volume",
    text: "A total of 3,23,313 candidates appeared for the examination.",
    source: "NDTV (https://www.ndtv.com/education/example)",
    official: false,
    reported_by: "NDTV",
};

const official: ExamFact = {
    kind: "structure",
    text: "GATE 2026 will be conducted for 30 test papers.",
    source: "GATE 2026 (https://gate2026.iitg.ac.in/exam-papers-and-syllabus.html)",
    official: true,
    reported_by: "GATE 2026, IIT Guwahati",
};

const derived: ExamFact = {
    kind: "rejection",
    text: "Applications with a blurred photograph will be rejected.",
    source: "Notice (https://example.gov.in/notice.pdf)",
};

describe("fact attribution", () => {
    test("a reported figure never reads as the authority's own word", () => {
        expect(factAttribution(reported)).toBe("Reported by NDTV");
        expect(factAttribution(reported)).not.toMatch(/^From /);
    });

    test("an unset official flag with a publisher is treated as reported, not official", () => {
        expect(factAttribution({ ...reported, official: null })).toBe("Reported by NDTV");
    });

    test("an official fact names the authority it came from", () => {
        expect(factAttribution(official)).toBe("From GATE 2026, IIT Guwahati");
    });

    test("a derived fact keeps the plain link, with no publisher invented", () => {
        expect(factAttribution(derived)).toBe("Read it in the source");
        expect(factAttribution({ ...derived, reported_by: "   " })).toBe("Read it in the source");
    });

    test("a link goes to the URL inside the source, never to the source label", () => {
        // The phone sheet once used `source` as the href, which reads
        // "Title (https://…)" and led nowhere.
        expect(factUrl(reported)).toBe("https://www.ndtv.com/education/example");
        expect(factUrl(reported)).not.toContain("(");
        expect(factUrl({ ...derived, source: "Notice, page 4" })).toBeUndefined();
    });

    test("the panel shows the attribution and a label for a researched kind", () => {
        render(<ExamFacts facts={[reported]} examName="Bihar D.El.Ed" />);

        expect(screen.getByRole("link", { name: /Reported by NDTV/ })).toHaveAttribute(
            "href",
            "https://www.ndtv.com/education/example",
        );
        expect(screen.getByText("How many candidates")).toBeInTheDocument();
        expect(screen.queryByText("From the notice")).toBeNull();
    });
});
