import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { loadExam, loadExams } from "../../../../lib/catalogue.server";
import { appearanceGuidance } from "../../../../lib/appearance-rules";
import { estimateCount } from "../../../../lib/spec-format";
import { GuidanceList } from "../../../../components/exam/guidance-list";
import { SourceNote } from "../../../../components/exam/source-note";

/**
 * The reference half of an examination: its photograph rules, where they came
 * from, and what applies to the application as a whole.
 *
 * Split off the workspace deliberately. This is material a candidate reads
 * once, or comes back to after a portal rejects something — not while they are
 * uploading. Keeping it inline is what made the exam page six screens long.
 *
 * It also has its own SEO job: "CAT photo rules", "IBPS signature size" are
 * reference queries, and this is the page that answers them.
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
    title: `${exam.exam_name} photo rules — what they accept and reject`,
    description: `${exam.conducting_body}'s published photograph rules for ${exam.exam_name}: spectacles, headwear, expression, recency, and the causes of rejection they list.`,
    alternates: { canonical: `/exam/${exam.exam_id}/rules` },
  };
}

export default async function RulesPage({
  params,
}: {
  params: Promise<{ examId: string }>;
}) {
  const { examId } = await params;
  const exam = await loadExam(examId);
  if (!exam) notFound();

  const guidance = appearanceGuidance(exam.image_requirements);
  const estimates = estimateCount(exam);

  return (
    <main className="min-h-dvh">
      <header className="flex items-center justify-between border-b border-line px-6 py-3">
        <div className="flex items-baseline gap-3">
          <Link href="/" className="font-semibold tracking-tight">
            Upload<span className="text-accent">Ready</span>
          </Link>
          <span className="text-line-strong">/</span>
          <Link
            href={`/exam/${exam.exam_id}`}
            className="text-sm font-medium hover:text-accent"
          >
            {exam.exam_name}
          </Link>
          <span className="text-xs text-muted">Rules</span>
        </div>
        <Link
          href={`/exam/${exam.exam_id}`}
          className="text-sm text-accent hover:underline"
        >
          ← Back to your files
        </Link>
      </header>

      <div className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="text-2xl font-semibold">
          What {exam.conducting_body} asks for
        </h1>
        <p className="mt-2 text-ink-soft">
          Their published rules for {exam.exam_name}. Where they used particular
          wording, it is quoted.
        </p>

        {guidance.length > 0 ? (
          <GuidanceList items={guidance} />
        ) : (
          <p className="mt-6 rounded-lg border border-line bg-sunk p-4 text-sm text-ink-soft">
            This exam has not published rules about spectacles, headwear or
            expression — or we have not found them. We have not invented any.
          </p>
        )}

        {exam.application_rejection_conditions.length > 0 && (
          <section className="mt-10 rounded-xl border border-caveat-soft bg-caveat-soft/40 p-5">
            <h2 className="font-semibold text-caveat">About the application itself</h2>
            <ul className="mt-3 space-y-2">
              {exam.application_rejection_conditions.map((condition) => (
                <li
                  key={condition}
                  className="flex gap-2 text-sm leading-relaxed text-ink-soft"
                >
                  <span
                    aria-hidden="true"
                    className="mt-2 size-1 shrink-0 rounded-full bg-caveat"
                  />
                  <span>{condition}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        <SourceNote exam={exam} estimates={estimates} />
      </div>
    </main>
  );
}
