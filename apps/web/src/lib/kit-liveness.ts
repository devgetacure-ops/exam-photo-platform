/**
 * Whether a file the kit remembers is still a file (owner's testing, 1 October).
 *
 * The kit is this browser's memory of what was prepared (DEC-058). The server
 * deletes a prepared file thirty minutes later, an hour if asked to keep it,
 * and the kit used to go on calling it "Ready": the phone flow then led a
 * candidate to pay for a file that no longer existed and offered no way back.
 *
 * The server's word is final where there is one. Until it answers, the
 * deletion time the kit was given at preparation decides, which is right
 * unless the file was kept for longer, and the server's answer corrects that
 * within a moment of the screen opening.
 */

import type { KitEntry } from "./kit-state";
import type { PreparedFile } from "./journey-client";

/** What the server says about a job, as far as liveness goes. */
export interface JobLife {
    status: string;
    expires_at?: string | null;
}

export function entryPrepared(entry: KitEntry | undefined): entry is KitEntry {
    return !!entry && ["prepared", "prepared_with_findings"].includes(entry.outcome);
}

function past(iso: string | null | undefined, now: number): boolean {
    if (!iso) return false;
    const time = Date.parse(iso);
    return Number.isFinite(time) && time <= now;
}

/** The server has said this job's file is gone. */
export function jobGone(job: JobLife, now: number): boolean {
    return job.status.toLowerCase() === "deleted" || past(job.expires_at, now);
}

/**
 * A prepared entry whose file can still be previewed, paid for and downloaded.
 * `job` is the server's latest answer, or undefined while it has not answered.
 */
export function entryLive(
    entry: KitEntry | undefined,
    job: JobLife | undefined,
    now: number,
): entry is KitEntry {
    if (!entryPrepared(entry)) return false;
    if (job) return !jobGone(job, now);
    return !past(entry.expiresAt, now);
}

/**
 * The remembered entry in the shape the result view takes, so a candidate who
 * comes back to a ready file sees that file and not an empty upload form.
 */
export function resultFromEntry(entry: KitEntry, examId: string, job?: JobLife): PreparedFile {
    return {
        job_id: entry.jobId,
        exam_id: examId,
        requirement_id: entry.requirementId,
        requirement_type: entry.requirementType as PreparedFile["requirement_type"],
        platform_support: "supported" as PreparedFile["platform_support"],
        status: entry.status,
        outcome: entry.outcome,
        expires_at: job?.expires_at ?? entry.expiresAt ?? null,
        output_url: entry.outputUrl ?? null,
        output_filename: entry.outputFilename ?? null,
        output_media_type: entry.outputMediaType ?? null,
        report_url: entry.reportUrl ?? null,
        preview_url: entry.previewUrl ?? null,
        preview_watermarked: !!entry.previewUrl,
        findings: entry.findings ?? [],
        issue_codes: [],
    };
}
