import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { loadExamFacts } from "../../../lib/exam-facts.server";
import { loadExam, loadExams } from "../../../lib/catalogue.server";
import { liveCaptureStance } from "../../../lib/appearance-rules";
import { SiteHeader } from "../../../components/site-header";
import { SiteFooter } from "../../../components/site-footer";
import { ExamHero } from "../../../components/exam/exam-hero";
import { KitWorkspace } from "../../../components/exam/kit-workspace";
import { PrepareCta } from "../../../components/m/prepare-cta";
import { ExamFiles } from "../../../components/m/exam-files";

/**
 * One examination: what it asks for, the kit that answers it, and each file
 * prepared to its own rules.
 *
 * Statically generated per examination: these are the pages the acquisition
 * strategy rests on, so they must be real HTML to a crawler. The reference
 * material (every source citation, application-level rejection conditions)
 * stays on `/exam/[examId]/rules`.
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
        title: `${exam.exam_name} — photo, signature and document upload rules`,
        description: `Every file ${exam.exam_name} asks you to upload, with its exact size, dimensions and format. Prepared automatically to ${exam.conducting_body}'s published specification.`,
        alternates: { canonical: `/exam/${exam.exam_id}` },
    };
}

export default async function ExamPage({
    params,
}: {
    params: Promise<{ examId: string }>;
}) {
    const { examId } = await params;
    const exam = await loadExam(examId);
    if (!exam) notFound();

    const requirements = exam.requirements ?? [];
    const preparesPhotograph = requirements.some(
        (requirement) =>
            requirement.requirement_type === "photograph" &&
            (requirement.platform_support === "supported" ||
                requirement.platform_support === "partially_supported"),
    );
    const liveCapture = liveCaptureStance(
        exam.image_requirements,
        preparesPhotograph,
    );
    const facts = await loadExamFacts(examId);

    return (
        <main className="euk exam-page" id="main-content">
            <SiteHeader
                mobileTitle={`${exam.exam_name} upload kit`}
                examName={exam.exam_name}
            />
            <ExamHero exam={exam} facts={facts} liveCapture={liveCapture} />
            <ExamFiles exam={exam} facts={facts} />
            <KitWorkspace exam={exam} facts={facts} />
            <SiteFooter />
            {/* After the footer, so the bar's spacer is the last thing in the
                document and the footer's end is never under the fixed bar. */}
            <PrepareCta exam={exam} />
        </main>
    );
}
