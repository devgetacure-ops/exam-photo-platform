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

/**
 * Where the checkout for an examination is: the workspace above it reads this
 * so it never offers "Review and pay" for files already paid for (testing
 * note 11). Published by `KitCheckout`, which is the only thing that knows.
 */
export type CheckoutStage = "empty" | "review" | "paying" | "failed" | "delivered";

const stages = new Map<string, CheckoutStage>();

export function publishCheckoutStage(examId: string, stage: CheckoutStage) {
    if (stages.get(examId) === stage) return;
    stages.set(examId, stage);
    listeners.forEach((listener) => listener());
}

export function useCheckoutStage(examId: string): CheckoutStage | undefined {
    return useSyncExternalStore(
        subscribe,
        () => stages.get(examId),
        () => undefined,
    );
}
