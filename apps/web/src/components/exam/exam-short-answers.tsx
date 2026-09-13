import type { ExamAnswer } from "../../lib/exam-answers";

/**
 * The questions a search asks about this examination, answered in a sentence
 * each, before the detail (DEC-087). The same text is the page's FAQ
 * structured data, so what a search engine is told is exactly what a
 * candidate reads.
 */
export function ExamShortAnswers({ answers }: { answers: ExamAnswer[] }) {
    if (answers.length === 0) return null;
    return (
        <section aria-labelledby="rules-short">
            <h2 id="rules-short" className="euk-display euk-rules-h2">
                In short
            </h2>
            <dl className="euk-short">
                {answers.map((item) => (
                    <div key={item.question}>
                        <dt>{item.question}</dt>
                        <dd>{item.answer}</dd>
                    </div>
                ))}
            </dl>
        </section>
    );
}
