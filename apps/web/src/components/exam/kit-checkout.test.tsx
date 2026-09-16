import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
    cleanup,
    fireEvent,
    render,
    screen,
    waitFor,
} from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import {
    KitCheckout,
    jobDownloadable,
    jobExpired,
    type LiveJob,
} from "./kit-checkout";
import type { ExamDetail } from "../../lib/types";
import type { KitEntry } from "../../lib/kit-state";

vi.mock("../../lib/kit-state", () => ({
    getKit: () => ({ kitId: "kit_test" }),
}));
const entry: KitEntry = {
    jobId: "job_test",
    requirementId: "photo",
    requirementType: "photograph",
    status: "SUCCEEDED",
    outcome: "prepared",
    findings: [],
    updatedAt: "2026-09-07",
    outputFilename: "photo.jpg",
};
const exam = {
    exam_id: "test",
    exam_name: "Test examination",
    requirements: [
        {
            requirement_id: "photo",
            requirement_name: "Photograph",
            platform_support: "supported",
        },
    ],
} as ExamDetail;
const future = () => new Date(Date.now() + 600000).toISOString();
let released = false;
let failQuote = false;
let hiddenFile = false;
let checkoutHandler: (() => void) | undefined;
let failedHandler: (() => void) | undefined;
let failOnOpen = false;
let opened: Record<string, unknown> | undefined;
const requests: { url: string; options?: RequestInit }[] = [];
const fetchMock = vi.fn(async (url: URL | string, options?: RequestInit) => {
    const path = String(url);
    requests.push({ url: path, options });
    if (path.includes("/quote"))
        return {
            ok: !failQuote,
            status: failQuote ? 503 : 200,
            json: async () => ({
                amount_paise: 500,
                list_amount_paise: 800,
                currency: "INR",
                is_payable: true,
                included_free_count: 0,
                lines: [
                    {
                        job_id: hiddenFile ? "job_hidden" : "job_test",
                        reason: "charged",
                    },
                ],
            }),
        };
    if (path.includes("/order"))
        return {
            ok: true,
            json: async () => ({
                amount_paise: 500,
                currency: "INR",
                order_id: "order_test",
                key_id: "rzp_test_example",
            }),
        };
    return {
        ok: true,
        json: async () => ({
            job_id: "job_test",
            status: "SUCCEEDED",
            expires_at: future(),
            entitlement: released ? "released" : "preview_only",
            output_url: "/v1/jobs/job_test/output",
            extendable: true,
        }),
    };
});
beforeEach(() => {
    released = false;
    failQuote = false;
    hiddenFile = false;
    failOnOpen = false;
    failedHandler = undefined;
    requests.length = 0;
    opened = undefined;
    sessionStorage.clear();
    vi.stubGlobal("fetch", fetchMock);
    window.Razorpay = class {
        constructor(options: Record<string, unknown>) {
            opened = options;
            checkoutHandler = options.handler as () => void;
        }
        open() {
            if (failOnOpen) failedHandler?.();
            else checkoutHandler?.();
        }
        on(event: string, callback: () => void) {
            if (event === "payment.failed") failedHandler = callback;
        }
    } as unknown as typeof window.Razorpay;
});
afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    delete window.Razorpay;
});
const show = () =>
    render(
        <KitCheckout exam={exam} entries={{ photo: entry }} onBusy={vi.fn()} />,
    );

describe("payment and retention boundaries", () => {
    it("blocks payment while a prepared file is changing", async () => {
        render(
            <KitCheckout
                exam={exam}
                entries={{ photo: entry }}
                onBusy={vi.fn()}
                preparationBusy
            />,
        );
        const pay = await screen.findByRole("button", { name: "Pay ₹5" });
        fireEvent.click(
            screen.getByRole("checkbox", { name: /I have reviewed/ }),
        );
        expect(pay).toBeDisabled();
        expect(requests.some((r) => r.url.includes("/order"))).toBe(false);
    });
    it("quotes only the selected prepared file IDs", async () => {
        render(
            <KitCheckout
                exam={exam}
                entries={{
                    photo: entry,
                    excluded: {
                        ...entry,
                        requirementId: "excluded",
                        jobId: "job_excluded",
                    },
                }}
                selectedRequirements={[entry.requirementId]}
                onBusy={vi.fn()}
            />,
        );
        await screen.findByRole("button", { name: "Pay ₹5" });
        const quote = requests.find((r) => r.url.includes("/quote"));
        expect(new URL(quote!.url).searchParams.getAll("job_ids")).toEqual([
            entry.jobId,
        ]);
    });
    it("never makes an unpaid, expired or malformed-deadline job downloadable", () => {
        const job: LiveJob = {
            job_id: "job_test",
            status: "SUCCEEDED",
            entitlement: "released",
            output_url: "/output",
            expires_at: future(),
        };
        expect(jobDownloadable(job, Date.now())).toBe(true);
        expect(
            jobDownloadable(
                { ...job, entitlement: "preview_only" },
                Date.now(),
            ),
        ).toBe(false);
        expect(
            jobDownloadable({ ...job, expires_at: "invalid" }, Date.now()),
        ).toBe(false);
        expect(jobDownloadable({ ...job, status: "DELETED" }, Date.now())).toBe(
            false,
        );
        expect(
            jobExpired(
                { ...job, expires_at: new Date(Date.now() - 1).toISOString() },
                Date.now(),
            ),
        ).toBe(true);
    });
    it("uses the server quote, requires review, and waits for entitlement after checkout", async () => {
        show();
        const pay = await screen.findByRole("button", { name: "Pay ₹5" });
        expect(pay).toBeDisabled();
        fireEvent.click(
            screen.getByRole("checkbox", { name: /I have reviewed/ }),
        );
        await waitFor(() => expect(pay).toBeEnabled());
        fireEvent.click(pay);
        await screen.findByText(/Payment submitted/);
        expect(opened?.order_id).toBe("order_test");
        expect(opened?.amount).toBe(500);
        expect(
            requests.find((r) => r.url.includes("/order"))?.options?.body,
        ).toBeUndefined();
        expect(
            screen.queryByRole("link", { name: "Download file" }),
        ).not.toBeInTheDocument();
        released = true;
        fireEvent.click(screen.getByRole("button", { name: "Refresh status" }));
        await screen.findByRole("link", { name: "Download file" });
        expect(requests.some((r) => r.url.includes("/release"))).toBe(false);
    });
    it("a failed payment gets its own state, releases nothing, and leads back to review", async () => {
        failOnOpen = true;
        show();
        const pay = await screen.findByRole("button", { name: "Pay ₹5" });
        fireEvent.click(
            screen.getByRole("checkbox", { name: /I have reviewed/ }),
        );
        await waitFor(() => expect(pay).toBeEnabled());
        fireEvent.click(pay);
        await screen.findByText(/payment didn’t go through/i);
        expect(
            screen.queryByRole("link", { name: "Download file" }),
        ).not.toBeInTheDocument();
        fireEvent.click(
            screen.getByRole("button", { name: "Review and try again" }),
        );
        await screen.findByRole("button", { name: "Pay ₹5" });
    });
    describe("after payment is confirmed", () => {
        const payAndConfirm = async () => {
            show();
            const pay = await screen.findByRole("button", { name: "Pay ₹5" });
            fireEvent.click(
                screen.getByRole("checkbox", { name: /I have reviewed/ }),
            );
            await waitFor(() => expect(pay).toBeEnabled());
            fireEvent.click(pay);
            await screen.findByText(/Payment submitted/);
            released = true;
            fireEvent.click(screen.getByRole("button", { name: "Refresh status" }));
            await screen.findByRole("heading", { name: "Your downloads" });
        };
        const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));
        let scrollTo: ReturnType<typeof vi.fn>;
        beforeEach(() => {
            scrollTo = vi.fn();
            vi.stubGlobal("scrollTo", scrollTo);
        });

        it("shows the success moment, then carries the candidate to the downloads two seconds later", async () => {
            await payAndConfirm();
            expect(
                screen.getByRole("heading", { name: /We’ve prepared the files/ }),
            ).toHaveFocus();
            const before = scrollTo.mock.calls.length;
            await wait(1500);
            expect(scrollTo.mock.calls.length).toBe(before);
            await waitFor(
                () =>
                    expect(
                        screen.getByRole("heading", { name: "Your downloads" }),
                    ).toHaveFocus(),
                { timeout: 2000 },
            );
            expect(scrollTo.mock.calls.length).toBe(before + 1);
        });

        it("a touch during the success moment keeps the candidate where they are", async () => {
            await payAndConfirm();
            const before = scrollTo.mock.calls.length;
            window.dispatchEvent(new Event("touchstart"));
            await wait(2400);
            expect(scrollTo.mock.calls.length).toBe(before);
            expect(
                screen.getByRole("heading", { name: "Your downloads" }),
            ).not.toHaveFocus();
        });

        it("arriving at a kit that is already paid does not move the page", async () => {
            released = true;
            show();
            const downloads = await screen.findByRole("heading", {
                name: "Your downloads",
            });
            const settled = scrollTo.mock.calls.length;
            await wait(2400);
            expect(scrollTo.mock.calls.length).toBe(settled);
            expect(downloads).not.toHaveFocus();
        });
    });
    it("fails closed when the quote cannot be fetched", async () => {
        failQuote = true;
        show();
        await screen.findByText(/Pricing is unavailable/);
        expect(
            screen.getByRole("button", { name: "Checkout unavailable" }),
        ).toBeDisabled();
        expect(requests.some((r) => r.url.includes("/order"))).toBe(false);
    });
    it("will not charge for a server file missing from the displayed review", async () => {
        hiddenFile = true;
        show();
        await screen.findByText(/outside this review/);
        fireEvent.click(
            screen.getByRole("checkbox", { name: /I have reviewed/ }),
        );
        expect(screen.getByRole("button", { name: "Pay ₹5" })).toBeDisabled();
    });
});
