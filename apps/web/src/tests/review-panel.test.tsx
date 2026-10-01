import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createRef } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PaymentScene } from "../components/exam/payment-scene";
import { ReviewPanel } from "../components/exam/review-panel";

const TAGS = { good: ["Fast", "Easy to use"], bad: ["Too slow", "Confusing"] };

function mockFetch(state: object, reward: string | null = null) {
    const calls: { url: string; body?: string }[] = [];
    vi.stubGlobal(
        "fetch",
        vi.fn(async (url: URL | string, init?: RequestInit) => {
            calls.push({ url: String(url), body: init?.body as string | undefined });
            if (init?.method === "POST") return new Response(JSON.stringify({ ok: true, reward_code: reward }));
            return new Response(JSON.stringify(state));
        }),
    );
    return calls;
}

afterEach(() => vi.unstubAllGlobals());

describe("the review box (DEC-112)", () => {
    it("offers words that match the stars and sends the review", async () => {
        const calls = mockFetch({ review: null, reward_code: null, offer: true, tags: TAGS }, "THANKS-ABCD1234");
        render(<ReviewPanel kitId="kit_a" orderId="order_1" />);
        expect(await screen.findByText(/next examination’s files are free/)).toBeTruthy();

        fireEvent.click(screen.getByLabelText(/2 stars/));
        expect(screen.getByText("What went wrong?")).toBeTruthy();
        expect(screen.queryByLabelText("Fast")).toBeNull();

        fireEvent.click(screen.getByLabelText(/5 stars/));
        fireEvent.click(screen.getByLabelText("Fast"));
        fireEvent.click(screen.getByText("Send my review"));

        expect(await screen.findByText("THANKS-ABCD1234")).toBeTruthy();
        const sent = JSON.parse(calls.find((c) => c.body)!.body!);
        expect(sent).toMatchObject({ order_id: "order_1", rating: 5, tags: ["Fast"] });
        expect(calls.find((c) => c.body)!.url).toContain("/v1/kits/kit_a/review");
    });

    it("shows an earlier review and its code without asking again", async () => {
        mockFetch({
            review: { rating: 4, tags: ["Fast"], comment: "Good", name: "", may_publish: 0 },
            reward_code: "THANKS-OLD00001",
            offer: true,
            tags: TAGS,
        });
        render(<ReviewPanel kitId="kit_a" orderId="order_1" />);
        expect(await screen.findByText("Thank you for your review")).toBeTruthy();
        expect(screen.getByText("THANKS-OLD00001")).toBeTruthy();
        // Folded to one line: no open form, and no offer of a second code.
        expect(screen.getByText(/You rated us/)).toBeTruthy();
        expect(screen.queryByText("Update my review")).toBeNull();
        expect(screen.queryByText(/Rate us and your next/)).toBeNull();
        fireEvent.click(screen.getByText("Change my review"));
        expect(screen.getByText("Update my review")).toBeTruthy();
    });

    it("folds the form and leads with the code once the review is sent", async () => {
        mockFetch({ review: null, reward_code: null, offer: true, tags: TAGS }, "THANKS-NEW00001");
        render(<ReviewPanel kitId="kit_a" orderId="order_1" />);
        fireEvent.click(await screen.findByLabelText(/5 stars/));
        fireEvent.click(screen.getByText("Send my review"));
        expect(await screen.findByText("THANKS-NEW00001")).toBeTruthy();
        expect(screen.queryByText("Send my review")).toBeNull();
        expect(screen.queryByLabelText(/5 stars/)).toBeNull();
        expect(screen.getByText(/You rated us/)).toBeTruthy();
    });

    it("shows the email link what the order already said, with its one code", async () => {
        const calls = mockFetch({
            review: { rating: 5, tags: [], comment: "", name: "", may_publish: 0 },
            reward_code: "THANKS-OLD00001",
            offer: true,
            tags: TAGS,
        });
        render(<ReviewPanel orderId="order_1" token="0123456789abcdef0123456789abcdef" />);
        expect(await screen.findByText("THANKS-OLD00001")).toBeTruthy();
        expect(screen.getByText(/You rated us/)).toBeTruthy();
        expect(screen.queryByLabelText(/5 stars/)).toBeNull();
        expect(calls[0].url).toContain("/v1/feedback?order_id=order_1&token=0123456789abcdef0123456789abcdef");
    });

    it("uses the signed link when opened from the email", async () => {
        const calls = mockFetch({ review: null, reward_code: null, offer: false, tags: TAGS });
        render(<ReviewPanel orderId="order_1" token="0123456789abcdef0123456789abcdef" />);
        await waitFor(() => expect(screen.getByLabelText(/3 stars/)).toBeTruthy());
        fireEvent.click(screen.getByLabelText(/3 stars/));
        fireEvent.click(screen.getByText("Send my review"));
        await screen.findByText("Thank you for your review");
        const post = calls.find((c) => c.body)!;
        expect(post.url).toContain("/v1/feedback");
        expect(JSON.parse(post.body!).token).toBe("0123456789abcdef0123456789abcdef");
    });
});

describe("the waiting screen", () => {
    it("never says PAID before the payment is confirmed", () => {
        const { container } = render(
            <PaymentScene examName="CTET" facts={[]} title="Payment sent. Confirming it." note="Waiting" headingRef={createRef()} />,
        );
        expect(container.textContent).not.toMatch(/\bPAID\b/);
    });
});
