"use client";
import Link from "next/link";
import type { ExamDetail, RequirementSummary } from "../../lib/types";
import { requirementSpecRows, photographSpecRows } from "../../lib/spec-format";
import { appearanceGuidance, type Verdict } from "../../lib/appearance-rules";
import { specimensFor } from "../../lib/specimens";
import { DocumentWorkspace } from "./document-workspace";
import { RequirementUpload } from "./requirement-upload";
import { SpecimenSheet, Tick, Cross } from "./specimen-sheet";
import { ReportIssue } from "./report-issue";
import { FileTypeDrawing } from "../euk/doodles";

/**
 * One file, curated for itself.
 *
 * Every panel speaks the same language: the file's name and what we do to it,
 * its measurements as the notice publishes them, the upload, and beside it the
 * specimen sheet and the rules. What changes is the file. A photograph panel
 * talks about faces, caps and backgrounds; a signature panel about ink and
 * capitals; a document panel about pages. Nothing on a panel is generic advice:
 * the specimens and verdicts come from this examination's own record.
 */

const MEANINGLESS = /^(not_found|unknown|none)$/i;

function meaningful(value?: string | null): string | null {
    return value && !MEANINGLESS.test(value.trim()) ? value : null;
}

function backgroundPhrase(raw: unknown): string | null {
    const background = raw as { mode?: string; required_colour?: string } | undefined;
    switch (background?.mode) {
        case "exact_colour": {
            const colour = background.required_colour;
            if (!colour) return "the exact colour it asks for";
            if (colour.startsWith("#"))
                return colour.toUpperCase() === "#FFFFFF"
                    ? "plain white"
                    : "the exact colour it asks for";
            return `plain ${colour.toLowerCase()}`;
        }
        case "plain_light":
            return "plain and light";
        case "plain_background":
            return "plain";
        default:
            return null;
    }
}

function introFor(r: RequirementSummary, exam: ExamDetail): string {
    if (r.platform_support === "not_yet_supported")
        return "We can’t prepare this file yet. Here is what the notice asks, so you can do it yourself.";
    if (r.platform_support === "physical_stage")
        return "This happens in person, at a later stage. Here is what the notice asks.";
    if (r.platform_support === "guidance_only")
        return r.submission_method === "official_live_capture"
            ? "The portal takes this photograph itself. There is nothing to upload."
            : "This is a step you take yourself. Here is what the notice asks.";

    const partial =
        r.platform_support === "partially_supported"
            ? " One thing it asks for, we can’t add yet. It is named below."
            : "";
    switch (r.requirement_type) {
        case "photograph": {
            const background = backgroundPhrase(
                (exam.image_requirements as Record<string, unknown>)?.background,
            );
            return `Any clear photo of you will do. We frame it, ${background ? `make the background ${background}, ` : ""}and size it to the rules.${partial}`;
        }
        case "signature":
            return `Sign on plain paper and take a photo of it. We crop to the ink and size it to the rules, without stretching a stroke.${partial}`;
        case "thumb_impression":
            return `Press your thumb on plain paper and take a photo of it. We crop to the impression and size it to the rules.${partial}`;
        case "handwritten_declaration":
            return `Write it out on plain paper and photograph the whole page. We size it to the rules and never crop the page down to the writing.${partial}`;
        default:
            return `Bring the pages as photos or PDFs. Put them in order, leave out what isn’t needed, and we make one file to the rules.${partial}`;
    }
}

const GOOD: Record<string, string> = {
    photograph: "A good photograph, and what to avoid",
    signature: "A good signature, and what to avoid",
    thumb_impression: "A good thumb impression, and what to avoid",
    handwritten_declaration: "A good declaration, and what to avoid",
};

const VERDICT_WORD: Record<Verdict, string> = {
    prohibited: "Not allowed",
    conditional: "Allowed, on a condition",
    required: "Required",
    permitted: "Allowed",
};

function VerdictMark({ verdict }: { verdict: Verdict }) {
    return (
        <span className="euk-verdict-mark" aria-hidden="true">
            {verdict === "prohibited" ? (
                <Cross />
            ) : verdict === "conditional" ? (
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round">
                    <path d="M3 11 C 6 6, 9 6, 10 10 C 11 14, 14 14, 17 9" />
                </svg>
            ) : (
                <Tick />
            )}
        </span>
    );
}

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
    const r = requirement;
    const supported =
        r.platform_support === "supported" ||
        r.platform_support === "partially_supported";
    const partial = r.platform_support === "partially_supported";
    const photo = r.requirement_type === "photograph";
    const documents =
        r.requirement_type === "certificate_scan" ||
        r.requirement_type === "identity_document";
    const rows = photo
        ? photographSpecRows(exam)
        : requirementSpecRows(r, index, exam.provenance);
    const guidance = photo ? appearanceGuidance(exam.image_requirements) : [];
    const specimens = supported ? specimensFor(r, exam) : [];
    const instructions = meaningful(r.content_instructions);
    const official = exam.source_evidence.some((s) => s.official_source);
    const rulesHref = `/exam/${exam.exam_id}/rules`;

    return (
        <section
            className={`euk-file euk-file--${r.requirement_type.replace(/_/g, "-")}`}
            aria-label={r.requirement_name}
        >
            <header className="euk-file-head">
                <FileTypeDrawing type={r.requirement_type} className="euk-file-icon" />
                <div className="min-w-0">
                    <h2 className="euk-display euk-file-title">{r.requirement_name}</h2>
                    <p className="euk-file-intro">{introFor(r, exam)}</p>
                </div>
            </header>

            {r.requirement_status === "conditional" && meaningful(r.applicability) && (
                <p className="euk-file-when">
                    <strong>Only if it applies to you.</strong> {r.applicability}
                </p>
            )}

            {!supported ? (
                <div className="euk-file-self">
                    <p>
                        {instructions ||
                            meaningful(r.notes) ||
                            "Complete this requirement through the examination’s official instructions."}
                    </p>
                    {r.rejection_conditions.length > 0 && (
                        <>
                            <h3 className="euk-file-h3">What the notice says gets rejected</h3>
                            <ul>
                                {r.rejection_conditions.map((condition) => (
                                    <li key={condition}>{condition}</li>
                                ))}
                            </ul>
                        </>
                    )}
                    <Link className="euk-link" href={rulesHref}>
                        Read the examination’s sources
                    </Link>
                </div>
            ) : (
                <div className="euk-file-grid">
                    <div className="euk-file-work">
                        <div className="euk-file-work-inner">
                        {rows.length > 0 && (
                            <dl
                                className="euk-measure"
                                aria-label={`${r.requirement_name} specification`}
                            >
                                {rows.map((row) => (
                                    <div key={row.term} className="euk-measure-cell">
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
                        )}
                        {partial && (
                            <div className="euk-file-partial">
                                <p className="euk-file-partial-title">One step stays yours</p>
                                <p>
                                    {guidance.find((g) => g.id === "imprint")?.detail ||
                                        meaningful(r.notes) ||
                                        "Check the examination’s instructions before submitting."}
                                </p>
                            </div>
                        )}
                        {documents ? (
                            <DocumentWorkspace
                                onWorking={onWorking}
                                examId={exam.exam_id}
                                examName={exam.exam_name}
                                requirementId={r.requirement_id}
                                requirementName={r.requirement_name}
                                partiallySupported={partial}
                            />
                        ) : (
                            <RequirementUpload
                                onWorking={onWorking}
                                examId={exam.exam_id}
                                examName={exam.exam_name}
                                requirementId={r.requirement_id}
                                requirementName={r.requirement_name}
                                requirementType={r.requirement_type}
                                partiallySupported={partial}
                            />
                        )}
                        </div>
                    </div>

                    <div className="euk-file-guide">
                        {specimens.length > 0 && (
                            <>
                                <h3 className="euk-file-h3">
                                    {GOOD[r.requirement_type] ?? "A good document, and what to avoid"}
                                </h3>
                                <SpecimenSheet
                                    specimens={specimens}
                                    note={`Drawn to show each rule. Marked from ${exam.conducting_body}’s published rules and the checks we run on every upload.`}
                                />
                            </>
                        )}

                        {guidance.length > 0 && (
                            <>
                                <h3 className="euk-file-h3">What the notice says about how you look</h3>
                                <ul className="euk-verdicts">
                                    {guidance.map((g) => (
                                        <li key={g.id} className={`euk-verdict euk-verdict--${g.verdict}`}>
                                            <VerdictMark verdict={g.verdict} />
                                            <div className="min-w-0">
                                                <p className="euk-verdict-title">
                                                    {g.title}{" "}
                                                    <span className="euk-verdict-word">
                                                        {VERDICT_WORD[g.verdict]}
                                                    </span>
                                                </p>
                                                <p>{g.detail}</p>
                                                {g.sourceWording && (
                                                    <p className="euk-verdict-quote">
                                                        The notice: “{g.sourceWording}”
                                                    </p>
                                                )}
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            </>
                        )}

                        <div className="euk-file-mores">
                            {instructions && (
                                <details className="euk-file-more">
                                    <summary>How the notice says to prepare it</summary>
                                    <p>{instructions}</p>
                                </details>
                            )}
                            <details className="euk-file-more">
                                <summary>What may be rejected</summary>
                                <h4>By the examination authority</h4>
                                {r.rejection_conditions.length ? (
                                    <ul>
                                        {r.rejection_conditions.map((condition) => (
                                            <li key={condition}>{condition}</li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p>
                                        No specific rejection conditions are recorded
                                        for this file. Check the linked source.
                                    </p>
                                )}
                                <h4>When we can’t prepare a file</h4>
                                <p>
                                    {photo
                                        ? "We need a readable image with one clear, detectable face. Anything else we notice is shown for you to review."
                                        : "We need a readable file. We’ll tell you if we can’t prepare it or can’t meet a specification."}
                                </p>
                            </details>
                        </div>

                        <p className="euk-file-sources">
                            <Link href={rulesHref}>
                                {official
                                    ? "View the examination’s sources"
                                    : "View the sources we found"}
                            </Link>
                            <ReportIssue
                                examName={exam.exam_name}
                                requirementName={r.requirement_name}
                                ruleId={exam.rule_id}
                            />
                        </p>
                    </div>
                </div>
            )}
        </section>
    );
}
