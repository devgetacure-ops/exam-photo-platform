"use client";

import { getApiBaseUrl, jobOutputUrl } from "../../lib/api-client";
import type { KitEntry } from "../../lib/kit-state";
import { plainFindings } from "../../lib/finding-text";
import { FileTypeDrawing } from "../euk/doodles";
import { PreviewThumb } from "./preview-thumb";
import { useLocale, useTr } from "../locale-context";
import { toolText } from "../../lib/i18n-tool";

/**
 * A kit's prepared files and their deletion clock, shared by the free
 * downloads view (`kit-downloads.tsx`) and the paid checkout kept in
 * `src/billing/` (DEC-127).
 */

// Additive engine contracts, kept in the UI lane pending shared-client coordination.
export interface LiveJob {
    job_id: string;
    status: string;
    entitlement?: string;
    expires_at?: string | null;
    extendable?: boolean;
    output_filename?: string | null;
    output_url?: string | null;
}

export function jobExpired(job: LiveJob, now: number): boolean {
    return (
        job.status.toLowerCase() === "deleted" ||
        (!!job.expires_at && Date.parse(job.expires_at) <= now)
    );
}
export function jobDownloadable(job: LiveJob, now: number): boolean {
    return (
        job.entitlement === "released" &&
        !!job.expires_at &&
        Number.isFinite(Date.parse(job.expires_at)) &&
        !jobExpired(job, now) &&
        !!job.output_url
    );
}

export const clock = (ms: number) =>
    new Date(ms).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

/** The file retention window a fresh preparation gets, for the clock's bar. */
const WINDOW_SECONDS = 30 * 60;

/** Each digit in a box of its own width, so the text beside the clock never moves. */
function Digits({ value }: { value: string }) {
    return (
        <>
            {value.split("").map((digit, i) => (
                <span key={i} className="euk-clock-digit">
                    {digit}
                </span>
            ))}
        </>
    );
}

export function ExpiryClock({
    seconds,
    at,
    delivered,
}: {
    seconds: number;
    at: number;
    delivered: boolean;
}) {
    const tr = useTr();
    const minutes = Math.floor(seconds / 60);
    const rest = seconds % 60;
    return (
        <div className="euk-clock" data-urgent={seconds < 5 * 60}>
            <div className="euk-clock-row">
                <p className="euk-clock-figure" aria-hidden="true">
                    <Digits value={String(minutes).padStart(2, "0")} />
                    <span className="euk-clock-colon">:</span>
                    <Digits value={String(rest).padStart(2, "0")} />
                </p>
                <div className="min-w-0">
                    <p className="euk-clock-title">
                        {delivered
                            ? tr(`Download them before ${clock(at)}`, `${clock(at)} से पहले डाउनलोड कर लें`)
                            : tr(`Deleted at ${clock(at)}`, `${clock(at)} पर हट जाएँगी`)}
                    </p>
                    <p className="euk-clock-text">
                        {delivered
                            ? tr(
                                  "After that they are deleted from our side and can’t be recovered. An emailed copy stays in your inbox.",
                                  "उसके बाद ये हमारी तरफ़ से हट जाती हैं और वापस नहीं मिलतीं। ईमेल की गई कॉपी आपके इनबॉक्स में रहती है।",
                              )
                            : tr(
                                  "Files are deleted within 30 minutes of being prepared, or within an hour if you ask us to keep them. Download or email them straight after.",
                                  "फ़ाइलें तैयार होने के 30 मिनट में हट जाती हैं, या कहने पर एक घंटे में। तैयार होते ही डाउनलोड या ईमेल कर लें।",
                              )}
                    </p>
                </div>
            </div>
            <span className="euk-clock-bar" aria-hidden="true">
                <span
                    style={{
                        transform: `scaleX(${Math.min(1, seconds / WINDOW_SECONDS)})`,
                    }}
                />
            </span>
        </div>
    );
}

export function FileRow({
    entry,
    job,
    now,
    name,
    partial,
    reason,
    extending,
    onExtend,
    onPrepareAgain,
}: {
    entry: KitEntry;
    job?: LiveJob;
    now: number;
    name: string;
    partial: boolean;
    reason?: string;
    extending: string | null;
    onExtend: () => void;
    /** Opens this file's own screen, where it can be added again. */
    onPrepareAgain?: () => void;
}) {
    const tr = useTr();
    const locale = useLocale();
    const expired = !!job && jobExpired(job, now);
    const available = !!job && jobDownloadable(job, now);
    const notes = plainFindings(entry.findings);
    const seconds =
        job?.expires_at && now > 0
            ? Math.max(0, Math.ceil((Date.parse(job.expires_at) - now) / 1000))
            : null;
    return (
        <li
            className="euk-order-file"
            data-state={expired ? "expired" : available ? "released" : "protected"}
            data-thumb={(entry.previewUrl && !expired) || undefined}
        >
            {entry.previewUrl && !expired ? (
                <PreviewThumb
                    src={new URL(entry.previewUrl, getApiBaseUrl()).toString()}
                    name={name}
                />
            ) : (
                <FileTypeDrawing type={entry.requirementType} className="euk-order-icon" />
            )}
            <div className="euk-order-body">
                <h3 className="euk-order-name">{name}</h3>
                <p className="euk-order-filename">
                    {job?.output_filename ?? entry.outputFilename}
                </p>
                <p className="euk-order-status">
                    {expired
                        ? tr("Expired — prepare this file again", "समय ख़त्म, यह फ़ाइल फिर से तैयार करें")
                        : available
                          ? tr("Ready to download", "डाउनलोड के लिए तैयार")
                          : job
                            ? "Protected until payment is confirmed"
                            : tr("Checking availability…", "जाँच रहे हैं…")}
                    {!expired && seconds !== null && (
                        <span className="euk-order-countdown">
                            {" "}
                            {tr(
                                `· deletes in ${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, "0")}s`,
                                `· ${Math.floor(seconds / 60)} मिनट ${String(seconds % 60).padStart(2, "0")} सेकंड में हटेगी`,
                            )}
                        </span>
                    )}
                </p>
                {reason === "document_work_is_free" && (
                    <p className="euk-order-free">
                        Document preparation included free with your purchase
                    </p>
                )}
                {entry.outputMediaType === "application/pdf" && !entry.previewUrl && (
                    <p className="euk-order-meta">PDF · no visual preview available</p>
                )}
                {partial && (
                    <p className="euk-order-meta">
                        {tr(
                            "Partly prepared — your exam still requires additional steps. Review its instructions.",
                            "कुछ हद तक तैयार, आपकी परीक्षा में अभी और कदम बाकी हैं। उसके निर्देश देख लें।",
                        )}
                    </p>
                )}
                {notes.length > 0 && (
                    <details className="euk-order-findings">
                        <summary>{tr(`Worth a look (${notes.length})`, `एक बार देख लें (${notes.length})`)}</summary>
                        <ul>
                            {notes.map((note) => (
                                <li key={note}>{toolText(locale, note)}</li>
                            ))}
                        </ul>
                    </details>
                )}
            </div>
            <div className="euk-order-actions">
                {/* An expired file used to be a dead end here: the row said
                    to prepare it again and offered nowhere to do it (owner's
                    testing, 1 October). */}
                {expired && onPrepareAgain && (
                    <button type="button" className="primary-button" onClick={onPrepareAgain}>
                        {tr("Prepare it again", "फिर से तैयार करें")}
                    </button>
                )}
                {available && (
                    <a className="primary-button" href={jobOutputUrl(entry.jobId)}>
                        {tr("Download file", "फ़ाइल डाउनलोड करें")}
                    </a>
                )}
                {job?.extendable && !expired && (
                    <button
                        type="button"
                        className="secondary-button"
                        disabled={extending !== null}
                        onClick={onExtend}
                    >
                        {extending === entry.jobId ? tr("Extending…", "समय बढ़ा रहे हैं…") : tr("Keep for longer", "ज़्यादा देर रखें")}
                    </button>
                )}
            </div>
        </li>
    );
}
