import { afterEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { SimulatedCheckout } from "../components/exam/simulated-checkout";

/**
 * The test payment sheet (DEC-089). It must say it is a test before anything
 * else, and each of its three ways out must reach the checkout's own handler.
 */

function sheet(overrides: Partial<Parameters<typeof SimulatedCheckout>[0]> = {}) {
    const props = {
        amount: "₹8",
        examName: "NEET (UG) 2026",
        onPay: vi.fn(async () => {}),
        onFail: vi.fn(),
        onClose: vi.fn(),
        ...overrides,
    };
    render(<SimulatedCheckout {...props} />);
    return props;
}

describe("the test payment sheet", () => {
    afterEach(() => cleanup());

    test("says it is a test, and that nothing is charged, first", () => {
        sheet();
        expect(screen.getByText("Test payment · nothing is charged")).toBeInTheDocument();
        expect(screen.getByText(/stands in for Razorpay/i)).toBeInTheDocument();
    });

    test("paying settles through the checkout's handler", async () => {
        const props = sheet();
        fireEvent.click(screen.getByRole("button", { name: "Pay ₹8" }));
        await waitFor(() => expect(props.onPay).toHaveBeenCalledTimes(1));
    });

    test("a settlement that fails says so and lets the tester try again", async () => {
        sheet({ onPay: vi.fn(async () => Promise.reject(new Error("down"))) });
        fireEvent.click(screen.getByRole("button", { name: "Pay ₹8" }));
        expect(await screen.findByRole("alert")).toHaveTextContent(/could not be settled/i);
        expect(screen.getByRole("button", { name: "Pay ₹8" })).toBeEnabled();
    });

    test("a failed payment and closing each reach their own handler", () => {
        const props = sheet();
        fireEvent.click(screen.getByRole("button", { name: "Simulate a failed payment" }));
        fireEvent.click(screen.getByRole("button", { name: "Close without paying" }));
        expect(props.onFail).toHaveBeenCalledTimes(1);
        expect(props.onClose).toHaveBeenCalledTimes(1);
        expect(props.onPay).not.toHaveBeenCalled();
    });
});
