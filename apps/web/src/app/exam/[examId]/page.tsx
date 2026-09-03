import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { loadExam, loadExams } from "../../../lib/catalogue.server";
import { appearanceGuidance, liveCaptureStance } from "../../../lib/appearance-rules";
import { estimateCount } from "../../../lib/spec-format";
import { RequirementCard } from "../../../components/exam/requirement-card";
import { SourceNote } from "../../../components/exam/source-note";
import { GuidanceList } from "../../../components/exam/guidance-list";

/**
 * One examination's page — the inventory, the rules, and the price.
 *
 * Statically generated from the catalogue on disk, one page per examination.
 * These are the pages the acquisition strategy rests on: a candidate searching
 * "CAT photo size" should land here, and a page whose content arrives by
 * client-side fetch is an empty document to a crawler.
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

  // The title is written for the query a candidate actually types — "CAT 2025
  // photo size" — rather than for the brand.
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
  const indexed = requirements.map((requirement, index) => ({ requirement, index }));

  const ours = indexed.filter(
    ({ requirement }) =>
      requirement.platform_support === "supported" ||
      requirement.platform_support === "partially_supported"
  );
  const theirs = indexed.filter(
    ({ requirement }) =>
      requirement.platform_support === "guidance_only" ||
      requirement.platform_support === "physical_stage"
  );
  const pending = indexed.filter(
    ({ requirement }) => requirement.platform_support === "not_yet_supported"
  );

  const guidance = appearanceGuidance(exam.image_requirements);
  const estimates = estimateCount(exam);

  // Whether the exam also photographs the candidate itself, and crucially
  // whether that *replaces* the uploaded photograph or sits alongside it.
  const preparesPhotograph = ours.some(
    ({ requirement }) => requirement.requirement_type === "photograph"
  );
  const liveCapture = liveCaptureStance(exam.image_requirements, preparesPhotograph);

  // The kit is only a real bundle when there is more than one file in it.
  // "Do not manufacture a meaningless Complete Kit" — an exam with a single
  // supported upload is sold as that upload, at the single-file price.
  const bundleWorthOffering = ours.length > 1;

  return (
    <main className="flex flex-1 flex-col">
      <header className="border-b border-line">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-5 py-4 sm:px-8">
          <Link href="/" className="font-semibold tracking-tight">
            Upload<span className="text-accent">Ready</span>
          </Link>
          <Link href="/" className="text-sm text-ink-soft hover:text-ink">
            Change exam
          </Link>
        </div>
      </header>

      <div className="mx-auto w-full max-w-4xl px-5 py-10 sm:px-8 sm:py-14">
        {/* --- Identity ------------------------------------------------- */}
        <p className="label">{exam.conducting_body}</p>
        <h1 className="mt-2 text-3xl font-semibold sm:text-4xl">{exam.exam_name}</h1>
        {exam.aliases.length > 0 && (
          <p className="mt-2 text-sm text-muted">
            Also called <span className="spec text-ink-soft">{exam.aliases.join(", ")}</span>
          </p>
        )}

        <p className="mt-5 max-w-prose text-lg leading-relaxed text-ink-soft">
          {ours.length > 0 ? (
            <>
              This application asks for {requirements.length} item
              {requirements.length === 1 ? "" : "s"}.{" "}
              <span className="text-ink">
                We prepare {ours.length} of them
              </span>
              {theirs.length > 0 && (
                <>
                  {" "}
                  — the other {theirs.length} {theirs.length === 1 ? "is" : "are"}{" "}
                  handled by the exam itself, and we show you what to expect.
                </>
              )}
            </>
          ) : (
            <>
              This application is handled entirely through the exam&rsquo;s own
              portal. There is nothing here for us to prepare — but here is what
              it will ask you for.
            </>
          )}
        </p>

        {liveCapture === "additional" && (
          <div className="mt-6 rounded-xl border border-self-line bg-self-soft p-5">
            <p className="font-medium text-self">
              This exam takes a live photo as well
            </p>
            <p className="mt-2 max-w-prose text-sm leading-relaxed text-ink-soft">
              At some point you will also be photographed through the
              exam&rsquo;s portal or at the centre.{" "}
              <span className="text-ink">
                That is in addition to the photograph you upload, not instead of
                it
              </span>{" "}
              — you still need the file below, and we still prepare it.
            </p>
          </div>
        )}

        {liveCapture === "instead" && (
          <div className="mt-6 rounded-xl border border-self-line bg-self-soft p-5">
            <p className="font-medium text-self">This exam takes your photo itself</p>
            <p className="mt-2 max-w-prose text-sm leading-relaxed text-ink-soft">
              You will be photographed through the exam&rsquo;s portal or at the
              centre, so there is no photograph to upload and none for us to
              prepare. Anything below that we do prepare is separate from that
              step.
            </p>
          </div>
        )}

        {/* --- What we prepare ------------------------------------------ */}
        {ours.length > 0 && (
          <section className="mt-12">
            <div className="flex items-baseline gap-3">
              <h2 className="text-xl font-semibold">We prepare these</h2>
              <span className="label">{ours.length}</span>
            </div>
            <div className="mt-5 space-y-4">
              {ours.map(({ requirement, index }) => (
                <RequirementCard
                  key={requirement.requirement_id}
                  requirement={requirement}
                  index={index}
                  exam={exam}
                />
              ))}
            </div>
          </section>
        )}

        {/* --- What the candidate does themselves ----------------------- */}
        {theirs.length > 0 && (
          <section className="mt-12">
            <div className="flex items-baseline gap-3">
              <h2 className="text-xl font-semibold text-self">You do these yourself</h2>
              <span className="label">{theirs.length}</span>
            </div>
            <p className="mt-2 max-w-prose text-sm text-ink-soft">
              Listed so nothing on your application surprises you. We never
              charge for these and they are not part of any package.
            </p>
            <div className="mt-5 space-y-4">
              {theirs.map(({ requirement, index }) => (
                <RequirementCard
                  key={requirement.requirement_id}
                  requirement={requirement}
                  index={index}
                  exam={exam}
                />
              ))}
            </div>
          </section>
        )}

        {pending.length > 0 && (
          <section className="mt-12">
            <h2 className="text-xl font-semibold">Not supported yet</h2>
            <p className="mt-2 max-w-prose text-sm text-ink-soft">
              We know this exam asks for{" "}
              {pending.map((row) => row.requirement.requirement_name).join(", ")}, and
              we cannot prepare {pending.length === 1 ? "it" : "them"} yet. Told
              plainly here rather than left off the list.
            </p>
          </section>
        )}

        {/* --- Photograph rules, from this exam's own record ------------- */}
        {guidance.length > 0 && (
          <section className="mt-14">
            <h2 className="text-xl font-semibold">
              What this exam wants in the photograph
            </h2>
            <p className="mt-2 max-w-prose text-sm text-ink-soft">
              Taken from {exam.conducting_body}&rsquo;s own rules for this cycle.
              Where they used specific wording, it is quoted.
            </p>
            <GuidanceList items={guidance} />
          </section>
        )}

        {/*
          Causes of rejection that are about the application rather than any
          one upload, so they belong to the page rather than to a card.
        */}
        {exam.application_rejection_conditions.length > 0 && (
          <section className="mt-14 rounded-xl border border-caveat-soft bg-caveat-soft/40 p-5 sm:p-6">
            <h2 className="text-lg font-semibold text-caveat">
              About the application itself
            </h2>
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

        {/* --- Price ----------------------------------------------------- */}
        {ours.length > 0 && (
          <section className="mt-14">
            <h2 className="text-xl font-semibold">Price</h2>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-line bg-surface p-5">
                <p className="label">Photo Ready</p>
                <p className="mt-2 text-3xl font-semibold">
                  ₹4<span className="ml-1 text-sm font-normal text-muted">final</span>
                </p>
                <p className="mt-3 text-sm text-ink-soft">
                  Your photograph, prepared to the specification above.
                </p>
              </div>

              {bundleWorthOffering ? (
                <div className="rounded-xl border-2 border-accent bg-accent-soft p-5">
                  <p className="label text-accent-ink">Complete kit · best value</p>
                  <p className="mt-2 text-3xl font-semibold text-accent-ink">
                    ₹8<span className="ml-1 text-sm font-normal text-accent-ink/70">final</span>
                  </p>
                  <p className="mt-3 text-sm text-accent-ink/90">
                    All {ours.length} files this exam needs from you, prepared
                    together and packaged in the order you upload them.
                  </p>
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-line p-5">
                  <p className="label">No bundle for this exam</p>
                  <p className="mt-3 text-sm text-ink-soft">
                    This application only needs one file from us, so there is
                    nothing to bundle. You pay ₹4.
                  </p>
                </div>
              )}
            </div>
            <p className="mt-4 text-sm text-muted">
              You see your finished file, watermarked, before you pay. Final
              price — nothing added at checkout.
            </p>
          </section>
        )}

        {/* --- Where these rules came from ------------------------------ */}
        <SourceNote exam={exam} estimates={estimates} />
      </div>

      <footer className="mt-auto border-t border-line">
        <div className="mx-auto max-w-4xl px-5 py-8 text-xs text-muted sm:px-8">
          <p>
            Rules for {exam.exam_name} as researched for the {exam.application_cycle}{" "}
            cycle. Always check your exam&rsquo;s own notification before you submit —
            and tell us if anything here is out of date.
          </p>
        </div>
      </footer>
    </main>
  );
}
