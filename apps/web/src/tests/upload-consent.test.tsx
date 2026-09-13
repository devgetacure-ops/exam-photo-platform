import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";

import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { RequirementUpload } from "../components/exam/requirement-upload";
import { DocumentWorkspace } from "../components/exam/document-workspace";
import { TERMS_VERSION, UNDER_18 } from "../lib/consent";
import type { PrepareRequirementResponse } from "../lib/types";
import * as api from "../lib/api-client";
import * as pdfjs from "../lib/pdfjs";

/**
 * The agreements before the first file (DEC-086).
 *
 * The refusals lead: no file leaves the device until every agreement this
 * upload needs is given, and a candidate who can be under 18 or a thumb
 * impression each add their own. Then that one tick is enough for an adult,
 * and that it is remembered rather than asked for every file.
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

    test("an adult's signature needs one tick, with both policies linked", () => {
        upload("ssc-junior-engineer-examination");

        expect(screen.getAllByRole("checkbox")).toHaveLength(1);
        expect(screen.getByRole("link", { name: "terms and conditions" })).toHaveAttribute("href", "/terms");
        expect(screen.getByRole("link", { name: "privacy policy" })).toHaveAttribute("href", "/privacy");
    });

    test("once agreed, the file goes, and the next upload does not ask again", async () => {
        prepareRequirement.mockResolvedValue(prepared("ssc-junior-engineer-examination", "signature"));
        upload("ssc-junior-engineer-examination");
        fireEvent.click(screen.getByRole("checkbox", { name: /terms and conditions/i }));
        addFile();

        await waitFor(() => expect(prepareRequirement).toHaveBeenCalled());
        expect(window.localStorage.getItem("uploadready:terms-accepted")).toBe(TERMS_VERSION);

        cleanup();
        upload("ssc-junior-engineer-examination");
        expect(screen.queryByRole("checkbox")).toBeNull();
    });

    test("unticking takes the agreement back", () => {
        upload("ssc-junior-engineer-examination");
        const box = screen.getByRole("checkbox", { name: /terms and conditions/i });
        fireEvent.click(box);
        fireEvent.click(box);

        expect(window.localStorage.getItem("uploadready:terms-accepted")).toBeNull();
    });

    test("a candidate who can be under 18 needs a parent's or guardian's agreement too", async () => {
        prepareRequirement.mockResolvedValue(prepared("neet-ug-2026", "signature"));
        upload("neet-ug-2026");
        fireEvent.click(screen.getByRole("checkbox", { name: /terms and conditions/i }));
        addFile();

        expect(await screen.findByRole("alert")).toBeInTheDocument();
        expect(prepareRequirement).not.toHaveBeenCalled();

        fireEvent.click(
            screen.getByRole("checkbox", { name: /18 or older, or my parent or guardian agrees/i }),
        );
        addFile();
        await waitFor(() => expect(prepareRequirement).toHaveBeenCalled());
    });

    test("a school examination asks as the child's parent or guardian", () => {
        upload("jawahar-navodaya-vidyalaya-selection-test-class-vi");

        expect(
            screen.getByRole("checkbox", { name: /i am the candidate’s parent or guardian/i }),
        ).toBeInTheDocument();
    });

    test("a thumb impression asks for its own agreement, and only that file does", () => {
        window.localStorage.setItem("uploadready:terms-accepted", TERMS_VERSION);
        upload("sbi-probationary-officers-2025", "thumb_impression", "Thumb impression");

        // The terms stay on show, already ticked, beside the one still missing.
        expect(screen.getAllByRole("checkbox")).toHaveLength(2);
        expect(screen.getByRole("checkbox", { name: /terms and conditions/i })).toBeChecked();
        expect(
            screen.getByRole("checkbox", { name: /thumb impression being used only to prepare/i }),
        ).not.toBeChecked();

        cleanup();
        upload("sbi-probationary-officers-2025");
        expect(screen.queryByRole("checkbox")).toBeNull();
    });

    test("a document upload is held back the same way", async () => {
        window.localStorage.setItem("uploadready:terms-accepted", TERMS_VERSION);
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

    test("every examination on the under-18 list is one the catalogue has", () => {
        const dir = path.join(process.cwd(), "..", "..", "examples", "rules");
        const ids = new Set(
            readdirSync(dir)
                .filter((file) => file.startsWith("exam_") && file.endsWith(".json"))
                .map((file) => {
                    const record = JSON.parse(readFileSync(path.join(dir, file), "utf8")) as {
                        exam_id?: string;
                        exam?: { exam_id?: string };
                    };
                    return record.exam_id ?? record.exam?.exam_id;
                }),
        );
        const stale = Object.keys(UNDER_18).filter((id) => !ids.has(id));

        expect(stale).toEqual([]);
    });
});
