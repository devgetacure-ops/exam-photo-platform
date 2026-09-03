"use client";

import { useCallback, useRef, useState } from "react";

import { prepareRequirement } from "../../lib/api-client";
import { validateImageFile } from "../../lib/file-validation";
import { startKit } from "../../lib/kit-state";
import { useKit } from "./use-kit";
import {
  RequirementNotServedError,
  type PrepareRequirementResponse,
  type RequirementNotServed,
} from "../../lib/types";
import { OutcomeResult } from "./outcome-result";

/**
 * Preparing one requirement.
 *
 * A client island inside an otherwise static exam page: the catalogue is
 * prerendered, and only this needs the browser and the processing service.
 *
 * Two things shape the interaction.
 *
 * **The wait is around ten seconds and it lands before payment, deliberately.**
 * The candidate watches their own file being fixed while they are curious,
 * rather than staring at a spinner after they have paid — and they decide to
 * buy against the real result rather than a promise. That ordering is the whole
 * argument for preparing first.
 *
 * **A refusal is not a failure.** If the support gate returns 409 the platform
 * was never going to prepare this item, and the candidate needs to be told what
 * to do instead, in the requirement's own words (DEC-056). Rendering that as an
 * error would be the product's worst failure mode wearing a different hat.
 */

type Phase = "idle" | "working" | "done" | "refused" | "error";

interface Props {
  examId: string;
  examName: string;
  requirementId: string;
  requirementName: string;
  /** Drives the accepted file types and the copy on the empty state. */
  requirementType: string;
}

const ACCEPT = "image/jpeg,image/png,image/webp,application/pdf";

/** What we ask the candidate for, in their words rather than the schema's. */
const PROMPT: Record<string, string> = {
  photograph: "Add a photo of yourself",
  signature: "Add a photo of your signature",
  thumb_impression: "Add a photo of your thumb impression",
  handwritten_declaration: "Add a photo of the written declaration",
  certificate_scan: "Add your certificate",
  identity_document: "Add your identity document",
};

export function RequirementUpload({
  examId,
  examName,
  requirementId,
  requirementName,
  requirementType,
}: Props) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [result, setResult] = useState<PrepareRequirementResponse | null>(null);
  const [refusal, setRefusal] = useState<RequirementNotServed | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { record } = useKit(examId);

  const submit = useCallback(
    async (file: File) => {
      // A PDF is a legitimate certificate upload, so the image-only check runs
      // for the requirements that genuinely take an image.
      if (file.type !== "application/pdf") {
        const check = validateImageFile(file);
        if (!check.valid) {
          setPhase("error");
          setMessage(check.error ?? "That file will not work.");
          return;
        }
      }

      setPhase("working");
      setMessage(null);
      setRefusal(null);

      // Selecting an examination is what starts a kit; there is no separate
      // step, and the id lives only in this browser (DEC-058).
      const kit = startKit(examId, examName);

      try {
        const prepared = await prepareRequirement({
          examId,
          requirementId,
          file,
          kitId: kit.kitId,
        });
        record(prepared, examName);
        setResult(prepared);
        setPhase("done");
      } catch (error) {
        if (error instanceof RequirementNotServedError) {
          setRefusal(error.info);
          setPhase("refused");
          return;
        }
        setPhase("error");
        setMessage(
          error instanceof Error ? error.message : "Something went wrong."
        );
      }
    },
    [examId, examName, requirementId, record]
  );

  const onDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) void submit(file);
  };

  if (phase === "working") {
    return (
      <div
        className="mt-4 rounded-lg border border-line bg-sunk p-5 text-center"
        role="status"
        aria-live="polite"
      >
        <div className="mx-auto flex w-fit items-center gap-3">
          <span
            aria-hidden="true"
            className="size-4 animate-spin rounded-full border-2 border-line-strong border-t-accent"
          />
          <span className="text-sm font-medium">Preparing your file…</span>
        </div>
        <p className="mt-2 text-sm text-muted">
          This takes about ten seconds. We are cropping, sizing and compressing
          it to {examName}&rsquo;s specification.
        </p>
      </div>
    );
  }

  if (phase === "refused" && refusal) {
    return (
      <div className="mt-4 rounded-lg border border-self-line bg-self-soft p-4">
        <p className="font-medium text-self">We do not prepare this one</p>
        <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">
          {refusal.detail}
        </p>
        {refusal.content_instructions && (
          <p className="mt-2 text-sm text-ink-soft">
            {refusal.content_instructions}
          </p>
        )}
      </div>
    );
  }

  if (phase === "done" && result) {
    return (
      <OutcomeResult
        result={result}
        requirementName={requirementName}
        onReplace={() => {
          setResult(null);
          setPhase("idle");
        }}
      />
    );
  }

  return (
    <div className="mt-4">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`rounded-lg border border-dashed p-5 text-center transition-colors ${
          dragging ? "border-accent bg-accent-soft" : "border-line-strong bg-sunk"
        }`}
      >
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="text-sm font-medium text-accent underline underline-offset-2"
        >
          {PROMPT[requirementType] ?? "Add your file"}
        </button>
        <p className="mt-1 text-sm text-muted">
          or drop it here — JPEG, PNG or PDF, up to 5&nbsp;MB
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="sr-only"
          aria-label={`Upload for ${requirementName}`}
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void submit(file);
            // Reset so choosing the same file twice still fires a change.
            event.target.value = "";
          }}
        />
      </div>

      {phase === "error" && message && (
        <p className="mt-2 flex items-start gap-2 text-sm text-blocked" role="alert">
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
          <span>{message}</span>
        </p>
      )}

      <p className="mt-2 text-xs text-muted">
        You see the finished file before you pay. Everything you upload is
        deleted after 30 minutes.
      </p>
    </div>
  );
}
