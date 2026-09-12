import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { WipeDemo } from "../components/euk/wipe-demo";

/**
 * The band drives itself with requestAnimationFrame, which a test environment
 * never runs on its own, so the clock is stubbed and stepped by hand. That is
 * also the only way to prove the sweep advances the example at the far end
 * rather than at some arbitrary moment.
 */

const photos = ["a1", "a2", "a3"].map((id) => ({
    id,
    before: `/examples/demo/photo-${id}-before.jpg`,
    after: `/examples/demo/photo-${id}-after.jpg`,
    alt: `photo ${id}`,
}));

const signatures = ["s1", "s2"].map((id) => ({
    id,
    before: `/examples/demo/sign-${id}-before.jpg`,
    after: `/examples/demo/sign-${id}-after.jpg`,
    alt: `signature ${id}`,
}));

const checks = [
    { label: "Background", before: "your wall", after: "plain" },
    { label: "Light", before: "uneven", after: "even" },
];

let pending = new Map<number, FrameRequestCallback>();
let nextFrameId = 1;
let reduceMotion = false;

function step(now: number) {
    const due = [...pending.values()];
    pending = new Map();
    act(() => {
        for (const callback of due) callback(now);
    });
}

/** What the frame is showing, ignoring the layer fading out behind it. */
function showing(container: HTMLElement): string {
    const images = [...container.querySelectorAll<HTMLImageElement>("img")];
    return images.find((image) => image.alt !== "")?.alt ?? "";
}

/** The photograph frame's sweep position, as the CSS custom property holds it. */
function wipeOf(container: HTMLElement, which = 0): number {
    const frame = container.querySelectorAll<HTMLElement>(".euk-wipe-frame")[which];
    return Number.parseFloat(frame.style.getPropertyValue("--wipe"));
}

function renderBand() {
    return render(
        <WipeDemo
            photos={photos}
            photoChecks={checks}
            signatures={signatures}
            signatureChecks={checks}
        />,
    );
}

describe("the before-and-after band", () => {
    beforeEach(() => {
        pending = new Map();
        nextFrameId = 1;
        reduceMotion = false;
        vi.stubGlobal("requestAnimationFrame", (cb: FrameRequestCallback) => {
            const id = nextFrameId++;
            pending.set(id, cb);
            return id;
        });
        vi.stubGlobal("cancelAnimationFrame", (id: number) => {
            pending.delete(id);
        });
        vi.stubGlobal("matchMedia", (query: string) => ({
            matches: reduceMotion,
            media: query,
            onchange: null,
            addEventListener: () => {},
            removeEventListener: () => {},
            addListener: () => {},
            removeListener: () => {},
            dispatchEvent: () => false,
        }));
        vi.stubGlobal(
            "IntersectionObserver",
            class {
                constructor(callback: IntersectionObserverCallback) {
                    callback(
                        [{ isIntersecting: true } as IntersectionObserverEntry],
                        this as unknown as IntersectionObserver,
                    );
                }
                observe() {}
                unobserve() {}
                disconnect() {}
            },
        );
    });
    afterEach(() => {
        cleanup();
        vi.unstubAllGlobals();
    });

    test("it sweeps on its own, from where the handle already rests", () => {
        const { container } = renderBand();

        step(0);
        const first = wipeOf(container);
        // The first frame picks the sweep up at the resting position rather
        // than throwing the partition to one edge.
        expect(first).toBeCloseTo(55, 0);

        step(1200);
        const second = wipeOf(container);
        step(2400);
        const third = wipeOf(container);

        expect(second).not.toBeCloseTo(first, 1);
        expect(third).not.toBeCloseTo(second, 1);
        for (const value of [first, second, third]) {
            expect(value).toBeGreaterThanOrEqual(4);
            expect(value).toBeLessThanOrEqual(96);
        }
    });

    test("it changes example at the far end of a sweep, not before", () => {
        const { container } = renderBand();
        step(0);
        expect(showing(container)).toBe("photo a1");

        // Most of a sweep: out to the far side and back, but not past the end.
        for (let now = 200; now <= 3600; now += 400) step(now);
        expect(showing(container)).toBe("photo a1");

        // Past the end of the sweep, where the prepared file fills the frame.
        for (let now = 4000; now <= 9200; now += 400) step(now);
        expect(showing(container)).toBe("photo a2");
    });

    test("pausing holds it still, and playing starts it again", () => {
        const { container } = renderBand();
        step(0);
        step(1200);
        const moving = wipeOf(container);

        fireEvent.click(screen.getByRole("button", { name: /pause/i }));
        step(2400);
        step(3600);
        expect(wipeOf(container)).toBeCloseTo(moving, 2);

        fireEvent.click(screen.getByRole("button", { name: /play/i }));
        step(4800);
        step(6000);
        expect(wipeOf(container)).not.toBeCloseTo(moving, 1);
    });

    test("dragging it hands the handle over and stops the motion", () => {
        const { container } = renderBand();
        step(0);
        const frame = container.querySelector<HTMLElement>(".euk-wipe-frame")!;
        frame.setPointerCapture = () => {};
        frame.hasPointerCapture = () => true;
        frame.getBoundingClientRect = () =>
            ({ left: 0, width: 400, top: 0, height: 500 }) as DOMRect;

        fireEvent.pointerDown(frame, { pointerId: 1, clientX: 100 });
        expect(wipeOf(container)).toBeCloseTo(25, 0);

        // The control now offers to start it again, and frames change nothing.
        expect(screen.getByRole("button", { name: /play/i })).toBeInTheDocument();
        step(1200);
        step(2400);
        expect(wipeOf(container)).toBeCloseTo(25, 0);
    });

    test("choosing an example pins it, so the sweep stops cycling", () => {
        const { container } = renderBand();
        step(0);

        const dots = screen.getAllByRole("button", { name: "Example 3 of 3" });
        fireEvent.click(dots[0]);
        expect(showing(container)).toBe("photo a3");

        for (let now = 400; now <= 12000; now += 400) step(now);
        expect(showing(container)).toBe("photo a3");
    });

    test("it does not move at all when the browser asks for less motion", () => {
        reduceMotion = true;
        const { container } = renderBand();

        expect(screen.getByRole("button", { name: /play/i })).toBeInTheDocument();
        step(0);
        step(2400);
        expect(wipeOf(container)).toBeCloseTo(55, 0);
    });

    test("both a photograph and a signature are shown, each with its own examples", () => {
        renderBand();

        expect(screen.getByText("Photograph")).toBeInTheDocument();
        expect(screen.getByText("Signature")).toBeInTheDocument();
        expect(screen.getAllByRole("button", { name: /^Example \d of 3$/ })).toHaveLength(3);
        expect(screen.getAllByRole("button", { name: /^Example \d of 2$/ })).toHaveLength(2);
        expect(screen.getByText(/Representational examples/)).toBeInTheDocument();
    });
});
