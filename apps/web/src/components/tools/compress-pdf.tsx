"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";

import { formatBytes } from "../../lib/spec-format";
import { loadPdfjs, lockedPdfMessage } from "../../lib/pdfjs";
import { MAX_PDF_BYTES, MAX_PDF_PAGES, isPdfFile, scaleForDpi } from "../../lib/pdf-image";
import {
    PDF_PRESET_KB,
    compressPdf,
    compressedPdfFilename,
    type DrawnPage,
} from "../../lib/pdf-compress";

/**
 * Compress a PDF to a size, in the candidate's own browser (DEC-098). The same
 * shape as the photo tool: the limit, the file, a result just under it.
 */

interface Result {
    url: string;
    bytes: number;
    pages: number;
    filename: string;
    targetKb: number;
}

type Failure =
    | { kind: "not-pdf" }
    | { kind: "too-large"; bytes: number }
    | { kind: "too-many"; pages: number }
    | { kind: "locked"; name: string }
    | { kind: "unreadable" }
    | { kind: "too-small"; targetKb: number };

function failureText(failure: Failure): string {
    switch (failure.kind) {
        case "not-pdf":
            return "That file isn’t a PDF. Choose a PDF file.";
        case "too-large":
            return `That PDF is ${formatBytes(failure.bytes)}. Choose one under 20 MB.`;
        case "too-many":
            return `That PDF has ${failure.pages} pages. Choose one with ${MAX_PDF_PAGES} or fewer.`;
        case "locked":
            return lockedPdfMessage([failure.name]);
        case "unreadable":
            return "This PDF couldn’t be read. It may be damaged. Choose it again, or another copy.";
        case "too-small":
            return `Even at a low resolution this PDF stays above ${failure.targetKb} KB. Choose a larger size, or fewer pages.`;
    }
}

const noSubscription = () => () => {};

/** A link such as /compress-pdf?kb=300 opens on that limit. */
function linkedKb(search: string): number | null {
    const kb = Math.round(Number(new URLSearchParams(search).get("kb")));
    return kb >= 1 && kb <= 20000 ? kb : null;
}

export function CompressPdf({ initialKb }: { initialKb?: number } = {}) {
    // Read as an external store rather than in an effect: the page is static,
    // so the server renders without the query and the browser fills it in.
    const search = useSyncExternalStore(noSubscription, () => window.location.search, () => "");
    const [chosenKb, setChosenKb] = useState<number | null>(null);
    const [typed, setTyped] = useState<string | null>(null);
    const targetKb = chosenKb ?? initialKb ?? linkedKb(search) ?? 200;
    const custom =
        typed ?? ((PDF_PRESET_KB as readonly number[]).includes(targetKb) ? "" : String(targetKb));
    const [status, setStatus] = useState<"idle" | "working" | "done" | "failed">("idle");
    const [progress, setProgress] = useState("");
    const [result, setResult] = useState<Result | null>(null);
    const [failure, setFailure] = useState<Failure | null>(null);
    const [file, setFile] = useState<File | null>(null);
    const input = useRef<HTMLInputElement>(null);
    const url = useRef<string | null>(null);

    useEffect(
        () => () => {
            if (url.current) URL.revokeObjectURL(url.current);
        },
        [],
    );

    function fail(next: Failure) {
        setFailure(next);
        setResult(null);
        setStatus("failed");
    }

    async function run(source: File, kb: number) {
        if (!isPdfFile(source)) return fail({ kind: "not-pdf" });
        if (source.size > MAX_PDF_BYTES) return fail({ kind: "too-large", bytes: source.size });
        setFile(source);
        setFailure(null);
        setProgress("Opening the PDF…");
        setStatus("working");

        let pdfjs: Awaited<ReturnType<typeof loadPdfjs>>;
        try {
            pdfjs = await loadPdfjs();
        } catch {
            return fail({ kind: "unreadable" });
        }
        const task = pdfjs.getDocument({ data: new Uint8Array(await source.arrayBuffer()) });
        let doc: Awaited<typeof task.promise>;
        try {
            doc = await task.promise;
        } catch (error) {
            void task.destroy();
            const name = (error as { name?: string })?.name;
            return fail(name === "PasswordException" ? { kind: "locked", name: source.name } : { kind: "unreadable" });
        }
        if (doc.numPages > MAX_PDF_PAGES) {
            const pages = doc.numPages;
            await task.destroy();
            return fail({ kind: "too-many", pages });
        }

        const draw = async (index: number, dpi: number): Promise<DrawnPage> => {
            const page = await doc.getPage(index + 1);
            const base = page.getViewport({ scale: 1 });
            const viewport = page.getViewport({ scale: scaleForDpi(dpi) });
            const canvas = document.createElement("canvas");
            canvas.width = Math.floor(viewport.width);
            canvas.height = Math.floor(viewport.height);
            const context = canvas.getContext("2d");
            if (!context) throw new Error("No canvas context");
            context.fillStyle = "#ffffff";
            context.fillRect(0, 0, canvas.width, canvas.height);
            // The print intent: display pacing stops in a background tab.
            await page.render({ canvas, canvasContext: context, viewport, intent: "print" }).promise;
            return {
                pointWidth: base.width,
                pointHeight: base.height,
                encode: async (quality) => {
                    const blob = await new Promise<Blob | null>((resolve) =>
                        canvas.toBlob(resolve, "image/jpeg", quality),
                    );
                    if (!blob) throw new Error("Could not encode the page");
                    return {
                        jpeg: new Uint8Array(await blob.arrayBuffer()),
                        width: canvas.width,
                        height: canvas.height,
                    };
                },
                release: () => {
                    page.cleanup();
                    canvas.width = 0;
                    canvas.height = 0;
                },
            };
        };

        try {
            const outcome = await compressPdf(doc.numPages, draw, kb, ({ dpi, page, pages }) =>
                setProgress(`Trying ${dpi} DPI: page ${page} of ${pages}…`),
            );
            if (!outcome.ok) return fail({ kind: "too-small", targetKb: kb });
            if (url.current) URL.revokeObjectURL(url.current);
            // buildJpegPdf allocates the array at its exact length, so its
            // buffer is the whole file.
            url.current = URL.createObjectURL(
                new Blob([outcome.pdf.buffer as ArrayBuffer], { type: "application/pdf" }),
            );
            setResult({
                url: url.current,
                bytes: outcome.pdf.length,
                pages: doc.numPages,
                filename: compressedPdfFilename(source.name, kb),
                targetKb: kb,
            });
            setStatus("done");
        } catch {
            fail({ kind: "unreadable" });
        } finally {
            await task.destroy();
        }
    }

    const working = status === "working";
    const stale = file !== null && result !== null && result.targetKb !== targetKb;

    return (
        <div className="euk-cmp-form">
            <fieldset className="euk-cmp-limit">
                <legend className="euk-cmp-label">1. Your form&rsquo;s limit</legend>
                <ul className="euk-cmp-sizes">
                    {PDF_PRESET_KB.map((kb) => (
                        <li key={kb}>
                            <button
                                type="button"
                                className="euk-cmp-size"
                                aria-pressed={targetKb === kb && custom === ""}
                                onClick={() => {
                                    setChosenKb(kb);
                                    setTyped("");
                                }}
                                disabled={working}
                            >
                                {kb} KB
                            </button>
                        </li>
                    ))}
                </ul>
                <label className="euk-cmp-custom">
                    <span>Or another size</span>
                    <input
                        type="number"
                        inputMode="numeric"
                        min={1}
                        max={20000}
                        value={custom}
                        placeholder="KB"
                        disabled={working}
                        onChange={(event) => {
                            setTyped(event.target.value);
                            const kb = Math.round(Number(event.target.value));
                            if (kb >= 1 && kb <= 20000) setChosenKb(kb);
                        }}
                    />
                    <span aria-hidden="true">KB</span>
                </label>
            </fieldset>

            <p className="euk-cmp-label euk-cmp-step">2. Your PDF</p>
            <button
                type="button"
                className="primary-button euk-cmp-choose"
                onClick={() => input.current?.click()}
                disabled={working}
            >
                {file ? "Choose another PDF" : "Choose a PDF"}
            </button>
            <input
                ref={input}
                type="file"
                accept="application/pdf,.pdf"
                className="sr-only"
                aria-label="PDF to compress"
                onChange={(event) => {
                    const next = event.target.files?.[0];
                    if (next) void run(next, targetKb);
                    event.target.value = "";
                }}
            />
            <p className="euk-cmp-privacy">It stays on this device. Nothing is uploaded.</p>

            <p role="status" className="euk-cmp-status">
                {working
                    ? progress
                    : result
                      ? `${formatBytes(result.bytes)}, under ${result.targetKb} KB · ${result.pages} page${result.pages === 1 ? "" : "s"} · PDF`
                      : ""}
            </p>
            {failure && (
                <p role="alert" className="euk-cmp-error">
                    {failureText(failure)}
                </p>
            )}
            {result && (
                <div className="euk-cmp-result">
                    <a className="primary-button euk-cmp-download" href={result.url} download={result.filename}>
                        Download {result.filename}
                    </a>
                </div>
            )}
            {stale && file && (
                <button
                    type="button"
                    className="euk-cmp-again"
                    onClick={() => void run(file, targetKb)}
                    disabled={working}
                >
                    Compress again to under {targetKb} KB
                </button>
            )}
        </div>
    );
}
