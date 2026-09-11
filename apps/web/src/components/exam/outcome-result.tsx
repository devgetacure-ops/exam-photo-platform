"use client";

import { useEffect, useState } from "react";

import { getApiBaseUrl } from "../../lib/api-client";
import type { PrepareRequirementResponse } from "../../lib/types";
import { formatBytes } from "../../lib/spec-format";
import { FileComparison } from "../file-comparison";
import { useLiveJob } from "./live-job-state";
import { Cross, Tick } from "./specimen-sheet";

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
 * its own mark, its own words, and its own next action.
 */

interface Props {
    result: PrepareRequirementResponse;
    requirementName: string;
    onReplace: () => void;
    sourceUrl?: string | null;
    partiallySupported?: boolean;
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
    INPUT_METADATA_REMOVED:
        "Removed the hidden data your camera saved in the file.",
    INPUT_COLOUR_MODE_CONVERTED:
        "Converted the colour mode for the exam's format.",
    INPUT_ICC_PROFILE_INVALID: "Replaced a broken colour profile.",
    INPUT_ORIENTATION_METADATA_INVALID: "Corrected the image's rotation.",
    INPUT_EXTENSION_MISMATCH:
        "The file extension did not match its actual format.",
};

function isRoutine(finding: string): boolean {
    return finding in ROUTINE_NOTES;
}

/**
 * Engine issue codes, said the way a person would say them.
 *
 * The engine reports its suitability checks as `SUITABILITY_*`. The earlier
 * table only knew an older vocabulary, so a blocked photograph read as
 * "suitability no face" to the candidate.
 */
const ISSUE_TEXT: Record<string, string> = {
    NO_FACE_DETECTED: "We could not find a face in this photo.",
    MULTIPLE_FACES: "There is more than one face in this photo.",
    FACE_TOO_SMALL: "The face is too small in the frame — move closer.",
    IMAGE_TOO_BLURRY: "The photo is too blurry to use.",
    IMAGE_TOO_DARK: "The photo is too dark.",
    IMAGE_TOO_BRIGHT: "The photo is too bright.",
    EYES_CLOSED: "The eyes look closed.",
    SUITABILITY_NO_FACE: "We could not find a face in this photo.",
    SUITABILITY_MULTIPLE_FACES: "There is more than one face in this photo.",
    SUITABILITY_FACE_REGION_TOO_SMALL:
        "The face is too small in the frame. Use a photo taken closer.",
    SUITABILITY_RESOLUTION_TOO_LOW:
        "The photo is too small to prepare. Use the original from the camera, not a screenshot or a forwarded copy.",
    SUITABILITY_BLUR_SEVERE: "The photo is too blurry to use.",
    SUITABILITY_BLUR_WARNING: "The photo is slightly blurred.",
    SUITABILITY_UNDEREXPOSED_SEVERE: "The photo is too dark.",
    SUITABILITY_UNDEREXPOSED_WARNING: "The photo is a little dark.",
    SUITABILITY_OVEREXPOSED_SEVERE: "The photo is too bright.",
    SUITABILITY_OVEREXPOSED_WARNING: "The photo is a little bright.",
    SUITABILITY_POSE_EXTREME: "The face is turned too far from the camera.",
    SUITABILITY_POSE_WARNING: "The face is turned slightly from the camera.",
    SUITABILITY_HEAD_TOP_CLIPPED: "The top of the head is cut off.",
    SUITABILITY_HEAD_SIDE_CLIPPED: "The side of the head is cut off.",
    SUITABILITY_CHIN_CLIPPED: "The chin is cut off.",
    SUITABILITY_EYES_NOT_VISIBLE: "The eyes are not clearly visible.",
    SUITABILITY_FACE_OCCLUDED: "Something is covering part of the face.",
};

function humanIssue(code: string): string {
    if (ISSUE_TEXT[code]) return ISSUE_TEXT[code];
    const words = code.replace(/^SUITABILITY_/, "").toLowerCase().replace(/_/g, " ");
    return words.charAt(0).toUpperCase() + words.slice(1);
}

function Caution() {
    return (
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round" aria-hidden="true">
            <path d="M10 4 V 11 M10 15.5 V 15.6" />
        </svg>
    );
}

export function OutcomeResult({
    result,
    requirementName,
    onReplace,
    sourceUrl,
    partiallySupported = false,
}: Props) {
    const live = useLiveJob(result.job_id);
    const [now, setNow] = useState(0);
    useEffect(() => {
        const timer = setInterval(() => setNow(Date.now()), 1000);
        return () => clearInterval(timer);
    }, []);
    const blocked =
        result.outcome === "blocked" || result.outcome === "not_produced";

    const substantive = result.findings.filter(
        (finding) => !isRoutine(finding),
    );
    const routine = result.findings.filter(isRoutine);
    const deadline = live?.expires_at ?? result.expires_at;
    const expiry = deadline ? new Date(deadline) : null;
    const expired =
        live?.status.toLowerCase() === "deleted" ||
        (expiry && expiry.getTime() <= now);
    // The API's outcome is authoritative about whether a file was produced; what
    // counts as worth the candidate's attention is a presentation judgement, and
    // routine normalisation is not it.
    const hasFindings =
        partiallySupported ||
        result.is_valid === false ||
        (result.outcome === "prepared_with_findings" && substantive.length > 0);
    const photo = result.requirement_type === "photograph";

    if (expired)
        return (
            <div className="euk-outcome euk-outcome--expired">
                <p className="euk-outcome-title">This file has expired.</p>
                <p className="euk-outcome-text">
                    The preview and download are no longer available. Prepare it
                    again to start a new retention window.
                </p>
                <button className="secondary-button" onClick={onReplace}>
                    Prepare again
                </button>
            </div>
        );

    if (blocked) {
        return (
            <div className="euk-outcome euk-outcome--blocked">
                <div className="euk-outcome-head">
                    <span className="euk-outcome-mark" aria-hidden="true">
                        <Cross />
                    </span>
                    <p className="euk-outcome-title">We could not prepare this one</p>
                </div>
                <ul>
                    {(result.issue_codes.length > 0
                        ? result.issue_codes.map(humanIssue)
                        : result.findings
                    ).map((line) => (
                        <li key={line}>{line}</li>
                    ))}
                </ul>
                <p className="euk-outcome-text">
                    Nothing has been charged.{" "}
                    {photo
                        ? "Try a different photo and we will have another go."
                        : "Try a different file and we will have another go."}
                </p>
                <button type="button" className="secondary-button" onClick={onReplace}>
                    Try another file
                </button>
            </div>
        );
    }

    return (
        <div
            className={`euk-outcome ${hasFindings ? "euk-outcome--findings" : "euk-outcome--ready"}`}
        >
            <div className="euk-outcome-head">
                <span className="euk-outcome-mark" aria-hidden="true">
                    {hasFindings ? <Caution /> : <Tick />}
                </span>
                <div className="min-w-0">
                    <p className="euk-outcome-title">
                        {partiallySupported
                            ? "Partly prepared — further steps needed"
                            : hasFindings
                              ? "Ready — with something to check"
                              : "Ready"}
                    </p>
                    <p className="euk-outcome-spec">
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
                <button type="button" onClick={onReplace} className="euk-outcome-replace">
                    Replace
                </button>
            </div>

            {/*
                The preview is watermarked and served at reduced resolution by
                the service; the clean file is what the candidate buys. That is
                the protection that actually works — blocking right-click stops
                nobody and would make a page selling precision feel cheap.
            */}
            {sourceUrl && result.preview_url && result.preview_watermarked === true ? (
                <FileComparison
                    before={sourceUrl}
                    after={new URL(result.preview_url, getApiBaseUrl()).toString()}
                />
            ) : (
                result.preview_url &&
                result.preview_watermarked === true && (
                    <figure className="euk-outcome-preview">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                            src={new URL(result.preview_url, getApiBaseUrl()).toString()}
                            onContextMenu={(event) => event.preventDefault()}
                            draggable={false}
                            alt={`Prepared ${requirementName}`}
                        />
                        <figcaption>Preview — watermarked until you buy it.</figcaption>
                    </figure>
                )
            )}

            {result.output_url &&
                !(result.preview_url && result.preview_watermarked === true) && (
                    <p className="euk-outcome-text">
                        {result.output_media_type === "application/pdf"
                            ? "PDF prepared. A visual preview is not available: review the file details and findings before purchasing."
                            : "Your file was prepared. A protected preview is not available yet."}
                    </p>
                )}

            {expiry && !Number.isNaN(expiry.getTime()) && (
                <p className="euk-outcome-expiry">
                    Scheduled for deletion at{" "}
                    <time dateTime={deadline ?? undefined} suppressHydrationWarning>
                        {expiry.toLocaleTimeString([], {
                            hour: "numeric",
                            minute: "2-digit",
                        })}
                    </time>
                    . Extension options are in your kit below.
                </p>
            )}

            {hasFindings && substantive.length > 0 && (
                <div className="euk-outcome-block">
                    <p className="euk-outcome-sub">Worth checking before you submit</p>
                    <ul>
                        {substantive.map((finding) => (
                            <li key={finding}>{finding}</li>
                        ))}
                    </ul>
                </div>
            )}

            {routine.length > 0 && (
                <details className="euk-outcome-changes">
                    <summary>What we changed ({routine.length})</summary>
                    <ul>
                        {routine.map((finding) => (
                            <li key={finding}>{ROUTINE_NOTES[finding]}</li>
                        ))}
                    </ul>
                </details>
            )}

            {/*
                A file that exists but that the platform could not fully verify
                is not a clean pass, and DEC-056 forbids collapsing that into
                one. Said in the candidate's terms, next to the file rather than
                in a report they will not open.
            */}
            {result.is_valid === false && result.issue_codes.length > 0 && (
                <div className="euk-outcome-block">
                    <p className="euk-outcome-sub">What we noticed</p>
                    <ul>
                        {result.issue_codes.map((code) => (
                            <li key={code}>{humanIssue(code)}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}
