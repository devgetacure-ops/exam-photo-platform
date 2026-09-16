import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { WipeDemo } from "../components/euk/wipe-demo";

/**
 * The band drives itself with requestAnimationFrame, which a test environment
 * never runs on its own, so the clock is stubbed and stepped by hand. The
 * three-second pick-up runs on a timer, so that is faked too. Between them
 * they are the only way to prove the rules that matter: both frames sweep the
 * same way, a drag holds one frame and not the other, and a held frame lets go
 * again by itself.
 */

const photos = ["a1", "a2", "a3"].map((id) => ({
    id,
    before: `/examples/band/photo-${id}-uploaded.jpg`,
    after: `/examples/band/photo-${id}-prepared.jpg`,
    alt: `photo ${id}`,
}));

const signatures = ["s1", "s2"].map((id) => ({
    id,
    before: `/examples/band/sign-${id}-uploaded.jpg`,
    after: `/examples/band/sign-${id}-prepared.jpg`,
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

function wait(ms: number) {
    act(() => {
        vi.advanceTimersByTime(ms);
    });
}

/** Where a frame's partition sits, as the CSS custom property holds it. */
function wipeOf(container: HTMLElement, which: number): number {
    const frame = container.querySelectorAll<HTMLElement>(".euk-wipe-frame")[which];
    return Number.parseFloat(frame.style.getPropertyValue("--wipe"));
}

/** What a frame is showing, ignoring the layer fading out behind it. */
function showing(container: HTMLElement, which: number): string {
    const figure = container.querySelectorAll(".euk-wipe")[which];
    const images = [...figure.querySelectorAll<HTMLImageElement>("img")];
    return images.find((image) => image.alt !== "")?.alt ?? "";
}

/** A touch on a frame: down at `clientX`, then lifted unless `keepDown`. */
function grab(
    container: HTMLElement,
    which: number,
    clientX: number,
    { keepDown = false }: { keepDown?: boolean } = {},
) {
    const frame = container.querySelectorAll<HTMLElement>(".euk-wipe-frame")[which];
    frame.setPointerCapture = () => {};
    frame.hasPointerCapture = () => true;
    frame.getBoundingClientRect = () =>
        ({ left: 0, width: 400, top: 0, height: 500 }) as DOMRect;
    fireEvent.pointerDown(frame, { pointerId: 1, clientX });
    if (!keepDown) fireEvent.pointerUp(frame, { pointerId: 1, clientX });
    return frame;
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
        vi.useFakeTimers();
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
        vi.useRealTimers();
    });

    test("both frames sweep the same way, never against each other", () => {
        const { container } = renderBand();

        for (const now of [0, 900, 1800, 2700, 3600]) {
            step(now);
            expect(wipeOf(container, 0)).toBeCloseTo(wipeOf(container, 1), 2);
        }
        // And it is a sweep, not a resting position.
        step(0);
        const first = wipeOf(container, 0);
        step(1500);
        expect(wipeOf(container, 0)).not.toBeCloseTo(first, 1);
    });

    test("the next example arrives on the sweep itself, with no broken frame between", () => {
        const { container } = renderBand();
        step(0);

        let previousShown = showing(container, 0);
        let previousWipe = wipeOf(container, 0);
        let handovers = 0;
        let reachedPrepared = false;
        let broughtNextUploadIn = false;

        for (let now = 100; now <= 16000; now += 100) {
            step(now);
            const wipe = wipeOf(container, 0);
            const shown = showing(container, 0);
            if (wipe <= 0.5) reachedPrepared = true;
            if (wipe > previousWipe + 0.5) broughtNextUploadIn = true;
            if (shown !== previousShown) {
                // The prepared file underneath changes only while the next
                // upload covers the whole frame: nothing visible jumps.
                handovers += 1;
                expect(previousWipe).toBeGreaterThanOrEqual(99.5);
                expect(wipe).toBeGreaterThanOrEqual(99);
            }
            // Never a jump: the partition moves smoothly between steps.
            expect(Math.abs(wipe - previousWipe)).toBeLessThan(20);
            previousWipe = wipe;
            previousShown = shown;
        }

        expect(reachedPrepared).toBe(true);
        expect(broughtNextUploadIn).toBe(true);
        expect(handovers).toBeGreaterThanOrEqual(1);
        // No outgoing layer fading over the frame any more.
        expect(container.querySelector(".euk-wipe-prev")).toBeNull();
    });

    test("the sweep back uncovers the next upload over the current prepared file", () => {
        const { container } = renderBand();
        step(0);
        const clip = () =>
            container.querySelectorAll(".euk-wipe")[0].querySelector(".euk-wipe-clip img")!.getAttribute("src") ?? "";
        expect(clip()).toContain("photo-a1-uploaded");
        // Past the rest on the prepared file, the upload layer is the next one.
        for (let now = 300; now <= 5100; now += 300) step(now);
        expect(clip()).toContain("photo-a2-uploaded");
        expect(showing(container, 0)).toBe("photo a1");
    });

    test("checks tick as the prepared file takes over, not as the upload does", () => {
        const { container } = renderBand();
        const ticked = () =>
            container
                .querySelectorAll(".euk-wipe")[0]
                .querySelectorAll('[data-done="true"]').length;

        // Hard over to the upload: nothing has been fixed yet.
        grab(container, 0, 396);
        expect(ticked()).toBe(0);

        // Hard over to the prepared file: everything has.
        grab(container, 0, 4);
        expect(ticked()).toBe(checks.length);
    });

    test("a drag holds that frame, and leaves the other one running", () => {
        const { container } = renderBand();
        step(0);
        step(900);
        const signatureWas = wipeOf(container, 1);

        grab(container, 0, 100);
        expect(wipeOf(container, 0)).toBeCloseTo(25, 0);

        step(1800);
        step(2700);
        expect(wipeOf(container, 0)).toBeCloseTo(25, 0);
        expect(wipeOf(container, 1)).not.toBeCloseTo(signatureWas, 1);
    });

    test("a held frame picks itself up three seconds after the last touch", () => {
        const { container } = renderBand();
        step(0);
        grab(container, 0, 100);

        wait(2000);
        step(900);
        expect(wipeOf(container, 0)).toBeCloseTo(25, 0);

        wait(1200);
        step(1800);
        step(2700);
        expect(wipeOf(container, 0)).not.toBeCloseTo(25, 0);
    });

    test("a finger still on the frame keeps it held, however long it stays", () => {
        const { container } = renderBand();
        step(0);
        const frame = grab(container, 0, 100, { keepDown: true });

        wait(5000);
        step(900);
        step(1800);
        expect(wipeOf(container, 0)).toBeCloseTo(25, 0);

        // Dragged further while down: follows the finger, measured once.
        fireEvent.pointerMove(frame, { pointerId: 1, clientX: 200 });
        expect(wipeOf(container, 0)).toBeCloseTo(50, 0);

        fireEvent.pointerUp(frame, { pointerId: 1, clientX: 200 });
        wait(3200);
        step(2700);
        step(3600);
        expect(wipeOf(container, 0)).not.toBeCloseTo(50, 0);
    });

    test("a drag the browser takes for a scroll lets the frame go, rather than freezing it", () => {
        const { container } = renderBand();
        step(0);
        const frame = grab(container, 0, 100, { keepDown: true });

        fireEvent.pointerCancel(frame, { pointerId: 1 });
        wait(3200);
        step(900);
        step(1800);
        expect(wipeOf(container, 0)).not.toBeCloseTo(25, 0);
    });

    test("each frame moves to its next example at the end of a sweep", () => {
        const { container } = renderBand();
        step(0);
        expect(showing(container, 0)).toBe("photo a1");
        expect(showing(container, 1)).toBe("signature s1");

        for (let now = 300; now <= 3600; now += 300) step(now);
        expect(showing(container, 0)).toBe("photo a1");

        for (let now = 3900; now <= 8700; now += 300) step(now);
        expect(showing(container, 0)).toBe("photo a2");
        expect(showing(container, 1)).toBe("signature s2");
    });

    test("a dot chooses an example and holds it, then the cycle resumes", () => {
        const { container } = renderBand();
        step(0);

        fireEvent.click(screen.getAllByRole("button", { name: "Example 3 of 3" })[0]);
        expect(showing(container, 0)).toBe("photo a3");

        // Held: the sweep stays put while the viewer is looking.
        step(900);
        step(1800);
        expect(showing(container, 0)).toBe("photo a3");

        wait(3100);
        for (let now = 2100; now <= 9000; now += 300) step(now);
        expect(showing(container, 0)).toBe("photo a1");
    });

    test("the control stops and starts both frames", () => {
        const { container } = renderBand();
        step(0);
        step(900);
        const [photo, signature] = [wipeOf(container, 0), wipeOf(container, 1)];

        fireEvent.click(screen.getByRole("button", { name: /pause both/i }));
        step(1800);
        step(2700);
        expect(wipeOf(container, 0)).toBeCloseTo(photo, 2);
        expect(wipeOf(container, 1)).toBeCloseTo(signature, 2);

        fireEvent.click(screen.getByRole("button", { name: /play both/i }));
        step(3600);
        step(4500);
        expect(wipeOf(container, 0)).not.toBeCloseTo(photo, 1);
    });

    test("nothing moves when the browser asks for less motion", () => {
        reduceMotion = true;
        const { container } = renderBand();

        expect(screen.getByRole("button", { name: /play both/i })).toBeInTheDocument();
        step(0);
        step(2400);
        expect(wipeOf(container, 0)).toBeCloseTo(50, 0);
        expect(wipeOf(container, 1)).toBeCloseTo(50, 0);
    });

    test("the pair carries a photograph and a signature, each with its examples", () => {
        const { container } = renderBand();

        // Side by side, two equal frames (testing note 1).
        expect(container.querySelector(".euk-band-pair")).toBeInTheDocument();
        expect(container.querySelectorAll(".euk-band-pair .euk-wipe")).toHaveLength(2);
        expect(screen.getByText("Photograph")).toBeInTheDocument();
        expect(screen.getByText("Signature")).toBeInTheDocument();
        expect(screen.getAllByRole("button", { name: /^Example \d of 3$/ })).toHaveLength(3);
        expect(screen.getAllByRole("button", { name: /^Example \d of 2$/ })).toHaveLength(2);
        expect(screen.getByText(/Representational examples/)).toBeInTheDocument();
    });
});
