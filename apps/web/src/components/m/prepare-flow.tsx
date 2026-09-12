"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";

import type { ExamDetail, RequirementSummary } from "../../lib/types";
import type { ExamFact } from "../exam/exam-facts";
import { isOurs, kitPrice, rupees } from "../../lib/kit-pricing";
import { useKit } from "../exam/use-kit";
import { DocumentWorkspace } from "../exam/document-workspace";
import { RequirementUpload } from "../exam/requirement-upload";
import { KitCheckout } from "../exam/kit-checkout";
import { AppBar } from "./app-bar";
import { ActionBar } from "./action-bar";
import { Sheet } from "./sheet";
import { photographSpecRows, requirementSpecRows } from "../../lib/spec-format";

/**
 * The paid path on a phone, as four screens rather than one long page.
 *
 * Choose the files, add them one at a time, check what came back, pay. Each
 * screen asks for one thing and carries one action, in the bar under the
 * thumb; everything else a candidate might want — this file's rules, the
 * measurements, the price breakdown — opens as a sheet over the screen they
 * are on, so they never lose their place.
 *
 * Steps are pushed into history, so Android's back button walks back through
 * the flow instead of leaving the site, and a refresh lands where they were.
 * The selection shares `uploadready:selection:<exam>` with the desktop
 * workspace: the same candidate on a laptop later finds the same kit.
 */

type Step = "files" | "add" | "pay";

const STEP_LABELS: { id: Step; label: string }[] = [
    { id: "files", label: "Your files" },
    { id: "add", label: "Add them" },
    { id: "pay", label: "Check" },
];

function isDocument(requirement: RequirementSummary): boolean {
    return (
        requirement.requirement_type === "certificate_scan" ||
        requirement.requirement_type === "identity_document"
    );
}

export function PrepareFlow({
    exam,
    facts = [],
}: {
    exam: ExamDetail;
    facts?: ExamFact[];
}) {
    const requirements = useMemo(() => exam.requirements ?? [], [exam.requirements]);
    const ours = useMemo(() => requirements.filter(isOurs), [requirements]);
    const yours = useMemo(
        () => requirements.filter((r) => !isOurs(r)),
        [requirements],
    );
    const { entries } = useKit(exam.exam_id);

    const [step, setStep] = useState<Step>("files");
    const [activeId, setActiveId] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);
    const [sheet, setSheet] = useState<null | "rules" | "price">(null);
    const [included, setIncluded] = useState<string[]>(() =>
        ours.filter((r) => r.requirement_status === "mandatory").map((r) => r.requirement_id),
    );

    const storageKey = `uploadready:selection:${exam.exam_id}`;
    useEffect(() => {
        // After paint, not during it: the server rendered the default
        // selection and the stored one has to arrive without tearing it.
        const timer = setTimeout(() => {
            try {
                const raw = localStorage.getItem(storageKey);
                if (!raw) return;
                const ids: unknown = JSON.parse(raw);
                if (Array.isArray(ids)) {
                    setIncluded(
                        ids.filter(
                            (id): id is string =>
                                typeof id === "string" &&
                                ours.some((r) => r.requirement_id === id),
                        ),
                    );
                }
            } catch {
                // A browser with storage blocked keeps the default selection.
            }
        }, 0);
        return () => clearTimeout(timer);
    }, [storageKey, ours]);

    useEffect(() => {
        try {
            localStorage.setItem(storageKey, JSON.stringify(included));
        } catch {
            // As above: the selection simply does not outlive this visit.
        }
    }, [storageKey, included]);

    // History, so the back button steps the flow rather than leaving it.
    const go = useCallback((next: Step, requirement: string | null = null) => {
        setStep(next);
        setActiveId(requirement);
        window.history.pushState({ euk: { step: next, requirement } }, "");
    }, []);

    useEffect(() => {
        const onPop = (event: PopStateEvent) => {
            const state = (event.state as { euk?: { step: Step; requirement: string | null } })?.euk;
            setStep(state?.step ?? "files");
            setActiveId(state?.requirement ?? null);
        };
        window.addEventListener("popstate", onPop);
        return () => window.removeEventListener("popstate", onPop);
    }, []);

    const chosen = ours.filter((r) => included.includes(r.requirement_id));
    const price = kitPrice(requirements, included);
    const ready = chosen.filter((r) => {
        const entry = entries[r.requirement_id];
        return (
            entry && ["prepared", "prepared_with_findings"].includes(entry.outcome)
        );
    });
    const active = activeId ? ours.find((r) => r.requirement_id === activeId) : null;
    const stepIndex = STEP_LABELS.findIndex((s) => s.id === step);

    // --- one file, on its own screen ------------------------------------
    if (active) {
        const entry = entries[active.requirement_id];
        const done =
            entry && ["prepared", "prepared_with_findings"].includes(entry.outcome);
        // A record may carry no photograph specification at all and still list
        // a photograph (DEC-079). Asking for its rows would throw, and a crash
        // on the file screen takes the whole flow with it.
        const rows =
            active.requirement_type === "photograph" && exam.image_requirements
                ? photographSpecRows(exam)
                : requirementSpecRows(active, ours.indexOf(active), exam.provenance);

        return (
            <div className="euk euk-m" data-flow="file">
                <AppBar
                    title={active.requirement_name}
                    onBack={() => window.history.back()}
                    right={
                        <button
                            type="button"
                            className="euk-m-linkbtn"
                            onClick={() => setSheet("rules")}
                        >
                            Rules
                        </button>
                    }
                />
                <div className="euk-m-screen">
                    {isDocument(active) ? (
                        <DocumentWorkspace
                            examId={exam.exam_id}
                            examName={exam.exam_name}
                            requirementId={active.requirement_id}
                            requirementName={active.requirement_name}
                            partiallySupported={active.platform_support === "partially_supported"}
                            onWorking={setBusy}
                        />
                    ) : (
                        <RequirementUpload
                            examId={exam.exam_id}
                            examName={exam.exam_name}
                            requirementId={active.requirement_id}
                            requirementName={active.requirement_name}
                            requirementType={active.requirement_type}
                            partiallySupported={active.platform_support === "partially_supported"}
                            onWorking={setBusy}
                        />
                    )}
                </div>

                {!busy && (
                    <ActionBar note={done ? <strong>Ready</strong> : "Add this file"}>
                        <button
                            type="button"
                            className={done ? "primary-button" : "secondary-button"}
                            onClick={() => window.history.back()}
                        >
                            {done ? "Back to the list" : "Do this later"}
                        </button>
                    </ActionBar>
                )}

                <Sheet
                    open={sheet === "rules"}
                    title={`${active.requirement_name}: the rules`}
                    onClose={() => setSheet(null)}
                >
                    <dl className="euk-m-specs">
                        {rows.map((row) => (
                            <div key={row.term}>
                                <dt>{row.term}</dt>
                                <dd>
                                    {row.value}
                                    {row.estimated ? (
                                        <span className="euk-m-est"> est.</span>
                                    ) : null}
                                </dd>
                            </div>
                        ))}
                    </dl>
                    <p className="euk-m-sheet-note">
                        Every figure comes from what {exam.conducting_body} published.{" "}
                        <Link href={`/exam/${exam.exam_id}/rules`}>
                            The full rules and their sources
                        </Link>
                    </p>
                </Sheet>
            </div>
        );
    }

    // --- the flow --------------------------------------------------------
    return (
        <div className="euk euk-m" data-flow={step}>
            <AppBar
                title={exam.exam_name}
                onBack={step === "files" ? undefined : () => window.history.back()}
                backHref={step === "files" ? `/exam/${exam.exam_id}` : undefined}
                pinned
            />

            <ol className="euk-m-steps" aria-label="Progress">
                {STEP_LABELS.map((item, i) => (
                    <li
                        key={item.id}
                        data-state={i < stepIndex ? "done" : i === stepIndex ? "now" : undefined}
                        aria-current={i === stepIndex ? "step" : undefined}
                    >
                        <span>{item.label}</span>
                    </li>
                ))}
            </ol>

            {step === "files" && (
                <div className="euk-m-screen">
                    <h2 className="euk-display euk-m-title">
                        What {exam.exam_name} asks you to upload
                    </h2>
                    <p className="euk-m-lede">
                        Everything it asks for is ticked. Untick anything your form
                        doesn&rsquo;t want, and the price follows.
                    </p>

                    <ul className="euk-m-files">
                        {ours.map((r) => {
                            const on = included.includes(r.requirement_id);
                            return (
                                <li key={r.requirement_id}>
                                    <label className="euk-m-file">
                                        <input
                                            type="checkbox"
                                            checked={on}
                                            onChange={() =>
                                                setIncluded((list) =>
                                                    on
                                                        ? list.filter((id) => id !== r.requirement_id)
                                                        : [...list, r.requirement_id],
                                                )
                                            }
                                        />
                                        <span className="euk-m-file-body">
                                            <strong>{r.requirement_name}</strong>
                                            <span>
                                                {r.requirement_status === "mandatory"
                                                    ? "Required by this form"
                                                    : "Optional"}
                                                {r.platform_support === "partially_supported"
                                                    ? " · we prepare part of this"
                                                    : ""}
                                            </span>
                                        </span>
                                        <span className="euk-m-file-tick" aria-hidden="true" />
                                    </label>
                                </li>
                            );
                        })}
                    </ul>

                    {yours.length > 0 && (
                        <div className="euk-m-yours">
                            <h3>You do these yourself</h3>
                            <ul>
                                {yours.map((r) => (
                                    <li key={r.requirement_id}>{r.requirement_name}</li>
                                ))}
                            </ul>
                            <p>
                                This examination handles them in its own portal, so there
                                is nothing for us to prepare.
                            </p>
                        </div>
                    )}
                </div>
            )}

            {step === "add" && (
                <div className="euk-m-screen">
                    <h2 className="euk-display euk-m-title">Add your files</h2>
                    <p className="euk-m-lede">
                        One at a time. Each one is prepared as soon as you add it, and
                        you see the result before you pay.
                    </p>
                    <ul className="euk-m-files">
                        {chosen.map((r) => {
                            const entry = entries[r.requirement_id];
                            const done =
                                entry &&
                                ["prepared", "prepared_with_findings"].includes(entry.outcome);
                            return (
                                <li key={r.requirement_id}>
                                    <button
                                        type="button"
                                        className="euk-m-file euk-m-file--go"
                                        onClick={() => go("add", r.requirement_id)}
                                    >
                                        <span className="euk-m-file-body">
                                            <strong>{r.requirement_name}</strong>
                                            <span>
                                                {done
                                                    ? entry.outcome === "prepared_with_findings"
                                                        ? "Ready, with a note to read"
                                                        : "Ready"
                                                    : "Not added yet"}
                                            </span>
                                        </span>
                                        <span
                                            className="euk-m-file-state"
                                            data-done={done || undefined}
                                            aria-hidden="true"
                                        />
                                    </button>
                                </li>
                            );
                        })}
                    </ul>
                </div>
            )}

            {step === "pay" && (
                <div className="euk-m-screen euk-m-screen--pay">
                    <KitCheckout
                        exam={exam}
                        entries={entries}
                        onBusy={setBusy}
                        selectedRequirements={included}
                        facts={facts}
                    />
                </div>
            )}

            {step !== "pay" && (
                <ActionBar
                    note={
                        <>
                            {price.chargeable > 0 ? (
                                <strong>{rupees(price.amount)}</strong>
                            ) : (
                                <strong>Free</strong>
                            )}
                            {price.free > 0
                                ? `${price.chosen} files, ${price.free} free`
                                : `${price.chosen} file${price.chosen === 1 ? "" : "s"}`}
                        </>
                    }
                >
                    {step === "files" ? (
                        <button
                            type="button"
                            className="primary-button"
                            disabled={chosen.length === 0}
                            onClick={() => go("add")}
                        >
                            Add your files
                        </button>
                    ) : (
                        <button
                            type="button"
                            className="primary-button"
                            disabled={ready.length === 0}
                            onClick={() => go("pay")}
                        >
                            {ready.length === chosen.length
                                ? "Check and pay"
                                : `Check ${ready.length} of ${chosen.length}`}
                        </button>
                    )}
                </ActionBar>
            )}
        </div>
    );
}
