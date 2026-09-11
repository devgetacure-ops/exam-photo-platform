import { getApiBaseUrl } from "./api-client";
import type { PrepareRequirementResponse } from "./types";

/** Additive DEC-072/074/075/076 contracts, isolated from the engine-owned client. */
export interface LightingState {
    enhancement_enabled?: boolean;
    enhancement_switchable?: boolean;
    enhancements_applied?: string[];
    preview_url?: string | null;
    preview_watermarked?: boolean;
    byte_size?: number | null;
    updated_at?: string;
}
export type PreparedFile = PrepareRequirementResponse & LightingState;
export interface PreparationProgress {
    fraction: number;
    label: string;
    stage: string;
    finished: boolean;
    failed: boolean;
    /** Engine stage names already done, in order (DEC-075). */
    completed_stages?: string[];
}
export interface EmailReceipt {
    sent: boolean;
    masked_address: string;
    job_ids: string[];
    filenames: string[];
}

export async function journeyRequest<T>(
    path: string,
    body?: unknown,
    signal?: AbortSignal,
): Promise<T> {
    const response = await fetch(new URL(path, getApiBaseUrl()), {
        method: body === undefined ? "GET" : "POST",
        cache: "no-store",
        signal: signal ?? AbortSignal.timeout(20000),
        ...(body === undefined
            ? {}
            : {
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(body),
              }),
    });
    if (!response.ok) {
        const messages: Record<number, string> = {
            403: "Please complete the verification and try again.",
            404: "This file is no longer available. Please prepare it again.",
            409: "This option is no longer available for this file. Refresh its status.",
            422: "We couldn’t send these files. Check the email address and file availability, then try again.",
            429: "Preparation is busy. Please wait a moment before trying again.",
        };
        throw new Error(
            messages[response.status] ??
                "We couldn’t reach this service. Please try again.",
        );
    }
    return response.json() as Promise<T>;
}

export function switchLighting(jobId: string, enabled: boolean) {
    return journeyRequest<LightingState>(
        `/v1/jobs/${encodeURIComponent(jobId)}/enhancement`,
        { enabled },
    );
}

export function emailKit(kitId: string, address: string, jobIds: string[]) {
    return journeyRequest<EmailReceipt>(
        `/v1/kits/${encodeURIComponent(kitId)}/email`,
        { address, job_ids: jobIds },
    );
}
