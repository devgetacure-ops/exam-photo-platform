"use client";

import Link from "next/link";
import { useState } from "react";

import type { ExamDetail, RequirementSummary } from "../../lib/types";
import { factAttribution, factUrl, type ExamFact } from "../exam/exam-facts";
import { isOurs } from "../../lib/requirement-support";
import { photographSpecRows, requirementSpecRows } from "../../lib/spec-format";
import { specimensFor } from "../../lib/specimens";
import { SpecimenSheet } from "../exam/specimen-sheet";
import { FileTypeDrawing } from "../euk/doodles";
import { useLocale, useTr } from "../locale-context";
import { localePath, localValue, type Locale } from "../../lib/i18n";
import { toolText } from "../../lib/i18n-tool";
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
    locale: Locale,
): string {
    const rows =
        requirement.requirement_type === "photograph" && exam.image_requirements
            ? photographSpecRows(exam)
            : requirementSpecRows(requirement, index, exam.provenance);
    const wanted = rows.filter((row) =>
        ["Dimensions", "File size", "Format"].includes(row.term),
    );
    const shown = (wanted.length > 0 ? wanted : rows).slice(0, 3);
    return shown.map((row) => localValue(locale, row.value)).join(" · ");
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
    const tr = useTr();
    const locale = useLocale();

    const active = open && open !== "facts" ? ours.find((r) => r.requirement_id === open) : null;

    return (
        <section className="euk-m-only euk-mexam" aria-labelledby="mexam-title">
            <h2 id="mexam-title" className="euk-display euk-mexam-title">
                {tr(
                    `${ours.length} file${ours.length === 1 ? "" : "s"}, and what each one has to be`,
                    `${ours.length} फ़ाइलें, और हर एक कैसी होनी चाहिए`,
                )}
            </h2>

            <ul className="euk-mexam-list">
                {ours.map((r, index) => (
                    <li key={r.requirement_id}>
                        {/* A link, not a button: on a slow phone a tap can land
                            before the page's script has, and a button does
                            nothing then. The link still goes to this file's
                            rules; once the script is in, it opens the sheet. */}
                        <Link
                            href={`/exam/${exam.exam_id}/rules#rules-files`}
                            className="euk-mexam-row"
                            onClick={(event) => {
                                if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
                                event.preventDefault();
                                setOpen(r.requirement_id);
                            }}
                        >
                            <FileTypeDrawing
                                type={r.requirement_type}
                                className="euk-mexam-icon"
                            />
                            <span className="euk-mexam-body">
                                <strong>{r.requirement_name}</strong>
                                <span>{summarise(r, exam, index, locale) || tr("Rules and specimens", "नियम और नमूने")}</span>
                                {r.platform_support === "partially_supported" && (
                                    <span className="euk-mexam-part">
                                        {tr("We prepare part of this one", "इसका कुछ हिस्सा हम तैयार करते हैं")}
                                    </span>
                                )}
                            </span>
                            <span className="euk-mexam-go" aria-hidden="true">
                                <svg width="9" height="15" viewBox="0 0 9 15" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M1.5 1 L7.5 7.5 L1.5 14" />
                                </svg>
                            </span>
                        </Link>
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
                    <h3 className="euk-label">{tr("You do these yourself", "ये आप खुद करेंगे")}</h3>
                    <ul>
                        {yours.map((r) => (
                            <li key={r.requirement_id}>{r.requirement_name}</li>
                        ))}
                    </ul>
                </div>
            )}

            <p className="euk-mexam-sources">
                {tr(
                    `Every figure here is ${exam.conducting_body}’s own.`,
                    `यहाँ हर आँकड़ा ${exam.conducting_body} का अपना है।`,
                )}{" "}
                <Link href={`/exam/${exam.exam_id}/rules`}>
                    {tr("The rules, and where each came from", "नियम, और हर एक कहाँ से आया (अंग्रेज़ी में)")}
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
    const tr = useTr();
    const locale = useLocale();

    return (
        <>
            {rows.length > 0 && (
                <dl className="euk-m-specs">
                    {rows.map((row) => (
                        <div key={row.term}>
                            <dt>{toolText(locale, row.term)}</dt>
                            <dd>
                                {localValue(locale, row.value)}
                                {row.estimated ? (
                                    <span className="euk-m-est"> {tr("est.", "अनुमानित")}</span>
                                ) : null}
                            </dd>
                        </div>
                    ))}
                </dl>
            )}

            {specimens.length > 0 && (
                <div className="euk-mexam-specimens">
                    <SpecimenSheet
                        locale={locale}
                        specimens={specimens}
                        note={tr(
                            "Drawn to show the rule. Every one of these is either ruled out by this examination's record or checked on every upload.",
                            "नियम दिखाने के लिए बनाया गया। इनमें से हर एक या तो इस परीक्षा के नियमों में मना है, या हर अपलोड पर जाँचा जाता है।",
                        )}
                    />
                </div>
            )}

            <p className="euk-m-sheet-note">
                <Link href={localePath(locale, `/exam/${exam.exam_id}/prepare`)}>
                    {tr("Prepare this file now →", "यह फ़ाइल अभी तैयार करें →")}
                </Link>
            </p>
        </>
    );
}
