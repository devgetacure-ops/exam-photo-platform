import type { ExamDetail } from "../../lib/types";

/**
 * Where this exam's rules came from, stated honestly.
 *
 * The temptation is a reassuring "Official source" badge on every page. Seven
 * of the 39 examinations rest on secondary references — one is a forum
 * reproduction of the notification — and stamping those as official would be a
 * false claim about evidence, on a page whose entire value is that its numbers
 * can be trusted. So the badge reflects what the record actually says, and
 * where the source is weaker the page says that too.
 *
 * The report link is the other half of the same idea. 86 figures across the
 * catalogue are our own estimates, and rules change between cycles; the only
 * mechanism that converts an estimate into a researched value is a candidate
 * telling us it was wrong. Inviting that is worth more than an unearned badge.
 */

const VERIFICATION: Record<string, { label: string; detail: string }> = {
  verified: {
    label: "Verified",
    detail:
      "We found this exam's own published instructions and encoded them directly.",
  },
  verified_with_ambiguity: {
    label: "Verified, with gaps",
    detail:
      "We found this exam's published instructions, but they leave some values unstated. Those are marked as our estimates.",
  },
  provisional: {
    label: "Provisional",
    detail:
      "We have not been able to confirm every value against an official document for this cycle. Check your own notification before submitting.",
  },
};

export function SourceNote({
  exam,
  estimates,
}: {
  exam: ExamDetail;
  estimates: number;
}) {
  const verification =
    VERIFICATION[exam.verification_status ?? ""] ?? VERIFICATION.provisional;
  const official = exam.source_evidence.filter((source) => source.official_source);
  const secondary = exam.source_evidence.filter((source) => !source.official_source);

  return (
    <section className="mt-14 rounded-xl border border-line bg-sunk p-5 sm:p-6">
      <h2 className="text-lg font-semibold">Where these rules came from</h2>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <span
          className={`label rounded px-2 py-1 ${
            official.length > 0
              ? "bg-ready-soft text-ready"
              : "bg-caveat-soft text-caveat"
          }`}
        >
          {official.length > 0 ? "Official source" : "Secondary source only"}
        </span>
        <span className="label rounded border border-line-strong px-2 py-1">
          {verification.label}
        </span>
      </div>

      <p className="mt-3 max-w-prose text-sm leading-relaxed text-ink-soft">
        {verification.detail}
      </p>

      {official.length > 0 && (
        <ul className="mt-4 space-y-2">
          {official.map((source, index) => (
            <li key={index} className="text-sm">
              {source.source_url ? (
                <a
                  href={source.source_url}
                  target="_blank"
                  rel="noopener noreferrer nofollow"
                  className="text-accent underline underline-offset-2"
                >
                  {source.document_title ?? source.source_url}
                </a>
              ) : (
                <span className="text-ink-soft">{source.document_title}</span>
              )}
            </li>
          ))}
        </ul>
      )}

      {secondary.length > 0 && (
        <div className="mt-4 rounded-lg border border-caveat-soft bg-caveat-soft/40 p-3">
          <p className="text-sm text-ink-soft">
            {official.length > 0
              ? "We also used a secondary reference for some values:"
              : "We could not find this exam's own published file rules. What we have comes from a secondary reference:"}{" "}
            {secondary.map((source, index) => (
              <span key={index}>
                {index > 0 && ", "}
                {source.source_url ? (
                  <a
                    href={source.source_url}
                    target="_blank"
                    rel="noopener noreferrer nofollow"
                    className="text-accent underline underline-offset-2"
                  >
                    {source.document_title ?? source.source_url}
                  </a>
                ) : (
                  (source.document_title ?? "unnamed source")
                )}
              </span>
            ))}
            .
          </p>
        </div>
      )}

      {estimates > 0 && (
        <p className="mt-4 max-w-prose text-sm leading-relaxed text-ink-soft">
          <span className="spec text-caveat">est.</span> marks a figure this exam
          has not published, where we chose a sensible value. There{" "}
          {estimates === 1 ? "is 1" : `are ${estimates}`} on this page. Your file
          is prepared to it, and the report we give you names every one.
        </p>
      )}

      <p className="mt-5 text-sm">
        <a
          href={`mailto:corrections@example.invalid?subject=${encodeURIComponent(
            `Correction: ${exam.exam_name}`
          )}`}
          className="text-accent underline underline-offset-2"
        >
          Something here look wrong?
        </a>{" "}
        <span className="text-muted">
          Tell us and we will re-check it against the notification. Rules change
          between cycles and we would rather hear it from you than have you find
          out at the portal.
        </span>
      </p>
    </section>
  );
}
