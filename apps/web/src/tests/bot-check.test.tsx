import { afterEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, render } from "@testing-library/react";
import { PreparationChallenge } from "../components/exam/preparation-challenge";

/**
 * Every upload box gets its own pass from the bot check, and a fresh one after
 * each attempt (live failure, 11 November 2026).
 */

vi.mock("next/script", () => ({ default: () => null }));

afterEach(() => {
    cleanup();
    vi.useRealTimers();
    delete (window as { turnstile?: unknown }).turnstile;
});

function fakeTurnstile() {
    const rendered: string[] = [];
    const resets: string[] = [];
    window.turnstile = {
        render: (_el, options) => {
            const id = `w${rendered.length}`;
            rendered.push(id);
            options.callback(`pass-${id}`);
            return id;
        },
        reset: (id) => resets.push(id),
        remove: () => {},
    };
    return { rendered, resets };
}

describe("the bot check", () => {
    it("draws a widget in every box, not only the first", async () => {
        vi.useFakeTimers();
        const { rendered } = fakeTurnstile();
        const tokens: string[] = [];
        render(
            <>
                <PreparationChallenge siteKey="k" onToken={(t) => t && tokens.push(t)} />
                <PreparationChallenge siteKey="k" onToken={(t) => t && tokens.push(t)} />
                <PreparationChallenge siteKey="k" onToken={(t) => t && tokens.push(t)} />
            </>,
        );
        await act(async () => {
            vi.advanceTimersByTime(10);
        });
        expect(rendered).toHaveLength(3);
        expect(tokens).toEqual(["pass-w0", "pass-w1", "pass-w2"]);
    });

    it("asks for a fresh pass after each attempt", async () => {
        vi.useFakeTimers();
        const { resets } = fakeTurnstile();
        const onToken = vi.fn();
        const view = render(<PreparationChallenge siteKey="k" onToken={onToken} round={0} />);
        await act(async () => {
            vi.advanceTimersByTime(10);
        });
        view.rerender(<PreparationChallenge siteKey="k" onToken={onToken} round={1} />);
        expect(resets).toEqual(["w0"]);
        expect(onToken).toHaveBeenLastCalledWith("");
    });

    it("waits for the script when it arrives after the box", async () => {
        vi.useFakeTimers();
        const onToken = vi.fn();
        render(<PreparationChallenge siteKey="k" onToken={onToken} />);
        fakeTurnstile();
        await act(async () => {
            vi.advanceTimersByTime(600);
        });
        expect(onToken).toHaveBeenCalledWith("pass-w0");
    });
});
