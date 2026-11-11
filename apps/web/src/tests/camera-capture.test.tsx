import { afterEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { CameraCapture, inPageCameraAvailable } from "../components/exam/camera-capture";

/**
 * The camera opens inside the page, because Android can discard the tab while
 * its own camera app is open and the photograph is lost (DEC-131).
 */

const media = navigator as Navigator & { mediaDevices?: unknown };

afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    Object.defineProperty(media, "mediaDevices", { value: undefined, configurable: true });
});

function fakeCamera(result: "ok" | "refused") {
    const stop = vi.fn();
    const getUserMedia = vi.fn(async () => {
        if (result === "refused") throw new DOMException("no", "NotAllowedError");
        return { getTracks: () => [{ stop }] } as unknown as MediaStream;
    });
    Object.defineProperty(media, "mediaDevices", {
        value: { getUserMedia },
        configurable: true,
    });
    vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue(undefined);
    return { getUserMedia, stop };
}

async function open(props: Partial<Parameters<typeof CameraCapture>[0]> = {}) {
    const handlers = {
        onCapture: vi.fn(),
        onClose: vi.fn(),
        onUseCameraApp: vi.fn(),
    };
    render(<CameraCapture facing="user" {...handlers} {...props} />);
    await act(async () => {
        await new Promise((resolve) => setTimeout(resolve, 5));
    });
    return handlers;
}

describe("the in-page camera", () => {
    it("is offered only where the browser can show a camera", () => {
        expect(inPageCameraAvailable()).toBe(false);
        fakeCamera("ok");
        expect(inPageCameraAvailable()).toBe(true);
    });

    it("asks for the front camera for a photograph and stops it on cancel", async () => {
        const { getUserMedia, stop } = fakeCamera("ok");
        const { onClose } = await open();
        expect(getUserMedia).toHaveBeenCalledWith(
            expect.objectContaining({ video: expect.objectContaining({ facingMode: "user" }) }),
        );
        expect(screen.getByRole("dialog")).toBeTruthy();
        fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
        expect(onClose).toHaveBeenCalled();
        cleanup();
        expect(stop).toHaveBeenCalled();
    });

    it("offers the camera app when permission is refused", async () => {
        fakeCamera("refused");
        const { onUseCameraApp } = await open();
        expect(screen.getByRole("alert").textContent).toMatch(/wasn’t allowed/);
        fireEvent.click(screen.getByRole("button", { name: "Use the camera app" }));
        expect(onUseCameraApp).toHaveBeenCalled();
    });
});
