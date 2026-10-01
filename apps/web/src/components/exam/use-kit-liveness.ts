"use client";

import { useEffect, useMemo, useState } from "react";

import { getApiBaseUrl } from "../../lib/api-client";
import { entryLive, entryPrepared, jobGone, type JobLife } from "../../lib/kit-liveness";
import type { KitEntry } from "../../lib/kit-state";
import { publishJobs } from "./live-job-state";

/**
 * Ask the server which of the kit's prepared files still exist, and drop the
 * ones that do not (see `lib/kit-liveness.ts`).
 *
 * Asked when the screen opens, when the app comes back to the front, and once
 * a minute while it stays open. A file the server reports deleted is forgotten
 * from the kit, so every screen agrees it has to be added again.
 */
export function useKitLiveness(
    entries: Record<string, KitEntry>,
    forget: (requirementId: string) => void,
): { isLive: (requirementId: string) => boolean; expired: ReadonlySet<string> } {
    const [jobs, setJobs] = useState<Record<string, JobLife>>({});
    const [now, setNow] = useState(() => Date.now());
    // Requirements whose file expired while this screen was open, so the row
    // can say so instead of silently reverting to "Not added yet".
    const [expired, setExpired] = useState<ReadonlySet<string>>(() => new Set());

    const prepared = useMemo(
        () => Object.values(entries).filter(entryPrepared),
        [entries],
    );
    const signature = prepared.map((e) => `${e.requirementId}:${e.jobId}`).join("|");

    useEffect(() => {
        if (!signature) return;
        let stopped = false;
        const pairs = signature.split("|").map((pair) => pair.split(":") as [string, string]);

        const ask = async () => {
            const answers = await Promise.all(
                pairs.map(async ([requirementId, jobId]) => {
                    try {
                        const response = await fetch(
                            new URL(`/v1/jobs/${encodeURIComponent(jobId)}`, getApiBaseUrl()),
                            { cache: "no-store", signal: AbortSignal.timeout(15000) },
                        );
                        // A job the server no longer knows is as gone as a deleted one.
                        if (response.status === 404)
                            return [requirementId, jobId, { status: "deleted" }] as const;
                        if (!response.ok) return null;
                        return [requirementId, jobId, (await response.json()) as JobLife] as const;
                    } catch {
                        return null; // Offline: the stored deletion time decides.
                    }
                }),
            );
            if (stopped) return;
            const at = Date.now();
            const known: Record<string, JobLife> = {};
            const gone: string[] = [];
            for (const answer of answers) {
                if (!answer) continue;
                const [requirementId, jobId, job] = answer;
                known[jobId] = job;
                if (jobGone(job, at)) gone.push(requirementId);
            }
            setNow(at);
            setJobs((old) => ({ ...old, ...known }));
            publishJobs(
                Object.fromEntries(
                    Object.entries(known).map(([jobId, job]) => [jobId, { job_id: jobId, ...job }]),
                ),
            );
            if (gone.length > 0) {
                setExpired((old) => new Set([...old, ...gone]));
                gone.forEach(forget);
            }
        };

        void ask();
        const timer = setInterval(() => void ask(), 60_000);
        const onVisible = () => {
            if (document.visibilityState === "visible") void ask();
        };
        document.addEventListener("visibilitychange", onVisible);
        return () => {
            stopped = true;
            clearInterval(timer);
            document.removeEventListener("visibilitychange", onVisible);
        };
    }, [signature, forget]);

    return {
        isLive: (requirementId) => {
            const entry = entries[requirementId];
            return entryLive(entry, entry ? jobs[entry.jobId] : undefined, now);
        },
        expired,
    };
}
