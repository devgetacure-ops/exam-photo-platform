import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { LocaleProvider } from "../components/locale-context";
import { KitDownloads } from "../components/exam/kit-downloads";
import { toolText } from "../lib/i18n-tool";
import { ISSUE_TEXT, RETAKE_GUIDANCE, ROUTINE_NOTES } from "../lib/finding-text";
import type { ExamDetail } from "../lib/types";

/** The preparation tool in Hindi (DEC-129). */

vi.mock("../lib/kit-state", () => ({ getKit: () => ({ kitId: "kit_test" }) }));

beforeEach(() => {
    vi.stubGlobal(
        "fetch",
        vi.fn(async () => ({ ok: true, status: 200, json: async () => ({}) })),
    );
});
afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
});

const exam = { exam_id: "t", exam_name: "Test", requirements: [] } as unknown as ExamDetail;

describe("the tool in Hindi", () => {
    it("speaks Hindi inside a Hindi provider and English outside one", () => {
        render(
            <LocaleProvider locale="hi">
                <KitDownloads exam={exam} entries={{}} />
            </LocaleProvider>,
        );
        expect(screen.getByText("आपके डाउनलोड यहाँ दिखेंगे")).toBeInTheDocument();
        cleanup();
        render(<KitDownloads exam={exam} entries={{}} />);
        expect(screen.getByText("Your downloads appear here")).toBeInTheDocument();
    });

    it("has Hindi for every finding the engine can report", () => {
        const sentences = [...Object.values(ISSUE_TEXT), ...Object.values(ROUTINE_NOTES), RETAKE_GUIDANCE];
        const untranslated = sentences.filter((text) => toolText("hi", text) === text);
        expect(untranslated).toEqual([]);
    });

    it("leaves a notice's own words alone", () => {
        const quoted = "Candidates must upload a recent colour photograph.";
        expect(toolText("hi", quoted)).toBe(quoted);
    });
});
