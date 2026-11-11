import Link from "next/link";
import { examQuickAnswer, examSource, examSpecs } from "../../lib/exam-answers";
import { COPY, localValue, type Locale } from "../../lib/i18n";
import type { ExamDetail } from "../../lib/types";

/**
 * The answer, first (DEC-127). One sentence a search or answer engine can
 * quote, the figures for each file we prepare, and where they came from,
 * before the candidate is asked to do anything. Every value is the record's;
 * our own estimates keep their "est." here as everywhere else.
 */
export function ExamAnswer({ exam, locale = "en" }: { exam: ExamDetail; locale?: Locale }) {
    const copy = COPY[locale];
    const sentence = examQuickAnswer(exam, locale);
    const specs = examSpecs(exam).slice(0, 4);
    if (!sentence || specs.length === 0) return null;
    const source = examSource(exam);

    return (
        <section className="euk-answer-card" aria-labelledby="exam-answer-title">
            <p id="exam-answer-title" className="euk-answer-kicker">
                {copy.answer}
            </p>
            <p className="euk-answer-sentence">{sentence}</p>
            <dl className="euk-answer-specs">
                {specs.map(({ type, rows }) => (
                    <div key={type}>
                        <dt>{copy.fileNames[type]?.[0] ?? type}</dt>
                        <dd>
                            {rows.map((row, i) => (
                                <span key={row.term}>
                                    {i > 0 && " · "}
                                    {localValue(locale, row.value)}
                                    {row.estimated && <abbr title={copy.estimatedTitle}> {copy.estimated}</abbr>}
                                </span>
                            ))}
                        </dd>
                    </div>
                ))}
            </dl>
            <p className="euk-answer-source">
                {source ? (
                    <>
                        {copy.from} {source.url ? (
                            <a href={source.url} target="_blank" rel="noreferrer">
                                {source.title} ↗
                            </a>
                        ) : (
                            source.title
                        )}
                        .{" "}
                    </>
                ) : null}
                <Link href={`/exam/${exam.exam_id}/rules`}>{copy.everyRule}</Link>
            </p>
        </section>
    );
}
