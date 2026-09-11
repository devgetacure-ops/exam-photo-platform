import { isPdfFile } from "./pdf-image";

/**
 * pdf.js (Apache-2.0), loaded only once a PDF is in hand, so no page pays
 * for it until a candidate chooses one.
 */
export async function loadPdfjs() {
    const pdfjs = await import("pdfjs-dist");
    if (!pdfjs.GlobalWorkerOptions.workerSrc) {
        pdfjs.GlobalWorkerOptions.workerSrc = new URL(
            "pdfjs-dist/build/pdf.worker.min.mjs",
            import.meta.url,
        ).toString();
    }
    return pdfjs;
}

/**
 * Whether a PDF can't be opened without a password.
 *
 * Asked of pdf.js rather than read from the file's bytes. A PDF can carry
 * encryption and still open with no password (a lock against printing or
 * copying), and the engine accepts those, so only a PDF that needs a password
 * to be read at all counts as locked. The product never asks for the
 * password: a locked PDF is turned away with a direction to upload a copy
 * without one.
 *
 * Anything else, pdf.js failing to load included, answers false and leaves
 * the file to the engine, so a slow connection never blocks a good PDF.
 */
export async function isPasswordLocked(file: File): Promise<boolean> {
    if (!isPdfFile(file)) return false;
    try {
        const pdfjs = await loadPdfjs();
        const task = pdfjs.getDocument({
            data: new Uint8Array(await file.arrayBuffer()),
        });
        try {
            await task.promise;
            return false;
        } catch (error) {
            return (error as { name?: string } | null)?.name === "PasswordException";
        } finally {
            void task.destroy();
        }
    } catch {
        return false;
    }
}

/** What a candidate is told about the locked PDFs among their files. */
export function lockedPdfMessage(names: string[]): string {
    const list = new Intl.ListFormat("en-GB", { type: "conjunction" }).format(names);
    return names.length === 1
        ? `${list} is password-protected, so we can’t open it. Upload a copy of the PDF without a password.`
        : `${list} are password-protected, so we can’t open them. Upload copies of these PDFs without a password.`;
}
