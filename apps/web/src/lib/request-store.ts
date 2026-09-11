import { createHash, randomUUID } from "node:crypto";
import { mkdir, open, readFile, readdir, unlink } from "node:fs/promises";
import path from "node:path";

export interface CandidateRequest {
    kind: "exam" | "support";
    exam: string;
    email: string;
    message: string;
    consent: true;
}
export function validateRequest(raw: unknown): CandidateRequest | null {
    if (!raw || typeof raw !== "object") return null;
    const value = raw as Record<string, unknown>;
    if (
        value.website ||
        value.consent !== true ||
        !["exam", "support"].includes(String(value.kind))
    )
        return null;
    const exam = typeof value.exam === "string" ? value.exam.trim() : "";
    const email = typeof value.email === "string" ? value.email.trim() : "";
    const message =
        typeof value.message === "string" ? value.message.trim() : "";
    if (
        !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ||
        email.length > 254 ||
        exam.length > 200 ||
        message.length > 3000
    )
        return null;
    if (
        (value.kind === "exam" && !exam) ||
        (value.kind === "support" && !message)
    )
        return null;
    return {
        kind: value.kind as CandidateRequest["kind"],
        exam,
        email,
        message,
        consent: true,
    };
}

/** Single-host durable queue; no public read endpoint. Configure a persistent volume in production. */
export async function saveRequest(value: CandidateRequest, directory: string) {
    await mkdir(directory, { recursive: true });
    const now = Date.now();
    const names = await readdir(directory);
    // Purge expired requests before every write; an operator schedule must also purge on idle deployments.
    for (const name of names.filter((name) =>
        /^[a-f0-9]{64}\.json$/.test(name),
    )) {
        try {
            const record = JSON.parse(
                await readFile(path.join(directory, name), "utf8"),
            );
            if (Date.parse(record.expires_at) <= now)
                await unlink(path.join(directory, name));
        } catch {
            /* An unreadable record cannot be returned to a candidate. */
        }
    }
    if (names.length > 10000) throw new Error("queue_full");
    const day = new Date(now).toISOString().slice(0, 10);
    const digest = createHash("sha256")
        .update(JSON.stringify({ ...value, day }))
        .digest("hex");
    const filename = path.join(directory, `${digest}.json`);
    const reference = `EUK-${randomUUID().slice(0, 8).toUpperCase()}`;
    try {
        const handle = await open(filename, "wx", 0o600);
        try {
            await handle.writeFile(
                JSON.stringify({
                    ...value,
                    reference,
                    created_at: new Date(now).toISOString(),
                    expires_at: new Date(now + 30 * 86400000).toISOString(),
                }),
            );
        } finally {
            await handle.close();
        }
        return reference;
    } catch (error) {
        if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error;
        return String(JSON.parse(await readFile(filename, "utf8")).reference);
    }
}
