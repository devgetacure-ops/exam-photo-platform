import { describe, expect, it } from "vitest";
import { candidateError } from "../components/exam/requirement-upload";
import { ApiStatusError } from "../lib/api-client";

/** What a candidate reads when a preparation is refused (DEC-130, DEC-134). */
const en = (english: string) => english;

describe("refusal messages", () => {
    it("tells a candidate who hit the hourly limit to wait, not that we are busy", () => {
        const error = new ApiStatusError(
            "Too many files prepared in the last hour. Please try again in about 12 minutes.",
            429,
        );
        expect(candidateError(error, en)).toMatch(/a lot of files in the last hour/);
    });

    it("still calls a full queue busy", () => {
        const error = new ApiStatusError("All preparation slots are busy. Please retry in a few seconds.", 429);
        expect(candidateError(error, en)).toMatch(/busy right now/);
    });
});
