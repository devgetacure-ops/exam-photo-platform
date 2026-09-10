"use client";
import { useRef, useState } from "react";
import { assembleDocument, planDocument } from "../../lib/api-client";
import { startKit } from "../../lib/kit-state";
import type {
    DocumentPage,
    DocumentPlan,
    PrepareRequirementResponse,
} from "../../lib/types";
import { useKit } from "./use-kit";
import { OutcomeResult } from "./outcome-result";
import { PreparationLoader } from "./preparation-loader";

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
    if (busy) return <PreparationLoader />;
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
    return (
        <div className="document-workspace">
            <p>
                Bring images or PDFs together. Arrange the pages, leave out what
                you don’t need, then prepare one document for this requirement.
            </p>
            <button
                className="primary-button"
                type="button"
                onClick={() => input.current?.click()}
            >
                {plan ? "Choose different source files" : "Add images or PDFs"}
            </button>
            <input
                className="sr-only"
                ref={input}
                aria-label={`Source files for ${requirementName}`}
                type="file"
                multiple
                accept="image/jpeg,image/png,image/webp,application/pdf"
                onChange={async (event) => {
                    const files = Array.from(event.target.files ?? []);
                    event.target.value = "";
                    if (!files.length) return;
                    if (
                        files.length > 10 ||
                        files.some((file) => file.size > 5 * 1024 * 1024)
                    ) {
                        setError(
                            "Choose up to 10 files, each no larger than 5 MB.",
                        );
                        return;
                    }
                    setBusy(true);
                    onWorking?.(true);
                    setError("");
                    try {
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
                            "We couldn’t read these files. Check that they are readable images or unprotected PDFs, then try again.",
                        );
                    } finally {
                        setBusy(false);
                        onWorking?.(false);
                    }
                }}
            />
            <p className="fine-copy">
                Up to 10 sources, 5 MB each. Page order is shown below; rendered
                PDF previews are not available.
            </p>
            {plan && (
                <>
                    {Object.keys(plan.unreadable).length > 0 && (
                        <div className="inline-notice" role="alert">
                            <strong>Some sources could not be read.</strong>
                            <ul>
                                {Object.entries(plan.unreadable).map(
                                    ([index, reason]) => (
                                        <li key={index}>
                                            {names[Number(index)] ??
                                                "Source file"}
                                            : {reason}
                                        </li>
                                    ),
                                )}
                            </ul>
                            <p>
                                These sources are not included. Replace them
                                before continuing if they are required.
                            </p>
                        </div>
                    )}
                    <ol className="document-pages">
                        {pages.map((page, index) => (
                            <li
                                key={`${page.source_index}-${page.page_index}-${index}`}
                            >
                                <div>
                                    <strong>
                                        {names[page.source_index] ??
                                            `Source ${page.source_index + 1}`}
                                    </strong>
                                    <span>
                                        Page {page.page_index + 1} · position{" "}
                                        {index + 1}
                                    </span>
                                </div>
                                <div className="document-actions">
                                    <button
                                        type="button"
                                        className="secondary-button"
                                        aria-label={`Move page ${index + 1} up`}
                                        disabled={index === 0}
                                        onClick={() =>
                                            setPages((value) => {
                                                const next = [...value];
                                                [next[index - 1], next[index]] =
                                                    [
                                                        next[index],
                                                        next[index - 1],
                                                    ];
                                                return next;
                                            })
                                        }
                                    >
                                        ↑
                                    </button>
                                    <button
                                        type="button"
                                        className="secondary-button"
                                        aria-label={`Move page ${index + 1} down`}
                                        disabled={index === pages.length - 1}
                                        onClick={() =>
                                            setPages((value) => {
                                                const next = [...value];
                                                [next[index], next[index + 1]] =
                                                    [
                                                        next[index + 1],
                                                        next[index],
                                                    ];
                                                return next;
                                            })
                                        }
                                    >
                                        ↓
                                    </button>
                                    <button
                                        type="button"
                                        className="secondary-button"
                                        aria-label={`Remove page ${index + 1}`}
                                        onClick={() =>
                                            setPages((value) =>
                                                value.filter(
                                                    (_, i) => i !== index,
                                                ),
                                            )
                                        }
                                    >
                                        Remove
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ol>
                    <div className="file-actions">
                        <button
                            className="secondary-button"
                            type="button"
                            onClick={() => setPages(plan.pages)}
                        >
                            Restore original order and pages
                        </button>
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
                            Prepare {pages.length} page
                            {pages.length === 1 ? "" : "s"} ↗
                        </button>
                    </div>
                </>
            )}
            {error && (
                <p role="alert" className="inline-notice">
                    {error}
                </p>
            )}
        </div>
    );
}
