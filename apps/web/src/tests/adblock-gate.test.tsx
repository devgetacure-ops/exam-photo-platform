import { afterEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

/** With ads on, an ad blocker covers the site until it is off (DEC-134). */

let pathname = "/exam/ctet-september-2026";
vi.mock("next/navigation", () => ({ usePathname: () => pathname }));

afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    vi.useRealTimers();
    document.body.style.overflow = "";
});

async function mount(fetchOk: boolean) {
    vi.useFakeTimers();
    vi.stubGlobal(
        "fetch",
        vi.fn(async () => {
            if (!fetchOk) throw new TypeError("Failed to fetch");
            return new Response(null, { status: 200 });
        }),
    );
    const { AdblockGate } = await import("../components/adblock-gate");
    render(
        <>
            <main>page</main>
            <AdblockGate />
        </>,
    );
    await act(async () => {
        await vi.advanceTimersByTimeAsync(2000);
    });
}

describe("the ad-blocker gate", () => {
    it("covers the site when the ad script is blocked", async () => {
        await mount(false);
        expect(screen.getByRole("dialog")).toBeInTheDocument();
        expect(screen.getByText("Please pause your ad blocker")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /refresh/i })).toBeInTheDocument();
        expect(document.body.style.overflow).toBe("hidden");
    });

    it("asks in Hindi on a Hindi page", async () => {
        pathname = "/hi/exam/ctet-september-2026";
        await mount(false);
        expect(screen.getByText("कृपया अपना ऐड ब्लॉकर रोकें")).toBeInTheDocument();
        pathname = "/exam/ctet-september-2026";
    });
});
