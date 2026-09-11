import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { DocumentWorkspace } from "../components/exam/document-workspace";
import * as api from "../lib/api-client";
import * as pdfjs from "../lib/pdfjs";

vi.mock("../lib/api-client", async () => {
    const actual = await vi.importActual<typeof api>("../lib/api-client");
    return { ...actual, planDocument: vi.fn(), assembleDocument: vi.fn() };
});

vi.mock("../lib/pdfjs", async () => {
    const actual = await vi.importActual<typeof pdfjs>("../lib/pdfjs");
    return { ...actual, isPasswordLocked: vi.fn(async () => false) };
});

const planDocument = vi.mocked(api.planDocument);
const assembleDocument = vi.mocked(api.assembleDocument);
const isPasswordLocked = vi.mocked(pdfjs.isPasswordLocked);

function renderWorkspace() {
    return render(
        <DocumentWorkspace
            examId="exam"
            examName="Exam"
            requirementId="certificate"
            requirementName="Class 10 certificate"
            partiallySupported={false}
        />,
    );
}

async function planTwoPages() {
    planDocument.mockResolvedValue({
        job_id: "job_doc",
        exam_id: "exam",
        requirement_id: "certificate",
        pages: [
            { source_index: 0, page_index: 0, origin: "document_scan", rotation: 0 },
            { source_index: 0, page_index: 1, origin: "document_scan", rotation: 0 },
        ],
        unreadable: {},
    });
    renderWorkspace();
    const file = new File(["%PDF-1.4"], "marks.pdf", { type: "application/pdf" });
    fireEvent.change(screen.getByLabelText(/source files for class 10 certificate/i), {
        target: { files: [file] },
    });
    await screen.findByRole("button", { name: "Rotate page 1 clockwise" });
}

describe("arranging a document", () => {
    beforeEach(() => {
        window.localStorage.clear();
        planDocument.mockReset();
        assembleDocument.mockReset();
    });
    afterEach(() => cleanup());

    test("rotation turns a page by quarters and reaches the engine with the order", async () => {
        await planTwoPages();
        const rotate = screen.getByRole("button", { name: "Rotate page 2 clockwise" });
        fireEvent.click(rotate);
        fireEvent.click(rotate);
        expect(screen.getByText(/turned 180°/)).toBeInTheDocument();

        assembleDocument.mockResolvedValue({
            job_id: "job_doc",
            exam_id: "exam",
            requirement_id: "certificate",
            requirement_type: "certificate_scan",
            platform_support: "supported",
            status: "SUCCEEDED",
            outcome: "prepared",
            findings: [],
            issue_codes: [],
        });
        fireEvent.click(screen.getByRole("button", { name: "Prepare 2 pages" }));
        await waitFor(() => expect(assembleDocument).toHaveBeenCalled());
        const [, order] = assembleDocument.mock.calls[0];
        expect(order?.map((page) => page.rotation)).toEqual([0, 180]);
    });

    test("four quarter turns come back upright", async () => {
        await planTwoPages();
        const rotate = screen.getByRole("button", { name: "Rotate page 1 clockwise" });
        for (let i = 0; i < 4; i++) fireEvent.click(rotate);
        expect(screen.queryByText(/turned/)).toBeNull();
    });

    test("the PDF to image tool is offered alongside, and says what it costs", () => {
        renderWorkspace();
        expect(screen.getByText("Need a page as an image?")).toBeInTheDocument();
        expect(
            screen.getByText(/can’t be verified the way the PDF can/),
        ).toBeInTheDocument();
    });

    test("a password-protected PDF is turned away before anything is uploaded", async () => {
        isPasswordLocked.mockResolvedValueOnce(false).mockResolvedValueOnce(true);
        renderWorkspace();
        fireEvent.change(screen.getByLabelText(/source files for class 10 certificate/i), {
            target: {
                files: [
                    new File(["%PDF-1.7"], "marks.pdf", { type: "application/pdf" }),
                    new File(["%PDF-1.7"], "aadhaar.pdf", { type: "application/pdf" }),
                ],
            },
        });

        expect(await screen.findByRole("alert")).toHaveTextContent(
            "aadhaar.pdf is password-protected, so we can’t open it. Upload a copy of the PDF without a password.",
        );
        expect(planDocument).not.toHaveBeenCalled();
    });

    test("a file the engine couldn't read is named once", async () => {
        planDocument.mockResolvedValue({
            job_id: "job_doc",
            exam_id: "exam",
            requirement_id: "certificate",
            pages: [{ source_index: 1, page_index: 0, origin: "document_scan", rotation: 0 }],
            unreadable: { 0: "marks.pdf: the PDF is damaged." },
        });
        renderWorkspace();
        fireEvent.change(screen.getByLabelText(/source files for class 10 certificate/i), {
            target: {
                files: [
                    new File(["%PDF-1.7"], "marks.pdf", { type: "application/pdf" }),
                    new File(["x"], "scan.jpg", { type: "image/jpeg" }),
                ],
            },
        });

        const warning = await screen.findByRole("alert");
        expect(warning).toHaveTextContent("marks.pdf: the PDF is damaged.");
        expect(warning.textContent).not.toContain("marks.pdf: marks.pdf");
    });
});
