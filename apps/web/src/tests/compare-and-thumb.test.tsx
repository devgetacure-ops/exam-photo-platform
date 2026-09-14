import { afterEach, describe, expect, test } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { FileComparison } from "../components/file-comparison";
import { PreviewThumb } from "../components/exam/preview-thumb";

/**
 * Testing notes 6 and 7: the comparison drags from anywhere on the picture,
 * and the review shows each preview small with a larger view on a tap.
 */

afterEach(cleanup);

function clipOf(container: HTMLElement): string {
    return (container.querySelector(".comparison-before") as HTMLElement).style.clipPath;
}

describe("dragging the comparison", () => {
    test("a press anywhere on the picture moves the divider there", () => {
        const { container } = render(<FileComparison before="/a.jpg" after="/b.jpg" />);
        const frame = screen.getByTestId("comparison-frame");
        frame.getBoundingClientRect = () => ({ left: 100, width: 400 }) as DOMRect;

        fireEvent.pointerDown(frame, { clientX: 200, pointerId: 1 });
        expect(clipOf(container)).toBe("inset(0 75% 0 0)");

        fireEvent.pointerMove(frame, { clientX: 420, pointerId: 1 });
        expect(clipOf(container)).toBe("inset(0 20% 0 0)");
    });

    test("the divider never leaves the picture", () => {
        const { container } = render(<FileComparison before="/a.jpg" after="/b.jpg" />);
        const frame = screen.getByTestId("comparison-frame");
        frame.getBoundingClientRect = () => ({ left: 0, width: 300 }) as DOMRect;
        fireEvent.pointerDown(frame, { clientX: -80, pointerId: 1 });
        expect(clipOf(container)).toBe("inset(0 100% 0 0)");
        fireEvent.pointerDown(frame, { clientX: 900, pointerId: 1 });
        expect(clipOf(container)).toBe("inset(0 0% 0 0)");
    });

    test("the keyboard still works, through the range", () => {
        const { container } = render(<FileComparison before="/a.jpg" after="/b.jpg" />);
        fireEvent.change(screen.getByRole("slider"), { target: { value: "30" } });
        expect(clipOf(container)).toBe("inset(0 70% 0 0)");
    });

    test("the caption says the download is unmarked, not that the preview is poor", () => {
        render(<FileComparison before="/a.jpg" after="/b.jpg" />);
        expect(screen.getByText(/your download is the full, unmarked file/i)).toBeInTheDocument();
        expect(screen.queryByText(/reduced-resolution/i)).toBeNull();
    });
});

describe("the preview in the review", () => {
    test("a tap opens it larger, and Close puts it away", () => {
        const { container } = render(<PreviewThumb src="https://engine/p.jpg" name="Candidate photograph" />);
        fireEvent.click(screen.getByRole("button", { name: "See the Candidate photograph preview larger" }));
        const dialog = container.querySelector("dialog") as HTMLDialogElement;
        expect(dialog).toHaveAttribute("open");
        expect(screen.getByAltText("Candidate photograph, watermarked preview")).toBeInTheDocument();

        fireEvent.click(screen.getByRole("button", { name: "Close" }));
        expect(dialog).not.toHaveAttribute("open");
    });
});
