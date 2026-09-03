import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { loadExam, loadExams } from "../../../lib/catalogue.server";
import { liveCaptureStance } from "../../../lib/appearance-rules";
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
    <main className="flex h-dvh flex-col">
      <header className="flex shrink-0 items-center justify-between border-b border-line px-6 py-3">
        <div className="flex items-baseline gap-3">
          <Link href="/" className="font-semibold tracking-tight">
            Upload<span className="text-accent">Ready</span>
          </Link>
          <span className="text-line-strong">/</span>
          <span className="text-sm font-medium">{exam.exam_name}</span>
          <span className="text-xs text-muted">{exam.conducting_body}</span>
        </div>
        <div className="flex items-center gap-4">
          <Link
            href={`/exam/${exam.exam_id}/rules`}
            className="text-sm text-ink-soft hover:text-ink"
          >
            Rules &amp; sources
          </Link>
          <Link href="/" className="text-sm text-ink-soft hover:text-ink">
            Change exam
          </Link>
        </div>
      </header>

      {/*
        Live capture is the one thing that must be said before the candidate
        starts, because it changes what they have to do rather than how they do
        it — and "the exam takes a photo too" is the opposite of "so skip the
        upload" on the 16 exams that want both.
      */}
      {liveCapture === "additional" && (
        <p className="shrink-0 border-b border-self-line bg-self-soft px-6 py-2 text-sm text-ink-soft">
          <span className="font-medium text-self">Note:</span> this exam also
          photographs you at the centre — that is{" "}
          <span className="text-ink">in addition to</span> the photo you upload
          here, not instead of it.
        </p>
      )}
      {liveCapture === "instead" && (
        <p className="shrink-0 border-b border-self-line bg-self-soft px-6 py-2 text-sm text-ink-soft">
          <span className="font-medium text-self">Note:</span> this exam
          photographs you itself, so there is no photo to upload.
        </p>
      )}

      <KitWorkspace exam={exam} />
    </main>
  );
}
