"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { prepareRequirement } from "../../lib/api-client";
import { validateImageFile } from "../../lib/file-validation";
import { prepareUpload, uploadRefusal } from "../../lib/upload-image";
import { isPasswordLocked, lockedPdfMessage } from "../../lib/pdfjs";
import { startKit } from "../../lib/kit-state";
import { useKit } from "./use-kit";
import { useTr } from "../locale-context";
import {
    RequirementNotServedError,
    type RequirementNotServed,
} from "../../lib/types";
import { OutcomeResult } from "./outcome-result";
import { PreparationChallenge } from "./preparation-challenge";
import { useLiveJob } from "./live-job-state";
import { switchLighting, type PreparedFile } from "../../lib/journey-client";
import { entryLive, resultFromEntry } from "../../lib/kit-liveness";
import { PreparationLoader } from "./preparation-loader";
import { FileTypeDrawing } from "../euk/doodles";
import { useUploadConsent } from "./upload-consent";
import { randomHex } from "../../lib/random-hex";

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
const PROMPT: Record<string, [string, string]> = {
    photograph: ["Add a photo of yourself", "अपनी फ़ोटो जोड़ें"],
    signature: ["Add a photo of your signature", "अपने हस्ताक्षर की फ़ोटो जोड़ें"],
    thumb_impression: ["Add a photo of your thumb impression", "अपने अंगूठे के निशान की फ़ोटो जोड़ें"],
    handwritten_declaration: ["Add a photo of the written declaration", "लिखी हुई घोषणा की फ़ोटो जोड़ें"],
    certificate_scan: ["Add your certificate", "अपना प्रमाणपत्र जोड़ें"],
    identity_document: ["Add your identity document", "अपना पहचान पत्र जोड़ें"],
};

function candidateError(error: unknown, tr: (english: string, hindi: string) => string): string {
    const detail = error instanceof Error ? error.message.toLowerCase() : "";
    if (detail.includes("birefnet") || detail.includes("download_birefnet")) {
        return tr(
            "Photo preparation is temporarily unavailable. Please try again shortly.",
            "फ़ोटो तैयार करना अभी कुछ देर के लिए बंद है। थोड़ी देर बाद फिर कोशिश करें।",
        );
    }
    if (
        detail.includes("not reachable") ||
        detail.includes("failed to fetch") ||
        detail.includes("network")
    ) {
        return tr(
            "We can’t reach file preparation right now. Please try again in a moment.",
            "अभी फ़ाइल तैयार करने वाली सेवा तक नहीं पहुँच पा रहे। थोड़ी देर में फिर कोशिश करें।",
        );
    }
    return tr("We couldn’t prepare that file. Please try again.", "यह फ़ाइल तैयार नहीं हो सकी। फिर से कोशिश करें।");
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
    const [fresh, setResult] = useState<PreparedFile | null>(null);
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
    const cameraRef = useRef<HTMLInputElement>(null);
    const { entries, record, forget } = useKit(examId);
    // Coming back to a file that is already ready shows that file, not an
    // empty upload form under a bar that says "Ready" (owner's testing,
    // 1 October). The kit remembers it; the server says whether it still exists.
    const saved = entries[requirementId];
    const savedJob = useLiveJob(saved?.jobId ?? "");
    const [openedAt] = useState(() => Date.now());
    const result: PreparedFile | null =
        fresh ??
        (phase === "idle" && entryLive(saved, savedJob, openedAt)
            ? resultFromEntry(saved, examId, savedJob)
            : null);
    const live = useLiveJob(result?.job_id ?? "");
    const documents = ["certificate_scan", "identity_document"].includes(
        requirementType,
    );
    const photo = requirementType === "photograph";
    const tr = useTr();
    const consent = useUploadConsent();

    const submit = useCallback(
        async (chosen: File) => {
            if (challengeKey && !challengeToken) {
                setMessage(tr("Complete the verification before uploading.", "अपलोड से पहले जाँच पूरी करें।"));
                setPhase("error");
                return;
            }
            // A phone photograph of any size, or a WebP, is made into a JPEG the
            // engine takes before it is uploaded (DEC-103). PDFs pass untouched.
            const prepared = await prepareUpload(chosen);
            if (!prepared.ok) {
                setPhase("error");
                setMessage(uploadRefusal(prepared.reason));
                return;
            }
            const file = prepared.file;
            if (file.size > 5 * 1024 * 1024) {
                setPhase("error");
                setMessage(tr("Choose a PDF smaller than 5 MB.", "5 MB से छोटी PDF चुनें।"));
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
                    tr(
                        "Choose a JPEG, PNG or WebP image for this requirement.",
                        "इसके लिए JPEG, PNG या WebP फ़ोटो चुनें।",
                    ),
                );
                return;
            }
            // A PDF is a legitimate certificate upload, so the image-only check runs
            // for the requirements that genuinely take an image.
            if (file.type !== "application/pdf") {
                const check = validateImageFile(file);
                if (!check.valid) {
                    setPhase("error");
                    setMessage(check.error ?? tr("That file will not work.", "यह फ़ाइल नहीं चलेगी।"));
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
            const token = `prg_${randomHex()}`;
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
                setMessage(candidateError(error, tr));
            } finally {
                onWorking?.(false);
            }
        },
        [
            tr,
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

    if (result && (phase === "done" || phase === "idle")) {
        return (
            <>
                {/* DEC-095: offered only where switching shows a difference
                    a person can see; the engine withholds the alternate
                    otherwise, so there is nothing to switch to. */}
                {photo &&
                    result.enhancement_switchable &&
                    result.enhancement_enabled !== undefined &&
                    !["blocked", "not_produced"].includes(result.outcome) && (
                    <div className="euk-lighting">
                        <LightingSwitch
                            title={tr("Intelligent lighting", "समझदार रोशनी")}
                            checked={result.enhancement_enabled}
                            disabled={
                                switching ||
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
                                            : tr("Could not switch lighting.", "रोशनी बदली नहीं जा सकी।"),
                                    );
                                } finally {
                                    setSwitching(false);
                                    onWorking?.(false);
                                }
                            }}
                        />
                        <p role="status">
                            {switching
                                ? tr("Updating your preview…", "प्रीव्यू बदल रहा है…")
                                : !result.enhancement_enabled
                                  ? tr("Original lighting preserved.", "असली रोशनी जस की तस रखी गई।")
                                  : result.enhancements_applied?.length
                                    ? result.enhancements_applied.join(" · ")
                                    : tr("Your photograph needed no correction.", "आपकी फ़ोटो में किसी सुधार की ज़रूरत नहीं थी।")}
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
                    {PROMPT[requirementType]
                        ? tr(PROMPT[requirementType][0], PROMPT[requirementType][1])
                        : tr("Add your file", "अपनी फ़ाइल जोड़ें")}
                </button>
                {/* The camera, directly (owner's note, 16 September). An installed
                    app hands the picker to Android, which offers the camera only
                    when asked for one: a list of exact image types gets files
                    alone. `capture` asks for it; the front camera for a photo of
                    yourself, the back one for paper. Hidden where there is a
                    mouse, because a desktop has no camera to open this way. */}
                <button
                    type="button"
                    onClick={() => {
                        if (consent.allow()) cameraRef.current?.click();
                    }}
                    className="secondary-button euk-drop-camera"
                >
                    {photo ? tr("Take a photo now", "अभी फ़ोटो खींचें") : tr("Use the camera", "कैमरा इस्तेमाल करें")}
                </button>
                <input
                    ref={cameraRef}
                    type="file"
                    accept="image/*"
                    capture={photo ? "user" : "environment"}
                    className="sr-only"
                    tabIndex={-1}
                    aria-hidden="true"
                    onChange={(event) => {
                        const file = event.target.files?.[0];
                        if (file && consent.allow()) void submit(file);
                        event.target.value = "";
                    }}
                />
                <p className="euk-drop-hint">
                    {tr("or drop it here: JPEG, PNG, WebP up to 40 MB", "या यहाँ छोड़ें: JPEG, PNG, WebP, 40 MB तक")}
                    {documents ? tr("; PDF up to 5 MB", "; PDF 5 MB तक") : ""}
                </p>
                <input
                    ref={inputRef}
                    type="file"
                    accept={documents ? ACCEPT : "image/jpeg,image/png,image/webp"}
                    className="sr-only"
                    aria-label={tr(`Upload for ${requirementName}`, `${requirementName} के लिए अपलोड`)}
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
                        title={tr("Intelligent lighting adjustment", "रोशनी अपने-आप ठीक करें")}
                        label={tr("Intelligent lighting adjustment", "रोशनी अपने-आप ठीक करें")}
                        checked={enhancementEnabled}
                        onChange={setEnhancementEnabled}
                    />
                    <p>
                        {tr(
                            "Adjusts exposure and colour only when your photograph needs it, and you see the change before you download. No whitening, reshaping or beauty filters.",
                            "रोशनी और रंग तभी ठीक करता है जब फ़ोटो को ज़रूरत हो, और डाउनलोड से पहले आप बदलाव देखते हैं। कोई गोरापन, चेहरा बदलना या ब्यूटी फ़िल्टर नहीं।",
                        )}
                    </p>
                </div>
            )}
            <p className="euk-upload-note">
                {tr("Free. No account needed.", "मुफ़्त। कोई अकाउंट नहीं चाहिए।")}
            </p>
        </div>
    );
}
