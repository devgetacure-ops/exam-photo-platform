import type { RequirementSummary, ExamDetail } from "../../lib/types";
import { requirementSpecRows, photographSpecRows, type SpecRow } from "../../lib/spec-format";
import { DiagramFor } from "./framing-diagram";
import { RequirementUpload } from "./requirement-upload";

/**
 * One requirement of one examination.
 *
 * The whole component exists to keep three things visibly distinct, because
 * confusing them is this product's worst failure: a file *we* prepare, a step
 * *you* complete yourself, and a thing nobody can do yet. A candidate who
 * believes we handled their SSC live capture discovers otherwise at the portal,
 * and that is a labelling problem rather than a technical one (DEC-056).
 *
 * So the distinction is carried three ways at once, not one: by grouping (they
 * sit under different headings on the page), by colour, and by affordance — a
 * requirement we do not prepare has no upload control at all. Colour alone
 * would fail a colour-blind candidate; an affordance alone would be missed by
 * someone scanning. Text alone gets skipped. All three, and it survives.
 */

const TYPE_LABELS: Record<string, string> = {
  photograph: "Photograph",
  signature: "Signature",
  thumb_impression: "Thumb impression",
  handwritten_declaration: "Handwritten declaration",
  certificate_scan: "Certificate",
  identity_document: "Identity document",
  portal_declaration: "Portal declaration",
  other: "Document",
};

/**
 * Does this `applicability` narrow who the requirement applies to?
 *
 * 114 of the 116 values in the catalogue are the bare "All applicants", which
 * tells the reader nothing and, shown in the caveat colour, actively misleads —
 * it implies a condition on a row that has none. The handful that genuinely
 * narrow ("PwD candidates", "SC/ST candidates requesting the free travel
 * facility") are exactly the ones worth a candidate's attention, so the colour
 * is spent only on those.
 */
function narrowsAudience(applicability: string | null | undefined): boolean {
  if (!applicability) return false;
  return applicability.trim().toLowerCase() !== "all applicants";
}

/** Why a requirement is not ours, in the candidate's terms rather than the schema's. */
function notOursBecause(requirement: RequirementSummary): string {
  switch (requirement.submission_method) {
    case "official_live_capture":
      return "The exam photographs you directly through their portal or at the centre. There is no file to upload, and nothing for us to prepare.";
    case "typed_or_selected_declaration":
      return "You type or tick this on the exam's own website. It never becomes a file.";
    case "physical_stage_requirement":
      return "You bring this to a later stage in person. Nothing is uploaded now.";
    case "external_identity_verification":
      return "This is verified through a separate government service, not by uploading anything here.";
    default:
      return "This one is not a file we can prepare for you.";
  }
}

function SpecList({ rows }: { rows: SpecRow[] }) {
  if (rows.length === 0) return null;
  return (
    <dl className="mt-4 grid gap-x-6 gap-y-0 sm:grid-cols-2">
      {rows.map((row) => (
        <div
          key={row.term}
          className="flex items-baseline justify-between gap-4 border-b border-line py-2"
        >
          <dt className="text-sm text-muted">{row.term}</dt>
          <dd className="spec flex items-baseline gap-1.5 text-sm text-ink">
            {row.value}
            {/*
              DEC-057: a value the platform chose because no body published one
              is marked, but quietly. A candidate cannot act on it — they cannot
              research the figure and ours is the best available — so a loud
              warning on more than half the catalogue would only read as a
              platform that does not know its own rules. It is never absent,
              because it must not be mistaken for something the exam said.
            */}
            {row.estimated && (
              <abbr
                title="Our estimate — this exam has not published a figure for it."
                className="cursor-help text-xs font-normal text-caveat no-underline"
              >
                est.
              </abbr>
            )}
          </dd>
        </div>
      ))}
    </dl>
  );
}

interface Props {
  requirement: RequirementSummary;
  /** Position in the record — provenance is keyed positionally. */
  index: number;
  exam: ExamDetail;
}

export function RequirementCard({ requirement, index, exam }: Props) {
  const isPhotograph = requirement.requirement_type === "photograph";
  const prepared =
    requirement.platform_support === "supported" ||
    requirement.platform_support === "partially_supported";

  const rows = isPhotograph
    ? photographSpecRows(exam)
    : requirementSpecRows(requirement, index, exam.provenance);

  const typeLabel = TYPE_LABELS[requirement.requirement_type] ?? "File";

  // --- Not ours to make ---------------------------------------------------
  if (!prepared) {
    return (
      <article className="rounded-xl border border-self-line bg-self-soft p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="font-medium text-ink">{requirement.requirement_name}</h3>
            <p className="label mt-1 text-self">You do this one yourself</p>
          </div>
          <span className="label rounded border border-self-line px-2 py-1 text-self">
            Not a file
          </span>
        </div>
        <p className="mt-3 max-w-prose text-sm leading-relaxed text-ink-soft">
          {notOursBecause(requirement)}
        </p>
        {requirement.content_instructions && (
          <p className="mt-2 max-w-prose text-sm text-ink-soft">
            {requirement.content_instructions}
          </p>
        )}
        {/* Deliberately no upload control, no price, no progress. */}
      </article>
    );
  }

  // --- Ours to prepare ----------------------------------------------------
  return (
    <article className="overflow-hidden rounded-xl border border-line bg-surface">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-line px-5 py-4">
        <div>
          <h3 className="font-medium">{requirement.requirement_name}</h3>
          <p className="label mt-1">
            {typeLabel}
            {requirement.requirement_status === "conditional" && " · only if it applies to you"}
            {requirement.requirement_status === "optional" && " · optional"}
          </p>
        </div>
        {requirement.platform_support === "partially_supported" && (
          <span className="label rounded bg-caveat-soft px-2 py-1 text-caveat">
            Partly — read below
          </span>
        )}
      </div>

      <div className="grid gap-5 px-5 py-5 sm:grid-cols-[auto_1fr] sm:gap-6">
        <div className="flex gap-3 sm:flex-col">
          <figure className="w-20">
            <DiagramFor
              requirementType={requirement.requirement_type}
              variant="good"
              className="w-full rounded"
            />
            <figcaption className="label mt-1.5 text-center text-ready">Like this</figcaption>
          </figure>
          <figure className="w-20">
            <DiagramFor
              requirementType={requirement.requirement_type}
              variant="bad"
              className="w-full rounded opacity-70"
            />
            <figcaption className="label mt-1.5 text-center text-blocked">Not this</figcaption>
          </figure>
        </div>

        <div className="min-w-0">
          {requirement.content_instructions && (
            <p className="max-w-prose text-sm leading-relaxed text-ink-soft">
              {requirement.content_instructions}
            </p>
          )}
          {rows.length > 0 ? (
            <SpecList rows={rows} />
          ) : (
            <p className="mt-3 text-sm text-muted">
              This exam has not published dimensions or a size limit for this
              file. We prepare it to a sensible standard and tell you what we
              used.
            </p>
          )}
          {/*
            What this examination itself says will get the file rejected.
            Kept separate from anything we check: these are the body's own
            published causes, most of them not verifiable from a file at all
            (DEC-041 — we produce and warn, we do not refuse for appearance).
            Attributing them to the exam rather than to us is the point; a
            candidate who reads "we reject shadows" hears a different and
            wrong thing from "your exam rejects shadows".
          */}
          {requirement.rejection_conditions.length > 0 && (
            <div className="mt-4 rounded-lg border border-blocked-soft bg-blocked-soft/40 p-3.5">
              <p className="label text-blocked">
                What gets this rejected
              </p>
              <ul className="mt-2 space-y-1.5">
                {requirement.rejection_conditions.map((condition) => (
                  <li
                    key={condition}
                    className="flex gap-2 text-sm leading-relaxed text-ink-soft"
                  >
                    <span aria-hidden="true" className="mt-2 size-1 shrink-0 rounded-full bg-blocked" />
                    <span>{condition}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-2.5 text-xs text-muted">
                Published by the exam, not by us. We prepare your file and flag
                what we can see — the rest is worth checking yourself.
              </p>
            </div>
          )}

          {narrowsAudience(requirement.applicability) && (
            <p className="mt-3 flex items-start gap-2 text-sm text-caveat">
              <svg
                className="mt-0.5 size-4 shrink-0"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="9" />
                <path d="M12 8v5M12 16h.01" />
              </svg>
              <span>
                <span className="font-medium">Only for:</span>{" "}
                {requirement.applicability}
              </span>
            </p>
          )}
        </div>
      </div>

      <div className="border-t border-line px-5 pb-5">
        <RequirementUpload
          examId={exam.exam_id}
          examName={exam.exam_name}
          requirementId={requirement.requirement_id}
          requirementName={requirement.requirement_name}
          requirementType={requirement.requirement_type}
        />
      </div>
    </article>
  );
}
