import { afterEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

vi.mock("pdfjs-dist", () => ({
    GlobalWorkerOptions: { workerSrc: "pdf.worker.min.mjs" },
    getDocument: vi.fn(),
}));

import { PdfToImage } from "../components/exam/pdf-to-image";
import { PhonePdf } from "../components/m/pdf-home";
import { AnswerSearch } from "../components/m/answer-search";
import { PhonePolicy } from "../components/m/policy-phone";
import { PDF_JOBS } from "../lib/pdf-work";

/**
 * Phase 3 of the phone build: the PDF work, support and the policies.
 *
 * The negative cases lead. The PDF work must not present a job that needs a
 * prepared file as a tool anybody can start; the desktop converter must keep
 * its settings above the picker; a search that matches nothing must hand the
 * candidate the next step rather than an empty screen.
 */

afterEach(cleanup);

function follows(a: HTMLElement, b: HTMLElement): boolean {
    return Boolean(b.compareDocumentPosition(a) & Node.DOCUMENT_POSITION_FOLLOWING);
}

describe("PDF to image on its own screen", () => {
    test("the desktop converter still sets its options above the picker", () => {
        render(<PdfToImage />);

        const choose = screen.getByRole("button", { name: "Choose a PDF" });
        const format = screen.getByRole("group", { name: "Save as" });
        expect(follows(choose, format)).toBe(true);
        expect(document.querySelector("[data-layout]")).toBeNull();
        expect(document.querySelector("details")).toBeNull();
    });

    test("picker first puts the picker first and folds the options under it", () => {
        render(<PdfToImage pickerFirst />);

        const choose = screen.getByRole("button", { name: "Choose a PDF" });
        const format = screen.getByRole("group", { name: "Save as" });
        expect(follows(format, choose)).toBe(true);
        expect(choose).toHaveClass("primary-button");

        const settings = document.querySelector("details") as HTMLDetailsElement;
        expect(settings).not.toBeNull();
        expect(settings.open).toBe(false);
        expect(settings.querySelector("summary")?.textContent).toMatch(/JPEG, 150 dpi/);
        expect(settings.contains(format)).toBe(true);
    });
});

describe("the PDF work on a phone", () => {
    test("only the converter is offered as a tool to start; the jobs open a sheet", () => {
        render(<PhonePdf />);

        expect(screen.getByRole("link", { name: /A PDF page as an image/ })).toHaveAttribute(
            "href",
            "/pdf/to-image",
        );
        for (const job of PDF_JOBS) {
            // A job that needs a prepared file is never a link to a tool.
            expect(screen.queryByRole("link", { name: job.title })).toBeNull();
            expect(screen.getByRole("button", { name: job.title })).toBeInTheDocument();
        }
    });

    test("a job's sheet says what it is and how to get it", () => {
        render(<PhonePdf />);
        const job = PDF_JOBS[0];

        fireEvent.click(screen.getByRole("button", { name: job.title }));

        const sheet = document.querySelector("dialog[open]") as HTMLElement;
        expect(within(sheet).getByText(job.body)).toBeInTheDocument();
        expect(within(sheet).getByRole("link", { name: "Find your examination" })).toHaveAttribute(
            "href",
            "/exams",
        );
    });
});

describe("searching the support answers", () => {
    function page() {
        return render(
            <div className="euk-support">
                <AnswerSearch scope=".euk-support" />
                <section className="euk-answers" aria-label="About a payment">
                    <details className="euk-answer">
                        <summary>I was charged twice.</summary>
                        <p>Write to us with both references.</p>
                    </details>
                </section>
                <section className="euk-answers" aria-label="About your files">
                    <details className="euk-answer">
                        <summary>The email with my files didn’t arrive.</summary>
                        <p>Look in spam first.</p>
                    </details>
                </section>
            </div>,
        );
    }

    test("hides the answers that do not match, and a group left empty", () => {
        page();
        fireEvent.change(screen.getByRole("searchbox"), { target: { value: "spam" } });

        const [payment, files] = document.querySelectorAll("section.euk-answers");
        expect(payment).toHaveAttribute("hidden");
        expect(files).not.toHaveAttribute("hidden");
    });

    test("a search that matches nothing hands over to writing in", () => {
        page();
        fireEvent.change(screen.getByRole("searchbox"), { target: { value: "aadhaar" } });

        expect(screen.getByText(/None of these answers mention/)).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Write to us" })).toHaveAttribute("href", "#write");
    });

    test("clearing the search brings every answer back", () => {
        page();
        const box = screen.getByRole("searchbox");
        fireEvent.change(box, { target: { value: "aadhaar" } });
        fireEvent.change(box, { target: { value: "" } });

        for (const answer of document.querySelectorAll("details.euk-answer")) {
            expect(answer).not.toHaveAttribute("hidden");
        }
    });
});

describe("a policy on a phone", () => {
    const sections = [
        { title: "Temporary preparation", text: "Access ends at the deadline shown in your kit." },
        { title: "Browser and payment records", text: "Payment is handled through Razorpay." },
    ];

    test("starts collapsed, with every section's heading listed", () => {
        render(<PhonePolicy sections={sections} />);

        const items = document.querySelectorAll("details");
        expect(items).toHaveLength(2);
        for (const item of items) expect((item as HTMLDetailsElement).open).toBe(false);
    });

    test("a search keeps and opens only the sections that mention it", () => {
        render(<PhonePolicy sections={sections} />);
        fireEvent.change(screen.getByRole("searchbox"), { target: { value: "razorpay" } });

        const items = document.querySelectorAll("details");
        expect(items).toHaveLength(1);
        expect((items[0] as HTMLDetailsElement).open).toBe(true);
        expect(items[0]).toHaveTextContent("Browser and payment records");
    });

    test("a search that matches nothing points to support", () => {
        render(<PhonePolicy sections={sections} />);
        fireEvent.change(screen.getByRole("searchbox"), { target: { value: "passport" } });

        expect(screen.getByRole("link", { name: "Ask us" })).toHaveAttribute("href", "/support");
    });
});
