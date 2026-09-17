"use client";
import { useRef, useState } from "react";
import { assembleDocument, planDocument } from "../../lib/api-client";
import { isPasswordLocked, lockedPdfMessage } from "../../lib/pdfjs";
import { startKit } from "../../lib/kit-state";
import type {
    DocumentPage,
    DocumentPlan,
    PrepareRequirementResponse,
} from "../../lib/types";
import { useKit } from "./use-kit";
import { useUploadConsent } from "./upload-consent";
import { OutcomeResult } from "./outcome-result";
import { PreparationLoader } from "./preparation-loader";
import { Tick } from "./specimen-sheet";
import { PdfToImage } from "./pdf-to-image";
import { prepareUpload, uploadRefusal } from "../../lib/upload-image";

/**
 * Documents: the page work candidates otherwise do in three free tools, done
 * here in one place and included with the kit.
 *
 * Bring any mix of photos and PDFs; every page is laid out as a card to put in
 * order or leave out, and one file is prepared from what remains. Each move
 * has a keyboard-reachable button, and the original order is one tap away.
 */

const TOOLS = [
    "Image to PDF",
    "Merge files",
    "Reorder pages",
    "Rotate pages",
    "Remove pages",
    "PDF to image",
];

/** Turned to the page's rotation, so the card shows what the PDF will. */
function PageDrawing({ rotation = 0 }: { rotation?: number }) {
    return (
        <svg className="euk-doc-page-art" style={{ rotate: `${rotation}deg` }} viewBox="0 0 60 72" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M8 4 H 40 L 52 16 V 68 H 8 Z" />
            <path d="M40 4 V 16 H 52" />
            <path d="M16 30 H 44 M16 40 H 44 M16 50 H 34" />
        </svg>
    );
}

export function DocumentWorkspace({
    examId,
    examName,
    requirementId,
    requirementName,
    partiallySupported,
    onWorking,
}: {
    examId: string;
    examName: string;
    requirementId: string;
    requirementName: string;
    partiallySupported: boolean;
    onWorking?: (value: boolean) => void;
}) {
    const [plan, setPlan] = useState<DocumentPlan | null>(null);
    const [pages, setPages] = useState<DocumentPage[]>([]);
    const [names, setNames] = useState<string[]>([]);
    const [result, setResult] = useState<PrepareRequirementResponse | null>(
        null,
    );
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const input = useRef<HTMLInputElement>(null);
    const { record, forget } = useKit(examId);
    const consent = useUploadConsent();
    if (busy) return <PreparationLoader requirementType="certificate_scan" />;
    if (result)
        return (
            <OutcomeResult
                result={result}
                requirementName={requirementName}
                partiallySupported={partiallySupported}
                onReplace={() => {
                    forget(requirementId);
                    setResult(null);
                    setPlan(null);
                    setPages([]);
                }}
            />
        );

    const move = (from: number, to: number) =>
        setPages((value) => {
            const next = [...value];
            [next[from], next[to]] = [next[to], next[from]];
            return next;
        });

    return (
        <div className="euk-doc">
            <div className="euk-doc-toolbar">
                <ul className="euk-doc-tools" aria-label="Included free with your kit">
                    {TOOLS.map((tool) => (
                        <li key={tool}>
                            <Tick />
                            {tool}
                        </li>
                    ))}
                </ul>
                <p className="euk-doc-free">Free with your kit</p>
            </div>

            {consent.panel}
            <div className="euk-drop" data-type="document">
                <button
                    className="primary-button euk-drop-button"
                    type="button"
                    onClick={() => {
                        if (consent.allow()) input.current?.click();
                    }}
                >
                    {plan ? "Choose different source files" : "Add images or PDFs"}
                </button>
                <p className="euk-drop-hint">
                    Up to 10 files: photos up to 40&nbsp;MB, PDFs up to
                    5&nbsp;MB. PDF pages are listed in order, without a
                    picture of each page yet.
                </p>
                <input
                    className="sr-only"
                    ref={input}
                    aria-label={`Source files for ${requirementName}`}
                    type="file"
                    multiple
                    accept="image/jpeg,image/png,image/webp,application/pdf"
                    onChange={async (event) => {
                        const chosen = Array.from(event.target.files ?? []);
                        event.target.value = "";
                        if (!chosen.length) return;
                        if (!consent.allow()) return;
                        if (chosen.length > 10) {
                            setError("Choose up to 10 files.");
                            return;
                        }
                        // Photographs of certificates are made into JPEGs the
                        // engine takes (DEC-103). Do them one at a time: ten
                        // decoded phone photographs at once can exhaust a
                        // phone's memory before any upload begins.
                        const files: File[] = [];
                        for (const file of chosen) {
                            const prepared = await prepareUpload(file);
                            if (!prepared.ok) {
                                setError(uploadRefusal(prepared.reason));
                                return;
                            }
                            files.push(prepared.file);
                        }
                        if (files.some((file) => file.size > 5 * 1024 * 1024)) {
                            setError("Choose PDFs no larger than 5 MB each.");
                            return;
                        }
                        setBusy(true);
                        onWorking?.(true);
                        setError("");
                        try {
                            // A locked PDF is turned away here, before anything
                            // is uploaded, with the files named (DEC-052).
                            const lockedFlags = await Promise.all(files.map(isPasswordLocked));
                            const locked = files
                                .filter((_, index) => lockedFlags[index])
                                .map((file) => file.name);
                            if (locked.length) {
                                setError(lockedPdfMessage(locked));
                                return;
                            }
                            const kit = startKit(examId, examName);
                            const next = await planDocument({
                                examId,
                                requirementId,
                                files,
                                kitId: kit.kitId,
                            });
                            setPlan(next);
                            setPages(next.pages);
                            setNames(files.map((file) => file.name));
                        } catch {
                            setError(
                                "We couldn’t read these files. Check that they are images or PDFs without a password, then try again.",
                            );
                        } finally {
                            setBusy(false);
                            onWorking?.(false);
                        }
                    }}
                />
            </div>

            {plan && (
                <>
                    {Object.keys(plan.unreadable).length > 0 && (
                        <div className="euk-doc-warn" role="alert">
                            <strong>Some files could not be read.</strong>
                            <ul>
                                {Object.entries(plan.unreadable).map(
                                    ([index, reason]) => {
                                        const name = names[Number(index)] ?? "Source file";
                                        // The engine's reason already starts with the file's name.
                                        const detail = reason.startsWith(`${name}: `)
                                            ? reason.slice(name.length + 2)
                                            : reason;
                                        return (
                                            <li key={index}>
                                                {name}: {detail}
                                            </li>
                                        );
                                    },
                                )}
                            </ul>
                            <p>
                                They are left out. Replace them before continuing
                                if they are required.
                            </p>
                        </div>
                    )}
                    <ol className="euk-doc-pages">
                        {pages.map((page, index) => (
                            <li
                                key={`${page.source_index}-${page.page_index}-${index}`}
                                className="euk-doc-page"
                            >
                                <PageDrawing rotation={page.rotation} />
                                <strong>
                                    {names[page.source_index] ??
                                        `Source ${page.source_index + 1}`}
                                </strong>
                                <span>
                                    Page {page.page_index + 1}, placed {index + 1} of{" "}
                                    {pages.length}
                                    {page.rotation ? `, turned ${page.rotation}°` : ""}
                                </span>
                                <div className="euk-doc-actions">
                                    <button
                                        type="button"
                                        aria-label={`Move page ${index + 1} up`}
                                        disabled={index === 0}
                                        onClick={() => move(index, index - 1)}
                                    >
                                        ↑
                                    </button>
                                    <button
                                        type="button"
                                        aria-label={`Move page ${index + 1} down`}
                                        disabled={index === pages.length - 1}
                                        onClick={() => move(index, index + 1)}
                                    >
                                        ↓
                                    </button>
                                    <button
                                        type="button"
                                        aria-label={`Rotate page ${index + 1} clockwise`}
                                        onClick={() =>
                                            setPages((value) =>
                                                value.map((item, i) =>
                                                    i === index
                                                        ? { ...item, rotation: (item.rotation + 90) % 360 }
                                                        : item,
                                                ),
                                            )
                                        }
                                    >
                                        ↻
                                    </button>
                                    <button
                                        type="button"
                                        aria-label={`Remove page ${index + 1}`}
                                        onClick={() =>
                                            setPages((value) =>
                                                value.filter((_, i) => i !== index),
                                            )
                                        }
                                    >
                                        Remove
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ol>
                    <div className="euk-doc-bar">
                        <button
                            type="button"
                            className="primary-button"
                            disabled={!pages.length}
                            onClick={async () => {
                                setBusy(true);
                                onWorking?.(true);
                                setError("");
                                try {
                                    const prepared = await assembleDocument(
                                        plan.job_id,
                                        pages,
                                    );
                                    record(prepared, examName);
                                    setResult(prepared);
                                } catch {
                                    setError(
                                        "We couldn’t assemble the document. It may have expired. Try uploading again.",
                                    );
                                } finally {
                                    setBusy(false);
                                    onWorking?.(false);
                                }
                            }}
                        >
                            Prepare {pages.length} page{pages.length === 1 ? "" : "s"}
                        </button>
                        <button
                            className="quiet-link euk-doc-restore"
                            type="button"
                            onClick={() => setPages(plan.pages)}
                        >
                            Restore the original order
                        </button>
                    </div>
                </>
            )}
            {error && (
                <p role="alert" className="euk-upload-error">
                    {error}
                </p>
            )}

            <details className="euk-pdfimg-wrap">
                <summary>
                    <span className="euk-pdfimg-title">Need a page as an image?</span>
                    <span className="euk-pdfimg-sub">
                        PDF to image, free with your kit. Your PDF never leaves
                        this browser.
                    </span>
                </summary>
                <p className="euk-pdfimg-caution">
                    An image of a digitally issued certificate can’t be verified
                    the way the PDF can. Use this only when the portal asks for
                    an image.
                </p>
                <PdfToImage />
            </details>
        </div>
    );
}
