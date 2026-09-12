import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { loadExam, loadExams } from "../../../../lib/catalogue.server";
import { loadExamFacts } from "../../../../lib/exam-facts.server";
import { PrepareFlow } from "../../../../components/m/prepare-flow";

/**
 * The flow: choose the files, add them, check, pay.
 *
 * Its own route rather than a mode of the examination page, because a flow
 * needs somewhere to come back to. `/exam/[examId]` stays the page a crawler
 * and a desktop visitor get — every specification, every rule, every source —
 * and this is the thing a candidate on a phone actually works through. It is
 * deliberately not indexed: the same examination should not appear twice in a
 * result page, and this screen says nothing a crawler wants.
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

    return {
        title: `Prepare your ${exam.exam_name} files`,
        description: `Add your photograph, signature and documents for ${exam.exam_name}, one at a time, and see each one before you pay.`,
        robots: { index: false, follow: true },
        alternates: { canonical: `/exam/${exam.exam_id}` },
    };
}

export default async function PreparePage({
    params,
}: {
    params: Promise<{ examId: string }>;
}) {
    const { examId } = await params;
    const exam = await loadExam(examId);
    if (!exam) notFound();
    const facts = await loadExamFacts(examId);

    return (
        <main id="main-content">
            <PrepareFlow exam={exam} facts={facts} />
        </main>
    );
}
