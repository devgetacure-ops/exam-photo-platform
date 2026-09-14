import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { bringIntoView, focusQuietly } from "../lib/scroll";

/**
 * Where a button lands (testing notes 9, 11, H): the section's top just under
 * the sticky bar, never under it, and no jump when it is already in view.
 */

function sectionAt(top: number, bar = "56px"): HTMLElement {
    const el = document.createElement("section");
    el.style.setProperty("--bar", bar);
    document.body.appendChild(el);
    el.getBoundingClientRect = () => ({ top }) as DOMRect;
    return el;
}

describe("bringing a section into view", () => {
    let scrollTo: ReturnType<typeof vi.fn>;
    beforeEach(() => {
        scrollTo = vi.fn();
        window.scrollTo = scrollTo as unknown as typeof window.scrollTo;
        Object.defineProperty(window, "scrollY", { value: 1000, configurable: true });
        Object.defineProperty(window, "innerHeight", { value: 800, configurable: true });
    });
    afterEach(() => {
        document.body.innerHTML = "";
    });

    test("the section's top lands just under the bar, not beneath it", () => {
        bringIntoView(sectionAt(420));
        expect(scrollTo).toHaveBeenCalledWith(
            expect.objectContaining({ top: 1000 + 420 - (56 + 12) }),
        );
    });

    test("a section above the viewport is brought down to the same line", () => {
        bringIntoView(sectionAt(-300, "69px"));
        expect(scrollTo).toHaveBeenCalledWith(expect.objectContaining({ top: 1000 - 300 - 81 }));
    });

    test("already in view: no jump when asked only if needed", () => {
        expect(bringIntoView(sectionAt(120), { onlyIfNeeded: true })).toBe(false);
        expect(scrollTo).not.toHaveBeenCalled();
    });

    test("under the bar still moves, even when only if needed", () => {
        expect(bringIntoView(sectionAt(20), { onlyIfNeeded: true })).toBe(true);
    });

    test("focus moves without the browser's own scroll", () => {
        const heading = document.createElement("h2");
        heading.tabIndex = -1;
        document.body.appendChild(heading);
        const focus = vi.spyOn(heading, "focus");
        focusQuietly(heading);
        expect(focus).toHaveBeenCalledWith({ preventScroll: true });
    });
});
