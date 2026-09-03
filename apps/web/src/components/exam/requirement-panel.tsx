"use client";

import type { ExamDetail, RequirementSummary } from "../../lib/types";
import { requirementSpecRows, photographSpecRows } from "../../lib/spec-format";
import { RequirementUpload } from "./requirement-upload";
import { ExampleStrip } from "./example-strip";

/**
 * One file: what it must be, what to send, and what came back.
 *
 * Everything a candidate needs to *act* is above the fold — the specification
 * in one line, the examples, the upload. Everything they might want to *read*
 * — the exam's own wording, its published causes of rejection — is behind a
 * disclosure, because it is reference material and an earlier version that
 * printed all of it inline is what made these pages six screens long.
 */

interface Props {
  requirement: RequirementSummary;
  index: number;
  exam: ExamDetail;
}

function notOursBecause(requirement: RequirementSummary): string {
  switch (requirement.submission_method) {
    case "official_live_capture":
      return "The exam photographs you itself, through its portal or at the centre. There is no file to upload and nothing for us to prepare.";
    case "typed_or_selected_declaration":
      return "You type or tick this on the exam's own website. It never becomes a file.";
    case "physical_stage_requirement":
      return "You bring this in person at a later stage. Nothing is uploaded now.";
    case "external_identity_verification":
      return "This is verified through a separate government service, not by uploading anything here.";
    default:
      return "This one is not a file we can prepare for you.";
  }
}

export function RequirementPanel({ requirement, index, exam }: Props) {
  const prepared =
    requirement.platform_support === "supported" ||
    requirement.platform_support === "partially_supported";

  const rows =
    requirement.requirement_type === "photograph"
      ? photographSpecRows(exam)
      : requirementSpecRows(requirement, index, exam.provenance);

  // --- Not ours ------------------------------------------------------------
  if (!prepared) {
    return (
      <div className="mx-auto max-w-3xl px-10 py-8">
        <h2 className="text-xl font-semibold">{requirement.requirement_name}</h2>
        <p className="label mt-1 text-self">You do this one yourself</p>
        <div className="mt-5 rounded-lg border border-self-line bg-self-soft p-5">
          <p className="text-sm leading-relaxed text-ink-soft">
            {notOursBecause(requirement)}
          </p>
          {requirement.content_instructions && (
            <p className="mt-3 text-sm leading-relaxed text-ink-soft">
              {requirement.content_instructions}
            </p>
          )}
        </div>
        {/* No upload control, no price, and it counts toward no total. */}
      </div>
    );
  }

  // --- Ours ----------------------------------------------------------------
  return (
    <div className="mx-auto max-w-3xl px-10 py-8">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="text-xl font-semibold">{requirement.requirement_name}</h2>
        {requirement.platform_support === "partially_supported" && (
          <span className="label rounded bg-caveat-soft px-2 py-1 text-caveat">
            Partly — see below
          </span>
        )}
      </div>

      {/* The specification as one scannable line, not a four-row table. */}
      {rows.length > 0 && (
        <p className="spec mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-ink-soft">
          {rows.map((row) => (
            <span key={row.term} className="flex items-baseline gap-1">
              {row.value}
              {row.estimated && (
                <abbr
                  title="Our estimate — this exam has not published a figure."
                  className="cursor-help text-xs text-caveat no-underline"
                >
                  est.
                </abbr>
              )}
            </span>
          ))}
        </p>
      )}

      <ExampleStrip requirementType={requirement.requirement_type} />

      <RequirementUpload
        examId={exam.exam_id}
        examName={exam.exam_name}
        requirementId={requirement.requirement_id}
        requirementName={requirement.requirement_name}
        requirementType={requirement.requirement_type}
      />

      {/* --- Reference, folded away ------------------------------------- */}
      {(requirement.rejection_conditions.length > 0 ||
        requirement.content_instructions) && (
        <details className="mt-6 border-t border-line pt-4">
          <summary className="cursor-pointer text-sm font-medium text-ink-soft hover:text-ink">
            What {exam.conducting_body} says about this file
          </summary>

          {requirement.content_instructions && (
            <p className="mt-3 text-sm leading-relaxed text-ink-soft">
              {requirement.content_instructions}
            </p>
          )}

          {requirement.rejection_conditions.length > 0 && (
            <>
              <p className="label mt-4 text-blocked">Causes of rejection they list</p>
              <ul className="mt-2 space-y-1.5">
                {requirement.rejection_conditions.map((condition) => (
                  <li
                    key={condition}
                    className="flex gap-2 text-sm leading-relaxed text-ink-soft"
                  >
                    <span
                      aria-hidden="true"
                      className="mt-2 size-1 shrink-0 rounded-full bg-blocked"
                    />
                    <span>{condition}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-xs text-muted">
                Published by the exam, not by us.
              </p>
            </>
          )}
        </details>
      )}
    </div>
  );
}
