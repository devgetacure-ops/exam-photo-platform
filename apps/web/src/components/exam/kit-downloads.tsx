"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { getApiBaseUrl, kitPackageDownloadUrl } from "../../lib/api-client";
import { getKit, type KitEntry } from "../../lib/kit-state";
import { bringIntoView, focusQuietly } from "../../lib/scroll";
import type { ExamDetail } from "../../lib/types";
import { Note } from "../euk/note";
import { EmailDelivery } from "./email-delivery";
import { ExpiryClock, FileRow, clock, jobDownloadable, type LiveJob } from "./kit-files";
import { KitSuccess } from "./kit-success";
import { publishCheckoutStage, publishJobs } from "./live-job-state";

/**
 * The kit's downloads, free (DEC-127).
 *
 * Every prepared file is the candidate's the moment it exists, so there is no
 * review, total or payment: the good wishes, the files, the deletion clock,
 * a copy by email and a WhatsApp reminder. The paid version of this screen is
 * `KitCheckout` in `src/billing/`, rendered instead while billing is on.
 */
export function KitDownloads({
    exam,
    entries,
    selectedRequirements,
    onPrepareAgain,
}: {
    exam: ExamDetail;
    entries: Record<string, KitEntry>;
    selectedRequirements?: string[];
    onPrepareAgain?: (requirementId: string) => void;
}) {
    const prepared = Object.values(entries).filter((e) =>
        ["prepared", "prepared_with_findings"].includes(e.outcome),
    );
    const files = prepared.filter(
        (e) => !selectedRequirements || selectedRequirements.includes(e.requirementId),
    );
    const completeKitSelected = prepared.length === files.length;
    const revisionKey = files.map((e) => `${e.jobId}:${e.updatedAt}`).join(",");
    const signature = files.map((e) => e.jobId).join(",");
    const [jobs, setJobs] = useState<Record<string, LiveJob>>({});
    const [error, setError] = useState("");
    const [note, setNote] = useState("");
    const [now, setNow] = useState(0);
    const [extending, setExtending] = useState<string | null>(null);
    const revision = useRef(0);
    const mounted = useRef(true);
    const headingRef = useRef<HTMLHeadingElement>(null);
    const kitId = files.length ? getKit(exam.exam_id)?.kitId : undefined;

    const refresh = useCallback(async () => {
        if (!signature) return;
        const version = ++revision.current;
        const ids = signature.split(",");
        const results = await Promise.allSettled(
            ids.map(async (id) => {
                const response = await fetch(
                    new URL(`/v1/jobs/${encodeURIComponent(id)}`, getApiBaseUrl()),
                    { cache: "no-store", signal: AbortSignal.timeout(15000) },
                );
                if (!response.ok) throw new Error(String(response.status));
                return (await response.json()) as LiveJob;
            }),
        );
        if (!mounted.current || version !== revision.current) return;
        const next: Record<string, LiveJob> = {};
        results.forEach((result, i) => {
            if (result.status === "fulfilled") next[ids[i]] = result.value;
        });
        setJobs(next);
        publishJobs(next);
        setNow(Date.now());
        setError(
            results.some((r) => r.status === "rejected")
                ? "Some files couldn’t be checked. Refresh the page to try again."
                : "",
        );
    }, [signature]);

    useEffect(() => {
        mounted.current = true;
        return () => {
            mounted.current = false;
        };
    }, []);
    useEffect(() => {
        let stopped = false;
        let poll: ReturnType<typeof setTimeout> | undefined;
        const check = async () => {
            await refresh();
            if (!stopped) poll = setTimeout(() => void check(), 5000);
        };
        const start = setTimeout(() => void check(), 0);
        return () => {
            stopped = true;
            clearTimeout(start);
            clearTimeout(poll);
        };
    }, [refresh, revisionKey]);
    useEffect(() => {
        const tick = setInterval(() => setNow(Date.now()), 1000);
        return () => clearInterval(tick);
    }, []);

    const ready = files.length > 0 && files.some((e) => jobs[e.jobId] && jobDownloadable(jobs[e.jobId], now));
    const stage = !files.length ? "empty" : "delivered";
    // The workspace reads this to say "Downloads" rather than "Review".
    useEffect(() => {
        publishCheckoutStage(exam.exam_id, stage);
    }, [exam.exam_id, stage]);

    // The first file to become ready is a change worth landing on; arriving
    // at a page that already has them is not.
    const shown = useRef<boolean | null>(null);
    useEffect(() => {
        const previous = shown.current;
        shown.current = ready;
        if (previous === null || previous || !ready) return;
        focusQuietly(headingRef.current);
        bringIntoView(headingRef.current?.closest("section") ?? null, { onlyIfNeeded: true });
    }, [ready]);

    const extend = async (id: string) => {
        setExtending(id);
        setError("");
        try {
            const response = await fetch(
                new URL(`/v1/jobs/${encodeURIComponent(id)}/extend`, getApiBaseUrl()),
                { method: "POST", cache: "no-store", signal: AbortSignal.timeout(15000) },
            );
            if (!response.ok) throw new Error("Could not keep this file for longer.");
            await refresh();
            setNote("The new deletion time is shown below.");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Could not keep this file for longer.");
        } finally {
            setExtending(null);
        }
    };

    if (stage === "empty")
        return (
            <section className="euk-review-empty" aria-labelledby="review-empty-title">
                <h2 id="review-empty-title" className="euk-review-empty-title">
                    Your downloads appear here
                </h2>
                <p>Prepare a file above and it lands here, ready to download. Free.</p>
            </section>
        );

    const deadlines = files
        .map((file) => Date.parse(jobs[file.jobId]?.expires_at ?? ""))
        .filter((value) => Number.isFinite(value));
    const earliest = deadlines.length ? Math.min(...deadlines) : null;
    const secondsLeft =
        earliest !== null && now > 0 ? Math.max(0, Math.ceil((earliest - now) / 1000)) : null;
    const deadline = earliest !== null ? clock(earliest) : null;
    const reminder = `My ${exam.exam_name} upload files are ready on ExamUploadKit.${deadline ? ` Download them before ${deadline}, in the browser I used.` : ""} ${typeof window !== "undefined" ? window.location.origin : ""}/exam/${exam.exam_id}`;

    return (
        <section className="euk-delivered" aria-labelledby="done-title">
            <KitSuccess examName={exam.exam_name} titleRef={headingRef} />
            <div className="euk-delivered-grid">
                <div className="min-w-0">
                    {secondsLeft !== null && earliest !== null && (
                        <ExpiryClock seconds={secondsLeft} at={earliest} delivered />
                    )}
                    <div className="euk-delivered-head">
                        <h3 id="kit-downloads">Your downloads</h3>
                        {completeKitSelected && kitId && files.length > 1 && (
                            <a className="primary-button" href={kitPackageDownloadUrl(kitId)}>
                                Download everything (ZIP)
                            </a>
                        )}
                    </div>
                    <ol className="euk-order-files">
                        {files.map((entry) => {
                            const requirement = exam.requirements?.find(
                                (r) => r.requirement_id === entry.requirementId,
                            );
                            return (
                                <FileRow
                                    key={entry.jobId}
                                    entry={entry}
                                    job={jobs[entry.jobId]}
                                    now={now}
                                    name={requirement?.requirement_name ?? entry.requirementType}
                                    partial={requirement?.platform_support === "partially_supported"}
                                    extending={extending}
                                    onExtend={() => void extend(entry.jobId)}
                                    onPrepareAgain={
                                        onPrepareAgain
                                            ? () => onPrepareAgain(entry.requirementId)
                                            : undefined
                                    }
                                />
                            );
                        })}
                    </ol>
                    <Note className="euk-delivered-note">
                        Save them somewhere you will find on the day you upload, not only in
                        Downloads.
                    </Note>
                    {error && (
                        <p className="euk-total-alert" role="alert">
                            {error}
                        </p>
                    )}
                    {note && (
                        <p className="euk-total-note" role="status">
                            {note}
                        </p>
                    )}
                </div>
                <aside className="euk-delivered-side" aria-label="Keep a copy">
                    {kitId && (
                        <EmailDelivery
                            kitId={kitId}
                            jobIds={files.map((file) => file.jobId)}
                            released
                        />
                    )}
                    <div className="euk-whatsapp">
                        <a
                            className="secondary-button"
                            href={`https://wa.me/?text=${encodeURIComponent(reminder)}`}
                            target="_blank"
                            rel="noreferrer"
                        >
                            Send yourself a reminder on WhatsApp
                        </a>
                        <p>WhatsApp carries the link and the deletion time, not the files.</p>
                    </div>
                    <p className="euk-order-help">
                        Something wrong with a file?{" "}
                        <Link className="euk-link" href="/support">
                            Tell us
                        </Link>
                        .
                    </p>
                </aside>
            </div>
        </section>
    );
}
