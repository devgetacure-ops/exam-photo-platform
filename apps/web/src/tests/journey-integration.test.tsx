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
    const sentOk = () =>
        vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                sent: true,
                masked_address: "t***@example.com",
                filenames: ["photo.jpg"],
                job_ids: ["job_one"],
            }),
        });
    // Only sends are counted: the form also asks the engine once whether
    // email is set up at all (testing note 18).
    const sendsOf = (fetcher: ReturnType<typeof vi.fn>) => () =>
        fetcher.mock.calls.filter(([url]) => String(url).includes("/email"));

    it("asks for no tick: an address typed before payment is sent once payment is confirmed, once", async () => {
        const fetcher = sentOk();
        vi.stubGlobal("fetch", fetcher);
        const sends = sendsOf(fetcher);
        const { rerender } = render(
            <EmailDelivery
                kitId="kit_before"
                jobIds={["job_one"]}
                released={false}
            />,
        );
        expect(screen.queryByRole("checkbox")).toBeNull();
        fireEvent.change(screen.getByLabelText(/Email address/), {
            target: { value: "test@example.com" },
        });
        expect(sends()).toHaveLength(0);
        rerender(
            <EmailDelivery kitId="kit_before" jobIds={["job_one"]} released />,
        );
        await screen.findByText(/Sent 1 file to t\*\*\*@example.com/);
        expect(sends()).toHaveLength(1);
        expect(JSON.parse(sends()[0][1].body)).toEqual({
            address: "test@example.com",
            job_ids: ["job_one"],
        });
        rerender(
            <EmailDelivery kitId="kit_before" jobIds={["job_one"]} released />,
        );
        await waitFor(() => expect(sends()).toHaveLength(1));
    });
    it("after payment, a half-typed address that already looks valid is never sent by itself", async () => {
        const fetcher = sentOk();
        vi.stubGlobal("fetch", fetcher);
        const sends = sendsOf(fetcher);
        render(
            <EmailDelivery kitId="kit_after" jobIds={["job_one"]} released />,
        );
        const field = screen.getByLabelText(/Email address/);
        fireEvent.change(field, { target: { value: "test@example.co" } });
        fireEvent.change(field, { target: { value: "test@example.com" } });
        await new Promise((resolve) => setTimeout(resolve, 20));
        expect(sends()).toHaveLength(0);
        fireEvent.click(screen.getByRole("button", { name: "Email my files" }));
        await screen.findByText(/Sent 1 file/);
        expect(sends()).toHaveLength(1);
        expect(JSON.parse(sends()[0][1].body).address).toBe("test@example.com");

        // A second tap does not send the same files again.
        const sent = screen.getByRole("button", { name: "Sent" });
        expect(sent).toBeDisabled();
        fireEvent.click(sent);
        await new Promise((resolve) => setTimeout(resolve, 20));
        expect(sends()).toHaveLength(1);

        // A different address is a new request.
        fireEvent.change(field, { target: { value: "other@example.com" } });
        expect(screen.getByRole("button", { name: "Email my files" })).toBeEnabled();
    });
    it("waits for something that looks like an address, before and after payment", async () => {
        const fetcher = sentOk();
        vi.stubGlobal("fetch", fetcher);
        const sends = sendsOf(fetcher);
        const { rerender } = render(
            <EmailDelivery
                kitId="kit_invalid"
                jobIds={["job_one"]}
                released={false}
            />,
        );
        fireEvent.change(screen.getByLabelText(/Email address/), {
            target: { value: "test@gmail" },
        });
        rerender(
            <EmailDelivery kitId="kit_invalid" jobIds={["job_one"]} released />,
        );
        await new Promise((resolve) => setTimeout(resolve, 20));
        expect(sends()).toHaveLength(0);
        expect(
            screen.getByRole("button", { name: "Email my files" }),
        ).toBeDisabled();
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
        fireEvent.click(screen.getByRole("button", { name: "Email my files" }));
        await screen.findByRole("alert");
        await new Promise((resolve) => setTimeout(resolve, 20));
        expect(
            fetcher.mock.calls.filter(([url]) => String(url).includes("/email")),
        ).toHaveLength(1);
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
