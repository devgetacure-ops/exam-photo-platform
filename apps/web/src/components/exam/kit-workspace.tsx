"use client";
import { useEffect, useMemo, useState } from "react";
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
    return (
        <div className="euk-sheet">
            <header className="euk-sheet-head">
                <div className="min-w-0">
                    <p className="euk-label text-[10px] text-[var(--ink-55)]">
                        {exam.conducting_body}
                    </p>
                    <h1 className="euk-display pt-1 text-[30px] md:text-[44px]">
                        {exam.exam_name}
                    </h1>
                </div>
                <p className="euk-label shrink-0 border-2 border-[var(--ink)] px-3 py-2 text-[10px]">
                    {ready}/{ours.length} prepared
                </p>
            </header>

            {/*
                One list, not three.

                This previously rendered the same requirements three times: a
                checkbox fieldset at the top, a navigation rail down the left,
                and a select for mobile — three widgets, three vocabularies,
                one set of files. A row here does both jobs. The checkbox
                decides what you are buying; the row decides what you are
                looking at.

                The boundary is still carried three ways and is easier to read
                for the collapse: Part A and Part B are separate groups, they
                are coloured differently, and nothing in Part B has a checkbox
                or an upload control.
            */}
            <fieldset className="euk-parts" disabled={checkoutBusy || preparing}>
                <legend className="sr-only">Files for this application</legend>

                <p className="euk-part-head">Part A — we prepare these</p>
                <ul>
                    {ours.map((r) => {
                        const entry = entries[r.requirement_id];
                        const on = included.includes(r.requirement_id);
                        return (
                            <li
                                key={r.requirement_id}
                                className="euk-part-row"
                                data-active={selectedId === r.requirement_id}
                            >
                                <input
                                    type="checkbox"
                                    checked={on}
                                    aria-label={`Include ${r.requirement_name} in your kit`}
                                    onChange={(event) => {
                                        const next = event.target.checked
                                            ? [...included, r.requirement_id]
                                            : included.filter(
                                                  (id) =>
                                                      id !== r.requirement_id,
                                              );
                                        setIncluded(next);
                                        try {
                                            localStorage.setItem(
                                                `uploadready:selection:${exam.exam_id}`,
                                                JSON.stringify(next),
                                            );
                                        } catch {
                                            /* Optional preference. */
                                        }
                                    }}
                                />
                                <button
                                    type="button"
                                    onClick={() =>
                                        setSelectedId(r.requirement_id)
                                    }
                                    aria-current={
                                        selectedId === r.requirement_id
                                            ? "step"
                                            : undefined
                                    }
                                >
                                    <span className="euk-part-name">
                                        {r.requirement_name}
                                        {r.requirement_status !==
                                            "mandatory" && (
                                            <small>
                                                {r.applicability ||
                                                    r.requirement_status}
                                            </small>
                                        )}
                                    </span>
                                    <span className="euk-part-state">
                                        {entry?.outcome === "prepared" &&
                                        r.platform_support !==
                                            "partially_supported"
                                            ? "Prepared"
                                            : entry?.outcome ===
                                                "prepared_with_findings"
                                              ? "Check findings"
                                              : entry &&
                                                  r.platform_support ===
                                                      "partially_supported"
                                                ? "One step yours"
                                                : entry
                                                  ? "Try again"
                                                  : "Not added yet"}
                                    </span>
                                </button>
                            </li>
                        );
                    })}
                </ul>

                {requirements.some((r) => !ours.includes(r)) && (
                    <>
                        <p className="euk-part-head euk-part-head--self">
                            Part B — you complete these
                        </p>
                        <ul>
                            {requirements
                                .filter((r) => !ours.includes(r))
                                .map((r) => (
                                    <li
                                        key={r.requirement_id}
                                        className="euk-part-row euk-part-row--self"
                                        data-active={
                                            selectedId === r.requirement_id
                                        }
                                    >
                                        <span
                                            className="euk-part-dash"
                                            aria-hidden="true"
                                        />
                                        <button
                                            type="button"
                                            onClick={() =>
                                                setSelectedId(r.requirement_id)
                                            }
                                            aria-current={
                                                selectedId === r.requirement_id
                                                    ? "step"
                                                    : undefined
                                            }
                                        >
                                            <span className="euk-part-name">
                                                {r.requirement_name}
                                            </span>
                                            <span className="euk-part-state">
                                                {r.platform_support ===
                                                "not_yet_supported"
                                                    ? "We cannot prepare this yet"
                                                    : "You complete this"}
                                            </span>
                                        </button>
                                    </li>
                                ))}
                        </ul>
                    </>
                )}
            </fieldset>

            <fieldset
                className="euk-panel-wrap"
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
                                    This file is not in your kit. Tick it above
                                    to prepare and buy it.
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

            <div className="euk-sheet-links">
                <Link href={`/exam/${exam.exam_id}/rules`}>Rules &amp; sources</Link>
                <ReportIssue
                    examName={exam.exam_name}
                    requirementName={selected?.requirement_name}
                    ruleId={exam.rule_id}
                />
                <Link href="/exams">Change exam</Link>
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
