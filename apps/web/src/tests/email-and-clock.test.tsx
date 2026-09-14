import { afterEach, describe, expect, test, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { EmailDelivery } from "../components/exam/email-delivery";
import { ExpiryClock } from "../components/exam/kit-checkout";

/**
 * Testing note 18: the clock's figures sit in boxes of one width, so nothing
 * beside them moves; and email is offered only where the host can send it.
 */

afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
});

function engineSays(body: Record<string, unknown>) {
    vi.stubGlobal(
        "fetch",
        vi.fn(async () => ({ ok: true, status: 200, json: async () => body })),
    );
}

describe("the deletion clock", () => {
    test("every digit is its own box, and the colon is separate", () => {
        const { container } = render(<ExpiryClock seconds={21 * 60 + 36} at={Date.now()} delivered={false} />);
        const digits = container.querySelectorAll(".euk-clock-digit");
        expect([...digits].map((d) => d.textContent)).toEqual(["2", "1", "3", "6"]);
        expect(container.querySelector(".euk-clock-colon")?.textContent).toBe(":");
    });
});

describe("emailing the files", () => {
    test("no form where the engine says email is not set up", async () => {
        engineSays({ status: "ready", email: "not_configured" });
        const { container } = render(<EmailDelivery kitId="kit_1" jobIds={["job_1"]} released />);
        await waitFor(() => expect(container.querySelector("form")).toBeNull());
    });

    test("the form stays where email is set up", async () => {
        engineSays({ status: "ready", email: "configured" });
        render(<EmailDelivery kitId="kit_2" jobIds={["job_1"]} released />);
        await new Promise((resolve) => setTimeout(resolve, 20));
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    });

    test("an engine that cannot be reached does not hide the form", async () => {
        vi.stubGlobal("fetch", vi.fn(async () => Promise.reject(new TypeError("offline"))));
        render(<EmailDelivery kitId="kit_3" jobIds={["job_1"]} released />);
        await new Promise((resolve) => setTimeout(resolve, 20));
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    });
});
