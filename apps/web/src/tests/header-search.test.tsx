import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import {
    act,
    render,
    screen,
    fireEvent,
    waitFor,
} from "@testing-library/react";
import { HeaderSearch } from "../components/header-search";
import type { SearchEntry } from "../lib/types";

const push = vi.fn();
vi.mock("next/navigation", () => ({
    useRouter: () => ({ push }),
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
    {
        id: "neet-ug-2026",
        name: "NEET (UG) 2026",
        body: "National Testing Agency",
        year: 2026,
        aliases: ["NEET"],
        prepares: 4,
        total: 18,
    },
];

/** The observer the bar uses, with its callback in reach of the test. */
let fire: ((entries: { isIntersecting: boolean }[]) => void) | null = null;

class StubObserver {
    constructor(callback: (entries: { isIntersecting: boolean }[]) => void) {
        fire = callback;
    }
    observe() {}
    disconnect() {}
    unobserve() {}
}

const field = () => screen.getByRole("combobox");

function type(value: string) {
    fireEvent.change(field(), { target: { value } });
}

beforeEach(() => {
    push.mockClear();
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

describe("the search in the bar", () => {
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
        expect(field().hasAttribute("inert")).toBe(true);

        act(() => fire?.([{ isIntersecting: false }]));
        await waitFor(() =>
            expect(slot?.getAttribute("data-shown")).toBe("true"),
        );
        expect(field().hasAttribute("inert")).toBe(false);

        act(() => fire?.([{ isIntersecting: true }]));
        await waitFor(() =>
            expect(slot?.getAttribute("data-shown")).toBe("false"),
        );
        page.remove();
    });

    test("is a field to type in, not a button that opens one", async () => {
        render(<HeaderSearch examName="GATE 2026" />);

        // No second search to open: the field in the bar is the search.
        expect(screen.queryByRole("dialog")).toBeNull();
        expect(field().getAttribute("placeholder")).toBe("GATE 2026");

        fireEvent.focus(field());
        type("neet");

        const row = await screen.findByRole("option", { name: /NEET/ });
        fireEvent.click(row);
        expect(push).toHaveBeenCalledWith("/exam/neet-ug-2026");
    });

    test("fetches the catalogue once, on first focus", async () => {
        render(<HeaderSearch examName="GATE 2026" />);
        expect(fetch).not.toHaveBeenCalled();

        fireEvent.focus(field());
        await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));

        fireEvent.blur(field());
        fireEvent.focus(field());
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    test("says the list is loading rather than claiming nothing matches", async () => {
        let release: (value: unknown) => void = () => {};
        vi.stubGlobal(
            "fetch",
            vi.fn(
                () =>
                    new Promise((resolve) => {
                        release = resolve;
                    }),
            ),
        );
        render(<HeaderSearch />);
        fireEvent.focus(field());
        type("gate");

        expect(screen.getByText(/Loading examinations/)).toBeTruthy();
        expect(screen.queryByText(/Nothing matches/)).toBeNull();

        await act(async () => {
            release({
                ok: true,
                json: async () => ({ exams, unavailable: [] }),
            });
        });
        await waitFor(() =>
            expect(screen.getByRole("option", { name: /GATE/ })).toBeTruthy(),
        );
    });

    test("opens on the slash key, but not while something else is being typed into", async () => {
        render(
            <>
                <input aria-label="somewhere else" />
                <HeaderSearch />
            </>,
        );

        const elsewhere = screen.getByLabelText("somewhere else");
        elsewhere.focus();
        fireEvent.keyDown(document, { key: "/" });
        expect(document.activeElement).toBe(elsewhere);

        elsewhere.blur();
        fireEvent.keyDown(document, { key: "/" });
        await waitFor(() => expect(document.activeElement).toBe(field()));
    });

    test("clicking away puts the list down without losing what was typed", async () => {
        render(<HeaderSearch />);
        fireEvent.focus(field());
        type("gate");
        await waitFor(() =>
            expect(screen.getByRole("option", { name: /GATE/ })).toBeTruthy(),
        );

        fireEvent.mouseDown(document.body);
        await waitFor(() => expect(screen.queryByRole("option")).toBeNull());
        expect((field() as HTMLInputElement).value).toBe("gate");
    });
});
