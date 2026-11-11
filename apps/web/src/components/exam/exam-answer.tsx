import Link from "next/link";
import { examQuickAnswer, examSource, examSpecs } from "../../lib/exam-answers";
import type { ExamDetail } from "../../lib/types";

const TITLE: Record<string, string> = {
    photograph: "Photograph",
    signature: "Signature",
    thumb_impression: "Thumb impression",
    handwritten_declaration: "Declaration",
};

/**
 * The answer, first (DEC-127). One sentence a search or answer engine can
 * quote, the figures for each file we prepare, and where they came from,
 * before the candidate is asked to do anything. Every value is the record's;
 * our own estimates keep their "est." here as everywhere else.
 */
export function ExamAnswer({ exam }: { exam: ExamDetail }) {
    const sentence = examQuickAnswer(exam);
    const specs = examSpecs(exam).slice(0, 4);
    if (!sentence || specs.length === 0) return null;
    const source = examSource(exam);

    return (
        <section className="euk-answer-card" aria-labelledby="exam-answer-title">
            <p id="exam-answer-title" className="euk-answer-kicker">
                The answer
            </p>
            <p className="euk-answer-sentence">{sentence}</p>
            <dl className="euk-answer-specs">
                {specs.map(({ type, rows }) => (
                    <div key={type}>
                        <dt>{TITLE[type] ?? type}</dt>
                        <dd>
                            {rows.map((row, i) => (
                                <span key={row.term}>
                                    {i > 0 && " · "}
                                    {row.value.replace(/#fff(fff)?\b/gi, "white")}
                                    {row.estimated && <abbr title="our estimate"> est.</abbr>}
                                </span>
                            ))}
                        </dd>
                    </div>
                ))}
            </dl>
            <p className="euk-answer-source">
                {source ? (
                    <>
                        From {source.url ? (
                            <a href={source.url} target="_blank" rel="noreferrer">
                                {source.title} ↗
                            </a>
                        ) : (
                            source.title
                        )}
                        .{" "}
                    </>
                ) : null}
                <Link href={`/exam/${exam.exam_id}/rules`}>Every rule, in full</Link>
            </p>
        </section>
    );
}
