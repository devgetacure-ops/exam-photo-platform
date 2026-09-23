// @vitest-environment node
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { beforeEach, describe, expect, it } from "vitest";
import {
    accessConfig,
    operatorFromHeaders,
    resetAccessKeyCache,
    verifyAccessAssertion,
} from "../lib/operator/access";
import { orderState, pictureFiles, revenue, rupees, safeFileRequest, type Order } from "../lib/operator/data";
import { maskEmail, readRequests } from "../lib/operator/requests";

const TEAM = "https://examuploadkit.cloudflareaccess.com";
const AUD = "aud-tag-123";
const ENV = { NODE_ENV: "production", EUK_ACCESS_TEAM_DOMAIN: TEAM, EUK_ACCESS_AUD: AUD };

function b64url(bytes: ArrayBuffer | Uint8Array | string): string {
    const raw =
        typeof bytes === "string" ? new TextEncoder().encode(bytes) : new Uint8Array(bytes);
    return Buffer.from(raw).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function keyPair() {
    const pair = await crypto.subtle.generateKey(
        { name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" },
        true,
        ["sign", "verify"],
    );
    const jwk = await crypto.subtle.exportKey("jwk", pair.publicKey);
    return { pair, jwk: { ...jwk, kid: "k1" } };
}

async function sign(privateKey: CryptoKey, claims: Record<string, unknown>, kid = "k1") {
    const head = b64url(JSON.stringify({ alg: "RS256", kid, typ: "JWT" }));
    const body = b64url(JSON.stringify(claims));
    const signature = await crypto.subtle.sign(
        "RSASSA-PKCS1-v1_5",
        privateKey,
        new TextEncoder().encode(`${head}.${body}`),
    );
    return `${head}.${body}.${b64url(signature)}`;
}

describe("Cloudflare Access check", () => {
    beforeEach(() => resetAccessKeyCache());

    const now = Date.now();
    const good = { aud: [AUD], iss: TEAM, exp: now / 1000 + 600, email: "owner@example.com" };

    it("admits a genuine, current assertion for our audience", async () => {
        const { pair, jwk } = await keyPair();
        const fetcher = (async () => Response.json({ keys: [jwk] })) as unknown as typeof fetch;
        const token = await sign(pair.privateKey, good);
        expect(await verifyAccessAssertion(token, accessConfig(ENV), fetcher, now)).toBe("owner@example.com");
    });

    it.each([
        ["another audience", { ...good, aud: ["someone-else"] }],
        ["another team", { ...good, iss: "https://evil.cloudflareaccess.com" }],
        ["an expired token", { ...good, exp: now / 1000 - 1 }],
    ])("refuses %s", async (_label, claims) => {
        const { pair, jwk } = await keyPair();
        const fetcher = (async () => Response.json({ keys: [jwk] })) as unknown as typeof fetch;
        const token = await sign(pair.privateKey, claims);
        expect(await verifyAccessAssertion(token, accessConfig(ENV), fetcher, now)).toBeNull();
    });

    it("refuses a token signed by a key Cloudflare did not publish", async () => {
        const published = await keyPair();
        const forger = await keyPair();
        const fetcher = (async () => Response.json({ keys: [published.jwk] })) as unknown as typeof fetch;
        const token = await sign(forger.pair.privateKey, good);
        expect(await verifyAccessAssertion(token, accessConfig(ENV), fetcher, now)).toBeNull();
    });

    it("fails shut in production when Access is not configured or no header came", async () => {
        const headers = new Headers();
        expect(await operatorFromHeaders(headers, { NODE_ENV: "production" })).toBeNull();
        expect(await operatorFromHeaders(headers, ENV)).toBeNull();
        expect(
            await operatorFromHeaders(headers, { NODE_ENV: "production", EUK_OPERATOR_DEV_OPEN: "true" }),
        ).toBeNull();
        expect(accessConfig({ EUK_ACCESS_TEAM_DOMAIN: "http://x.com", EUK_ACCESS_AUD: "a" })).toBeNull();
    });

    it("opens locally only with the explicit development switch", async () => {
        expect(
            await operatorFromHeaders(new Headers(), { NODE_ENV: "development", EUK_OPERATOR_DEV_OPEN: "true" }),
        ).toBe("local developer");
        expect(await operatorFromHeaders(new Headers(), { NODE_ENV: "development" })).toBeNull();
    });
});

describe("the operator token stays on the server", () => {
    it("is never named in a browser-visible variable", async () => {
        const { readFileSync, readdirSync, statSync } = await import("node:fs");
        const files: string[] = [];
        const walk = (dir: string) => {
            for (const entry of readdirSync(dir)) {
                const full = path.join(dir, entry);
                if (statSync(full).isDirectory()) walk(full);
                else if (/\.(ts|tsx)$/.test(entry)) files.push(full);
            }
        };
        walk(path.join(process.cwd(), "src"));
        const offenders = files.filter((file) => {
            const text = readFileSync(file, "utf8");
            return /NEXT_PUBLIC_[A-Z_]*OPERATOR/.test(text) || (text.includes("EXAM_PHOTO_OPERATOR_TOKEN") && text.startsWith('"use client"'));
        });
        expect(offenders).toEqual([]);
        const engine = readFileSync(path.join(process.cwd(), "src/lib/operator/engine.ts"), "utf8");
        expect(engine).toContain('import "server-only"');
    });
});

const order = (overrides: Partial<Order>): Order => ({
    order_id: "order_x",
    kit_id: "kit_x",
    job_ids: [],
    amount_paise: 300,
    currency: "INR",
    created_at: "2026-09-20T10:00:00+00:00",
    ...overrides,
});

describe("orders and money", () => {
    it("applies the refund rule: paid and not delivered", () => {
        expect(orderState(order({ paid_at: "2026-09-20T10:01:00Z" }))).toBe("refund-due");
        expect(orderState(order({ paid_at: "2026-09-20T10:01:00Z", delivered_at: "2026-09-20T10:02:00Z" }))).toBe("delivered");
        expect(orderState(order({}))).toBe("unpaid");
    });

    it("counts only paid money, by Indian calendar day", () => {
        const now = Date.parse("2026-09-23T12:00:00Z");
        const totals = revenue(
            [
                order({ amount_paise: 300, paid_at: "2026-09-23T05:00:00Z", delivered_at: "x" }),
                // 20:00 UTC on the 22nd is 01:30 on the 23rd in India.
                order({ amount_paise: 500, paid_at: "2026-09-22T20:00:00Z" }),
                order({ amount_paise: 800, paid_at: "2026-09-01T05:00:00Z", delivered_at: "x" }),
                order({ amount_paise: 999 }),
            ],
            now,
        );
        expect(totals.todayPaise).toBe(800);
        expect(totals.weekPaise).toBe(800);
        expect(totals.monthPaise).toBe(1600);
        expect(totals.allPaise).toBe(1600);
        expect(totals.unpaidOrders).toBe(1);
        expect(totals.refundDue).toBe(1);
        expect(totals.refundDuePaise).toBe(500);
        expect(rupees(1600)).toBe("₹16");
    });
});

describe("uploads", () => {
    it("shows the candidate's photograph first, then the prepared file", () => {
        expect(
            pictureFiles({
                job_id: "job_a",
                status: "succeeded",
                created_at: "",
                updated_at: "",
                expires_at: "",
                output_filename: "photo.jpg",
                files: [
                    { name: "preview.jpg", bytes: 1 },
                    { name: "report.json", bytes: 1 },
                    { name: "photo.jpg", bytes: 1 },
                    { name: "input.jpg", bytes: 1 },
                ],
            }),
        ).toEqual(["input.jpg", "photo.jpg", "preview.jpg"]);
    });

    it("passes only a job id and a plain file name to the engine", () => {
        expect(safeFileRequest("job_abc", "input.jpg")).toBe(true);
        expect(safeFileRequest("job_abc", "../job_b/input.jpg")).toBe(false);
        expect(safeFileRequest("job_abc", "..")).toBe(false);
        expect(safeFileRequest("kit_abc", "input.jpg")).toBe(false);
    });
});

describe("requests", () => {
    it("masks the address and drops expired requests", async () => {
        const dir = await mkdtemp(path.join(tmpdir(), "req-"));
        const now = Date.parse("2026-09-23T00:00:00Z");
        const write = (name: string, value: object) =>
            writeFile(path.join(dir, `${name.repeat(64)}.json`), JSON.stringify(value));
        await write("a", {
            kind: "exam",
            exam: "Bihar Police",
            email: "candidate@example.com",
            message: "Please add it",
            reference: "EUK-1",
            created_at: "2026-09-22T00:00:00Z",
            expires_at: "2026-10-22T00:00:00Z",
        });
        await write("b", {
            kind: "support",
            exam: "",
            email: "old@example.com",
            message: "old",
            reference: "EUK-2",
            created_at: "2026-08-01T00:00:00Z",
            expires_at: "2026-08-31T00:00:00Z",
        });
        const found = await readRequests(dir, now);
        expect(found).toHaveLength(1);
        expect(found[0].maskedEmail).toBe("c***@example.com");
        expect(JSON.stringify(found)).not.toContain("candidate@");
        expect(maskEmail("nope")).toBe("***");
    });
});
