import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { RequirementUpload } from "../components/exam/requirement-upload";
import { DocumentWorkspace } from "../components/exam/document-workspace";
import { TERMS_VERSION } from "../lib/consent";
import type { PrepareRequirementResponse } from "../lib/types";
import * as api from "../lib/api-client";
import * as pdfjs from "../lib/pdfjs";

/**
 * One agreement before the first file (DEC-086, amended 2026-09-14).
 *
 * The refusals lead: no file leaves the device until the terms are agreed.
 * Then one tick is enough for every examination and every kind of file --
 * a school examination and a thumb impression included -- and it is
 * remembered rather than asked for every file.
 */

vi.mock("../lib/api-client", async () => {
    const actual = await vi.importActual<typeof api>("../lib/api-client");
    return { ...actual, prepareRequirement: vi.fn(), planDocument: vi.fn() };
});

vi.mock("../lib/pdfjs", async () => {
    const actual = await vi.importActual<typeof pdfjs>("../lib/pdfjs");
    return { ...actual, isPasswordLocked: vi.fn(async () => false) };
});

const prepareRequirement = vi.mocked(api.prepareRequirement);
const planDocument = vi.mocked(api.planDocument);

const image = () => new File(["x".repeat(64)], "file.jpg", { type: "image/jpeg" });

function prepared(examId: string, type: string): PrepareRequirementResponse {
    return {
        job_id: "job_1",
        exam_id: examId,
        requirement_id: "file",
        requirement_type: type,
        platform_support: "supported",
        status: "SUCCEEDED",
        outcome: "prepared",
        findings: [],
        issue_codes: [],
        output_filename: "file.jpg",
        byte_size: 14000,
    } as PrepareRequirementResponse;
}

function upload(examId: string, type = "signature", name = "Candidate signature") {
    return render(
        <RequirementUpload
            examId={examId}
            examName="Examination"
            requirementId="file"
            requirementName={name}
            requirementType={type}
        />,
    );
}

function addFile(name = "Candidate signature") {
    fireEvent.change(screen.getByLabelText(`Upload for ${name}`), {
        target: { files: [image()] },
    });
}

describe("agreeing before the first file", () => {
    beforeEach(() => {
        window.localStorage.clear();
        prepareRequirement.mockReset();
        planDocument.mockReset();
    });
    afterEach(() => {
        cleanup();
        vi.clearAllMocks();
    });

    test("no file leaves the device until the terms are agreed", async () => {
        upload("ssc-junior-engineer-examination");
        addFile();

        expect(await screen.findByRole("alert")).toHaveTextContent(/tick this first/i);
        expect(prepareRequirement).not.toHaveBeenCalled();
    });

    test("one tick, worded as the owner approved, with both policies linked", () => {
        upload("ssc-junior-engineer-examination");

        expect(screen.getAllByRole("checkbox")).toHaveLength(1);
        expect(
            screen.getByRole("checkbox", {
                name: "I have read and agree to the terms and conditions and the privacy policy.",
            }),
        ).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "terms and conditions" })).toHaveAttribute("href", "/terms");
        expect(screen.getByRole("link", { name: "privacy policy" })).toHaveAttribute("href", "/privacy");
    });

    test.each([
        ["an examination whose candidates can be under 18", "neet-ug-2026", "signature", "Candidate signature"],
        ["a school examination", "jawahar-navodaya-vidyalaya-selection-test-class-vi", "photograph", "Photograph"],
        ["a thumb impression", "sbi-probationary-officers-2025", "thumb_impression", "Thumb impression"],
    ])("%s asks for the same single tick and nothing more", (_label, examId, type, name) => {
        upload(examId, type, name);
        expect(screen.getAllByRole("checkbox")).toHaveLength(1);
        expect(screen.queryByText(/18 or older|parent or guardian|thumb impression being used/i)).toBeNull();
    });

    test("once agreed, the file goes, and no upload anywhere asks again", async () => {
        prepareRequirement.mockResolvedValue(prepared("neet-ug-2026", "thumb_impression"));
        upload("neet-ug-2026", "thumb_impression", "Thumb impression");
        fireEvent.click(screen.getByRole("checkbox", { name: /terms and conditions/i }));
        addFile("Thumb impression");

        await waitFor(() => expect(prepareRequirement).toHaveBeenCalled());
        expect(window.localStorage.getItem("uploadready:terms-accepted")).toBe(TERMS_VERSION);

        cleanup();
        upload("ssc-junior-engineer-examination");
        expect(screen.queryByRole("checkbox")).toBeNull();
    });

    test("an agreement to an earlier version of the terms asks again", () => {
        window.localStorage.setItem("uploadready:terms-accepted", "2026-09-13");
        upload("ssc-junior-engineer-examination");
        expect(screen.getAllByRole("checkbox")).toHaveLength(1);
    });

    test("unticking takes the agreement back", () => {
        upload("ssc-junior-engineer-examination");
        const box = screen.getByRole("checkbox", { name: /terms and conditions/i });
        fireEvent.click(box);
        fireEvent.click(box);

        expect(window.localStorage.getItem("uploadready:terms-accepted")).toBeNull();
    });

    test("a document upload is held back the same way", async () => {
        render(
            <DocumentWorkspace
                examId="cuet-ug-2026"
                examName="CUET (UG) 2026"
                requirementId="certificate"
                requirementName="Class 10 certificate"
                partiallySupported={false}
            />,
        );
        fireEvent.change(screen.getByLabelText(/source files for class 10 certificate/i), {
            target: { files: [new File(["%PDF-1.4"], "marks.pdf", { type: "application/pdf" })] },
        });

        expect(await screen.findByRole("alert")).toBeInTheDocument();
        expect(planDocument).not.toHaveBeenCalled();
    });
});
