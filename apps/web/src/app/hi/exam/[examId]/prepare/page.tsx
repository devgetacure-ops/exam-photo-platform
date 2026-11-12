import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { loadExam, loadExams } from "../../../../../lib/catalogue.server";
import { PrepareFlow } from "../../../../../components/m/prepare-flow";
import { LocaleProvider } from "../../../../../components/locale-context";

// DEC-136: re-rendered every 5 minutes, and at once after a console edit,
// so the owner's changes to records and dates reach this page.
export const revalidate = 300;

/**
 * The phone flow, in Hindi (DEC-129). Not indexed, like the English flow:
 * the Hindi examination page is the one a search should land on.
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
    return {
        title: `${exam.exam_name} की फ़ाइलें तैयार करें`,
        description: `${exam.exam_name} के लिए फ़ोटो, हस्ताक्षर और दस्तावेज़ एक-एक करके जोड़ें और हर एक मुफ़्त डाउनलोड करें।`,
        robots: { index: false, follow: true },
        alternates: { canonical: `/hi/exam/${exam.exam_id}` },
    };
}

export default async function HindiPreparePage({
    params,
}: {
    params: Promise<{ examId: string }>;
}) {
    const { examId } = await params;
    const exam = await loadExam(examId);
    if (!exam) notFound();
    return (
        <main id="main-content" lang="hi">
            <LocaleProvider locale="hi">
                <PrepareFlow key={exam.exam_id} exam={exam} facts={[]} />
            </LocaleProvider>
        </main>
    );
}
