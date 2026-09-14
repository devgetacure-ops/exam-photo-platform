import { afterEach, describe, expect, test, vi } from "vitest";
import { cleanup, render } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

vi.mock("server-only", () => ({}));

import { BusinessContact } from "../components/business-contact";

/**
 * The owner's name and home address never render (owner, 2026-09-14), even on
 * a machine that still has the old variables set. Fictional values only.
 */

afterEach(() => {
    cleanup();
    vi.unstubAllEnvs();
});

function setOldAndNew(extra: Record<string, string> = {}) {
    vi.stubEnv("EUK_BUSINESS_NAME", "Fictional Person Name");
    vi.stubEnv("EUK_BUSINESS_ADDRESS", "12 Imaginary Lane, Nowhere 000000");
    vi.stubEnv("EUK_BUSINESS_PHONE", "+91 00000 00000");
    vi.stubEnv("EUK_BUSINESS_HOURS", "Monday to Saturday, 10 AM to 5 PM");
    for (const [key, value] of Object.entries(extra)) vi.stubEnv(key, value);
}

describe("how to reach the service", () => {
    test("never shows the owner's name or home address", () => {
        setOldAndNew();
        const { container } = render(<BusinessContact />);
        const text = container.textContent ?? "";
        expect(text).not.toContain("Fictional Person Name");
        expect(text).not.toContain("Imaginary Lane");
        expect(text).not.toMatch(/Proprietor\s*$/m);
        expect(text).toContain("Proprietor and Grievance Officer");
        expect(text).toContain("+91 00000 00000");
    });

    test("the grievance officer is the designation alone", () => {
        setOldAndNew();
        const { getByText } = render(<BusinessContact />);
        const cell = getByText(/Proprietor and Grievance Officer/);
        expect(cell.textContent?.startsWith("Proprietor and Grievance Officer")).toBe(true);
    });

    test("a published business address shows only once one is set", () => {
        setOldAndNew();
        const { queryByText, unmount } = render(<BusinessContact />);
        expect(queryByText("Address")).toBeNull();
        unmount();
        setOldAndNew({ EUK_BUSINESS_PUBLIC_ADDRESS: "Unit 1, Fictional Business Park" });
        const again = render(<BusinessContact />);
        expect(again.getByText("Unit 1, Fictional Business Park")).toBeInTheDocument();
    });

    test("nothing renders without a phone and hours", () => {
        vi.stubEnv("EUK_BUSINESS_PHONE", "");
        vi.stubEnv("EUK_BUSINESS_HOURS", "");
        const { container } = render(<BusinessContact />);
        expect(container).toBeEmptyDOMElement();
    });
});
