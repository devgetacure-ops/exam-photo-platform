// @vitest-environment node
import { describe, expect, it } from "vitest";
import { actionFor } from "../lib/operator/actions";
import { campaignFrom, deviceOf, latestKit, referrerHost, sessionId, tracked } from "../lib/visit-beacon";

function form(fields: Record<string, string>): FormData {
    const data = new FormData();
    for (const [key, value] of Object.entries(fields)) data.set(key, value);
    return data;
}

describe("the visit beacon (DEC-110)", () => {
    it("keeps one session id per tab", () => {
        const store = new Map<string, string>();
        const storage = { getItem: (k: string) => store.get(k) ?? null, setItem: (k: string, v: string) => void store.set(k, v) };
        const first = sessionId(storage);
        expect(first).toMatch(/^s_[a-f0-9]{20}$/);
        expect(sessionId(storage)).toBe(first);
    });

    it("joins a visit to the most recently touched kit", () => {
        const raw = JSON.stringify({
            a: { kitId: "kit_old", updatedAt: "2026-09-01T00:00:00Z" },
            b: { kitId: "kit_new", updatedAt: "2026-09-20T00:00:00Z" },
            c: { kitId: "../evil", updatedAt: "2026-09-30T00:00:00Z" },
        });
        expect(latestKit(raw)).toBe(undefined);
        expect(latestKit(JSON.stringify({ a: { kitId: "kit_old", updatedAt: "1" }, b: { kitId: "kit_new", updatedAt: "2" } }))).toBe("kit_new");
        expect(latestKit("not json")).toBeUndefined();
    });

    it("names the device and browser coarsely", () => {
        expect(deviceOf("Mozilla/5.0 (Linux; Android 14; SM-A146B) AppleWebKit Chrome/128 Mobile Safari", 390)).toEqual({ device: "mobile", browser: "chrome" });
        expect(deviceOf("Mozilla/5.0 (Linux; Android 13) SamsungBrowser/24 Mobile", 390).browser).toBe("samsung");
        expect(deviceOf("Mozilla/5.0 (Windows NT 10.0) Chrome/128 Edg/128", 1440)).toEqual({ device: "desktop", browser: "edge" });
        expect(deviceOf("Mozilla/5.0 (iPad; CPU OS 17) Safari", 1024).device).toBe("tablet");
    });

    it("records another site as the referrer, never our own", () => {
        expect(referrerHost("https://www.google.com/search?q=x", "examuploadkit.com")).toBe("www.google.com");
        expect(referrerHost("https://examuploadkit.com/exams", "examuploadkit.com")).toBeUndefined();
        expect(referrerHost("", "examuploadkit.com")).toBeUndefined();
    });

    it("reads campaign tags, with ?ref= as a short source", () => {
        expect(campaignFrom("?utm_source=coaching_a&utm_medium=whatsapp&utm_campaign=ssc")).toEqual({
            utm_source: "coaching_a",
            utm_medium: "whatsapp",
            utm_campaign: "ssc",
        });
        expect(campaignFrom("?ref=youtube").utm_source).toBe("youtube");
    });

    it("never counts the operator page or the feedback page", () => {
        expect(tracked("/admin/orders")).toBe(false);
        expect(tracked("/feedback")).toBe(false);
        expect(tracked("/exam/ctet")).toBe(true);
    });
});

describe("operator actions, Releases 2 and 3", () => {
    it("takes a coupon in rupees and sends paise", () => {
        expect(actionFor("coupon", undefined, form({ code: "coach", kind: "flat", value: "2", partner: "A" }), "o")).toMatchObject({
            path: "/v1/operator/coupons",
            body: { code: "COACH", kind: "flat", value: 200 },
        });
        expect(actionFor("coupon", undefined, form({ code: "P10", kind: "percent", value: "10" }), "o")).toMatchObject({ body: { value: 10 } });
    });

    it("sends a campaign only when the box is ticked", () => {
        const fields = { segment: "paid", subject: "Hi", body: "Hello" };
        expect("error" in actionFor("campaign", undefined, form(fields), "o")).toBe(true);
        expect(actionFor("campaign", undefined, form({ ...fields, confirm: "yes" }), "o")).toMatchObject({
            path: "/v1/operator/campaigns",
            body: { segment: "paid", subject: "Hi" },
        });
        expect("error" in actionFor("campaign", undefined, form({ ...fields, segment: "everyone_ever", confirm: "yes" }), "o")).toBe(true);
    });

    it("routes the exam-added email to everyone who asked", () => {
        expect(actionFor("exam-added", undefined, form({ target: "Bihar Police", subject: "s", body: "b", confirm: "yes" }), "o")).toMatchObject({
            path: "/v1/operator/exam-requests/notify",
            body: { segment: "asked_exam", target: "Bihar Police" },
        });
    });

    it("checks a test address and a deadline's date", () => {
        expect("error" in actionFor("campaign-test", undefined, form({ to: "nope", subject: "s", body: "b" }), "o")).toBe(true);
        expect("error" in actionFor("deadline", "ctet-2026", form({ closes_on: "tomorrow" }), "o")).toBe(true);
        expect(actionFor("deadline", "ctet-2026", form({ closes_on: "", note: "" }), "o")).toMatchObject({ body: { closes_on: null } });
        expect("error" in actionFor("deadline", "../x", form({}), "o")).toBe(true);
    });

    it("approves or rejects a review by order id, and nothing else", () => {
        expect(actionFor("review", "order_A1", form({ status: "approved" }), "o")).toEqual({
            path: "/v1/operator/reviews/order_A1/status",
            body: { actor: "o", status: "approved" },
        });
        expect("error" in actionFor("review", "order_A1", form({ status: "published" }), "o")).toBe(true);
        expect("error" in actionFor("review", "job_x", form({ status: "approved" }), "o")).toBe(true);
    });

    it("starts and stops the review offer, and saves free codes", () => {
        expect(actionFor("offer", undefined, form({ on: "false" }), "o")).toEqual({
            path: "/v1/operator/offers/review_reward",
            body: { actor: "o", on: false },
        });
        expect(actionFor("coupon", undefined, form({ code: "friend", kind: "free", value: "" }), "o")).toMatchObject({
            body: { code: "FRIEND", kind: "free", value: 100 },
        });
    });
});
