// @vitest-environment node
import { describe, expect, it } from "vitest";
import { actionFor, postedFromHere } from "../lib/operator/actions";
import { safeBack } from "../lib/operator/data";
import { mailto, replies } from "../lib/operator/templates";
import { validateRequest } from "../lib/request-store";

function form(fields: Record<string, string>): FormData {
    const data = new FormData();
    for (const [key, value] of Object.entries(fields)) data.set(key, value);
    return data;
}

describe("operator actions (DEC-109)", () => {
    it("accepts only forms posted from this site", () => {
        const same = new Headers({ origin: "https://examuploadkit.com", "sec-fetch-site": "same-origin" });
        expect(postedFromHere(same, "examuploadkit.com")).toBe(true);
        expect(postedFromHere(new Headers({ origin: "https://evil.example" }), "examuploadkit.com")).toBe(false);
        expect(postedFromHere(new Headers({ "sec-fetch-site": "cross-site", origin: "https://examuploadkit.com" }), "examuploadkit.com")).toBe(false);
        expect(postedFromHere(new Headers(), "examuploadkit.com")).toBe(false);
    });

    it("turns a ticket form into one engine change with the owner as actor", () => {
        expect(actionFor("ticket", "t_0123456789ab", form({ status: "resolved" }), "owner@example.com")).toEqual({
            path: "/v1/operator/tickets/t_0123456789ab",
            body: { actor: "owner@example.com", status: "resolved" },
        });
        expect(actionFor("ticket", "t_0123456789ab", form({ added: "true" }), "o")).toMatchObject({ body: { added: true } });
    });

    it.each([
        ["ticket", "t_0123456789ab", { status: "deleted" }],
        ["ticket", "t_0123456789ab", {}],
        ["ticket", "../etc", { status: "open" }],
        ["ticket", "t_0123456789ab", { order_id: "order_../x" }],
        ["refund", "../../v1/process", {}],
        ["note", undefined, { target: "elsewhere:x", text: "hi" }],
        ["note", undefined, { target: "order:order_1", text: "   " }],
        ["delete", "anything", {}],
    ])("refuses %s %s %o", (kind, id, fields) => {
        expect("error" in actionFor(kind, id, form(fields as Record<string, string>), "o")).toBe(true);
    });

    it("never sends an amount with a refund mark", () => {
        const planned = actionFor("refund", "order_ABC", form({ reference: "rfnd_1", amount_paise: "1" }), "o");
        expect(planned).toEqual({
            path: "/v1/operator/orders/order_ABC/refund",
            body: { actor: "o", reference: "rfnd_1", undo: false },
        });
    });

    it("redirects back only inside the operator page", () => {
        expect(safeBack("/admin/orders/order_1")).toBe("/admin/orders/order_1");
        expect(safeBack("/admin?days=7")).toBe("/admin?days=7");
        expect(safeBack("https://evil.example")).toBe("/admin");
        expect(safeBack("//evil.example/admin")).toBe("/admin");
        expect(safeBack("/administrator")).toBe("/admin");
        expect(safeBack("/admin/\\evil")).toBe("/admin");
    });
});

describe("reply templates", () => {
    it("fill in the order and open addressed in the mail app", () => {
        const [first] = replies({ exam: "CTET", paymentReference: "pay_1", amountPaise: 300, reference: "EUK-9" });
        expect(first.subject).toContain("EUK-9");
        const refund = replies({ exam: "CTET", paymentReference: "pay_1", amountPaise: 300, refundReference: "rfnd_2" }).find(
            (reply) => reply.id === "refund-done",
        );
        expect(refund?.body).toContain("pay_1");
        expect(refund?.body).toContain("rfnd_2");
        expect(refund?.body).toContain("Rs 3");
        const link = mailto("a+b@example.com", first);
        expect(link.startsWith("mailto:a%2Bb%40example.com?subject=")).toBe(true);
    });
});

describe("support form topics", () => {
    const base = { kind: "support", email: "a@example.com", message: "No file", consent: true };

    it("keeps the topic and the payment reference", () => {
        expect(validateRequest({ ...base, topic: "complaint", payment_reference: " pay_ABC " })).toMatchObject({
            topic: "complaint",
            payment_reference: "pay_ABC",
        });
    });

    it("reads an unknown topic as a question", () => {
        expect(validateRequest({ ...base, topic: "refund-me-now" })?.topic).toBe("question");
    });

    it("gives an exam request neither", () => {
        const value = validateRequest({ kind: "exam", exam: "Bihar Police", email: "a@example.com", consent: true, topic: "grievance" });
        expect(value?.topic).toBeUndefined();
        expect(value?.payment_reference).toBeUndefined();
    });
});
