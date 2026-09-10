"use client";
import { Fragment, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { ExamDetail } from "../../lib/types";
import { RequirementPanel } from "./requirement-panel";
import { useKit } from "./use-kit";
import { ReportIssue } from "./report-issue";
import { KitCheckout } from "./kit-checkout";

export function KitWorkspace({ exam }: { exam: ExamDetail }) {
    const requirements = useMemo(
        () => exam.requirements ?? [],
        [exam.requirements],
    );
    const { entries } = useKit(exam.exam_id);
    const [selectedId, setSelectedId] = useState(
        requirements.find((r) =>
            ["supported", "partially_supported"].includes(r.platform_support),
        )?.requirement_id ??
            requirements[0]?.requirement_id ??
            "",
    );
    const [included, setIncluded] = useState<string[]>(
        requirements
            .filter(
                (r) =>
                    ["supported", "partially_supported"].includes(
                        r.platform_support,
                    ) && r.requirement_status === "mandatory",
            )
            .map((r) => r.requirement_id),
    );
    useEffect(() => {
        const timer = setTimeout(() => {
            try {
                const raw = localStorage.getItem(
                    `uploadready:selection:${exam.exam_id}`,
                );
                if (raw) {
                    const ids: unknown = JSON.parse(raw);
                    if (Array.isArray(ids))
                        setIncluded(
                            ids.filter(
                                (id): id is string =>
                                    typeof id === "string" &&
                                    requirements.some(
                                        (r) =>
                                            r.requirement_id === id &&
                                            [
                                                "supported",
                                                "partially_supported",
                                            ].includes(r.platform_support),
                                    ),
                            ),
                        );
                }
            } catch {
                /* Optional preference. */
            }
        }, 0);
        return () => clearTimeout(timer);
    }, [exam.exam_id, requirements]);
    const [preparing, setPreparing] = useState(false);
    const [checkoutBusy, setCheckoutBusy] = useState(false);

    const ours = requirements.filter((r) =>
        ["supported", "partially_supported"].includes(r.platform_support),
    );
    const ready = ours.filter((r) =>
        ["prepared", "prepared_with_findings"].includes(
            entries[r.requirement_id]?.outcome,
        ),
    ).length;
    const selected = requirements.find((r) => r.requirement_id === selectedId);
    const selectedIndex = Math.max(
        0,
        requirements.findIndex((r) => r.requirement_id === selectedId),
    );
    return (
        <div className="exam-workspace">
            <div className="workspace-intro">
                <p className="eyebrow">{exam.conducting_body}</p>
                <h1>{exam.exam_name}</h1>
                <p>
                    {requirements.length} requirements. {ours.length} we can
                    help prepare. One less thing to worry about.
                </p>
            </div>
            <fieldset
                className="kit-selection"
                disabled={checkoutBusy || preparing}
            >
                <legend>Your kit, your choice.</legend>
                <p>
                    Required files we can prepare are selected. Uncheck what you
                    don’t need; add conditional items only if they apply to you.
                    Your review includes only selected prepared files.
                </p>
                <div>
                    {ours.map((r) => (
                        <label key={r.requirement_id}>
                            <input
                                type="checkbox"
                                checked={included.includes(r.requirement_id)}
                                onChange={(event) => {
                                    const next = event.target.checked
                                        ? [...included, r.requirement_id]
                                        : included.filter(
                                              (id) => id !== r.requirement_id,
                                          );
                                    setIncluded(next);
                                    try {
                                        localStorage.setItem(
                                            `uploadready:selection:${exam.exam_id}`,
                                            JSON.stringify(next),
                                        );
                                    } catch {
                                        /* Optional. */
                                    }
                                }}
                            />
                            <span>
                                {r.requirement_name}
                                {r.requirement_status !== "mandatory" && (
                                    <small>
                                        {r.applicability ||
                                            r.requirement_status}
                                    </small>
                                )}
                            </span>
                        </label>
                    ))}
                </div>
            </fieldset>
            <div className="mobile-kit-picker">
                <p>
                    {selected?.requirement_name} · {selectedIndex + 1} of{" "}
                    {requirements.length}
                </p>
                <span>
                    {ready} of {ours.length} prepared
                </span>
                <label
                    className="mobile-requirement-label"
                    htmlFor="mobile-requirement"
                >
                    Choose a requirement
                </label>
                <select
                    id="mobile-requirement"
                    value={selectedId}
                    onChange={(event) => setSelectedId(event.target.value)}
                >
                    <optgroup label="We prepare these">
                        {ours.map((r) => (
                            <option
                                key={r.requirement_id}
                                value={r.requirement_id}
                            >
                                {r.requirement_name}
                                {r.platform_support === "partially_supported"
                                    ? " — partly supported"
                                    : ""}
                            </option>
                        ))}
                    </optgroup>
                    <optgroup label="You do these yourself">
                        {requirements
                            .filter((r) => !ours.includes(r))
                            .map((r) => (
                                <option
                                    key={r.requirement_id}
                                    value={r.requirement_id}
                                >
                                    {r.requirement_name}
                                </option>
                            ))}
                    </optgroup>
                </select>
                <p
                    className={`mobile-support-group ${selected && !ours.includes(selected) ? "self-label" : ""}`}
                >
                    {selected && !ours.includes(selected)
                        ? "You do this yourself"
                        : selected?.platform_support === "partially_supported"
                          ? "We prepare part of this · further steps needed"
                          : "We prepare this file"}
                </p>
            </div>
            <div className="workspace-grid">
                <aside className="kit-rail">
                    <p className="rail-title">
                        Your upload kit{" "}
                        <span>
                            {ready}/{ours.length}
                        </span>
                    </p>
                    <nav aria-label="Required files">
                        {[
                            ...ours,
                            ...requirements.filter((r) => !ours.includes(r)),
                        ].map((r) => {
                            const entry = entries[r.requirement_id];
                            const served = [
                                "supported",
                                "partially_supported",
                            ].includes(r.platform_support);
                            const state =
                                entry?.outcome === "prepared" &&
                                r.platform_support !== "partially_supported"
                                    ? "Prepared"
                                    : entry?.outcome ===
                                        "prepared_with_findings"
                                      ? "Check findings"
                                      : entry &&
                                          r.platform_support ===
                                              "partially_supported"
                                        ? "Further steps needed"
                                        : entry
                                          ? "Try again"
                                          : served
                                            ? "Not added yet"
                                            : r.platform_support ===
                                                "not_yet_supported"
                                              ? "Not available yet"
                                              : "You complete this";
                            return (
                                <Fragment key={r.requirement_id}>
                                    {r === ours[0] && (
                                        <p className="rail-group-label">
                                            We prepare these
                                        </p>
                                    )}
                                    {r ===
                                        requirements.find(
                                            (item) => !ours.includes(item),
                                        ) && (
                                        <p className="rail-group-label self-label">
                                            You do these yourself
                                        </p>
                                    )}
                                    <button
                                        key={r.requirement_id}
                                        className="kit-step"
                                        data-self={!served}
                                        aria-current={
                                            selectedId === r.requirement_id
                                                ? "step"
                                                : undefined
                                        }
                                        onClick={() =>
                                            setSelectedId(r.requirement_id)
                                        }
                                    >
                                        <span className="step-number">
                                            {served ? "+" : "↗"}
                                        </span>
                                        <span>
                                            <strong>
                                                {r.requirement_name}
                                            </strong>
                                            <small>{state}</small>
                                        </span>
                                    </button>
                                </Fragment>
                            );
                        })}
                    </nav>
                    <div className="rail-links">
                        <Link href={`/exam/${exam.exam_id}/rules`}>
                            Rules & sources
                        </Link>
                        <ReportIssue
                            examName={exam.exam_name}
                            requirementName={selected?.requirement_name}
                            ruleId={exam.rule_id}
                        />
                        <Link href="/">Change exam</Link>
                    </div>
                </aside>
                <fieldset
                    className="workspace-panels"
                    disabled={checkoutBusy || preparing}
                >
                    {requirements.map((r, i) => (
                        <div
                            key={r.requirement_id}
                            hidden={selectedId !== r.requirement_id}
                        >
                            {!included.includes(r.requirement_id) &&
                                ours.includes(r) && (
                                    <p className="inline-notice">
                                        This file is not selected. Add it to
                                        your kit above to prepare and purchase
                                        it.
                                    </p>
                                )}
                            <fieldset
                                disabled={
                                    ours.includes(r) &&
                                    !included.includes(r.requirement_id)
                                }
                            >
                                <RequirementPanel
                                    requirement={r}
                                    index={i}
                                    exam={exam}
                                    onWorking={setPreparing}
                                />
                            </fieldset>
                        </div>
                    ))}
                </fieldset>
            </div>
            <KitCheckout
                exam={exam}
                entries={entries}
                onBusy={setCheckoutBusy}
                preparationBusy={preparing}
                selectedRequirements={included}
            />
        </div>
    );
}
