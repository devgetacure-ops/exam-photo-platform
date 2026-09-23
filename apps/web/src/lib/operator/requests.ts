import { readFile, readdir } from "node:fs/promises";
import path from "node:path";

/**
 * The requests candidates send through the form, read for the operator page
 * (DEC-108). Read-only: nothing here deletes a request early. The address is
 * masked here; the full one goes only to the support mailbox (euk-watch).
 */

export interface StoredRequest {
    reference: string;
    kind: "exam" | "support";
    exam: string;
    message: string;
    maskedEmail: string;
    createdAt: string;
    expiresAt: string;
}

export function maskEmail(address: string): string {
    const at = address.lastIndexOf("@");
    if (at < 1) return "***";
    return `${address[0]}***${address.slice(at)}`;
}

export function requestsDirectory(env: Record<string, string | undefined> = process.env) {
    return env.UPLOADREADY_REQUESTS_DIR ?? path.join(process.cwd(), ".data", "requests");
}

export async function readRequests(
    directory: string,
    now: number = Date.now(),
): Promise<StoredRequest[]> {
    let names: string[];
    try {
        names = await readdir(directory);
    } catch {
        return [];
    }
    const found: StoredRequest[] = [];
    for (const name of names.filter((n) => /^[a-f0-9]{64}\.json$/.test(n))) {
        try {
            const record = JSON.parse(await readFile(path.join(directory, name), "utf8"));
            if (Date.parse(record.expires_at) <= now) continue;
            found.push({
                reference: String(record.reference ?? ""),
                kind: record.kind === "support" ? "support" : "exam",
                exam: String(record.exam ?? ""),
                message: String(record.message ?? ""),
                maskedEmail: maskEmail(String(record.email ?? "")),
                createdAt: String(record.created_at ?? ""),
                expiresAt: String(record.expires_at ?? ""),
            });
        } catch {
            /* An unreadable record has nothing to show. */
        }
    }
    return found.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}
