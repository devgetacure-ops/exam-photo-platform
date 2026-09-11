import type { ExamDetail } from "../../lib/types";
import { ReportIssue } from "./report-issue";

/**
 * Where this exam's rules came from, stated honestly.
 *
 * The temptation is a reassuring "Official source" badge on every page. Some
 * examinations rest on secondary references — one is a forum reproduction of
 * the notification — and stamping those as official would be a false claim
 * about evidence, on a page whose entire value is that its numbers can be
 * trusted. So the badge reflects what the record actually says, and where the
 * source is weaker the page says that too.
 *
 * The report link is the other half of the same idea. Some figures are our own
 * estimates, and rules change between cycles; the only mechanism that turns an
 * estimate into a researched value is a candidate telling us it was wrong.
 */

const VERIFICATION: Record<string, { label: string; detail: string }> = {
    verified: {
        label: "Verified",
        detail:
            "We found this exam's own published instructions and encoded them directly.",
    },
    verified_with_ambiguity: {
        label: "Verified, with gaps",
        detail:
            "We found this exam's published instructions, but they leave some values unstated. Those are marked as our estimates.",
    },
    provisional: {
        label: "Provisional",
        detail:
            "We have not been able to confirm every value against an official document for this cycle. Check your own notification before submitting.",
    },
};

export function SourceNote({
    exam,
    estimates,
}: {
    exam: ExamDetail;
    estimates: number;
}) {
    const verification =
        VERIFICATION[exam.verification_status ?? ""] ?? VERIFICATION.provisional;
    const official = exam.source_evidence.filter((source) => source.official_source);
    const secondary = exam.source_evidence.filter((source) => !source.official_source);

    return (
        <section className="euk-source" aria-labelledby="source-title">
            <h2 id="source-title" className="euk-display euk-rules-h2">
                Where these rules came from
            </h2>

            <div className="euk-source-chips">
                <span
                    className={`euk-source-chip ${official.length > 0 ? "euk-source-chip--official" : "euk-source-chip--secondary"}`}
                >
                    {official.length > 0 ? "Official source" : "Secondary source only"}
                </span>
                <span className="euk-source-chip">{verification.label}</span>
            </div>

            <p className="euk-source-text">{verification.detail}</p>

            {official.length > 0 && (
                <ul className="euk-source-list">
                    {official.map((source, index) => (
                        <li key={index}>
                            {source.source_url ? (
                                <a
                                    className="euk-link"
                                    href={source.source_url}
                                    target="_blank"
                                    rel="noopener noreferrer nofollow"
                                >
                                    {source.document_title ?? source.source_url}
                                </a>
                            ) : (
                                <span>{source.document_title}</span>
                            )}
                        </li>
                    ))}
                </ul>
            )}

            {secondary.length > 0 && (
                <div className="euk-source-secondary">
                    <p>
                        {official.length > 0
                            ? "We also used a secondary reference for some values:"
                            : "We could not find this exam's own published file rules. What we have comes from a secondary reference:"}{" "}
                        {secondary.map((source, index) => (
                            <span key={index}>
                                {index > 0 && ", "}
                                {source.source_url ? (
                                    <a
                                        className="euk-link"
                                        href={source.source_url}
                                        target="_blank"
                                        rel="noopener noreferrer nofollow"
                                    >
                                        {source.document_title ?? source.source_url}
                                    </a>
                                ) : (
                                    (source.document_title ?? "unnamed source")
                                )}
                            </span>
                        ))}
                        .
                    </p>
                </div>
            )}

            {estimates > 0 && (
                <p className="euk-source-text">
                    <span className="euk-source-est">est.</span> marks a figure
                    this exam has not published, where we chose a sensible value.
                    There {estimates === 1 ? "is 1" : `are ${estimates}`} on this
                    page. Your file is prepared to it, and the report we give you
                    names every one.
                </p>
            )}

            <p className="euk-source-report">
                <ReportIssue examName={exam.exam_name} ruleId={exam.rule_id} />{" "}
                <span>
                    Tell us and we will re-check it against the notification.
                    Rules change between cycles, and we would rather hear it from
                    you than have you find out at the portal.
                </span>
            </p>
        </section>
    );
}
