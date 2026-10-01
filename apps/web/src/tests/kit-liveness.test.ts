import { describe, expect, test } from "vitest";

import { entryLive, jobGone, resultFromEntry } from "../lib/kit-liveness";
import type { KitEntry } from "../lib/kit-state";

/**
 * "Ready" has to mean the file still exists (owner's testing, 1 October): the
 * phone went on calling a deleted file ready and led a candidate to pay for it.
 */
const NOW = Date.parse("2026-10-01T12:00:00Z");

function entry(overrides: Partial<KitEntry> = {}): KitEntry {
    return {
        jobId: "job_a",
        requirementId: "candidate_photograph",
        requirementType: "photograph",
        status: "SUCCEEDED",
        outcome: "prepared",
        previewUrl: "/v1/jobs/job_a/preview",
        expiresAt: "2026-10-01T12:20:00Z",
        findings: [],
        updatedAt: "2026-10-01T11:50:00Z",
        ...overrides,
    } as KitEntry;
}

describe("whether a remembered file is still a file", () => {
    test("a prepared file inside its window is live", () => {
        expect(entryLive(entry(), undefined, NOW)).toBe(true);
    });

    test("past its deletion time it is not, without asking anyone", () => {
        expect(entryLive(entry({ expiresAt: "2026-10-01T11:59:00Z" }), undefined, NOW)).toBe(false);
    });

    test("the server's word outranks the stored time, both ways", () => {
        // Kept for longer: the stored time has passed, the server's has not.
        expect(
            entryLive(
                entry({ expiresAt: "2026-10-01T11:59:00Z" }),
                { status: "SUCCEEDED", expires_at: "2026-10-01T12:40:00Z" },
                NOW,
            ),
        ).toBe(true);
        // Deleted early by the candidate: the stored time has not passed.
        expect(entryLive(entry(), { status: "DELETED" }, NOW)).toBe(false);
        expect(jobGone({ status: "deleted" }, NOW)).toBe(true);
    });

    test("a file that was never prepared is never live", () => {
        expect(entryLive(entry({ outcome: "not_produced" as KitEntry["outcome"] }), undefined, NOW)).toBe(false);
        expect(entryLive(undefined, undefined, NOW)).toBe(false);
    });

    test("a remembered file can be shown again as a result", () => {
        const result = resultFromEntry(entry({ outputFilename: "otet_photo.jpg" }), "otet");
        expect(result).toMatchObject({
            job_id: "job_a",
            exam_id: "otet",
            outcome: "prepared",
            preview_url: "/v1/jobs/job_a/preview",
            preview_watermarked: true,
            output_filename: "otet_photo.jpg",
        });
    });
});
