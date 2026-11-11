"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";

import type { ExamDetail, RequirementSummary } from "../../lib/types";
import { factAttribution, factUrl, type ExamFact } from "../exam/exam-facts";
import { plainFindings } from "../../lib/finding-text";
import { isOurs } from "../../lib/requirement-support";
import { BILLING_ENABLED } from "../../billing/config";
import { kitPrice, rupees } from "../../billing/kit-pricing";
import { KitCheckout } from "../../billing/kit-checkout";
import { KitDownloads } from "../exam/kit-downloads";
import { useKit } from "../exam/use-kit";
import { useKitLiveness } from "../exam/use-kit-liveness";
import { DocumentWorkspace } from "../exam/document-workspace";
import { RequirementUpload } from "../exam/requirement-upload";
import { SelectAllToggle } from "../exam/select-all-toggle";
import { AppBar } from "./app-bar";
import { ActionBar } from "./action-bar";
import { Sheet } from "./sheet";
import { photographSpecRows, requirementSpecRows } from "../../lib/spec-format";

/**
 * The path on a phone, as screens rather than one long page.
 *
 * Choose the files, add them one at a time, download them (free, DEC-127;
 * with billing on, the last screen is checkout instead). Each
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
    { id: "pay", label: BILLING_ENABLED ? "Check" : "Download" },
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
    const { entries, forget } = useKit(exam.exam_id);
    // "Ready" is only true while the server still holds the file (owner's
    // testing, 1 October): a deleted one is forgotten and has to be added again.
    const { isLive, expired } = useKitLiveness(entries, forget);

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
    const flowKey = `uploadready:flow:${exam.exam_id}`;
    const remember = useCallback(
        (next: Step, requirement: string | null) => {
            try {
                sessionStorage.setItem(flowKey, JSON.stringify({ step: next, requirement }));
            } catch {
                // Storage blocked: a reload simply starts at the list.
            }
        },
        [flowKey],
    );
    const go = useCallback(
        (next: Step, requirement: string | null = null, replace = false) => {
            setStep(next);
            setActiveId(requirement);
            const state = { euk: { step: next, requirement } };
            if (replace) window.history.replaceState(state, "");
            else window.history.pushState(state, "");
            remember(next, requirement);
        },
        [remember],
    );

    // A phone reloads the page when the camera opens or a call comes in, and
    // the flow used to restart at the list with the candidate mid-file
    // (owner's testing, 1 October). Where they were is in the history entry,
    // which survives a reload, and in this tab's storage as a second copy.
    useEffect(() => {
        const timer = setTimeout(() => {
            type Saved = { step?: Step; requirement?: string | null };
            let saved: Saved | undefined = (window.history.state as { euk?: Saved } | null)?.euk;
            // The stored copy only answers a reload. On a fresh arrival it
            // would drop someone into a file with no list behind the back button.
            const arrival = (
                performance.getEntriesByType?.("navigation")[0] as PerformanceNavigationTiming | undefined
            )?.type;
            if (!saved && (arrival === "reload" || arrival === "back_forward")) {
                try {
                    const raw = sessionStorage.getItem(flowKey);
                    if (raw) saved = JSON.parse(raw) as Saved;
                } catch {
                    saved = undefined;
                }
            }
            if (!saved?.step || !STEP_LABELS.some((s) => s.id === saved!.step)) return;
            // Payment is never resumed into blind; the list of files is.
            setStep(saved.step === "pay" ? "add" : saved.step);
            const requirement = saved.requirement ?? null;
            setActiveId(
                requirement && ours.some((r) => r.requirement_id === requirement) ? requirement : null,
            );
        }, 0);
        return () => clearTimeout(timer);
    }, [flowKey, ours]);

    useEffect(() => {
        const onPop = (event: PopStateEvent) => {
            const state = (event.state as { euk?: { step: Step; requirement: string | null } })?.euk;
            setStep(state?.step ?? "files");
            setActiveId(state?.requirement ?? null);
            remember(state?.step ?? "files", state?.requirement ?? null);
        };
        window.addEventListener("popstate", onPop);
        return () => window.removeEventListener("popstate", onPop);
    }, [remember]);

    const chosen = ours.filter((r) => included.includes(r.requirement_id));
    const price = kitPrice(requirements, included);
    const ready = chosen.filter((r) => isLive(r.requirement_id));
    // A different one of the examination's facts each time a file comes back
    // ready, so returning to the list is never the same screen twice.
    const fact = facts.length > 0 ? facts[ready.length % facts.length] : null;
    const active = activeId ? ours.find((r) => r.requirement_id === activeId) : null;
    const stepIndex = STEP_LABELS.findIndex((s) => s.id === step);

    // --- one file, on its own screen ------------------------------------
    if (active) {
        const done = isLive(active.requirement_id);
        // A record may carry no photograph specification at all and still list
        // a photograph (DEC-079). Asking for its rows would throw, and a crash
        // on the file screen takes the whole flow with it.
        // The next chosen file with nothing ready yet, in the list's order.
        const nextFile =
            chosen.find(
                (r) =>
                    r.requirement_id !== active.requirement_id &&
                    !ready.some((d) => d.requirement_id === r.requirement_id),
            ) ?? null;
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

                {!busy && !done && (
                    <ActionBar note="Add this file">
                        <button
                            type="button"
                            className="secondary-button"
                            onClick={() => window.history.back()}
                        >
                            Do this later
                        </button>
                    </ActionBar>
                )}
                {/* A finished file leads on, never back: to the next file still
                    to add, or to the check when there is none (owner's testing,
                    1 October). The list is one tap away for anyone who wants it. */}
                {!busy && done && (
                    <ActionBar
                        note={
                            <span className="euk-m-barnote">
                                <strong>Ready</strong>
                                <button
                                    type="button"
                                    className="quiet-link"
                                    onClick={() => window.history.back()}
                                >
                                    Back to the list
                                </button>
                            </span>
                        }
                    >
                        {nextFile ? (
                            <button
                                type="button"
                                className="primary-button"
                                onClick={() => go("add", nextFile.requirement_id, true)}
                            >
                                Next: {nextFile.requirement_name}
                            </button>
                        ) : (
                            <button
                                type="button"
                                className="primary-button"
                                onClick={() => go("pay", null, true)}
                            >
                                {BILLING_ENABLED ? "Check and pay" : "Get my files"}
                            </button>
                        )}
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
                        doesn&rsquo;t want{BILLING_ENABLED ? ", and the price follows" : ""}.
                    </p>

                    {ours.length > 0 && (
                        <div className="euk-m-selectrow">
                            <p>
                                {included.length} of {ours.length} ticked
                            </p>
                            <SelectAllToggle
                                className="euk-m-selectall"
                                selected={included.length}
                                onClear={() => setIncluded([])}
                                onSelectAll={() =>
                                    setIncluded(ours.map((r) => r.requirement_id))
                                }
                            />
                        </div>
                    )}

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
                        One at a time. Each one is prepared as soon as you add it
                        {BILLING_ENABLED
                            ? ", and you see the result before you pay."
                            : ", and it is yours to download straight away."}
                    </p>
                    <ul className="euk-m-files">
                        {chosen.map((r) => {
                            const entry = entries[r.requirement_id];
                            const done = isLive(r.requirement_id);
                            const note =
                                done &&
                                !!entry &&
                                entry.outcome === "prepared_with_findings" &&
                                plainFindings(entry.findings).length > 0;
                            // Deleted by the server since it was prepared: said,
                            // so the row does not just go quiet.
                            const lapsed =
                                !done &&
                                (expired.has(r.requirement_id) ||
                                    (!!entry &&
                                        ["prepared", "prepared_with_findings"].includes(
                                            entry.outcome,
                                        )));
                            // An entry is written only once a preparation has
                            // finished, so one that is not prepared failed and
                            // wants another go, as the desktop row says.
                            const tone = lapsed
                                ? "retry"
                                : !entry
                                  ? undefined
                                  : done
                                    ? note
                                        ? "check"
                                        : "done"
                                    : "retry";
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
                                                {lapsed
                                                    ? "Expired. Add it again"
                                                    : tone === "check"
                                                    ? "Ready, with a note to read"
                                                    : tone === "done"
                                                      ? "Ready"
                                                      : tone === "retry"
                                                        ? "Try again"
                                                        : "Not added yet"}
                                            </span>
                                        </span>
                                        <span
                                            className="euk-m-file-state"
                                            data-tone={tone}
                                            aria-hidden="true"
                                        />
                                    </button>
                                </li>
                            );
                        })}
                    </ul>

                    {fact && (
                        <aside className="euk-m-fact" aria-label="Worth knowing">
                            <span className="euk-label">Worth knowing</span>
                            <p>{fact.text}</p>
                            {factUrl(fact) && (
                                <a href={factUrl(fact)} target="_blank" rel="noreferrer">
                                    {factAttribution(fact)} ↗
                                </a>
                            )}
                        </aside>
                    )}
                </div>
            )}

            {step === "pay" && (
                <div className="euk-m-screen euk-m-screen--pay">
                    {BILLING_ENABLED ? (
                        <KitCheckout
                            exam={exam}
                            entries={entries}
                            onBusy={setBusy}
                            selectedRequirements={included}
                            facts={facts}
                            onPrepareAgain={(requirementId) => go("add", requirementId, true)}
                        />
                    ) : (
                        <KitDownloads
                            exam={exam}
                            entries={entries}
                            selectedRequirements={included}
                            onPrepareAgain={(requirementId) => go("add", requirementId, true)}
                        />
                    )}
                </div>
            )}

            {step !== "pay" && (
                <ActionBar
                    note={
                        <>
                            {BILLING_ENABLED && price.chargeable > 0 ? (
                                <strong>{rupees(price.amount)}</strong>
                            ) : (
                                <strong>Free</strong>
                            )}
                            {BILLING_ENABLED && price.free > 0
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
                                ? BILLING_ENABLED
                                    ? "Check and pay"
                                    : "Get my files"
                                : BILLING_ENABLED
                                  ? `Check ${ready.length} of ${chosen.length}`
                                  : `Get ${ready.length} of ${chosen.length}`}
                        </button>
                    )}
                </ActionBar>
            )}
        </div>
    );
}
