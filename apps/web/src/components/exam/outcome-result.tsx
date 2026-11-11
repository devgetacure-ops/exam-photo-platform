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
import { useLocale, useTr } from "../locale-context";
import { toolText } from "../../lib/i18n-tool";
import { BILLING_ENABLED } from "../../billing/config";
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
    const tr = useTr();
    const locale = useLocale();
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
                <p className="euk-outcome-title">{tr("This file has expired.", "इस फ़ाइल का समय ख़त्म हो गया।")}</p>
                <p className="euk-outcome-text">
                    {tr(
                        "The preview and download are no longer available. Prepare it again to start a new retention window.",
                        "प्रीव्यू और डाउनलोड अब उपलब्ध नहीं हैं। इसे फिर से तैयार करें।",
                    )}
                </p>
                <button className="secondary-button" onClick={onReplace}>
                    {tr("Prepare again", "फिर से तैयार करें")}
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
                    <p className="euk-outcome-title">{tr("We could not prepare this one", "यह फ़ाइल तैयार नहीं हो सकी")}</p>
                </div>
                <ul>
                    {(() => {
                        const lines = plainFindings(
                            result.issue_codes.length > 0 ? result.issue_codes : result.findings,
                        );
                        return lines.length > 0 ? lines : [issueText("")];
                    })().map((line) => (
                        <li key={line}>{toolText(locale, line)}</li>
                    ))}
                </ul>
                <p className="euk-outcome-text">
                    {BILLING_ENABLED && "Nothing has been charged. "}
                    {photo
                        ? toolText(locale, RETAKE_GUIDANCE)
                        : tr("Try a different file and we will have another go.", "कोई दूसरी फ़ाइल आज़माएँ, हम फिर कोशिश करेंगे।")}
                </p>
                <button type="button" className="secondary-button" onClick={onReplace}>
                    {tr("Try another file", "दूसरी फ़ाइल आज़माएँ")}
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
                            ? tr("Partly prepared — further steps needed", "कुछ हद तक तैयार, आगे के कदम बाकी")
                            : hasFindings
                              ? tr("Ready — with something to check", "तैयार, पर कुछ देख लें")
                              : tr("Ready", "तैयार")}
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
                    {tr("Replace", "बदलें")}
                </button>
            </div>

            {/*
                With billing on (DEC-063) the preview is watermarked and served
                at reduced resolution; the clean file is what the candidate
                buys. Free (DEC-127) the engine serves a clean preview and the
                file itself downloads from the kit below.
            */}
            {sourceUrl && result.preview_url ? (
                <FileComparison
                    before={sourceUrl}
                    after={new URL(result.preview_url, getApiBaseUrl()).toString()}
                />
            ) : (
                result.preview_url && (
                    <figure className="euk-outcome-preview">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                            src={new URL(result.preview_url, getApiBaseUrl()).toString()}
                            onContextMenu={
                                result.preview_watermarked
                                    ? (event) => event.preventDefault()
                                    : undefined
                            }
                            draggable={false}
                            alt={tr(`Prepared ${requirementName}`, `तैयार ${requirementName}`)}
                        />
                        {result.preview_watermarked && (
                            <figcaption>Preview — watermarked until you buy it.</figcaption>
                        )}
                    </figure>
                )
            )}

            {result.output_url && !result.preview_url && (
                <p className="euk-outcome-text">
                    {result.output_media_type === "application/pdf"
                        ? tr(
                              "PDF prepared. We couldn’t make a picture of it this time, so check its details after you download it.",
                              "PDF तैयार है। इस बार इसकी तस्वीर नहीं बन सकी, इसलिए डाउनलोड के बाद इसे जाँच लें।",
                          )
                        : tr(
                              "Your file was prepared. A preview is not available this time; check the download.",
                              "आपकी फ़ाइल तैयार है। इस बार प्रीव्यू नहीं है, डाउनलोड करके जाँच लें।",
                          )}
                </p>
            )}

            {expiry && !Number.isNaN(expiry.getTime()) && (
                <p className="euk-outcome-expiry">
                    {tr("Scheduled for deletion at", "हटाने का समय:")}{" "}
                    <time dateTime={deadline ?? undefined} suppressHydrationWarning>
                        {expiry.toLocaleTimeString([], {
                            hour: "numeric",
                            minute: "2-digit",
                        })}
                    </time>
                    {tr(". Extension options are in your kit below.", "। समय बढ़ाने का विकल्प नीचे आपकी किट में है।")}
                </p>
            )}

            {hasFindings && substantive.length > 0 && (
                <div className="euk-outcome-block">
                    <p className="euk-outcome-sub">{tr("Worth checking before you submit", "जमा करने से पहले देख लें")}</p>
                    <ul>
                        {substantive.map((finding) => (
                            <li key={finding}>{toolText(locale, finding)}</li>
                        ))}
                    </ul>
                </div>
            )}

            {routine.length > 0 && (
                <details className="euk-outcome-changes">
                    <summary>{tr(`What we changed (${routine.length})`, `हमने क्या बदला (${routine.length})`)}</summary>
                    <ul>
                        {routine.map((finding) => (
                            <li key={finding}>{toolText(locale, ROUTINE_NOTES[finding])}</li>
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
                    <p className="euk-outcome-sub">{tr("What we noticed", "हमने क्या देखा")}</p>
                    <ul>
                        {plainFindings(result.issue_codes).map((line) => (
                            <li key={line}>{toolText(locale, line)}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}
