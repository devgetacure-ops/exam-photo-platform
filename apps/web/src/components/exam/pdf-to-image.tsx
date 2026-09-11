"use client";

import { useEffect, useRef, useState } from "react";
import type { PDFDocumentProxy } from "pdfjs-dist";
import { formatBytes } from "../../lib/spec-format";
import {
    DPI_CHOICES,
    MAX_PDF_BYTES,
    MAX_PDF_PAGES,
    isPdfFile,
    pdfPageFilename,
    scaleForDpi,
    type ImageFormat,
} from "../../lib/pdf-image";

/**
 * PDF to image, in the candidate's own browser.
 *
 * For the portal that wants a JPEG of a page the candidate holds as a PDF.
 * pdf.js (Apache-2.0) draws each page onto a canvas at the resolution they
 * choose, over a white ground so a JPEG has no black transparency, and the
 * canvas is saved as an image they download. Nothing is uploaded: the PDF
 * never leaves the page, which is also why this costs us nothing to offer.
 *
 * pdf.js is loaded only when a PDF is chosen, so no other page pays for it.
 * The engine still never does this on its own (DEC-052); this is the
 * candidate's decision about their own document.
 *
 * Each way this can fail gets the retry that fits it. A locked PDF (every
 * e-Aadhaar is one) asks for its password. A page that can't be drawn keeps
 * the pages before it and tries again from that page. A converter that didn't
 * load tries again. A file that can never work is not offered a retry at all.
 */

interface RenderedPage {
    page: number;
    url: string;
    bytes: number;
    width: number;
    height: number;
    filename: string;
}

interface Settings {
    format: ImageFormat;
    dpi: number;
}

type Failure =
    | { kind: "not-pdf" }
    | { kind: "too-large"; bytes: number }
    | { kind: "unreadable" }
    | { kind: "load" }
    | { kind: "locked" }
    | { kind: "wrong-password" }
    | { kind: "page"; page: number };

type Status = "idle" | "working" | "done" | "failed";

async function loadPdfjs() {
    const pdfjs = await import("pdfjs-dist");
    if (!pdfjs.GlobalWorkerOptions.workerSrc) {
        pdfjs.GlobalWorkerOptions.workerSrc = new URL(
            "pdfjs-dist/build/pdf.worker.min.mjs",
            import.meta.url,
        ).toString();
    }
    return pdfjs;
}

async function drawPage(
    doc: PDFDocumentProxy,
    number: number,
    sourceName: string,
    { format, dpi }: Settings,
): Promise<Omit<RenderedPage, "url"> & { blob: Blob }> {
    const page = await doc.getPage(number);
    const viewport = page.getViewport({ scale: scaleForDpi(dpi) });
    const canvas = document.createElement("canvas");
    canvas.width = Math.floor(viewport.width);
    canvas.height = Math.floor(viewport.height);
    try {
        const context = canvas.getContext("2d");
        if (!context) throw new Error("No canvas context");
        context.fillStyle = "#ffffff";
        context.fillRect(0, 0, canvas.width, canvas.height);
        // The print intent, not display: display paces its work with
        // requestAnimationFrame, which browsers stop in a background tab.
        // A candidate who switches to the exam portal while a
        // certificate converts would come back to it frozen on page 1.
        await page.render({
            canvas,
            canvasContext: context,
            viewport,
            intent: "print",
        }).promise;
        const blob = await new Promise<Blob | null>((resolve) =>
            canvas.toBlob(resolve, format === "png" ? "image/png" : "image/jpeg", 0.92),
        );
        if (!blob) throw new Error("Could not encode the page");
        return {
            page: number,
            blob,
            bytes: blob.size,
            width: canvas.width,
            height: canvas.height,
            filename: pdfPageFilename(sourceName, number, format),
        };
    } finally {
        page.cleanup();
        // Release the bitmap now rather than when the page is left.
        canvas.width = 0;
        canvas.height = 0;
    }
}

function failureText(failure: Failure, pagesKept: number): string {
    switch (failure.kind) {
        case "not-pdf":
            return "That file isn’t a PDF. Choose a PDF file.";
        case "too-large":
            return `That PDF is ${formatBytes(failure.bytes)}. Choose one under 20 MB.`;
        case "unreadable":
            return "This file couldn’t be read as a PDF. It may be damaged or incomplete. Choose it again, or choose another copy.";
        case "load":
            return "The converter didn’t finish loading. Check your connection, then try again.";
        case "locked":
            return "This PDF is locked with a password.";
        case "wrong-password":
            return "That password didn’t open it. Passwords here are case-sensitive.";
        case "page":
            return [
                `Page ${failure.page} couldn’t be drawn.`,
                pagesKept > 0 ? "The pages before it are ready below." : "",
                "On a phone, a lower resolution often gets past this.",
            ]
                .filter(Boolean)
                .join(" ");
    }
}

export function PdfToImage() {
    const [format, setFormat] = useState<ImageFormat>("jpeg");
    const [dpi, setDpi] = useState<number>(150);
    const [status, setStatus] = useState<Status>("idle");
    const [failure, setFailure] = useState<Failure | null>(null);
    const [progress, setProgress] = useState({ page: 0, total: 0 });
    const [pages, setPages] = useState<RenderedPage[]>([]);
    const [rendered, setRendered] = useState<Settings | null>(null);
    const [note, setNote] = useState("");
    const [sourceName, setSourceName] = useState("");
    const [lastFile, setLastFile] = useState<File | null>(null);
    const [password, setPassword] = useState("");
    const input = useRef<HTMLInputElement>(null);
    const chooseButton = useRef<HTMLButtonElement>(null);
    const retryButton = useRef<HTMLButtonElement>(null);
    const passwordInput = useRef<HTMLInputElement>(null);
    const urls = useRef<string[]>([]);
    // The password that opened this file, so a retry from a later page
    // doesn't ask for it again. Never stored beyond this component.
    const unlock = useRef<string | undefined>(undefined);

    const release = () => {
        urls.current.forEach((url) => URL.revokeObjectURL(url));
        urls.current = [];
    };
    useEffect(() => release, []);

    // The button that was pressed is disabled while the PDF converts, which
    // drops focus to the page. Put it back where the next step is.
    useEffect(() => {
        if (status !== "failed") return;
        (passwordInput.current ?? retryButton.current ?? chooseButton.current)?.focus();
    }, [status, failure]);

    function fail(next: Failure) {
        setFailure(next);
        setStatus("failed");
    }

    async function convert(file: File, from = 1, filePassword = unlock.current) {
        if (!isPdfFile(file)) return fail({ kind: "not-pdf" });
        if (file.size > MAX_PDF_BYTES) return fail({ kind: "too-large", bytes: file.size });

        const settings: Settings = { format, dpi };
        const done = from > 1 ? pages.slice(0, from - 1) : [];
        if (from === 1) {
            release();
            setPages([]);
        }
        setRendered(settings);
        setSourceName(file.name);
        setFailure(null);
        setNote("");
        setProgress({ page: from, total: 0 });
        setStatus("working");

        let pdfjs: Awaited<ReturnType<typeof loadPdfjs>>;
        try {
            pdfjs = await loadPdfjs();
        } catch {
            return fail({ kind: "load" });
        }

        let data: Uint8Array;
        try {
            data = new Uint8Array(await file.arrayBuffer());
        } catch {
            return fail({ kind: "unreadable" });
        }

        const task = pdfjs.getDocument({ data, password: filePassword });
        let doc: PDFDocumentProxy;
        try {
            doc = await task.promise;
        } catch (error) {
            void task.destroy();
            const { name, code } = (error ?? {}) as { name?: string; code?: number };
            if (name === "PasswordException") {
                // pdf.js: 1 is "needs a password", 2 is "wrong password".
                return fail({ kind: code === 2 ? "wrong-password" : "locked" });
            }
            return fail({ kind: name === "InvalidPDFException" ? "unreadable" : "load" });
        }
        unlock.current = filePassword;
        setPassword("");

        const count = doc.numPages;
        const total = Math.min(count, MAX_PDF_PAGES);
        for (let number = from; number <= total; number++) {
            setProgress({ page: number, total });
            try {
                const { blob, ...page } = await drawPage(doc, number, file.name, settings);
                const url = URL.createObjectURL(blob);
                urls.current.push(url);
                done.push({ ...page, url });
                setPages([...done]);
            } catch {
                await task.destroy();
                return fail({ kind: "page", page: number });
            }
        }

        await task.destroy();
        setStatus("done");
        if (count > MAX_PDF_PAGES) {
            setNote(`Converted the first ${MAX_PDF_PAGES} of ${count} pages.`);
        }
    }

    const working = status === "working";
    const sameSettings = rendered?.format === format && rendered?.dpi === dpi;
    const locked = failure?.kind === "locked" || failure?.kind === "wrong-password";

    let retry: { label: string; from: number } | null = null;
    if (status === "failed" && failure?.kind === "load") {
        retry = { label: "Try again", from: 1 };
    } else if (status === "failed" && failure?.kind === "page") {
        retry = !sameSettings
            ? { label: "Start again with these settings", from: 1 }
            : failure.page > 1
              ? { label: `Try again from page ${failure.page}`, from: failure.page }
              : { label: "Try again", from: 1 };
    }
    const retryFrom = retry?.from ?? 1;

    return (
        <div className="euk-pdfimg" aria-busy={working}>
            <div className="euk-pdfimg-controls">
                <fieldset className="euk-seg" disabled={working}>
                    <legend>Save as</legend>
                    {(["jpeg", "png"] as const).map((value) => (
                        <label key={value}>
                            <input
                                type="radio"
                                name="pdfimg-format"
                                value={value}
                                checked={format === value}
                                onChange={() => setFormat(value)}
                            />
                            <span>{value === "jpeg" ? "JPEG" : "PNG"}</span>
                        </label>
                    ))}
                </fieldset>
                <fieldset className="euk-seg" disabled={working}>
                    <legend>Resolution</legend>
                    {DPI_CHOICES.map((value) => (
                        <label key={value}>
                            <input
                                type="radio"
                                name="pdfimg-dpi"
                                value={value}
                                checked={dpi === value}
                                onChange={() => setDpi(value)}
                            />
                            <span>{value} dpi</span>
                        </label>
                    ))}
                </fieldset>
            </div>
            <p className="euk-pdfimg-hint">
                150 dpi reads clearly and keeps the file small. Most portals ask
                for JPEG.
            </p>

            <div className="euk-pdfimg-actions">
                <button
                    ref={chooseButton}
                    type="button"
                    className="secondary-button"
                    disabled={working}
                    onClick={() => input.current?.click()}
                >
                    {sourceName ? "Choose another PDF" : "Choose a PDF"}
                </button>
                {status === "done" && lastFile && !sameSettings && (
                    <button
                        type="button"
                        className="quiet-link"
                        onClick={() => void convert(lastFile)}
                    >
                        Convert again with these settings
                    </button>
                )}
                <input
                    ref={input}
                    type="file"
                    accept="application/pdf,.pdf"
                    className="sr-only"
                    aria-label="PDF to convert to images"
                    onChange={(event) => {
                        const file = event.target.files?.[0];
                        event.target.value = "";
                        if (!file) return;
                        unlock.current = undefined;
                        setPassword("");
                        setLastFile(file);
                        void convert(file, 1, undefined);
                    }}
                />
            </div>

            {working && (
                <p className="euk-pdfimg-status" role="status">
                    {progress.total
                        ? `Drawing page ${progress.page} of ${progress.total}…`
                        : "Opening the PDF…"}
                </p>
            )}

            {status === "failed" && failure && (
                <div className="euk-pdfimg-failure">
                    <p className="euk-upload-error" role="alert">
                        {failureText(failure, pages.length)}
                    </p>
                    {retry && lastFile && (
                        <button
                            ref={retryButton}
                            type="button"
                            className="primary-button"
                            onClick={() => void convert(lastFile, retryFrom)}
                        >
                            {retry.label}
                        </button>
                    )}
                    {locked && lastFile && (
                        <form
                            className="euk-pdfimg-lock"
                            onSubmit={(event) => {
                                event.preventDefault();
                                if (!password) {
                                    passwordInput.current?.focus();
                                    return;
                                }
                                void convert(lastFile, 1, password);
                            }}
                        >
                            <label htmlFor="pdfimg-password" className="euk-field-label">
                                Password for this PDF
                            </label>
                            <p id="pdfimg-password-hint" className="euk-field-hint">
                                It stays in this browser, like the PDF. An e-Aadhaar’s
                                password is the first four letters of your name in
                                capitals, then your year of birth.
                            </p>
                            <div className="euk-pdfimg-lock-row">
                                <input
                                    ref={passwordInput}
                                    id="pdfimg-password"
                                    type="password"
                                    autoComplete="off"
                                    value={password}
                                    onChange={(event) => setPassword(event.target.value)}
                                    aria-describedby="pdfimg-password-hint"
                                    aria-invalid={failure.kind === "wrong-password"}
                                />
                                <button type="submit" className="primary-button">
                                    Open the PDF
                                </button>
                            </div>
                        </form>
                    )}
                </div>
            )}

            {note && (
                <p className="euk-pdfimg-status" role="status">
                    {note}
                </p>
            )}

            {pages.length > 0 && (
                <ul className="euk-pdfimg-pages">
                    {pages.map((page) => (
                        <li key={page.page} className="euk-pdfimg-page">
                            <div className="euk-pdfimg-thumb">
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img src={page.url} alt={`Page ${page.page} of ${sourceName}`} />
                            </div>
                            <p className="euk-pdfimg-meta">
                                Page {page.page} · {page.width} × {page.height} px ·{" "}
                                {formatBytes(page.bytes)}
                            </p>
                            <a className="primary-button" href={page.url} download={page.filename}>
                                Download page {page.page}
                            </a>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
