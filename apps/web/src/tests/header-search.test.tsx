import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import { act, render, screen, fireEvent, waitFor } from "@testing-library/react";
import { HeaderSearch } from "../components/header-search";
import type { SearchEntry } from "../lib/types";

vi.mock("next/navigation", () => ({
    useRouter: () => ({ push: vi.fn() }),
}));

const exams: SearchEntry[] = [
    {
        id: "gate-2026",
        name: "GATE 2026",
        body: "Indian Institute of Science",
        year: 2026,
        aliases: ["GATE"],
        prepares: 2,
        total: 3,
    },
];

/** The observer the header uses, with its callback in reach of the test. */
let fire: ((entries: { isIntersecting: boolean }[]) => void) | null = null;

class StubObserver {
    constructor(callback: (entries: { isIntersecting: boolean }[]) => void) {
        fire = callback;
    }
    observe() {}
    disconnect() {}
    unobserve() {}
}

beforeEach(() => {
    fire = null;
    vi.stubGlobal("IntersectionObserver", StubObserver);
    vi.stubGlobal(
        "fetch",
        vi.fn(async () => ({
            ok: true,
            json: async () => ({ exams, unavailable: [] }),
        })),
    );
});

afterEach(() => {
    vi.unstubAllGlobals();
});

describe("the search in the header", () => {
    test("stays out of the way until the page's own search has gone", async () => {
        const page = document.createElement("div");
        page.id = "hero-search";
        document.body.append(page);

        const { container } = render(
            <HeaderSearch takesOverFrom="hero-search" />,
        );
        const slot = container.querySelector(".euk-topsearch");

        expect(slot?.getAttribute("data-shown")).toBe("false");
        // Out of the tab order too, not merely invisible.
        expect(
            container.querySelector(".euk-topsearch-open")?.hasAttribute("inert"),
        ).toBe(true);

        act(() => fire?.([{ isIntersecting: false }]));
        await waitFor(() =>
            expect(slot?.getAttribute("data-shown")).toBe("true"),
        );
        expect(
            container.querySelector(".euk-topsearch-open")?.hasAttribute("inert"),
        ).toBe(false);

        act(() => fire?.([{ isIntersecting: true }]));
        await waitFor(() =>
            expect(slot?.getAttribute("data-shown")).toBe("false"),
        );
        page.remove();
    });

    test("wears the examination's name where there is one", () => {
        render(<HeaderSearch examName="GATE 2026" />);
        expect(screen.getByRole("button").textContent).toContain("GATE 2026");
    });

    test("fetches the catalogue once, when it is first opened", async () => {
        render(<HeaderSearch examName="GATE 2026" />);
        expect(fetch).not.toHaveBeenCalled();

        fireEvent.click(screen.getByRole("button"));
        await waitFor(() =>
            expect(
                screen.getByRole("combobox", {
                    name: /search for your examination/i,
                }),
            ).toBeTruthy(),
        );
        expect(fetch).toHaveBeenCalledTimes(1);

        fireEvent.keyDown(document, { key: "Escape" });
        await waitFor(() =>
            expect(screen.queryByRole("dialog")).toBeNull(),
        );

        fireEvent.click(screen.getByRole("button"));
        await waitFor(() => expect(screen.getByRole("dialog")).toBeTruthy());
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    test("says so when the catalogue cannot be loaded", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn(async () => ({ ok: false, status: 500, json: async () => ({}) })),
        );
        render(<HeaderSearch examName="GATE 2026" />);
        fireEvent.click(screen.getByRole("button"));
        await waitFor(() =>
            expect(screen.getByText(/didn’t load/i)).toBeTruthy(),
        );
    });

    test("opens on the slash key, but not while something else is being typed into", async () => {
        render(
            <>
                <input aria-label="somewhere else" />
                <HeaderSearch examName="GATE 2026" />
            </>,
        );

        const elsewhere = screen.getByLabelText("somewhere else");
        elsewhere.focus();
        fireEvent.keyDown(document, { key: "/" });
        expect(screen.queryByRole("dialog")).toBeNull();

        elsewhere.blur();
        fireEvent.keyDown(document, { key: "/" });
        await waitFor(() => expect(screen.getByRole("dialog")).toBeTruthy());
    });
});
