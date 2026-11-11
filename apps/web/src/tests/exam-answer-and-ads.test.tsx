import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { ExamAnswer } from "../components/exam/exam-answer";
import { examQuickAnswer } from "../lib/exam-answers";
import type { ExamDetail } from "../lib/types";

/** The answer first, and no ads until AdSense is configured (DEC-127). */

afterEach(() => {
    cleanup();
    vi.unstubAllEnvs();
    vi.resetModules();
});

const exam = {
    exam_id: "ctet-test",
    exam_name: "CTET 2026",
    conducting_body: "Central Board of Secondary Education",
    source_evidence: [
        {
            source_type: "notice",
            official_source: true,
            document_title: "CTET information bulletin",
            source_url: "https://example.org/bulletin.pdf",
        },
    ],
    requirements: [],
} as unknown as ExamDetail;

describe("the answer card", () => {
    it("renders nothing for a record with no published figures", () => {
        const { container } = render(<ExamAnswer exam={exam} />);
        expect(container).toBeEmptyDOMElement();
        expect(examQuickAnswer(exam)).toBeNull();
    });
});

describe("ad slots", () => {
    it("render nothing without a publisher id", async () => {
        vi.stubEnv("NEXT_PUBLIC_ADSENSE_CLIENT", "");
        const { AdSlot } = await import("../components/ad-slot");
        const { container } = render(<AdSlot name="exam-after-kit" />);
        expect(container).toBeEmptyDOMElement();
    });

    it("render a labelled unit once the publisher and slot ids are set", async () => {
        vi.stubEnv("NEXT_PUBLIC_ADSENSE_CLIENT", "ca-pub-0000000000000000");
        vi.stubEnv("NEXT_PUBLIC_ADSENSE_SLOTS", "exam-after-kit=1234567890");
        const { AdSlot } = await import("../components/ad-slot");
        render(<AdSlot name="exam-after-kit" />);
        expect(screen.getByText("Advertisement")).toBeInTheDocument();
        expect(document.querySelector("ins.adsbygoogle")).toHaveAttribute("data-ad-slot", "1234567890");
    });

    it("a slot without its own id stays empty", async () => {
        vi.stubEnv("NEXT_PUBLIC_ADSENSE_CLIENT", "ca-pub-0000000000000000");
        vi.stubEnv("NEXT_PUBLIC_ADSENSE_SLOTS", "rules-mid=1234567890");
        const { AdSlot } = await import("../components/ad-slot");
        const { container } = render(<AdSlot name="exam-after-kit" />);
        expect(container).toBeEmptyDOMElement();
    });
});
