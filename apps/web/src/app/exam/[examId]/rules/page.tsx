import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { loadExam, loadExams } from "../../../../lib/catalogue.server";
import { appearanceGuidance } from "../../../../lib/appearance-rules";
import { photographSpecRows, requirementSpecRows } from "../../../../lib/spec-format";
import { RequirementRules } from "../../../../components/exam/requirement-rules";
import { GuidanceList } from "../../../../components/exam/guidance-list";
import { SourceNote } from "../../../../components/exam/source-note";
import { SiteHeader } from "../../../../components/site-header";
import { SiteFooter } from "../../../../components/site-footer";
import { Chevron } from "../../../../components/euk/doodles";
import { ExamShortAnswers } from "../../../../components/exam/exam-short-answers";
import { JsonLd } from "../../../../components/json-ld";
import { examAnswers } from "../../../../lib/exam-answers";
import { breadcrumbs, pageMetadata } from "../../../../lib/site";

/**
 * The reference half of an examination: every file's published rules, the
 * photograph's appearance rules, and where each came from.
 *
 * Split off the workspace deliberately. This is material a candidate reads
 * once, or comes back to after a portal rejects something — not while they are
 * uploading. It also has its own search job: "CAT photo rules" and "IBPS
 * signature size" are reference queries, and this is the page that answers
 * them, so everything here is server-rendered text.
 */

export async function generateStaticParams() {
    const exams = await loadExams();
    return exams.map((exam) => ({ examId: exam.exam_id }));
}

export async function generateMetadata({
    params,
}: {
    params: Promise<{ examId: string }>;
}): Promise<Metadata> {
    const { examId } = await params;
    const exam = await loadExam(examId);
    if (!exam) return { title: "Examination not found" };
    return pageMetadata({
        title: `${exam.exam_name} upload rules: file sizes, formats and rejection reasons`,
        description: `${exam.conducting_body}'s published upload rules for ${exam.exam_name}: every file's size, dimensions and format, how to look in the photograph, and the causes of rejection it lists.`,
        path: `/exam/${exam.exam_id}/rules`,
        image: `/exam/${exam.exam_id}/opengraph-image`,
    });
}

export default async function RulesPage({
    params,
}: {
    params: Promise<{ examId: string }>;
}) {
    const { examId } = await params;
    const exam = await loadExam(examId);
    if (!exam) notFound();

    const requirements = exam.requirements ?? [];
    const guidance = appearanceGuidance(exam.image_requirements);
    const answers = examAnswers(exam);
    const hasPhotograph = requirements.some(
        (r) => r.requirement_type === "photograph",
    );
    const estimates = requirements
        .flatMap((r, i) =>
            r.requirement_type === "photograph"
                ? photographSpecRows(exam)
                : requirementSpecRows(r, i, exam.provenance),
        )
        .filter((row) => row.estimated).length;

    return (
        <main className="euk euk-rules" id="main-content">
            <JsonLd
                data={breadcrumbs([
                    { name: "Home", path: "/" },
                    { name: "All examinations", path: "/exams" },
                    { name: exam.exam_name, path: `/exam/${exam.exam_id}` },
                    { name: "Upload rules", path: `/exam/${exam.exam_id}/rules` },
                ])}
            />
            {/* The same questions and answers as the "In short" block, word for word. */}
            <JsonLd
                data={{
                    "@context": "https://schema.org",
                    "@type": "FAQPage",
                    mainEntity: answers.map((item) => ({
                        "@type": "Question",
                        name: item.question,
                        acceptedAnswer: { "@type": "Answer", text: item.answer },
                    })),
                }}
            />
            <SiteHeader mobileTitle={`${exam.exam_name} rules`} />

            <section className="euk-rules-top">
                <div className="euk-wrap">
                    <Link href={`/exam/${exam.exam_id}`} className="euk-rules-back">
                        <span aria-hidden="true">←</span> {exam.exam_name}
                    </Link>
                    <h1 className="euk-display euk-rules-title">
                        {exam.exam_name}
                        <br />
                        <span className="euk-mark">The upload rules, as published.</span>
                    </h1>
                    <p className="euk-lede">
                        Set by {exam.conducting_body}. Every file the notice asks
                        for, its size and format, what gets it rejected, and where
                        each rule came from. Where the notice used particular
                        wording, it is quoted.
                    </p>
                    <Link className="primary-button euk-rules-cta" href={`/exam/${exam.exam_id}`}>
                        Prepare these files
                        <Chevron />
                    </Link>
                </div>
            </section>

            <div className="euk-rules-body">
            <div className="euk-wrap euk-rules-stack">
                <ExamShortAnswers answers={answers} />
                <section aria-labelledby="rules-files">
                    <h2 id="rules-files" className="euk-display euk-rules-h2">
                        The files
                    </h2>
                    <RequirementRules exam={exam} />
                </section>

                {hasPhotograph && (
                    <section aria-labelledby="rules-appearance">
                        <h2 id="rules-appearance" className="euk-display euk-rules-h2">
                            How you should look in the photograph
                        </h2>
                        {guidance.length > 0 ? (
                            <GuidanceList items={guidance} />
                        ) : (
                            <p className="euk-rules-empty">
                                This examination hasn&rsquo;t published rules
                                about spectacles, headwear or expression, or we
                                haven&rsquo;t found them. We haven&rsquo;t
                                invented any.
                            </p>
                        )}
                    </section>
                )}

                {exam.application_rejection_conditions.length > 0 && (
                    <section className="euk-app-rejects" aria-labelledby="rules-application">
                        <h2 id="rules-application" className="euk-display">
                            About the application itself
                        </h2>
                        <ul>
                            {exam.application_rejection_conditions.map((condition) => (
                                <li key={condition}>{condition}</li>
                            ))}
                        </ul>
                    </section>
                )}

                <SourceNote exam={exam} estimates={estimates} />
            </div>
            </div>
            <SiteFooter />
        </main>
    );
}
