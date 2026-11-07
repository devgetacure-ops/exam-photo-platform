import { describe, expect, it } from "vitest";
import { actionForClick, labelOf } from "../lib/visit-beacon";

function html(markup: string): HTMLElement {
    const root = document.createElement("div");
    root.innerHTML = markup;
    return root;
}

describe("what a tap is recorded as (DEC-124)", () => {
    it("names buttons by their words and links by kind", () => {
        const root = html(`
            <button id="b"><span id="inner">Start with SSC CGL</span></button>
            <a id="l" href="/pricing">Pricing</a>
            <a id="d" href="blob:x" download="ssc-photo.jpg">Download</a>
            <a id="w" href="https://wa.me/?text=hi">Remind me</a>
            <a id="t" href="tel:+910000000000">Call</a>
            <a id="m" href="mailto:support@examuploadkit.com">Email</a>
        `);
        const at = (id: string) => actionForClick(root.querySelector(`#${id}`));
        expect(at("inner")).toEqual({ name: "click", label: "Start with SSC CGL" });
        expect(at("l")).toEqual({ name: "link", label: "Pricing" });
        expect(at("d")).toEqual({ name: "download", label: "ssc-photo.jpg" });
        expect(at("w")?.name).toBe("whatsapp");
        expect(at("t")).toEqual({ name: "call" });
        expect(at("m")).toEqual({ name: "email_link" });
    });

    it("ignores plain text, disabled buttons and opted-out areas", () => {
        const root = html(`<p id="p">Hello</p><button id="x" disabled>Pay</button><div data-track-ignore><button id="i">Secret</button></div>`);
        expect(actionForClick(root.querySelector("#p"))).toBeNull();
        expect(actionForClick(root.querySelector("#x"))).toBeNull();
        expect(actionForClick(root.querySelector("#i"))).toBeNull();
    });

    it("never keeps long numbers shown on a button", () => {
        const root = html(`<button id="b">Order 9876543210 paid</button>`);
        expect(labelOf(root.querySelector("#b")!)).toBe("Order … paid");
    });
});
