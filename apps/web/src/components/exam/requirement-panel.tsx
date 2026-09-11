"use client";
import Link from "next/link";
import type { ExamDetail, RequirementSummary } from "../../lib/types";
import { requirementSpecRows, photographSpecRows } from "../../lib/spec-format";
import { appearanceGuidance } from "../../lib/appearance-rules";
import { DocumentWorkspace } from "./document-workspace";
import { RequirementUpload } from "./requirement-upload";
import { VisualGuide } from "./visual-guide";
import { ReportIssue } from "./report-issue";

export function RequirementPanel({
    requirement,
    index,
    exam,
    onWorking,
}: {
    requirement: RequirementSummary;
    index: number;
    exam: ExamDetail;
    onWorking?: (value: boolean) => void;
}) {
    const supported = ["supported", "partially_supported"].includes(
        requirement.platform_support,
    );
    // partially_supported means a file comes out that still needs something we
    // cannot do — printing a name onto a photograph, for TNPSC and Kerala PSC.
    // The panel said so further down while the heading above it promised "a
    // simpler application" and "we'll handle the formatting", which is this
    // state reading as success. It gets its own heading.
    const partial = requirement.platform_support === "partially_supported";
    const photo = requirement.requirement_type === "photograph";
    const rows = photo
        ? photographSpecRows(exam)
        : requirementSpecRows(requirement, index, exam.provenance);
    const guidance = photo ? appearanceGuidance(exam.image_requirements) : [];
    return (
        <section
            className="requirement-panel"
            aria-label={requirement.requirement_name}
        >
            <header className="requirement-heading">
                <h2>
                    {!supported
                        ? "A step to complete"
                        : partial
                          ? "Most of it, done."
                          : photo
                            ? "A good photo."
                            : "One more file."}
                    <br />
                    {!supported
                        ? "with your exam authority."
                        : partial
                          ? "One step stays yours."
                          : photo
                            ? "A simpler application."
                            : "Taken care of."}
                </h2>
                <p>
                    {!supported
                        ? "This requirement needs your attention outside this workspace."
                        : partial
                          ? "We’ll size and format it. There is one thing this exam asks for that we cannot add — it is named below, and you will need to do it before you upload."
                          : "Start with a clear upload. We’ll handle the sizing and formatting."}
                </p>
            </header>
            {requirement.requirement_status === "conditional" && (
                <p className="inline-notice">
                    Only required if: {requirement.applicability}
                </p>
            )}
            {!supported ? (
                <div className="self-guidance">
                    <h3>
                        {requirement.platform_support === "not_yet_supported"
                            ? "We can’t prepare this file yet"
                            : "You complete this yourself"}
                    </h3>
                    <p>
                        {(requirement.content_instructions &&
                        !/^(not_found|unknown|none)$/i.test(
                            requirement.content_instructions,
                        )
                            ? requirement.content_instructions
                            : null) ||
                            (requirement.notes &&
                            !/^(not_found|unknown|none)$/i.test(
                                requirement.notes,
                            )
                                ? requirement.notes
                                : null) ||
                            "Complete this requirement through the exam’s official instructions."}
                    </p>
                    <Link
                        className="quiet-link"
                        href={`/exam/${exam.exam_id}/rules`}
                    >
                        Read the exam’s sources
                    </Link>
                </div>
            ) : (
                <div className="requirement-content">
                    <VisualGuide
                        key={requirement.requirement_id}
                        type={requirement.requirement_type}
                    />
                    <div className="requirement-actions">
                        <h3>{requirement.requirement_name} requirements</h3>
                        {guidance.length > 0 && (
                            <ul
                                className="essential-checks"
                                aria-label="Key appearance rules"
                            >
                                {guidance.slice(0, 4).map((item) => (
                                    <li key={item.id}>
                                        <span>{item.detail}</span>
                                    </li>
                                ))}
                            </ul>
                        )}
                        <dl className="spec-list">
                            {rows.map((row) => (
                                <div key={row.term}>
                                    <dt>{row.term}</dt>
                                    <dd>
                                        {row.value}
                                        {row.estimated && (
                                            <abbr title="Platform estimate: this value has not been established by an official source.">
                                                {" "}
                                                est.
                                            </abbr>
                                        )}
                                    </dd>
                                </div>
                            ))}
                        </dl>
                        {requirement.platform_support ===
                            "partially_supported" && (
                            <div className="inline-notice">
                                <strong>
                                    We can prepare part of this requirement.
                                </strong>
                                <p>
                                    {guidance.find((g) => g.id === "imprint")
                                        ?.detail ||
                                        requirement.notes ||
                                        "Check the exam’s instructions before submitting."}
                                </p>
                            </div>
                        )}
                        {["certificate_scan", "identity_document"].includes(
                            requirement.requirement_type,
                        ) ? (
                            <DocumentWorkspace
                                onWorking={onWorking}
                                examId={exam.exam_id}
                                examName={exam.exam_name}
                                requirementId={requirement.requirement_id}
                                requirementName={requirement.requirement_name}
                                partiallySupported={
                                    requirement.platform_support ===
                                    "partially_supported"
                                }
                            />
                        ) : (
                            <RequirementUpload
                                onWorking={onWorking}
                                examId={exam.exam_id}
                                examName={exam.exam_name}
                                requirementId={requirement.requirement_id}
                                requirementName={requirement.requirement_name}
                                requirementType={requirement.requirement_type}
                                partiallySupported={
                                    requirement.platform_support ===
                                    "partially_supported"
                                }
                            />
                        )}
                        <div className="requirement-reference">
                            {guidance.length > 0 && (
                                <details>
                                    <summary>
                                        Appearance rules for this exam
                                    </summary>
                                    {guidance.map((g) => (
                                        <div
                                            className="guidance-rule"
                                            key={g.id}
                                        >
                                            <strong>
                                                {g.title} · {g.verdict}
                                            </strong>
                                            <p>{g.sourceWording || g.detail}</p>
                                        </div>
                                    ))}
                                </details>
                            )}
                            {requirement.content_instructions && (
                                <details>
                                    <summary>
                                        How to prepare this upload
                                    </summary>
                                    <p>{requirement.content_instructions}</p>
                                </details>
                            )}
                            <details>
                                <summary>What may be rejected?</summary>
                                <h4>By your exam authority</h4>
                                {requirement.rejection_conditions.length ? (
                                    <ul>
                                        {requirement.rejection_conditions.map(
                                            (c) => (
                                                <li key={c}>{c}</li>
                                            ),
                                        )}
                                    </ul>
                                ) : (
                                    <p>
                                        No specific rejection conditions are
                                        recorded for this item. Check the linked
                                        source.
                                    </p>
                                )}
                                <h4>When we cannot prepare a file</h4>
                                <p>
                                    {photo
                                        ? "We need a readable image and a detectable, unambiguous face. Other findings are shown for you to review."
                                        : "We need a readable file. We’ll tell you if we cannot prepare it or meet a specification."}
                                </p>
                            </details>
                        </div>
                        <div className="source-actions">
                            <Link href={`/exam/${exam.exam_id}/rules`}>
                                {exam.source_evidence.some(
                                    (s) => s.official_source,
                                )
                                    ? "View exam sources"
                                    : "View available sources"}
                            </Link>
                            <ReportIssue
                                examName={exam.exam_name}
                                requirementName={requirement.requirement_name}
                                ruleId={exam.rule_id}
                            />
                        </div>
                    </div>
                </div>
            )}
        </section>
    );
}
