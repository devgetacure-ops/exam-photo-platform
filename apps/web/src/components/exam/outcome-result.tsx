"use client";

import { jobOutputUrl } from "../../lib/api-client";
import type { PrepareRequirementResponse } from "../../lib/types";
import { formatBytes } from "../../lib/spec-format";

/**
 * What came back, in three states rather than two (WEB-002, DEC-056).
 *
 * The platform produces and warns; it does not refuse for appearance
 * (DEC-041). So a blank page, a ceiling we had to invent, an unreachable
 * published minimum and an oversized document are all things reported *about a
 * file that exists*. A two-state interface has to file every one of them under
 * success, and a caveat filed under success is a caveat nobody reads — which is
 * precisely how a candidate submits a file they should have looked at.
 *
 * Hence: clean, prepared-with-findings, and blocked, each with its own colour,
 * its own words, and its own next action.
 */

interface Props {
  result: PrepareRequirementResponse;
  requirementName: string;
  onReplace: () => void;
}

/**
 * Routine normalisation notes: things the engine *did* to the upload, not
 * things wrong with it.
 *
 * These are exactly the members of the engine's own `InputWarningCode` — EXIF
 * stripped, colour mode converted, an invalid ICC profile dropped. The API
 * reports any non-empty `findings` as `prepared_with_findings`, so a perfectly
 * ordinary JPEG comes back in the caveat state carrying
 * "INPUT_METADATA_REMOVED", which is both an internal code and not a caveat.
 *
 * Left as-is, almost every file would wear the amber badge, and a caveat state
 * that fires on everything trains candidates to ignore it — destroying the
 * mechanism the genuine ones depend on (DEC-056: a caveat nobody reads is a
 * caveat filed under success).
 *
 * The rule is fail-safe: only these recognised codes are demoted. Anything
 * else — including a code added later that this list has not learned — stays a
 * caveat, so the failure mode is showing too much rather than hiding
 * something.
 */
const ROUTINE_NOTES: Record<string, string> = {
  INPUT_METADATA_REMOVED: "Removed the hidden data your camera saved in the file.",
  INPUT_COLOUR_MODE_CONVERTED: "Converted the colour mode for the exam's format.",
  INPUT_ICC_PROFILE_INVALID: "Replaced a broken colour profile.",
  INPUT_ORIENTATION_METADATA_INVALID: "Corrected the image's rotation.",
  INPUT_EXTENSION_MISMATCH: "The file extension did not match its actual format.",
};

function isRoutine(finding: string): boolean {
  return finding in ROUTINE_NOTES;
}

/** Engine issue codes, said the way a person would say them. */
const ISSUE_TEXT: Record<string, string> = {
  NO_FACE_DETECTED: "We could not find a face in this photo.",
  MULTIPLE_FACES: "There is more than one face in this photo.",
  FACE_TOO_SMALL: "The face is too small in the frame — move closer.",
  IMAGE_TOO_BLURRY: "The photo is too blurry to use.",
  IMAGE_TOO_DARK: "The photo is too dark.",
  IMAGE_TOO_BRIGHT: "The photo is too bright.",
  EYES_CLOSED: "The eyes look closed.",
};

function humanIssue(code: string): string {
  return ISSUE_TEXT[code] ?? code.toLowerCase().replace(/_/g, " ");
}

export function OutcomeResult({ result, requirementName, onReplace }: Props) {
  const blocked = result.outcome === "blocked" || result.outcome === "not_produced";

  const substantive = result.findings.filter((finding) => !isRoutine(finding));
  const routine = result.findings.filter(isRoutine);
  // The API's outcome is authoritative about whether a file was produced; what
  // counts as worth the candidate's attention is a presentation judgement, and
  // routine normalisation is not it.
  const hasFindings =
    result.outcome === "prepared_with_findings" && substantive.length > 0;

  if (blocked) {
    return (
      <div className="mt-4 rounded-lg border border-blocked-soft bg-blocked-soft/40 p-4">
        <p className="font-medium text-blocked">We could not prepare this one</p>
        <ul className="mt-2 space-y-1">
          {(result.issue_codes.length > 0
            ? result.issue_codes.map(humanIssue)
            : result.findings
          ).map((line) => (
            <li key={line} className="text-sm leading-relaxed text-ink-soft">
              {line}
            </li>
          ))}
        </ul>
        <p className="mt-3 text-sm text-ink-soft">
          Nothing has been charged. Try a different photo and we will have
          another go.
        </p>
        <button
          type="button"
          onClick={onReplace}
          className="mt-3 rounded-md border border-line-strong px-3 py-1.5 text-sm font-medium hover:border-accent hover:text-accent"
        >
          Try another file
        </button>
      </div>
    );
  }

  return (
    <div
      className={`mt-4 rounded-lg border p-4 ${
        hasFindings
          ? "border-caveat-soft bg-caveat-soft/40"
          : "border-ready-soft bg-ready-soft/50"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className={`font-medium ${hasFindings ? "text-caveat" : "text-ready"}`}>
            {hasFindings ? "Ready — with something to check" : "Ready"}
          </p>
          <p className="spec mt-1 text-xs text-ink-soft">
            {[
              result.width && result.height
                ? `${result.width} × ${result.height} px`
                : null,
              result.byte_size ? formatBytes(result.byte_size) : null,
              result.output_filename,
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
        </div>
        <button
          type="button"
          onClick={onReplace}
          className="label rounded border border-line-strong px-2 py-1 hover:border-accent hover:text-accent"
        >
          Replace
        </button>
      </div>

      {/*
        The preview is watermarked and served at reduced resolution by the
        service; the clean file is what the candidate buys. That is the
        protection that actually works — blocking right-click stops nobody and
        would make a page selling precision feel cheap.
      */}
      {result.output_url && (
        <figure className="mt-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={jobOutputUrl(result.job_id)}
            alt={`Prepared ${requirementName}`}
            className="max-h-64 rounded border border-line bg-surface object-contain"
          />
          <figcaption className="mt-1.5 text-xs text-muted">
            Preview — watermarked until you buy it.
          </figcaption>
        </figure>
      )}

      {hasFindings && (
        <div className="mt-3">
          <p className="label text-caveat">Worth checking before you submit</p>
          <ul className="mt-1.5 space-y-1.5">
            {substantive.map((finding) => (
              <li key={finding} className="text-sm leading-relaxed text-ink-soft">
                {finding}
              </li>
            ))}
          </ul>
        </div>
      )}

      {routine.length > 0 && (
        <details className="mt-3">
          <summary className="label cursor-pointer hover:text-ink">
            What we changed ({routine.length})
          </summary>
          <ul className="mt-2 space-y-1">
            {routine.map((finding) => (
              <li key={finding} className="text-sm text-muted">
                {ROUTINE_NOTES[finding]}
              </li>
            ))}
          </ul>
        </details>
      )}

      {/*
        A file that exists but that the platform could not fully verify is not
        a clean pass, and DEC-056 forbids collapsing that into one. Said in the
        candidate's terms, next to the file rather than in a report they will
        not open.
      */}
      {result.is_valid === false && result.issue_codes.length > 0 && (
        <div className="mt-3">
          <p className="label text-caveat">What we noticed</p>
          <ul className="mt-1.5 space-y-1.5">
            {result.issue_codes.map((code) => (
              <li key={code} className="text-sm leading-relaxed text-ink-soft">
                {humanIssue(code)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
