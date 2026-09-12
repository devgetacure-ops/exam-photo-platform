import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { PrepareFlow } from "../components/m/prepare-flow";
import type { ExamDetail } from "../lib/types";

/**
 * The phone flow. The uploaders and the checkout are stubbed: what is under
 * test here is the flow itself — which screen you are on, what the action bar
 * offers, and that the back button walks back through the steps instead of
 * leaving the site.
 */

vi.mock("../components/exam/requirement-upload", () => ({
    RequirementUpload: ({ requirementName }: { requirementName: string }) => (
        <div data-testid="uploader">Upload for {requirementName}</div>
    ),
}));

vi.mock("../components/exam/document-workspace", () => ({
    DocumentWorkspace: ({ requirementName }: { requirementName: string }) => (
        <div data-testid="documents">Documents for {requirementName}</div>
    ),
}));

vi.mock("../components/exam/kit-checkout", () => ({
    KitCheckout: () => <div data-testid="checkout">Checkout</div>,
}));

function requirement(
    id: string,
    name: string,
    type: string,
    status: "mandatory" | "conditional" = "mandatory",
) {
    return {
        requirement_id: id,
        requirement_name: name,
        requirement_type: type,
        requirement_status: status,
        platform_support: "supported",
        file_spec: null,
    };
}

const exam = {
    exam_id: "test-exam",
    exam_name: "Test Examination",
    conducting_body: "A Board",
    provenance: {},
    source_evidence: [],
    image_requirements: null,
    requirements: [
        requirement("photo", "Recent photograph", "photograph"),
        requirement("sign", "Candidate signature", "signature"),
        requirement("marks", "Class 10 certificate", "certificate_scan"),
        requirement("extra", "Scribe certificate", "certificate_scan", "conditional"),
        {
            ...requirement("portal", "Portal declaration", "other"),
            platform_support: "not_supported",
        },
    ],
} as unknown as ExamDetail;

function actionBar(): HTMLElement {
    return document.querySelector(".euk-actionbar") as HTMLElement;
}

describe("the phone flow", () => {
    beforeEach(() => {
        window.localStorage.clear();
        window.history.replaceState(null, "");
    });
    afterEach(() => cleanup());

    test("it opens on the files this examination asks for, with the price", () => {
        render(<PrepareFlow exam={exam} />);

        expect(screen.getByText(/asks you to upload/i)).toBeInTheDocument();
        // Ours are offered as files; the portal's own declaration is not, and
        // is named as the candidate's own work instead.
        const files = document.querySelector(".euk-m-files") as HTMLElement;
        expect(within(files).getByText("Recent photograph")).toBeInTheDocument();
        expect(within(files).queryByText("Portal declaration")).toBeNull();
        const yours = document.querySelector(".euk-m-yours") as HTMLElement;
        expect(within(yours).getByText("Portal declaration")).toBeInTheDocument();

        // The three required files are ticked, the conditional one is not, and
        // the certificate among them is free.
        expect(within(actionBar()).getByText("₹5")).toBeInTheDocument();
        expect(within(actionBar()).getByText(/3 files, 1 free/)).toBeInTheDocument();
    });

    test("unticking a file changes what is charged", () => {
        render(<PrepareFlow exam={exam} />);

        fireEvent.click(screen.getByRole("checkbox", { name: /Recent photograph/i }));
        expect(within(actionBar()).getByText("₹3")).toBeInTheDocument();
        expect(within(actionBar()).getByText(/2 files, 1 free/)).toBeInTheDocument();
    });

    test("the action moves to the next screen, and the marks follow", () => {
        const { container } = render(<PrepareFlow exam={exam} />);
        const marks = () =>
            [...container.querySelectorAll(".euk-m-steps li")].map(
                (li) => (li as HTMLElement).dataset.state ?? "-",
            );

        expect(marks()).toEqual(["now", "-", "-"]);
        fireEvent.click(screen.getByRole("button", { name: "Add your files" }));

        expect(screen.getByText("Add your files")).toBeInTheDocument();
        expect(marks()).toEqual(["done", "now", "-"]);
        // Nothing is prepared yet, so there is nothing to check.
        expect(screen.getByRole("button", { name: /Check 0 of 3/ })).toBeDisabled();
    });

    test("a file opens on its own screen, with its rules a tap away", () => {
        render(<PrepareFlow exam={exam} />);
        fireEvent.click(screen.getByRole("button", { name: "Add your files" }));
        fireEvent.click(screen.getByRole("button", { name: /Recent photograph/ }));

        expect(screen.getByTestId("uploader")).toBeInTheDocument();
        expect(
            screen.getByRole("heading", { level: 1, name: "Recent photograph" }),
        ).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Rules" })).toBeInTheDocument();
    });

    test("a document requirement gets the page arranger, not the image uploader", () => {
        render(<PrepareFlow exam={exam} />);
        fireEvent.click(screen.getByRole("button", { name: "Add your files" }));
        fireEvent.click(screen.getByRole("button", { name: /Class 10 certificate/ }));

        expect(screen.getByTestId("documents")).toBeInTheDocument();
        expect(screen.queryByTestId("uploader")).toBeNull();
    });

    test("the back button walks back through the flow", () => {
        render(<PrepareFlow exam={exam} />);
        fireEvent.click(screen.getByRole("button", { name: "Add your files" }));
        fireEvent.click(screen.getByRole("button", { name: /Recent photograph/ }));
        expect(screen.getByTestId("uploader")).toBeInTheDocument();

        // What the browser sends on a back gesture.
        fireEvent.popState(window, { state: { euk: { step: "add", requirement: null } } });
        expect(screen.queryByTestId("uploader")).toBeNull();
        expect(screen.getByText("Add your files")).toBeInTheDocument();

        fireEvent.popState(window, { state: null });
        expect(screen.getByText(/asks you to upload/i)).toBeInTheDocument();
    });

    test("the selection is kept for the next visit, and shared with the desktop kit", () => {
        const { unmount } = render(<PrepareFlow exam={exam} />);
        fireEvent.click(screen.getByRole("checkbox", { name: /Candidate signature/i }));
        unmount();

        const stored = window.localStorage.getItem("uploadready:selection:test-exam");
        expect(stored).toBeTruthy();
        expect(JSON.parse(stored as string)).not.toContain("sign");
    });
});
