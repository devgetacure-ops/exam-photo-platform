import { afterEach, describe, expect, it, vi } from "vitest";
import {
    act,
    cleanup,
    fireEvent,
    render,
    screen,
    waitFor,
} from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { EmailDelivery } from "../components/exam/email-delivery";
import { validateRequest } from "../lib/request-store";
import { ExamFacts } from "../components/exam/exam-facts";

afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
});
describe("candidate delivery and evidence", () => {
    it("does not send before release or consent, then sends the reviewed job IDs once", async () => {
        const fetcher = vi
            .fn()
            .mockResolvedValue({
                ok: true,
                json: async () => ({
                    sent: true,
                    masked_address: "t***@example.com",
                    filenames: ["photo.jpg"],
                    job_ids: ["job_one"],
                }),
            });
        vi.stubGlobal("fetch", fetcher);
        const { rerender } = render(
            <EmailDelivery
                kitId="kit_test"
                jobIds={["job_one"]}
                released={false}
            />,
        );
        fireEvent.change(screen.getByLabelText(/Email address/), {
            target: { value: "test@example.com" },
        });
        fireEvent.click(screen.getByRole("checkbox"));
        expect(fetcher).not.toHaveBeenCalled();
        rerender(
            <EmailDelivery kitId="kit_test" jobIds={["job_one"]} released />,
        );
        await screen.findByText(/Sent 1 file to t\*\*\*@example.com/);
        expect(fetcher).toHaveBeenCalledTimes(1);
        expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual({
            address: "test@example.com",
            job_ids: ["job_one"],
        });
        rerender(
            <EmailDelivery kitId="kit_test" jobIds={["job_one"]} released />,
        );
        await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(1));
    });
    it("keeps email failure visible and does not retry without a new action", async () => {
        const fetcher = vi.fn().mockResolvedValue({ ok: false, status: 422 });
        vi.stubGlobal("fetch", fetcher);
        render(
            <EmailDelivery kitId="kit_test" jobIds={["job_one"]} released />,
        );
        fireEvent.change(screen.getByLabelText(/Email address/), {
            target: { value: "test@example.com" },
        });
        fireEvent.click(screen.getByRole("checkbox"));
        await screen.findByRole("alert");
        expect(fetcher).toHaveBeenCalledTimes(1);
        expect(
            screen.getByRole("button", { name: "Try email again" }),
        ).toBeEnabled();
    });
    it("preserves exact fact text, moves on by itself, and can be stopped", () => {
        vi.useFakeTimers();
        render(
            <ExamFacts
                examName="Example exam"
                facts={[
                    {
                        kind: "rejection",
                        text: "Original authority wording; unchanged.",
                        source: "https://example.com/official",
                    },
                    {
                        kind: "format",
                        text: "JPEG only.",
                        source: "https://example.com/rules",
                    },
                ]}
            />,
        );
        expect(
            screen.getByText("Original authority wording; unchanged."),
        ).toBeInTheDocument();

        // It advances on its own, which is what the exam page asks of it.
        const stop = screen.getByRole("button", { name: "Pause" });
        expect(stop).toHaveAttribute("aria-pressed", "true");
        act(() => {
            vi.advanceTimersByTime(9000);
        });
        expect(screen.getByText("JPEG only.")).toBeInTheDocument();

        // And stops when asked, which is what WCAG 2.2.2 asks of it.
        fireEvent.click(stop);
        expect(
            screen.getByRole("button", { name: "Play" }),
        ).toHaveAttribute("aria-pressed", "false");
        act(() => {
            vi.advanceTimersByTime(30000);
        });
        expect(screen.getByText("JPEG only.")).toBeInTheDocument();

        fireEvent.click(screen.getByRole("button", { name: "Next exam fact" }));
        expect(
            screen.getByText("Original authority wording; unchanged."),
        ).toBeInTheDocument();
        vi.useRealTimers();
    });
});
describe("private request validation", () => {
    const valid = {
        kind: "exam",
        exam: "Example exam",
        email: "test@example.com",
        consent: true,
        message: "",
    };
    it("requires explicit consent and a valid email", () => {
        expect(validateRequest(valid)).not.toBeNull();
        expect(validateRequest({ ...valid, consent: false })).toBeNull();
        expect(validateRequest({ ...valid, email: "invalid" })).toBeNull();
    });
    it("rejects bots, missing required content and oversized input", () => {
        expect(validateRequest({ ...valid, website: "spam" })).toBeNull();
        expect(validateRequest({ ...valid, exam: "" })).toBeNull();
        expect(
            validateRequest({ ...valid, kind: "support", message: "" }),
        ).toBeNull();
        expect(
            validateRequest({ ...valid, message: "x".repeat(3001) }),
        ).toBeNull();
    });
});
