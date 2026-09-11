import { afterEach, describe, expect, test, vi } from "vitest";

import { isPasswordLocked, lockedPdfMessage } from "../lib/pdfjs";

const { getDocument } = vi.hoisted(() => ({ getDocument: vi.fn() }));

vi.mock("pdfjs-dist", () => ({
    GlobalWorkerOptions: { workerSrc: "pdf.worker.min.mjs" },
    getDocument,
}));

function pdf(name = "marks.pdf") {
    const file = new File(["%PDF-1.7"], name, { type: "application/pdf" });
    Object.defineProperty(file, "arrayBuffer", { value: async () => new ArrayBuffer(8) });
    return file;
}

const task = (promise: () => Promise<unknown>) => () => ({
    promise: promise(),
    destroy: vi.fn(async () => {}),
});

const failure = (name: string) => Object.assign(new Error(name), { name });

describe("telling a password-protected PDF apart", () => {
    afterEach(() => getDocument.mockReset());

    test("a PDF that needs a password is locked", async () => {
        getDocument.mockImplementation(task(() => Promise.reject(failure("PasswordException"))));
        await expect(isPasswordLocked(pdf())).resolves.toBe(true);
        expect(getDocument.mock.calls[0][0]).not.toHaveProperty("password");
    });

    test("a PDF that opens is not", async () => {
        getDocument.mockImplementation(task(() => Promise.resolve({ numPages: 1 })));
        await expect(isPasswordLocked(pdf())).resolves.toBe(false);
    });

    test("a damaged PDF is left for the engine to judge", async () => {
        getDocument.mockImplementation(task(() => Promise.reject(failure("InvalidPDFException"))));
        await expect(isPasswordLocked(pdf())).resolves.toBe(false);
    });

    test("an image is never opened as a PDF", async () => {
        const image = new File(["x"], "sig.jpg", { type: "image/jpeg" });
        await expect(isPasswordLocked(image)).resolves.toBe(false);
        expect(getDocument).not.toHaveBeenCalled();
    });

    test("the message names the files and says what to upload instead", () => {
        expect(lockedPdfMessage(["aadhaar.pdf"])).toBe(
            "aadhaar.pdf is password-protected, so we can’t open it. Upload a copy of the PDF without a password.",
        );
        expect(lockedPdfMessage(["a.pdf", "b.pdf", "c.pdf"])).toBe(
            "a.pdf, b.pdf and c.pdf are password-protected, so we can’t open them. Upload copies of these PDFs without a password.",
        );
    });
});
