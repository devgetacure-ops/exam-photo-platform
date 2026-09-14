import { afterEach, describe, expect, test } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { OutcomeResult } from "../components/exam/outcome-result";
import type { PrepareRequirementResponse } from "../lib/types";

/**
 * Testing notes 15, 17 and 19: routine changes are not findings, no code is
 * ever on screen, and a photograph we could not prepare says how to retake it.
 */

afterEach(cleanup);

const CODE = /\b[A-Z]{2,}_[A-Z0-9_]+\b/;

function result(patch: Partial<PrepareRequirementResponse>): PrepareRequirementResponse {
    return {
        job_id: "job_1",
        exam_id: "neet-ug-2026",
        requirement_id: "candidate_signature",
        requirement_type: "signature",
        platform_support: "supported",
        status: "SUCCEEDED",
        outcome: "prepared",
        findings: [],
        issue_codes: [],
        output_filename: "neet-ug_signature.jpg",
        byte_size: 14000,
        ...patch,
    } as PrepareRequirementResponse;
}

describe("outcomes in plain words", () => {
    test("routine changes on an old kit do not make a file 'something to check'", () => {
        const { container } = render(
            <OutcomeResult
                result={result({
                    outcome: "prepared_with_findings",
                    findings: ["INPUT_COLOUR_MODE_CONVERTED", "INPUT_METADATA_REMOVED"],
                })}
                requirementName="Candidate signature"
                onReplace={() => {}}
            />,
        );
        expect(screen.getByText("Ready")).toBeInTheDocument();
        expect(screen.queryByText(/worth checking/i)).toBeNull();
        expect(container.textContent).not.toMatch(CODE);
        expect(screen.getByText(/What we changed \(2\)/)).toBeInTheDocument();
    });

    test("changes reported separately are listed, never as findings", () => {
        render(
            <OutcomeResult
                result={result({ changes: ["INPUT_METADATA_REMOVED"] })}
                requirementName="Candidate signature"
                onReplace={() => {}}
            />,
        );
        expect(screen.getByText(/Removed hidden camera data/)).toBeInTheDocument();
        expect(screen.getByText("Ready")).toBeInTheDocument();
    });

    test("a real finding is shown, in its own words", () => {
        const floor = "This file is 5.0 KB; NEET (UG) 2026 asks for at least 10 KB.";
        render(
            <OutcomeResult
                result={result({ outcome: "prepared_with_findings", findings: [floor] })}
                requirementName="Candidate signature"
                onReplace={() => {}}
            />,
        );
        expect(screen.getByText(floor)).toBeInTheDocument();
    });

    test("a photograph we could not frame says why and how to retake it, with no code", () => {
        const { container } = render(
            <OutcomeResult
                result={result({
                    requirement_type: "photograph",
                    status: "FAILED",
                    outcome: "blocked",
                    is_valid: false,
                    issue_codes: ["PIPELINE_CROP_FAILED"],
                })}
                requirementName="Candidate photograph"
                onReplace={() => {}}
            />,
        );
        expect(screen.getByText(/couldn't frame a photo/i)).toBeInTheDocument();
        expect(screen.getByText(/whole head and shoulders/i)).toBeInTheDocument();
        expect(container.textContent).not.toMatch(CODE);
        expect(container.textContent).not.toMatch(/pipeline crop failed/i);
    });
});
