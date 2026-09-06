"use client";
import { useState } from "react";
import Link from "next/link";
import type { ExamDetail } from "../../lib/types";
import { RequirementPanel } from "./requirement-panel";
import { useKit } from "./use-kit";
import { ReportIssue } from "./report-issue";

export function KitWorkspace({ exam }: { exam: ExamDetail }) {
    const requirements = exam.requirements ?? [];
    const { entries } = useKit(exam.exam_id);
    const [selectedId, setSelectedId] = useState(
        requirements[0]?.requirement_id ?? "",
    );
    const [purchase, setPurchase] = useState("kit");
    const [notice, setNotice] = useState("");
    const ours = requirements.filter((r) =>
        ["supported", "partially_supported"].includes(r.platform_support),
    );
    const ready = ours.filter((r) =>
        ["prepared", "prepared_with_findings"].includes(
            entries[r.requirement_id]?.outcome,
        ),
    ).length;
    const selected = requirements.find((r) => r.requirement_id === selectedId);
    const selectedIndex = Math.max(0, requirements.findIndex((r) => r.requirement_id === selectedId));
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
            <div className="mobile-kit-picker">
                <p>
                    {selected?.requirement_name} · {selectedIndex + 1} of {requirements.length}
                </p>
                <span>
                    {ready} of {ours.length} prepared
                </span>
                <div className="mobile-progress" aria-label={`Requirement ${selectedIndex + 1} of ${requirements.length}`}>
                    {requirements.map((requirement, index) => <button type="button" key={requirement.requirement_id} data-active={index === selectedIndex} onClick={() => setSelectedId(requirement.requirement_id)} aria-label={`Open ${requirement.requirement_name}`} />)}
                </div>
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
                        {requirements.map((r, i) => {
                            const entry = entries[r.requirement_id];
                            const served = [
                                "supported",
                                "partially_supported",
                            ].includes(r.platform_support);
                            const state =
                                entry?.outcome === "prepared"
                                    ? "Prepared"
                                    : entry?.outcome ===
                                        "prepared_with_findings"
                                      ? "Check findings"
                                      : entry
                                        ? "Try again"
                                        : served
                                          ? "Not added yet"
                                          : r.platform_support ===
                                              "not_yet_supported"
                                            ? "Not available yet"
                                            : "You complete this";
                            return (
                                <button
                                    key={r.requirement_id}
                                    className="kit-step"
                                    aria-current={
                                        selectedId === r.requirement_id
                                            ? "step"
                                            : undefined
                                    }
                                    onClick={() =>
                                        setSelectedId(r.requirement_id)
                                    }
                                >
                                    <span className="step-number">{i + 1}</span>
                                    <span>
                                        <strong>{r.requirement_name}</strong>
                                        <small>{state}</small>
                                    </span>
                                </button>
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
                <div className="workspace-panels">
                    {requirements.map((r, i) => (
                        <div
                            key={r.requirement_id}
                            hidden={selectedId !== r.requirement_id}
                        >
                            <RequirementPanel
                                requirement={r}
                                index={i}
                                exam={exam}
                            />
                        </div>
                    ))}
                </div>
            </div>
            <footer className="kit-price-bar">
                <div>
                    <strong>Choose what you need.</strong>
                    <p>Review the result before paying.</p>
                </div>
                <fieldset aria-label="Purchase option">
                    <label>
                        <input
                            type="radio"
                            name="purchase"
                            value="file"
                            checked={purchase === "file"}
                            onChange={() => setPurchase("file")}
                        />
                        <span>
                            One file<strong>₹4</strong>
                        </span>
                    </label>
                    {ours.length > 1 && (
                        <label>
                            <input
                                type="radio"
                                name="purchase"
                                value="kit"
                                checked={purchase === "kit"}
                                onChange={() => setPurchase("kit")}
                            />
                            <span>
                                Whole kit{" "}
                                <small>{ours.length} supported files</small>
                                <strong>₹8</strong>
                            </span>
                        </label>
                    )}
                </fieldset>
                <button
                    className="primary-button"
                    disabled={!ready}
                    onClick={() =>
                        setNotice(
                            "Your files can be prepared, but checkout is not available yet. Nothing has been charged.",
                        )
                    }
                >
                    {ready
                        ? `Review ${purchase === "kit" ? "kit" : "file"}`
                        : "Add a file to begin"}
                </button>
                {notice && (
                    <p role="status" className="purchase-notice">
                        {notice}
                    </p>
                )}
            </footer>
        </div>
    );
}
