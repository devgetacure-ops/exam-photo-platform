"use client";
import { useSyncExternalStore } from "react";
import type { LiveJob } from "./kit-checkout";

// Share authoritative polling results with previews. Never persist image bytes.
const jobs = new Map<string, LiveJob>();
const listeners = new Set<() => void>();
export function publishJobs(next: Record<string, LiveJob>) {
    for (const [id, job] of Object.entries(next)) jobs.set(id, job);
    listeners.forEach((listener) => listener());
}
function subscribe(listener: () => void) {
    listeners.add(listener);
    return () => {
        listeners.delete(listener);
    };
}
export function useLiveJob(id: string) {
    return useSyncExternalStore(
        subscribe,
        () => jobs.get(id),
        () => undefined,
    );
}
