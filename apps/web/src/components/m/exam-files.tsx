"use client";

import Link from "next/link";
import { useState } from "react";

import type { ExamDetail, RequirementSummary } from "../../lib/types";
import { factAttribution, factUrl, type ExamFact } from "../exam/exam-facts";
import { isOurs } from "../../lib/kit-pricing";
import { photographSpecRows, requirementSpecRows } from "../../lib/spec-format";
import { specimensFor } from "../../lib/specimens";
import { SpecimenSheet } from "../exam/specimen-sheet";
import { FileTypeDrawing } from "../euk/doodles";
import { Sheet } from "./sheet";

/**
 * The examination page, for a phone.
 *
 * The desktop page opens every file as a full panel — specimens, measurements,
 * an upload box each — which is right at a width where they sit side by side
 * and wrong on a phone, where it becomes several screens of scrolling before a
 * candidate learns what the examination even wants.
 *
 * Here each file is one row: what it is, and its measurements in a line. The
 * detail — every figure, the specimen sheet, what the notice said — opens in a
 * sheet over the page, and is built only when it is asked for, so the page
 * costs nothing to carry. Uploading happens in the flow, not here, so there is
 * exactly one way to add a file.
 */

function summarise(
    requirement: RequirementSummary,
    exam: ExamDetail,
    index: number,
): string {
    const rows =
        requirement.requirement_type === "photograph" && exam.image_requirements
            ? photographSpecRows(exam)
            : requirementSpecRows(requirement, index, exam.provenance);
    const wanted = rows.filter((row) =>
        ["Dimensions", "File size", "Format"].includes(row.term),
    );
    const shown = (wanted.length > 0 ? wanted : rows).slice(0, 3);
    return shown.map((row) => row.value).join(" · ");
}

export function ExamFiles({
    exam,
    facts = [],
}: {
    exam: ExamDetail;
    facts?: ExamFact[];
}) {
    const requirements = exam.requirements ?? [];
    const ours = requirements.filter(isOurs);
    const yours = requirements.filter((r) => !isOurs(r));
    const [open, setOpen] = useState<string | null>(null);

    const active = open && open !== "facts" ? ours.find((r) => r.requirement_id === open) : null;

    return (
        <section className="euk-m-only euk-mexam" aria-labelledby="mexam-title">
            <h2 id="mexam-title" className="euk-display euk-mexam-title">
                {ours.length} file{ours.length === 1 ? "" : "s"}, and what each
                one has to be
            </h2>

            <ul className="euk-mexam-list">
                {ours.map((r, index) => (
                    <li key={r.requirement_id}>
                        <button
                            type="button"
                            className="euk-mexam-row"
                            onClick={() => setOpen(r.requirement_id)}
                        >
                            <FileTypeDrawing
                                type={r.requirement_type}
                                className="euk-mexam-icon"
                            />
                            <span className="euk-mexam-body">
                                <strong>{r.requirement_name}</strong>
                                <span>{summarise(r, exam, index) || "Rules and specimens"}</span>
                                {r.platform_support === "partially_supported" && (
                                    <span className="euk-mexam-part">
                                        We prepare part of this one
                                    </span>
                                )}
                            </span>
                            <span className="euk-mexam-go" aria-hidden="true">
                                <svg width="9" height="15" viewBox="0 0 9 15" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M1.5 1 L7.5 7.5 L1.5 14" />
                                </svg>
                            </span>
                        </button>
                    </li>
                ))}
            </ul>

            {facts.length > 0 && (
                <button
                    type="button"
                    className="euk-mexam-fact"
                    onClick={() => setOpen("facts")}
                >
                    <span className="euk-label">Worth knowing</span>
                    <span>{facts[0].text}</span>
                    <span className="euk-mexam-fact-more">
                        {facts.length} thing{facts.length === 1 ? "" : "s"} this
                        examination says →
                    </span>
                </button>
            )}

            {yours.length > 0 && (
                <div className="euk-mexam-yours">
                    <h3 className="euk-label">You do these yourself</h3>
                    <ul>
                        {yours.map((r) => (
                            <li key={r.requirement_id}>{r.requirement_name}</li>
                        ))}
                    </ul>
                </div>
            )}

            <p className="euk-mexam-sources">
                Every figure here is {exam.conducting_body}&rsquo;s own.{" "}
                <Link href={`/exam/${exam.exam_id}/rules`}>
                    The rules, and where each came from
                </Link>
            </p>

            <Sheet
                open={Boolean(active)}
                title={active?.requirement_name ?? ""}
                onClose={() => setOpen(null)}
            >
                {active && <FileDetail requirement={active} exam={exam} ours={ours} />}
            </Sheet>

            <Sheet
                open={open === "facts"}
                title="Worth knowing"
                onClose={() => setOpen(null)}
            >
                <ul className="euk-mexam-factlist">
                    {facts.map((fact) => (
                        <li key={fact.text}>
                            <p>{fact.text}</p>
                            {/* The URL inside `source`, not `source` itself: it
                                reads "Title (https://…)", and used as an href
                                it sent every one of these links nowhere. */}
                            {factUrl(fact) && (
                                <a href={factUrl(fact)} target="_blank" rel="noreferrer">
                                    {factAttribution(fact)} ↗
                                </a>
                            )}
                        </li>
                    ))}
                </ul>
            </Sheet>
        </section>
    );
}

function FileDetail({
    requirement,
    exam,
    ours,
}: {
    requirement: RequirementSummary;
    exam: ExamDetail;
    ours: RequirementSummary[];
}) {
    const rows =
        requirement.requirement_type === "photograph" && exam.image_requirements
            ? photographSpecRows(exam)
            : requirementSpecRows(requirement, ours.indexOf(requirement), exam.provenance);
    const specimens = specimensFor(requirement, exam);

    return (
        <>
            {rows.length > 0 && (
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
            )}

            {specimens.length > 0 && (
                <div className="euk-mexam-specimens">
                    <SpecimenSheet
                        specimens={specimens}
                        note="Drawn to show the rule. Every one of these is either ruled out by this examination's record or checked on every upload."
                    />
                </div>
            )}

            <p className="euk-m-sheet-note">
                <Link href={`/exam/${exam.exam_id}/prepare`}>
                    Prepare this file now →
                </Link>
            </p>
        </>
    );
}
