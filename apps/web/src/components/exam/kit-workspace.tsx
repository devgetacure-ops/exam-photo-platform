"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import type { ExamDetail, RequirementSummary } from "../../lib/types";
import type { KitEntry } from "../../lib/kit-state";
import { RequirementPanel } from "./requirement-panel";
import { useKit } from "./use-kit";
import { useTr } from "../locale-context";
import { ReportIssue } from "./report-issue";
import { KitCheckout } from "../../billing/kit-checkout";
import { BILLING_ENABLED } from "../../billing/config";
import { CHARGEABLE_TYPES, kitPrice, rupees } from "../../billing/kit-pricing";
import { KitDownloads } from "./kit-downloads";
import { FileTypeDrawing } from "../euk/doodles";
import { isOurs } from "../../lib/requirement-support";
import { nextStep, waitingFile } from "../../lib/kit-next";
import { photographSpecRows, requirementSpecRows } from "../../lib/spec-format";
import { toolsReplaced } from "../../lib/value-tools";
import { plainFindings } from "../../lib/finding-text";
import { bringIntoView } from "../../lib/scroll";
import { useCheckoutStage } from "./live-job-state";
import type { ExamFact } from "./exam-facts";
import { SelectAllToggle } from "./select-all-toggle";

/**
 * The kit: every file this application asks for, and the file being worked
 * on. While billing is on (DEC-127) it also says what the kit costs.
 *
 * The whole kit starts selected. The candidate unticks what they don't need
 * and the price follows, and the moment the selection is short of the whole
 * kit, the card says what the rest would cost, because on the ladder it is
 * often nothing or very little. The price is a display of the server's ladder;
 * the review shows the server's own quote.
 *
 * The boundary is still carried three ways: files we prepare and files the
 * candidate completes are separate groups, they are drawn differently, and
 * nothing in the second has a checkbox or an upload control.
 */

type Tone = "idle" | "done" | "check" | "retry";

/**
 * The chip at the end of a row. There is none before a file has been added:
 * the row's own Add button already says so, and a "Not added yet" chip beside
 * an ADD button is the same sentence twice.
 */
function stateOf(
    entry: KitEntry | undefined,
    requirement: RequirementSummary,
    tr: (english: string, hindi: string) => string,
): { text: string; tone: Tone } {
    if (!entry) return { text: tr("Not added yet", "अभी जोड़ी नहीं गई"), tone: "idle" };
    if (
        entry.outcome === "prepared_with_findings" &&
        plainFindings(entry.findings).length > 0
    )
        return { text: tr("Worth a look", "एक बार देख लें"), tone: "check" };
    if (
        entry.outcome === "prepared" ||
        entry.outcome === "prepared_with_findings"
    )
        return requirement.platform_support === "partially_supported"
            ? { text: tr("One step yours", "एक काम आपका"), tone: "check" }
            : { text: tr("Prepared", "तैयार"), tone: "done" };
    return { text: tr("Try again", "फिर से कोशिश करें"), tone: "retry" };
}

function shortSpec(exam: ExamDetail, requirement: RequirementSummary): string {
    const index = (exam.requirements ?? []).indexOf(requirement);
    const rows =
        requirement.requirement_type === "photograph"
            ? photographSpecRows(exam)
            : requirementSpecRows(requirement, index, exam.provenance);
    return rows
        .filter((row) => row.term === "Dimensions" || row.term === "File size")
        .map((row) => row.value)
        .join(" · ");
}

function whenPhrase(requirement: RequirementSummary): string | null {
    switch (requirement.requirement_status) {
        case "conditional":
            return "only if it applies to you";
        case "portal_dependent":
            return "if the portal asks for it";
        case "optional":
            return "optional";
        default:
            return null;
    }
}

function yoursPhrase(
    requirement: RequirementSummary,
    tr: (english: string, hindi: string) => string,
): string {
    switch (requirement.platform_support) {
        case "not_yet_supported":
            return tr("We can’t prepare this yet", "इसे हम अभी तैयार नहीं कर सकते");
        case "physical_stage":
            return tr("Done in person", "यह खुद जाकर होता है");
        default:
            return tr("You complete this", "यह आप पूरा करेंगे");
    }
}

export function KitWorkspace({
    exam,
    facts = [],
}: {
    exam: ExamDetail;
    facts?: ExamFact[];
}) {
    const requirements = useMemo(
        () => exam.requirements ?? [],
        [exam.requirements],
    );
    const ours = useMemo(() => requirements.filter(isOurs), [requirements]);
    const yours = useMemo(
        () => requirements.filter((r) => !isOurs(r)),
        [requirements],
    );
    const tr = useTr();
    const { entries } = useKit(exam.exam_id);
    const [selectedId, setSelectedId] = useState(
        ours[0]?.requirement_id ?? requirements[0]?.requirement_id ?? "",
    );
    const [included, setIncluded] = useState<string[]>(() =>
        ours
            .filter((r) => r.requirement_status === "mandatory")
            .map((r) => r.requirement_id),
    );
    const storageKey = `uploadready:selection:${exam.exam_id}`;
    useEffect(() => {
        const timer = setTimeout(() => {
            try {
                const raw = localStorage.getItem(storageKey);
                if (!raw) return;
                const ids: unknown = JSON.parse(raw);
                if (Array.isArray(ids))
                    setIncluded(
                        ids.filter(
                            (id): id is string =>
                                typeof id === "string" &&
                                ours.some((r) => r.requirement_id === id),
                        ),
                    );
            } catch {
                /* Optional preference. */
            }
        }, 0);
        return () => clearTimeout(timer);
    }, [storageKey, ours]);
    const [preparing, setPreparing] = useState(false);
    const [checkoutBusy, setCheckoutBusy] = useState(false);
    const busy = preparing || checkoutBusy;

    const choose = (next: string[]) => {
        setIncluded(next);
        try {
            localStorage.setItem(storageKey, JSON.stringify(next));
        } catch {
            /* Optional preference. */
        }
    };
    const toggle = (id: string, on: boolean) =>
        choose(
            on
                ? [...included.filter((x) => x !== id), id]
                : included.filter((x) => x !== id),
        );
    // Every move the workspace makes lands the same way (lib/scroll).
    const goTo = (elementId: string) => {
        requestAnimationFrame(() =>
            bringIntoView(document.getElementById(elementId)),
        );
    };
    const checkoutStage = useCheckoutStage(exam.exam_id);
    // Free (DEC-127) there is no payment to wait for: downloads are simply
    // there once a file is prepared. `paid` keeps its billing meaning.
    const paid = BILLING_ENABLED && checkoutStage === "delivered";
    // The bar is hidden while the review itself is on screen, so the one
    // action is never shown twice (testing note E).
    const [reviewInView, setReviewInView] = useState(false);
    useEffect(() => {
        const el = document.getElementById("kit-review");
        if (!el || typeof IntersectionObserver === "undefined") return;
        const observer = new IntersectionObserver(([entry]) =>
            setReviewInView(entry.isIntersecting),
        );
        observer.observe(el);
        return () => observer.disconnect();
    }, []);
    // `take` is the difference between choosing a file and going to work on
    // it. The row switches the panel; Add carries the candidate down to it,
    // which is the whole reason the button exists.
    const open = (id: string, take = false) => {
        setSelectedId(id);
        if (take || window.matchMedia("(max-width: 999px)").matches) {
            goTo(`panel-${id}`);
        }
    };

    const price = kitPrice(requirements, included);
    const tools = useMemo(() => toolsReplaced(exam), [exam]);
    const hasDocuments = ours.some(
        (r) => !CHARGEABLE_TYPES.has(r.requirement_type),
    );
    const ready = ours.filter((r) =>
        ["prepared", "prepared_with_findings"].includes(
            entries[r.requirement_id]?.outcome,
        ),
    ).length;
    const selected = requirements.find((r) => r.requirement_id === selectedId);
    const preparedIds = ours
        .filter((r) =>
            ["prepared", "prepared_with_findings"].includes(
                entries[r.requirement_id]?.outcome,
            ),
        )
        .map((r) => r.requirement_id);
    // Whatever the candidate is looking at, this is what is still to do. The
    // floating bar, the list marker and the panel all take it from here.
    const waiting = waitingFile({
        kit: ours.map((r) => ({
            requirementId: r.requirement_id,
            name: r.requirement_name,
        })),
        included,
        prepared: preparedIds,
    });
    // A file has just been prepared: bring what follows into view, so the
    // next step arrives rather than waiting at the bottom of a long panel to
    // be found. Only when it is not already on screen, and never on arrival.
    const shownReady = useRef<number | null>(null);
    useEffect(() => {
        const previous = shownReady.current;
        shownReady.current = ready;
        if (previous === null || ready <= previous) return;
        const frame = requestAnimationFrame(() =>
            bringIntoView(document.getElementById("kit-onward"), {
                onlyIfNeeded: true,
            }),
        );
        return () => cancelAnimationFrame(frame);
    }, [ready]);

    const onward = nextStep({
        kit: ours.map((r) => ({
            requirementId: r.requirement_id,
            name: r.requirement_name,
        })),
        included,
        prepared: preparedIds,
        current: selectedId,
    });

    const everything = price.kitFiles > 0 && price.chosen === price.kitFiles;
    const priceName = everything
        ? "The whole kit"
        : `${price.chosen} of ${price.kitFiles} file${price.kitFiles === 1 ? "" : "s"}`;
    let note: string;
    if (price.kitChargeable === 0) {
        note =
            "Every file here is document work, which we do alongside a prepared photograph or signature. This application has none for us to prepare.";
    } else if (price.chosen === 0) {
        note = "Tick the files you want prepared.";
    } else if (price.chargeable === 0) {
        note =
            "Documents are free with a photograph, signature, thumb impression or declaration in the kit.";
    } else if (everything) {
        note =
            price.kitFree > 0
                ? `Every file we prepare for this application, with ${price.kitFree} document${price.kitFree === 1 ? "" : "s"} free.`
                : "Every file we prepare for this application.";
    } else {
        note = `The whole kit is ${rupees(price.kitAmount)} for all ${price.kitFiles}.`;
    }
    const missing = price.kitFiles - price.chosen;
    const extra = price.kitAmount - price.amount;
    const push =
        !everything && missing > 0 && price.kitChargeable > 0
            ? extra > 0
                ? `Add the other ${missing} for ${rupees(extra)} more`
                : `Add the other ${missing}, at no extra cost`
            : null;

    return (
        <div className="euk-kit">
            <div className="euk-wrap euk-kit-layout">
                <section className="euk-kit-list" aria-labelledby="kit-title">
                    <div className="euk-kit-head">
                        <h2 id="kit-title" className="euk-display">
                            {ours.length ? tr("Your kit", "आपकी किट") : tr("What it asks for", "इसमें क्या चाहिए")}
                        </h2>
                        {ours.length > 0 && (
                            <div className="euk-kit-head-meta">
                                <p className="euk-kit-progress">
                                    {tr(`${ready} of ${ours.length} prepared`, `${ours.length} में से ${ready} तैयार`)}
                                </p>
                                {!paid && (
                                    <SelectAllToggle
                                        className="euk-kit-selectall"
                                        selected={included.length}
                                        disabled={busy}
                                        onClear={() => choose([])}
                                        onSelectAll={() =>
                                            choose(
                                                ours.map(
                                                    (r) => r.requirement_id,
                                                ),
                                            )
                                        }
                                    />
                                )}
                            </div>
                        )}
                    </div>

                    {ours.length > 0 && (
                        <fieldset className="euk-kit-fieldset" disabled={busy}>
                            <legend className="sr-only">
                                {tr("Files we prepare for this application", "इस आवेदन के लिए हम जो फ़ाइलें तैयार करते हैं")}
                            </legend>
                            <ul className="euk-kit-files">
                                {ours.map((r) => {
                                    const id = r.requirement_id;
                                    const on = included.includes(id);
                                    const state = stateOf(entries[id], r, tr);
                                    const meta = [
                                        shortSpec(exam, r),
                                        !BILLING_ENABLED ||
                                        CHARGEABLE_TYPES.has(r.requirement_type)
                                            ? null
                                            : "free with the kit",
                                        whenPhrase(r),
                                    ]
                                        .filter(Boolean)
                                        .join(" · ");
                                    return (
                                        <li
                                            key={id}
                                            className="euk-kit-file"
                                            data-active={selectedId === id}
                                            data-on={on}
                                        >
                                            <input
                                                type="checkbox"
                                                className="euk-kit-check"
                                                checked={on}
                                                aria-label={tr(`Include ${r.requirement_name} in your kit`, `${r.requirement_name} को अपनी किट में शामिल करें`)}
                                                onChange={(event) =>
                                                    toggle(
                                                        id,
                                                        event.target.checked,
                                                    )
                                                }
                                            />
                                            <button
                                                type="button"
                                                className="euk-kit-open"
                                                onClick={() => open(id)}
                                                aria-controls={`panel-${id}`}
                                                aria-current={
                                                    selectedId === id
                                                        ? "step"
                                                        : undefined
                                                }
                                            >
                                                <FileTypeDrawing
                                                    type={r.requirement_type}
                                                    className="euk-kit-icon"
                                                />
                                                <span className="min-w-0">
                                                    <span className="euk-kit-name">
                                                        {r.requirement_name}
                                                    </span>
                                                    {meta && (
                                                        <span className="euk-kit-meta">
                                                            {meta}
                                                        </span>
                                                    )}
                                                </span>
                                                {waiting?.requirementId ===
                                                    id &&
                                                    !paid && (
                                                        <span className="euk-kit-next">
                                                            {tr("Next", "अगला")}
                                                        </span>
                                                    )}
                                                {state.tone !== "idle" && (
                                                    <span
                                                        className="euk-kit-state"
                                                        data-tone={state.tone}
                                                    >
                                                        {state.text}
                                                    </span>
                                                )}
                                            </button>
                                            <button
                                                type="button"
                                                className="euk-kit-add"
                                                onClick={() => {
                                                    if (!on) toggle(id, true);
                                                    open(id, true);
                                                }}
                                                aria-controls={`panel-${id}`}
                                                /* The visible word is the
                                                   start of the name, so the
                                                   two agree for anyone using
                                                   speech (WCAG 2.5.3). It is
                                                   a label rather than hidden
                                                   text because hidden text
                                                   inside this button would
                                                   inherit its capitals. */
                                                aria-label={`${entries[id] ? tr("Open", "खोलें") : tr("Add", "जोड़ें")} ${r.requirement_name}`}
                                            >
                                                {entries[id] ? tr("Open", "खोलें") : tr("Add", "जोड़ें")}
                                            </button>
                                        </li>
                                    );
                                })}
                            </ul>
                        </fieldset>
                    )}

                    {yours.length > 0 && (
                        <div className="euk-kit-yours">
                            <h3 className="euk-kit-yours-title">
                                {yours.length === 1
                                    ? tr("One you complete yourself", "एक आपको खुद पूरा करना है")
                                    : tr(`${yours.length} you complete yourself`, `${yours.length} आपको खुद पूरे करने हैं`)}
                            </h3>
                            <ul>
                                {yours.map((r) => (
                                    <li
                                        key={r.requirement_id}
                                        data-active={
                                            selectedId === r.requirement_id
                                        }
                                    >
                                        <button
                                            type="button"
                                            onClick={() =>
                                                open(r.requirement_id)
                                            }
                                            aria-controls={`panel-${r.requirement_id}`}
                                            aria-current={
                                                selectedId === r.requirement_id
                                                    ? "step"
                                                    : undefined
                                            }
                                        >
                                            <span
                                                className="euk-kit-dash"
                                                aria-hidden="true"
                                            />
                                            <span className="euk-kit-name">
                                                {r.requirement_name}
                                            </span>
                                            <span className="euk-kit-yours-state">
                                                {yoursPhrase(r, tr)}
                                            </span>
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </section>

                {ours.length > 0 && (
                    <aside
                        className="euk-kit-side"
                        aria-label={
                            BILLING_ENABLED ? "What your kit costs" : tr("Your kit", "आपकी किट")
                        }
                    >
                        {BILLING_ENABLED && (
                        <div className="euk-kit-price">
                            <p className="euk-kit-price-name">{priceName}</p>
                            <p className="euk-kit-price-row">
                                <span
                                    key={price.amount}
                                    className="euk-kit-price-figure"
                                >
                                    {rupees(price.amount)}
                                </span>
                                {price.list > price.amount && (
                                    <del>{rupees(price.list)}</del>
                                )}
                            </p>
                            <p className="euk-kit-price-note">{note}</p>
                            {push && (
                                <button
                                    type="button"
                                    className="primary-button euk-kit-push"
                                    disabled={busy}
                                    onClick={() =>
                                        choose(
                                            ours.map((r) => r.requirement_id),
                                        )
                                    }
                                >
                                    {push}
                                </button>
                            )}
                            <p className="euk-kit-price-fine">
                                You see every file before you pay. The total is
                                confirmed when you review.
                            </p>
                        </div>
                        )}

                        {tools.length >= 2 && (
                            <div className="euk-kit-without">
                                <h3>{tr("The other way", "दूसरा तरीका")}</h3>
                                <p>
                                    {tr(
                                        `These files would take ${tools.length} separate tools, usually on separate sites:`,
                                        `इन फ़ाइलों के लिए ${tools.length} अलग-अलग टूल लगते, अक्सर अलग-अलग साइटों पर:`,
                                    )}
                                </p>
                                <ul className="euk-chips">
                                    {tools.map((tool) => (
                                        <li
                                            key={tool.id}
                                            className="euk-chip euk-chip--gone"
                                        >
                                            {tool.label}
                                        </li>
                                    ))}
                                </ul>
                                <p>
                                    {!BILLING_ENABLED
                                        ? tr("Here each file is one upload, and all of it is free.", "यहाँ हर फ़ाइल एक अपलोड में, और सब मुफ़्त।")
                                        : hasDocuments
                                          ? "Here each file is one upload, and the PDF work is free with the kit."
                                          : "Here each file is one upload."}
                                </p>
                            </div>
                        )}
                    </aside>
                )}
            </div>

            {requirements.length > 0 && (
                <div className="euk-wrap euk-kit-panels">
                    <fieldset className="euk-kit-panelset" disabled={busy}>
                        <legend className="sr-only">
                            {tr("The file you are working on", "जिस फ़ाइल पर आप काम कर रहे हैं")}
                        </legend>
                        {requirements.map((r, i) => {
                            const id = r.requirement_id;
                            const excluded =
                                isOurs(r) && !included.includes(id);
                            return (
                                <div
                                    key={id}
                                    id={`panel-${id}`}
                                    className="euk-kit-panel"
                                    hidden={selectedId !== id}
                                >
                                    {excluded && (
                                        <div className="euk-kit-excluded">
                                            <p>{tr("This file isn’t in your kit.", "यह फ़ाइल आपकी किट में नहीं है।")}</p>
                                            <button
                                                type="button"
                                                className="secondary-button"
                                                onClick={() => toggle(id, true)}
                                            >
                                                {tr("Add it to the kit", "इसे किट में जोड़ें")}
                                            </button>
                                        </div>
                                    )}
                                    <fieldset
                                        className="euk-kit-panel-inner"
                                        disabled={excluded}
                                    >
                                        <RequirementPanel
                                            requirement={r}
                                            index={i}
                                            exam={exam}
                                            onWorking={setPreparing}
                                        />
                                    </fieldset>
                                    {selectedId === id &&
                                        onward.kind !== "none" && (
                                            <div
                                                className="euk-kit-onward"
                                                id="kit-onward"
                                            >
                                                <p className="euk-kit-onward-say">
                                                    {paid
                                                        ? "Paid. Your downloads are below"
                                                        : onward.kind ===
                                                            "review"
                                                          ? tr(`All ${onward.total} file${onward.total === 1 ? "" : "s"} in your kit are prepared`, `आपकी किट की सभी ${onward.total} फ़ाइलें तैयार हैं`)
                                                          : tr(`${onward.prepared} of ${onward.total} prepared`, `${onward.total} में से ${onward.prepared} तैयार`)}
                                                </p>
                                                {paid ? (
                                                    <button
                                                        type="button"
                                                        className="primary-button euk-kit-onward-go"
                                                        onClick={() =>
                                                            goTo("kit-review")
                                                        }
                                                    >
                                                        {tr("Go to your downloads", "अपने डाउनलोड पर जाएँ")}
                                                    </button>
                                                ) : onward.kind === "review" ? (
                                                    <button
                                                        type="button"
                                                        className="primary-button euk-kit-onward-go"
                                                        onClick={() =>
                                                            goTo("kit-review")
                                                        }
                                                    >
                                                        {BILLING_ENABLED
                                                            ? `Review and pay ${rupees(price.amount)}`
                                                            : tr("Go to your downloads", "अपने डाउनलोड पर जाएँ")}
                                                    </button>
                                                ) : (
                                                    <button
                                                        type="button"
                                                        className="primary-button euk-kit-onward-go"
                                                        onClick={() =>
                                                            open(
                                                                onward.requirementId,
                                                                true,
                                                            )
                                                        }
                                                    >
                                                        {tr("Next", "अगला")}: {onward.name}
                                                    </button>
                                                )}
                                            </div>
                                        )}
                                </div>
                            );
                        })}
                    </fieldset>
                </div>
            )}

            <div className="euk-wrap euk-kit-links">
                <Link href={`/exam/${exam.exam_id}/rules`}>
                    {tr("Rules and sources", "नियम और स्रोत")}
                </Link>
                <ReportIssue
                    examName={exam.exam_name}
                    requirementName={selected?.requirement_name}
                    ruleId={exam.rule_id}
                />
                <Link href="/exams">{tr("Change exam", "परीक्षा बदलें")}</Link>
            </div>

            <div id="kit-review" className="euk-wrap euk-kit-review">
                {BILLING_ENABLED ? (
                    <KitCheckout
                        exam={exam}
                        entries={entries}
                        onBusy={setCheckoutBusy}
                        preparationBusy={preparing}
                        selectedRequirements={included}
                        facts={facts}
                    />
                ) : (
                    <KitDownloads
                        exam={exam}
                        entries={entries}
                        selectedRequirements={included}
                        onPrepareAgain={(id) => open(id, true)}
                    />
                )}
            </div>

            {ours.length > 0 && (
                <div
                    className="euk-kit-bar"
                    data-ready={ready > 0 || undefined}
                    data-hidden={reviewInView || undefined}
                >
                    <span className="euk-kit-bar-name">
                        {paid
                            ? "Paid"
                            : waiting
                              ? tr(`${ready} of ${included.length} prepared`, `${included.length} में से ${ready} तैयार`)
                              : BILLING_ENABLED
                                ? priceName
                                : tr(`${ready} prepared`, `${ready} तैयार`)}
                    </span>
                    {BILLING_ENABLED && !paid && !waiting && (
                        <strong className="euk-kit-bar-figure">
                            {rupees(price.amount)}
                        </strong>
                    )}
                    {/* While anything is still to do, the one loud control is
                        the next file, not the payment: a candidate who had
                        prepared one of four was offered "Review and pay" and
                        nothing else, and could not find where to carry on
                        (owner, 23 September, DEC-107). Review stays one quiet
                        word away. */}
                    {!paid && waiting && (
                        <button
                            type="button"
                            className="euk-kit-bar-go"
                            onClick={() => open(waiting.requirementId, true)}
                        >
                            {tr("Next", "अगला")}: {waiting.name}
                        </button>
                    )}
                    <a
                        href="#kit-review"
                        className={
                            !paid && waiting ? "euk-kit-bar-quiet" : undefined
                        }
                        onClick={(event) => {
                            event.preventDefault();
                            goTo("kit-review");
                        }}
                    >
                        {paid || !BILLING_ENABLED
                            ? tr("Downloads", "डाउनलोड")
                            : waiting
                              ? "Review"
                              : "Review and pay"}
                    </a>
                </div>
            )}
        </div>
    );
}
