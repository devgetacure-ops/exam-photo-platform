import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { KitDownloads } from "../components/exam/kit-downloads";
import type { ExamDetail } from "../lib/types";
import type { KitEntry } from "../lib/kit-state";

/** The free downloads screen (DEC-127): files, a clock, no price. */

vi.mock("../lib/kit-state", () => ({
    getKit: () => ({ kitId: "kit_test" }),
}));

const entry = (id: string, requirementId: string): KitEntry => ({
    jobId: id,
    requirementId,
    requirementType: "photograph",
    status: "SUCCEEDED",
    outcome: "prepared",
    findings: [],
    updatedAt: "2026-11-11",
    outputFilename: `${requirementId}.jpg`,
});
const exam = {
    exam_id: "test",
    exam_name: "Test examination",
    requirements: [
        { requirement_id: "photo", requirement_name: "Photograph", platform_support: "supported" },
        { requirement_id: "sign", requirement_name: "Signature", platform_support: "supported" },
    ],
} as ExamDetail;

beforeEach(() => {
    vi.stubGlobal(
        "fetch",
        vi.fn(async (url: URL | string) => {
            const id = String(url).split("/v1/jobs/")[1];
            return {
                ok: true,
                status: 200,
                json: async () => ({
                    job_id: id,
                    status: "SUCCEEDED",
                    entitlement: "released",
                    expires_at: new Date(Date.now() + 600_000).toISOString(),
                    output_url: `/v1/jobs/${id}/output`,
                    output_filename: "photo.jpg",
                }),
            };
        }),
    );
});
afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
});

describe("free downloads", () => {
    it("says where the files will appear before any is prepared", () => {
        render(<KitDownloads exam={exam} entries={{}} />);
        expect(screen.getByText(/Your downloads appear here/)).toBeInTheDocument();
    });

    it("offers each prepared file for download, with no price anywhere", async () => {
        const { container } = render(
            <KitDownloads
                exam={exam}
                entries={{ photo: entry("job_a", "photo"), sign: entry("job_b", "sign") }}
            />,
        );
        expect(await screen.findAllByRole("link", { name: "Download file" })).toHaveLength(2);
        expect(screen.getByRole("link", { name: /Download everything/ })).toBeInTheDocument();
        expect(container.textContent).not.toMatch(/₹|pay|paid|watermark/i);
    });
});
