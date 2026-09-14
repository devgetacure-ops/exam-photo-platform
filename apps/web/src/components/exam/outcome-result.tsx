"use client";

import { useEffect, useState } from "react";

import { getApiBaseUrl } from "../../lib/api-client";
import type { PrepareRequirementResponse } from "../../lib/types";
import { formatBytes } from "../../lib/spec-format";
import {
    RETAKE_GUIDANCE,
    ROUTINE_NOTES,
    isRoutine,
    issueText,
    plainFindings,
} from "../../lib/finding-text";
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

    // Only what a candidate should read; routine changes (hidden camera data
    // removed, colour mode converted) are listed quietly and never earn the
    // findings state (testing notes 15, 17).
    const substantive = plainFindings(result.findings);
    const routine = [
        ...new Set([...result.findings, ...(result.changes ?? [])].filter(isRoutine)),
    ];
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
                    {(() => {
                        const lines = plainFindings(
                            result.issue_codes.length > 0 ? result.issue_codes : result.findings,
                        );
                        return lines.length > 0 ? lines : [issueText("")];
                    })().map((line) => (
                        <li key={line}>{line}</li>
                    ))}
                </ul>
                <p className="euk-outcome-text">
                    Nothing has been charged.{" "}
                    {photo
                        ? RETAKE_GUIDANCE
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
                        {plainFindings(result.issue_codes).map((line) => (
                            <li key={line}>{line}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}
