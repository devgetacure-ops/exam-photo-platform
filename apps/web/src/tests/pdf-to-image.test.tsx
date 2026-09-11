import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { PdfToImage } from "../components/exam/pdf-to-image";

const { getDocument } = vi.hoisted(() => ({ getDocument: vi.fn() }));

vi.mock("pdfjs-dist", () => ({
    GlobalWorkerOptions: { workerSrc: "pdf.worker.min.mjs" },
    getDocument,
}));

function passwordError(code: 1 | 2) {
    return Object.assign(new Error("password"), { name: "PasswordException", code });
}

/** A document whose pages draw, except each page in `failOnce` fails the first time. */
function fakeDocument(numPages: number, failOnce: number[] = []) {
    const pending = new Set(failOnce);
    const getPage = vi.fn(async (number: number) => ({
        getViewport: ({ scale }: { scale: number }) => ({
            width: 595 * scale,
            height: 842 * scale,
        }),
        render: () => {
            if (pending.delete(number)) {
                return { promise: Promise.reject(new Error("canvas memory")) };
            }
            return { promise: Promise.resolve() };
        },
        cleanup: () => {},
    }));
    return { doc: { numPages, getPage }, getPage };
}

function opens(doc: unknown) {
    return () => ({ promise: Promise.resolve(doc), destroy: vi.fn(async () => {}) });
}

function refuses(error: Error) {
    return () => ({ promise: Promise.reject(error), destroy: vi.fn(async () => {}) });
}

function choosePdf() {
    const file = new File(["%PDF-1.7"], "e-aadhaar.pdf", { type: "application/pdf" });
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(8) });
    fireEvent.change(screen.getByLabelText("PDF to convert to images"), {
        target: { files: [file] },
    });
}

describe("PDF to image, when it doesn't go right the first time", () => {
    beforeEach(() => {
        getDocument.mockReset();
        vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue({
            fillStyle: "",
            fillRect: () => {},
        } as never);
        vi.spyOn(HTMLCanvasElement.prototype, "toBlob").mockImplementation(function (callback) {
            callback(new Blob(["jpeg"], { type: "image/jpeg" }));
        });
        URL.createObjectURL = vi.fn(() => "blob:page");
        URL.revokeObjectURL = vi.fn();
    });
    afterEach(() => {
        cleanup();
        vi.restoreAllMocks();
    });

    test("a locked PDF asks for its password and opens with it", async () => {
        const { doc } = fakeDocument(1);
        getDocument
            .mockImplementationOnce(refuses(passwordError(1)))
            .mockImplementationOnce(opens(doc));
        render(<PdfToImage />);
        choosePdf();

        expect(await screen.findByRole("alert")).toHaveTextContent(
            "This PDF is locked with a password.",
        );
        const field = screen.getByLabelText("Password for this PDF");
        await waitFor(() => expect(field).toHaveFocus());

        fireEvent.change(field, { target: { value: "ABCD1999" } });
        fireEvent.click(screen.getByRole("button", { name: "Open the PDF" }));

        expect(await screen.findByRole("link", { name: "Download page 1" })).toBeInTheDocument();
        expect(getDocument.mock.calls[1][0].password).toBe("ABCD1999");
        expect(screen.queryByLabelText("Password for this PDF")).toBeNull();
    });

    test("a wrong password says so and keeps the field", async () => {
        getDocument
            .mockImplementationOnce(refuses(passwordError(1)))
            .mockImplementationOnce(refuses(passwordError(2)));
        render(<PdfToImage />);
        choosePdf();

        const field = await screen.findByLabelText("Password for this PDF");
        fireEvent.change(field, { target: { value: "abcd1999" } });
        fireEvent.click(screen.getByRole("button", { name: "Open the PDF" }));

        expect(await screen.findByRole("alert")).toHaveTextContent(/didn’t open it/);
        expect(screen.getByLabelText("Password for this PDF")).toHaveAttribute(
            "aria-invalid",
            "true",
        );
    });

    test("a page that fails keeps the pages before it, and the retry starts from that page", async () => {
        const { doc, getPage } = fakeDocument(3, [2]);
        getDocument.mockImplementation(opens(doc));
        render(<PdfToImage />);
        choosePdf();

        expect(await screen.findByRole("alert")).toHaveTextContent(
            /Page 2 couldn’t be drawn\. The pages before it are ready below\./,
        );
        expect(screen.getByRole("link", { name: "Download page 1" })).toBeInTheDocument();

        fireEvent.click(screen.getByRole("button", { name: "Try again from page 2" }));

        expect(await screen.findByRole("link", { name: "Download page 3" })).toBeInTheDocument();
        expect(screen.getAllByRole("link", { name: "Download page 1" })).toHaveLength(1);
        expect(getPage.mock.calls.map(([number]) => number)).toEqual([1, 2, 2, 3]);
    });

    test("changing the resolution after a failure starts again from the first page", async () => {
        const { doc, getPage } = fakeDocument(3, [2]);
        getDocument.mockImplementation(opens(doc));
        render(<PdfToImage />);
        choosePdf();

        await screen.findByRole("alert");
        fireEvent.click(screen.getByLabelText("100 dpi"));
        fireEvent.click(screen.getByRole("button", { name: "Start again with these settings" }));

        expect(await screen.findByRole("link", { name: "Download page 3" })).toBeInTheDocument();
        expect(getPage.mock.calls.map(([number]) => number)).toEqual([1, 2, 1, 2, 3]);
        expect(screen.getAllByText(/826 × 1169 px/, { selector: "p" })).toHaveLength(3);
    });

    test("a converter that didn't load offers to try again", async () => {
        const { doc } = fakeDocument(1);
        getDocument
            .mockImplementationOnce(refuses(Object.assign(new Error("worker"), { name: "UnknownErrorException" })))
            .mockImplementationOnce(opens(doc));
        render(<PdfToImage />);
        choosePdf();

        expect(await screen.findByRole("alert")).toHaveTextContent(/didn’t finish loading/);
        fireEvent.click(screen.getByRole("button", { name: "Try again" }));
        expect(await screen.findByRole("link", { name: "Download page 1" })).toBeInTheDocument();
    });

    test("a damaged file is not offered a retry that can't work", async () => {
        getDocument.mockImplementationOnce(
            refuses(Object.assign(new Error("bad"), { name: "InvalidPDFException" })),
        );
        render(<PdfToImage />);
        choosePdf();

        expect(await screen.findByRole("alert")).toHaveTextContent(/couldn’t be read as a PDF/);
        expect(screen.queryByRole("button", { name: /Try again/ })).toBeNull();
        expect(screen.getByRole("button", { name: "Choose another PDF" })).toHaveFocus();
    });
});
