import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { act, cleanup, fireEvent, render, renderHook, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { InstallCard, InstallMenuItem } from "../components/m/install-card";
import { useKit } from "../components/exam/use-kit";
import {
    DISMISS_FOR_MS,
    INSTALL_MOMENT,
    INSTALL_READY,
    isIos,
    markInstallMoment,
    recentlyDismissed,
} from "../lib/install";
import type { PrepareRequirementResponse } from "../lib/types";

/**
 * The invitation to install. The cases that matter most are the ones where
 * nothing should appear: on arrival, on a browser that cannot install, after
 * "Not now", and once installed — and an iPhone must never be shown a button
 * that cannot work.
 */

const IPHONE =
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1";
const originalAgent = navigator.userAgent;

function offerInstall(outcome: "accepted" | "dismissed" = "accepted") {
    const prompt = vi.fn(async () => {});
    const event = Object.assign(new Event("beforeinstallprompt"), {
        prompt,
        userChoice: Promise.resolve({ outcome }),
    });
    act(() => {
        window.__eukInstallPrompt = event;
        window.dispatchEvent(new Event(INSTALL_READY));
    });
    return prompt;
}

function moment() {
    act(() => markInstallMoment());
}

function setAgent(value: string) {
    Object.defineProperty(window.navigator, "userAgent", { value, configurable: true });
}

beforeEach(() => {
    localStorage.clear();
    window.__eukInstallPrompt = null;
});

afterEach(() => {
    cleanup();
    setAgent(originalAgent);
    vi.unstubAllGlobals();
});

describe("the invitation to install", () => {
    test("nothing is offered on arrival, even where the browser can install", () => {
        render(<InstallCard />);
        offerInstall();

        expect(screen.queryByText(/home screen/i)).toBeNull();
    });

    test("after something useful, it offers to install, and accepting installs for good", async () => {
        render(<InstallCard />);
        const prompt = offerInstall("accepted");
        moment();

        expect(screen.getByText("Keep ExamUploadKit on your home screen")).toBeInTheDocument();
        await act(async () => {
            fireEvent.click(screen.getByRole("button", { name: "Add to home screen" }));
        });

        expect(prompt).toHaveBeenCalledTimes(1);
        expect(screen.queryByText(/home screen/i)).toBeNull();
        expect(localStorage.getItem("uploadready:installed")).toBe("1");

        moment();
        expect(screen.queryByText(/home screen/i)).toBeNull();
    });

    test("Not now is remembered for thirty days", () => {
        render(<InstallCard />);
        offerInstall();
        moment();

        fireEvent.click(screen.getByRole("button", { name: "Not now" }));
        expect(screen.queryByText(/home screen/i)).toBeNull();

        moment();
        expect(screen.queryByText(/home screen/i)).toBeNull();
        expect(recentlyDismissed()).toBe(true);
        expect(recentlyDismissed(Date.now() + DISMISS_FOR_MS + 1000)).toBe(false);
    });

    test("declining the browser's own dialog is remembered as not now", async () => {
        render(<InstallCard />);
        offerInstall("dismissed");
        moment();

        await act(async () => {
            fireEvent.click(screen.getByRole("button", { name: "Add to home screen" }));
        });

        expect(recentlyDismissed()).toBe(true);
        expect(localStorage.getItem("uploadready:installed")).toBeNull();
    });

    test("a browser that cannot install is offered nothing", () => {
        render(<InstallCard />);
        moment();

        expect(screen.queryByText(/home screen/i)).toBeNull();
    });

    test("an iPhone is told the two steps, and never shown a button that cannot work", () => {
        setAgent(IPHONE);
        render(<InstallCard />);
        moment();

        expect(screen.getByText("Add to Home Screen")).toBeInTheDocument();
        expect(screen.queryByRole("button", { name: /add to home screen/i })).toBeNull();
        expect(screen.getByRole("button", { name: "Got it" })).toBeInTheDocument();
    });

    test("once installed and opened from the home screen, nothing is offered", () => {
        vi.stubGlobal("matchMedia", vi.fn(() => ({ matches: true })));
        render(<InstallCard />);
        offerInstall();
        moment();

        expect(screen.queryByText(/home screen/i)).toBeNull();
    });

    test("it makes no claim that the app works offline", () => {
        render(<InstallCard />);
        offerInstall();
        moment();

        expect(screen.queryByText(/offline/i)).toBeNull();
        expect(screen.getByText(/still needs the internet/)).toBeInTheDocument();
    });
});

describe("installing from the menu", () => {
    test("is offered only where installing can work", () => {
        render(<InstallMenuItem />);
        expect(screen.queryByRole("button", { name: "Install the app" })).toBeNull();

        const prompt = offerInstall();
        fireEvent.click(screen.getByRole("button", { name: "Install the app" }));
        expect(prompt).toHaveBeenCalledTimes(1);
    });

    test("on an iPhone it opens the two steps instead", () => {
        setAgent(IPHONE);
        render(<InstallMenuItem />);

        fireEvent.click(screen.getByRole("button", { name: "Install the app" }));
        expect(screen.getByText("Add to Home Screen")).toBeInTheDocument();
    });
});

describe("what counts as a useful moment", () => {
    function response(outcome: string) {
        return {
            job_id: `job-${outcome}`,
            exam_id: "test-exam",
            requirement_id: "photo",
            requirement_type: "photograph",
            platform_support: "supported",
            status: "completed",
            outcome,
            findings: [],
            issue_codes: [],
        } as unknown as PrepareRequirementResponse;
    }

    test("a file that came back prepared counts; a refused one does not", () => {
        const moments = vi.fn();
        window.addEventListener(INSTALL_MOMENT, moments);
        const { result } = renderHook(() => useKit("test-exam"));

        act(() => result.current.record(response("blocked")));
        act(() => result.current.record(response("not_produced")));
        expect(moments).not.toHaveBeenCalled();

        act(() => result.current.record(response("prepared_with_findings")));
        act(() => result.current.record(response("prepared")));
        expect(moments).toHaveBeenCalledTimes(2);

        window.removeEventListener(INSTALL_MOMENT, moments);
    });
});

describe("recognising an iPhone or iPad", () => {
    test("an iPad that reports itself as a Mac is recognised by its touch screen", () => {
        const mac = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15";
        expect(isIos(mac, 5)).toBe(true);
        expect(isIos(mac, 0)).toBe(false);
        expect(isIos(IPHONE, 5)).toBe(true);
    });
});
