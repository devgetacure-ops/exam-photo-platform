/**
 * One way to move the page to a section, used by every button that does
 * (testing notes 7, 9, 11, E and H).
 *
 * Before this, a stage change focused its heading with a plain `focus()`: the
 * browser scrolled the heading itself to the top edge, so the section's own
 * border and drawing slid under the sticky bar -- "a bit more than expected".
 * And each caller computed its own landing. Now there is one rule: the
 * section's top lands just under the bar (`--bar` plus 12px), smoothly unless
 * the candidate asked for reduced motion.
 */

const GAP = 12;

/** The sticky bar's height where `el` sits, from the one token that sets it. */
export function barHeight(el: Element): number {
    if (typeof window === "undefined") return 0;
    const raw = window.getComputedStyle(el).getPropertyValue("--bar").trim();
    const value = Number.parseFloat(raw);
    return Number.isFinite(value) ? value : 0;
}

export interface BringOptions {
    /**
     * Leave the page alone when the section's top is already comfortably in
     * view -- a stage that replaces the section the candidate is looking at
     * should not jump.
     */
    onlyIfNeeded?: boolean;
}

/** Scroll so `el`'s top sits just under the sticky bar. Returns whether it moved. */
export function bringIntoView(el: Element | null | undefined, options: BringOptions = {}): boolean {
    if (!el || typeof window === "undefined") return false;
    const offset = barHeight(el) + GAP;
    const top = el.getBoundingClientRect().top;
    if (options.onlyIfNeeded && top >= offset - 1 && top <= window.innerHeight * 0.4) {
        return false;
    }
    const reduce =
        typeof window.matchMedia === "function" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({
        top: Math.max(0, window.scrollY + top - offset),
        behavior: reduce ? "auto" : "smooth",
    });
    return true;
}

/** Move keyboard and screen-reader focus to `el` without the browser's own scroll. */
export function focusQuietly(el: HTMLElement | null | undefined): void {
    el?.focus({ preventScroll: true });
}
