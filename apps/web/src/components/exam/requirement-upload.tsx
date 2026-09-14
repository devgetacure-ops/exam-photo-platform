"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { prepareRequirement } from "../../lib/api-client";
import { validateImageFile } from "../../lib/file-validation";
import { isPasswordLocked, lockedPdfMessage } from "../../lib/pdfjs";
import { startKit } from "../../lib/kit-state";
import { useKit } from "./use-kit";
import {
    RequirementNotServedError,
    type RequirementNotServed,
} from "../../lib/types";
import { OutcomeResult } from "./outcome-result";
import { PreparationChallenge } from "./preparation-challenge";
import { useLiveJob } from "./live-job-state";
import { switchLighting, type PreparedFile } from "../../lib/journey-client";
import { PreparationLoader } from "./preparation-loader";
import { FileTypeDrawing } from "../euk/doodles";
import { useUploadConsent } from "./upload-consent";

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
    partiallySupported?: boolean;
    onWorking?: (value: boolean) => void;
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

function candidateError(error: unknown): string {
    const detail = error instanceof Error ? error.message.toLowerCase() : "";
    if (detail.includes("birefnet") || detail.includes("download_birefnet")) {
        return "Photo preparation is temporarily unavailable. Please try again shortly.";
    }
    if (
        detail.includes("not reachable") ||
        detail.includes("failed to fetch") ||
        detail.includes("network")
    ) {
        return "We can’t reach file preparation right now. Please try again in a moment.";
    }
    return "We couldn’t prepare that file. Please try again.";
}

function LightingSwitch({
    title,
    checked,
    disabled,
    label,
    onChange,
}: {
    title: string;
    checked: boolean;
    disabled?: boolean;
    label?: string;
    onChange: (checked: boolean) => void;
}) {
    return (
        <label className="euk-switch">
            <span className="euk-switch-title">{title}</span>
            <input
                type="checkbox"
                role="switch"
                checked={checked}
                disabled={disabled}
                aria-label={label}
                onChange={(event) => onChange(event.target.checked)}
            />
            <span className="euk-switch-track" aria-hidden="true">
                <span className="euk-switch-thumb" />
            </span>
        </label>
    );
}

export function RequirementUpload({
    examId,
    examName,
    requirementId,
    requirementName,
    requirementType,
    partiallySupported = false,
    onWorking,
}: Props) {
    const [phase, setPhase] = useState<Phase>("idle");
    const [result, setResult] = useState<PreparedFile | null>(null);
    const live = useLiveJob(result?.job_id ?? "");
    const [refusal, setRefusal] = useState<RequirementNotServed | null>(null);
    const [message, setMessage] = useState<string | null>(null);
    const challengeKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;
    const [challengeToken, setChallengeToken] = useState("");
    const [enhancementEnabled, setEnhancementEnabled] = useState(true);
    const [switching, setSwitching] = useState(false);
    const [progressToken, setProgressToken] = useState<string>();
    const [dragging, setDragging] = useState(false);
    const [sourceUrl, setSourceUrl] = useState<string | null>(null);
    const sourceRef = useRef<string | null>(null);
    useEffect(
        () => () => {
            if (sourceRef.current) URL.revokeObjectURL(sourceRef.current);
        },
        [],
    );
    const inputRef = useRef<HTMLInputElement>(null);
    const { record, forget } = useKit(examId);
    const documents = ["certificate_scan", "identity_document"].includes(
        requirementType,
    );
    const photo = requirementType === "photograph";
    const consent = useUploadConsent();

    const submit = useCallback(
        async (file: File) => {
            if (challengeKey && !challengeToken) {
                setMessage("Complete the verification before uploading.");
                setPhase("error");
                return;
            }
            if (file.size > 5 * 1024 * 1024) {
                setPhase("error");
                setMessage("Choose a file smaller than 5 MB.");
                return;
            }
            if (
                file.type === "application/pdf" &&
                !["certificate_scan", "identity_document"].includes(
                    requirementType,
                )
            ) {
                setPhase("error");
                setMessage(
                    "Choose a JPEG, PNG or WebP image for this requirement.",
                );
                return;
            }
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

            // A locked PDF is turned away before it is uploaded (DEC-052).
            if (await isPasswordLocked(file)) {
                setPhase("error");
                setMessage(lockedPdfMessage([file.name]));
                return;
            }

            if (sourceRef.current) URL.revokeObjectURL(sourceRef.current);
            const source =
                file.type.startsWith("image/") &&
                typeof URL.createObjectURL === "function"
                    ? URL.createObjectURL(file)
                    : null;
            sourceRef.current = source;
            setSourceUrl(source);
            const token = `prg_${crypto.randomUUID().replaceAll("-", "")}`;
            setProgressToken(token);
            setPhase("working");
            onWorking?.(true);
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
                    enhancementEnabled,
                    progressToken: token,
                    challengeToken,
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
                setMessage(candidateError(error));
            } finally {
                onWorking?.(false);
            }
        },
        [
            examId,
            examName,
            requirementId,
            requirementType,
            record,
            enhancementEnabled,
            onWorking,
            challengeKey,
            challengeToken,
        ],
    );

    const onDrop = (event: React.DragEvent) => {
        event.preventDefault();
        setDragging(false);
        if (!consent.allow()) return;
        const file = event.dataTransfer.files?.[0];
        if (file) void submit(file);
    };

    if (phase === "working") {
        return (
            <PreparationLoader
                sourceUrl={sourceUrl}
                progressToken={progressToken}
                requirementType={requirementType}
            />
        );
    }

    if (phase === "refused" && refusal) {
        return (
            <div className="euk-refusal">
                <p className="euk-refusal-title">We do not prepare this one</p>
                <p>{refusal.detail}</p>
                {refusal.content_instructions && (
                    <p>{refusal.content_instructions}</p>
                )}
            </div>
        );
    }

    if (phase === "done" && result) {
        return (
            <>
                {photo && result.enhancement_enabled !== undefined && (
                    <div className="euk-lighting">
                        <LightingSwitch
                            title="Intelligent lighting"
                            checked={result.enhancement_enabled}
                            disabled={
                                switching ||
                                !result.enhancement_switchable ||
                                live?.entitlement === "released"
                            }
                            onChange={async (enabled) => {
                                setSwitching(true);
                                onWorking?.(true);
                                setMessage(null);
                                try {
                                    const variant = await switchLighting(
                                        result.job_id,
                                        enabled,
                                    );
                                    const preview = variant.preview_url
                                        ? `${variant.preview_url}${variant.preview_url.includes("?") ? "&" : "?"}variant=${Date.now()}`
                                        : null;
                                    const next = {
                                        ...result,
                                        ...variant,
                                        preview_url: preview,
                                    };
                                    setResult(next);
                                    record(next, examName);
                                    setEnhancementEnabled(enabled);
                                } catch (error) {
                                    setMessage(
                                        error instanceof Error
                                            ? error.message
                                            : "Could not switch lighting.",
                                    );
                                } finally {
                                    setSwitching(false);
                                    onWorking?.(false);
                                }
                            }}
                        />
                        <p role="status">
                            {switching
                                ? "Updating your preview…"
                                : !result.enhancement_enabled
                                  ? "Original lighting preserved."
                                  : result.enhancements_applied?.length
                                    ? result.enhancements_applied.join(" · ")
                                    : "Your photograph needed no correction."}
                        </p>
                        {message && (
                            <p role="alert" className="euk-lighting-error">
                                {message}
                            </p>
                        )}
                    </div>
                )}
                <OutcomeResult
                    result={result}
                    requirementName={requirementName}
                    sourceUrl={sourceUrl}
                    partiallySupported={partiallySupported}
                    onReplace={() => {
                        forget(requirementId);
                        setResult(null);
                        if (sourceRef.current)
                            URL.revokeObjectURL(sourceRef.current);
                        sourceRef.current = null;
                        setSourceUrl(null);
                        setPhase("idle");
                    }}
                />
            </>
        );
    }

    return (
        <div className="euk-upload">
            {challengeKey && (
                <PreparationChallenge
                    siteKey={challengeKey}
                    onToken={setChallengeToken}
                />
            )}
            {consent.panel}
            <div
                className="euk-drop"
                data-dragging={dragging}
                data-type={requirementType}
                onDragOver={(event) => {
                    event.preventDefault();
                    setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={onDrop}
            >
                <FileTypeDrawing type={requirementType} className="euk-drop-art" />
                <button
                    type="button"
                    onClick={() => {
                        if (consent.allow()) inputRef.current?.click();
                    }}
                    className="primary-button euk-drop-button"
                >
                    {PROMPT[requirementType] ?? "Add your file"}
                </button>
                <p className="euk-drop-hint">
                    or drop it here: JPEG, PNG, WebP{documents ? " or PDF" : ""},
                    up to 5&nbsp;MB
                </p>
                <input
                    ref={inputRef}
                    type="file"
                    accept={documents ? ACCEPT : "image/jpeg,image/png,image/webp"}
                    className="sr-only"
                    aria-label={`Upload for ${requirementName}`}
                    onChange={(event) => {
                        const file = event.target.files?.[0];
                        if (file && consent.allow()) void submit(file);
                        // Reset so choosing the same file twice still fires a change.
                        event.target.value = "";
                    }}
                />
            </div>

            {phase === "error" && message && (
                <p className="euk-upload-error" role="alert">
                    <svg viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" aria-hidden="true">
                        <rect x="1.5" y="1.5" width="19" height="19" />
                        <path d="M7 7 L 15 15 M15 7 L 7 15" />
                    </svg>
                    <span>{message}</span>
                </p>
            )}

            {photo && (
                <div className="euk-lighting">
                    <LightingSwitch
                        title="Intelligent lighting adjustment"
                        label="Intelligent lighting adjustment"
                        checked={enhancementEnabled}
                        onChange={setEnhancementEnabled}
                    />
                    <p>
                        Adjusts exposure and colour only when your photograph
                        needs it, and you review the change before paying. No
                        whitening, reshaping or beauty filters.
                    </p>
                </div>
            )}
            <p className="euk-upload-note">
                No account needed. Review the result before you pay.
            </p>
        </div>
    );
}
