import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { loadExam, loadExams } from "../../../lib/catalogue.server";
import { liveCaptureStance } from "../../../lib/appearance-rules";
import { SiteHeader } from "../../../components/site-header";
import { KitWorkspace } from "../../../components/exam/kit-workspace";

/**
 * One examination, as a workspace.
 *
 * The page itself is a thin shell: identity at the top, the file list and the
 * selected file below it. The reference material an earlier version printed
 * inline — every appearance rule, every source citation, the pricing pitch —
 * now lives one level down, on `/exam/[examId]/rules`, because a candidate here
 * has come to produce files rather than to read.
 *
 * Still statically generated per examination: these are the pages the
 * acquisition strategy rests on, so they must be real HTML to a crawler.
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
        requirement.platform_support === "partially_supported")
  );
  const liveCapture = liveCaptureStance(exam.image_requirements, preparesPhotograph);

  return (
    <main className="exam-page"><SiteHeader mobileTitle={`${exam.exam_name} upload kit`}/>

      {/*
        Live capture is the one thing that must be said before the candidate
        starts, because it changes what they have to do rather than how they do
        it — and "the exam takes a photo too" is the opposite of "so skip the
        upload" on the 16 exams that want both.
      */}
      {liveCapture === "additional" && (
        <details className="live-capture-note">
          <summary>Centre photograph also required</summary>
          <p>This exam also photographs you at the centre. That is in addition to the photo you upload here, not instead of it.</p>
        </details>
      )}
      {liveCapture === "instead" && (
        <details className="live-capture-note">
          <summary>The exam takes this photograph</summary>
          <p>This exam photographs you itself, so there is no photo to upload.</p>
        </details>
      )}

      <KitWorkspace exam={exam} />
    </main>
  );
}
