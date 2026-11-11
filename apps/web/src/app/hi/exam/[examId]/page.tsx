import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { loadExam, loadExams } from "../../../../lib/catalogue.server";
import { liveCaptureStance } from "../../../../lib/appearance-rules";
import { SiteHeader } from "../../../../components/site-header";
import { SiteFooter } from "../../../../components/site-footer";
import { ExamHero } from "../../../../components/exam/exam-hero";
import { KitWorkspace } from "../../../../components/exam/kit-workspace";
import { PrepareCta } from "../../../../components/m/prepare-cta";
import { ExamFiles } from "../../../../components/m/exam-files";
import { JsonLd } from "../../../../components/json-ld";
import { LocaleProvider } from "../../../../components/locale-context";
import { AdSlot } from "../../../../components/ad-slot";
import { ExamRelated } from "../../../../components/exam/exam-related";
import { examQuickAnswer, examSpecs } from "../../../../lib/exam-answers";
import { COPY, languageAlternates } from "../../../../lib/i18n";
import { breadcrumbs, pageMetadata } from "../../../../lib/site";

/**
 * One examination, in Hindi (DEC-129). The same page as `/exam/[examId]`:
 * what the authority asks for, the answer and the related examinations are
 * in Hindi; the examination's name and every figure stay as published. The
 * preparation tool speaks Hindi through `LocaleProvider`; wording quoted
 * from a notice stays as the authority wrote it.
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
    if (!exam) return { title: "परीक्षा नहीं मिली" };
    const files = examSpecs(exam)
        .map((spec) => COPY.hi.searchLabel[spec.type])
        .filter(Boolean)
        .slice(0, 2);
    const title = files.length
        ? `${exam.exam_name} ${files.join(" और ")} का साइज़ और अपलोड नियम`
        : `${exam.exam_name} अपलोड नियम`;
    const answer = examQuickAnswer(exam, "hi");
    return pageMetadata({
        title,
        description: `${answer ?? `${exam.exam_name} के लिए अपलोड की जाने वाली हर फ़ाइल और उसके नियम।`} मुफ़्त, बिना अकाउंट, बिना वॉटरमार्क।`,
        path: `/hi/exam/${exam.exam_id}`,
        image: `/exam/${exam.exam_id}/opengraph-image`,
        languages: languageAlternates(`/exam/${exam.exam_id}`),
        locale: "hi_IN",
    });
}

export default async function HindiExamPage({
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
    const liveCapture = liveCaptureStance(exam.image_requirements, preparesPhotograph);

    return (
        <main className="euk exam-page" id="main-content">
            <JsonLd
                data={breadcrumbs([
                    { name: "होम", path: "/" },
                    { name: "सभी परीक्षाएँ", path: "/exams" },
                    { name: exam.exam_name, path: `/hi/exam/${exam.exam_id}` },
                ])}
            />
            <SiteHeader mobileTitle={`${exam.exam_name} अपलोड किट`} examName={exam.exam_name} />
            <div lang="hi">
                <ExamHero exam={exam} facts={[]} liveCapture={liveCapture} locale="hi" />
                <LocaleProvider locale="hi">
                    <ExamFiles exam={exam} facts={[]} />
                    <KitWorkspace exam={exam} facts={[]} />
                </LocaleProvider>
            </div>
            <div className="euk">
                <AdSlot name="exam-after-kit" />
            </div>
            <div lang="hi">
                <ExamRelated exam={exam} locale="hi" />
            </div>
            <SiteFooter />
            <div lang="hi">
                <LocaleProvider locale="hi">
                    <PrepareCta exam={exam} />
                </LocaleProvider>
            </div>
        </main>
    );
}
