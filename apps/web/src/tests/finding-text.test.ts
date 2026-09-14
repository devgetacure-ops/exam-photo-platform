import { describe, expect, test } from "vitest";

import { ISSUE_TEXT, plainFinding, plainFindings } from "../lib/finding-text";

/**
 * No code ever reaches a candidate (testing notes 15, 17, 19). Negative first.
 */

const CODE = /\b[A-Z]{2,}_[A-Z0-9_]+\b/;

describe("findings in plain words", () => {
    test("routine changes are never findings", () => {
        expect(plainFinding("INPUT_METADATA_REMOVED")).toBeNull();
        expect(plainFinding("INPUT_COLOUR_MODE_CONVERTED")).toBeNull();
        expect(plainFinding("INPUT_ICC_PROFILE_INVALID")).toBeNull();
    });

    test("an unknown code becomes a generic sentence, not the code", () => {
        const text = plainFinding("PIPELINE_SOMETHING_NEW_LATER");
        expect(text).not.toBeNull();
        expect(text).not.toMatch(CODE);
        expect(text).not.toMatch(/pipeline|something new later/i);
    });

    test("the crop failure the owner saw says what went wrong", () => {
        expect(plainFinding("PIPELINE_CROP_FAILED")).toMatch(/couldn't frame/i);
    });

    test("no sentence in the table contains a code", () => {
        for (const text of Object.values(ISSUE_TEXT)) expect(text).not.toMatch(CODE);
    });

    test("a sentence from the engine passes through, once", () => {
        const floor = "This photo is 17.7 KB; SBI Junior Associates 2025 asks for at least 20 KB.";
        expect(
            plainFindings([floor, "INPUT_METADATA_REMOVED", "PIPELINE_FINAL_BYTE_SIZE_BELOW_MINIMUM", floor]),
        ).toEqual([floor]);
    });
});
