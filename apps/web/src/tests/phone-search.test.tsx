import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

const replace = vi.fn();
const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace, push }) }));

import { PHONE_SEARCH_ID, PhoneSearch, openPhoneSearch } from "../components/m/search-screen";
import { PhoneHome } from "../components/m/home";

/**
 * The phone's search screen. What matters here is not the ranking (the picker
 * has its own tests) but the three things a phone gets wrong: the keyboard,
 * the back button, and history after choosing.
 */

const INDEX = {
    exams: [
        {
            id: "ssc-cgl",
            name: "Combined Graduate Level Examination",
            body: "Staff Selection Commission",
            year: 2026,
            aliases: ["SSC CGL", "CGL"],
            prepares: 2,
            total: 3,
        },
        {
            id: "neet-ug-2026",
            name: "NEET UG",
            body: "National Testing Agency",
            year: 2026,
            aliases: [],
            prepares: 3,
            total: 4,
        },
    ],
    unavailable: [],
};

function dialog(): HTMLElement {
    return document.getElementById(PHONE_SEARCH_ID) as HTMLElement;
}

function mount() {
    render(
        <>
            <button type="button" onClick={openPhoneSearch}>
                open
            </button>
            <PhoneSearch />
        </>,
    );
}

beforeEach(() => {
    replace.mockReset();
    push.mockReset();
    localStorage.clear();
    window.history.replaceState(null, "");
    vi.stubGlobal(
        "fetch",
        vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve(INDEX) })),
    );
});

afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
});

describe("the phone search", () => {
    test("focuses its field inside the tap itself, so iOS raises the keyboard", () => {
        mount();
        fireEvent.click(screen.getByText("open"));

        // No await: a focus that happens a frame later leaves the iOS
        // keyboard down.
        expect(dialog()).toHaveAttribute("open");
        expect(document.activeElement).toBe(screen.getByRole("combobox"));
        expect((window.history.state as { eukSearch?: boolean }).eukSearch).toBe(true);
    });

    test("offers only recents and shortcuts that still exist in the catalogue", async () => {
        localStorage.setItem(
            "uploadready:recent-exams",
            JSON.stringify([
                { id: "ssc-cgl", name: "Combined Graduate Level Examination" },
                { id: "withdrawn-exam", name: "An examination that left the catalogue" },
            ]),
        );
        mount();
        fireEvent.click(screen.getByText("open"));

        expect(
            await screen.findByRole("link", { name: "Combined Graduate Level Examination" }),
        ).toHaveAttribute("href", "/exam/ssc-cgl");
        expect(screen.queryByText("An examination that left the catalogue")).toBeNull();
        // NEET UG is one of the hand-picked shortcuts and is in this index.
        expect(screen.getByRole("link", { name: "NEET UG" })).toBeInTheDocument();
        // SSC CHSL is a shortcut too, but not in this index, so not offered.
        expect(screen.queryByRole("link", { name: "SSC CHSL" })).toBeNull();
    });

    test("choosing replaces the search's history entry and never pushes past it", async () => {
        mount();
        fireEvent.click(screen.getByText("open"));
        await waitFor(() => expect(fetch).toHaveBeenCalled());
        fireEvent.change(screen.getByRole("combobox"), { target: { value: "cgl" } });

        fireEvent.click(await screen.findByRole("option", { name: /Combined Graduate/ }));

        expect(push).not.toHaveBeenCalled();
        expect(replace).toHaveBeenCalledWith("/exam/ssc-cgl");
        expect(dialog()).not.toHaveAttribute("open");
        expect(JSON.parse(localStorage.getItem("uploadready:recent-exams") ?? "[]")).toEqual([
            { id: "ssc-cgl", name: "Combined Graduate Level Examination" },
        ]);
    });

    test("the back button closes it", () => {
        mount();
        fireEvent.click(screen.getByText("open"));

        window.dispatchEvent(new PopStateEvent("popstate", { state: null }));

        expect(dialog()).not.toHaveAttribute("open");
    });

    test("Escape and the close control step back through history, not just hide", () => {
        const back = vi
            .spyOn(window.history, "back")
            .mockImplementation(() =>
                window.dispatchEvent(new PopStateEvent("popstate", { state: null })),
            );
        mount();

        fireEvent.click(screen.getByText("open"));
        fireEvent.keyDown(screen.getByRole("combobox"), { key: "Escape" });
        expect(back).toHaveBeenCalledTimes(1);
        expect(dialog()).not.toHaveAttribute("open");

        fireEvent.click(screen.getByText("open"));
        fireEvent.click(screen.getByRole("button", { name: "Close search" }));
        expect(back).toHaveBeenCalledTimes(2);
        expect(dialog()).not.toHaveAttribute("open");
    });

    test("a list that failed to load says so instead of claiming nothing matches", async () => {
        vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("offline"))));
        mount();
        fireEvent.click(screen.getByText("open"));
        fireEvent.change(screen.getByRole("combobox"), { target: { value: "cgl" } });

        expect(await screen.findByText(/didn’t load/)).toBeInTheDocument();
        expect(screen.queryByText(/Nothing matches/)).toBeNull();
    });
});

describe("the phone home", () => {
    test("is short: the search, the facts and the shortcuts, with the story one link away", () => {
        render(
            <PhoneHome
                examCount={132}
                shortcuts={[{ id: "ssc-cgl", label: "SSC CGL", name: "Combined Graduate Level Examination" }]}
            />,
        );

        expect(screen.getByRole("button", { name: /Search your examination/ })).toBeInTheDocument();
        expect(screen.getByText("132")).toBeInTheDocument();
        expect(screen.getByRole("link", { name: /SSC CGL/ })).toHaveAttribute("href", "/exam/ssc-cgl");
        expect(screen.getByRole("link", { name: /How it works, what it costs/ })).toHaveAttribute(
            "href",
            "/about",
        );
        // The long argument is not carried on the phone home.
        expect(screen.queryByText(/Six tabs/)).toBeNull();
        // The examples are labelled as what they are.
        expect(screen.getByText(/Representational/)).toBeInTheDocument();
    });
});
