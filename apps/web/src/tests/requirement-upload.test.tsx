import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { RequirementUpload } from "../components/exam/requirement-upload";
import { OutcomeResult } from "../components/exam/outcome-result";
import {
    RequirementNotServedError,
    type PrepareRequirementResponse,
} from "../lib/types";
import { TERMS_VERSION } from "../lib/consent";
import * as api from "../lib/api-client";
import * as pdfjs from "../lib/pdfjs";
import { getKit } from "../lib/kit-state";

vi.mock("../lib/api-client", async () => {
    const actual = await vi.importActual<typeof api>("../lib/api-client");
    return { ...actual, prepareRequirement: vi.fn() };
});

vi.mock("../lib/pdfjs", async () => {
    const actual = await vi.importActual<typeof pdfjs>("../lib/pdfjs");
    return { ...actual, isPasswordLocked: vi.fn(async () => false) };
});

const prepareRequirement = vi.mocked(api.prepareRequirement);
const isPasswordLocked = vi.mocked(pdfjs.isPasswordLocked);

function prepared(
    overrides: Partial<PrepareRequirementResponse> = {},
): PrepareRequirementResponse {
    return {
        job_id: "job_1",
        exam_id: "rbi-assistant-panel-year-2025",
        requirement_id: "candidate_signature",
        requirement_type: "signature",
        platform_support: "supported",
        status: "SUCCEEDED",
        outcome: "prepared",
        findings: [],
        issue_codes: [],
        output_filename: "signature.jpg",
        byte_size: 14000,
        ...overrides,
    };
}

function renderUpload() {
    return render(
        <RequirementUpload
            examId="rbi-assistant-panel-year-2025"
            examName="RBI Assistant - Panel Year 2025"
            requirementId="candidate_signature"
            requirementName="Candidate signature"
            requirementType="signature"
        />,
    );
}

function drop(file: File) {
    const input = screen.getByLabelText(/upload for candidate signature/i);
    fireEvent.change(input, { target: { files: [file] } });
}

const image = () =>
    new File(["x".repeat(64)], "sig.jpg", { type: "image/jpeg" });

describe("preparing one requirement", () => {
    beforeEach(() => {
        window.localStorage.clear();
        // Agreed already: these tests are about preparing, and the
        // agreement before an upload has its own (upload-consent.test).
        window.localStorage.setItem("uploadready:terms-accepted", TERMS_VERSION);
        prepareRequirement.mockReset();
    });
    afterEach(() => vi.clearAllMocks());

    test("offers the phone camera without replacing the normal file picker", () => {
        render(
            <RequirementUpload
                examId="example"
                examName="Example exam"
                requirementId="photo"
                requirementName="Photograph"
                requirementType="photograph"
            />,
        );

        expect(
            screen.getByRole("button", { name: "Take a photo now" }),
        ).toBeTruthy();
        expect(
            screen.getByLabelText("Upload for Photograph").hasAttribute("capture"),
        ).toBe(false);
        expect(
            document.querySelector('input[type="file"][capture="user"]'),
        ).toBeTruthy();
    });

    test("honors the candidate's lighting choice and clears the checkout lock", async () => {
        prepareRequirement.mockResolvedValue(
            prepared({
                requirement_type: "photograph",
                requirement_id: "photo",
            }),
        );
        const onWorking = vi.fn();
        render(
            <RequirementUpload
                examId="example"
                examName="Example exam"
                requirementId="photo"
                requirementName="Photograph"
                requirementType="photograph"
                onWorking={onWorking}
            />,
        );
        fireEvent.click(
            screen.getByRole("switch", {
                name: "Intelligent lighting adjustment",
            }),
        );
        fireEvent.change(screen.getByLabelText("Upload for Photograph"), {
            target: { files: [image()] },
        });
        await waitFor(() => expect(prepareRequirement).toHaveBeenCalled());
        expect(prepareRequirement.mock.calls[0][0]).toMatchObject({
            enhancementEnabled: false,
            progressToken: expect.stringMatching(/^prg_/),
        });
        await waitFor(() => expect(onWorking).toHaveBeenLastCalledWith(false));
    });

    test.each([
        [true, 1],
        [false, 0],
    ])(
        "the lighting switch after preparing is offered only when switching shows a difference (switchable %s)",
        async (switchable, switches) => {
            // DEC-095: the engine withholds the alternate when the correction
            // is invisible, so there is nothing for the switch to show.
            prepareRequirement.mockResolvedValue({
                ...prepared({
                    requirement_type: "photograph",
                    requirement_id: "photo",
                }),
                enhancement_enabled: true,
                enhancement_switchable: switchable,
                enhancements_applied: ["Sharpened slightly"],
            } as PrepareRequirementResponse);
            render(
                <RequirementUpload
                    examId="example"
                    examName="Example exam"
                    requirementId="photo"
                    requirementName="Photograph"
                    requirementType="photograph"
                />,
            );
            fireEvent.change(screen.getByLabelText("Upload for Photograph"), {
                target: { files: [image()] },
            });
            await waitFor(() =>
                expect(
                    screen.queryByLabelText("Upload for Photograph"),
                ).toBeNull(),
            );
            expect(
                screen.queryAllByRole("switch", { name: "Intelligent lighting" }),
            ).toHaveLength(switches);
        },
    );

    test("it offers an upload before anything has been done", () => {
        renderUpload();
        expect(screen.getByText(/add a photo of your signature/i)).toBeTruthy();
    });

    test("it says the file is seen before payment", () => {
        renderUpload();
        expect(screen.getByText(/before you pay/i)).toBeTruthy();
    });

    test("a password-protected PDF is turned away before it is uploaded", async () => {
        isPasswordLocked.mockResolvedValueOnce(true);
        render(
            <RequirementUpload
                examId="example"
                examName="Example exam"
                requirementId="marksheet"
                requirementName="Class 10 marksheet"
                requirementType="certificate_scan"
            />,
        );
        fireEvent.change(screen.getByLabelText("Upload for Class 10 marksheet"), {
            target: {
                files: [new File(["%PDF-1.7"], "marksheet.pdf", { type: "application/pdf" })],
            },
        });

        expect(
            await screen.findByText(
                "marksheet.pdf is password-protected, so we can’t open it. Upload a copy of the PDF without a password.",
            ),
        ).toBeTruthy();
        expect(prepareRequirement).not.toHaveBeenCalled();
    });

    test("a PDF the engine refuses for its password says what to upload instead", () => {
        render(
            <OutcomeResult
                result={prepared({
                    requirement_type: "certificate_scan",
                    status: "FAILED",
                    outcome: "not_produced",
                    is_valid: false,
                    issue_codes: ["PDF_PASSWORD_PROTECTED"],
                    findings: [
                        "The PDF is password-protected, so it can't be opened. Upload a copy of the PDF without a password.",
                    ],
                    output_filename: undefined,
                    byte_size: undefined,
                })}
                requirementName="Class 10 marksheet"
                onReplace={() => {}}
            />,
        );

        expect(
            screen.getByText(
                "This PDF is password-protected, so we can’t open it. Upload a copy of the PDF without a password.",
            ),
        ).toBeTruthy();
        expect(screen.getByText(/Nothing has been charged/)).toBeTruthy();
    });

    test("a clean result reports Ready", async () => {
        prepareRequirement.mockResolvedValue(prepared());
        renderUpload();
        drop(image());
        await waitFor(() => expect(screen.getByText("Ready")).toBeTruthy());
    });

    test("findings are a distinct state, not filed under success (WEB-002)", async () => {
        prepareRequirement.mockResolvedValue(
            prepared({
                outcome: "prepared_with_findings",
                findings: [
                    "The 50 KB ceiling is our estimate, not a published figure.",
                ],
            }),
        );
        renderUpload();
        drop(image());
        await waitFor(() =>
            expect(
                screen.getByText(/ready — with something to check/i),
            ).toBeTruthy(),
        );
        expect(screen.getByText(/50 KB ceiling is our estimate/i)).toBeTruthy();
    });

    test("a blocked result explains itself and charges nothing", async () => {
        prepareRequirement.mockResolvedValue(
            prepared({ outcome: "blocked", issue_codes: ["NO_FACE_DETECTED"] }),
        );
        renderUpload();
        drop(image());
        await waitFor(() =>
            expect(
                screen.getByText(/could not prepare this one/i),
            ).toBeTruthy(),
        );
        expect(screen.getByText(/could not find a face/i)).toBeTruthy();
        expect(screen.getByText(/nothing has been charged/i)).toBeTruthy();
    });

    test("a support-gate refusal is guidance, never an error (DEC-056)", async () => {
        prepareRequirement.mockRejectedValue(
            new RequirementNotServedError({
                detail: "The exam photographs you directly at the centre.",
                exam_id: "e1",
                requirement_id: "live_photograph",
                requirement_name: "Live photograph",
                requirement_type: "photograph",
                submission_method: "official_live_capture",
                platform_support: "guidance_only",
            }),
        );
        renderUpload();
        drop(image());
        await waitFor(() =>
            expect(
                screen.getByText(/we do not prepare this one/i),
            ).toBeTruthy(),
        );
        // It must not be dressed as a failure the candidate caused.
        expect(screen.queryByRole("alert")).toBeNull();
        expect(screen.getByText(/photographs you directly/i)).toBeTruthy();
    });

    test("a transport failure is reported as an error", async () => {
        prepareRequirement.mockRejectedValue(
            new Error("The processing API is not reachable."),
        );
        renderUpload();
        drop(image());
        await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    });

    test("engine setup details are not exposed to candidates", async () => {
        prepareRequirement.mockRejectedValue(
            new Error("Run download_birefnet.py to install BiRefNet weights"),
        );
        renderUpload();
        drop(image());
        await waitFor(() =>
            expect(screen.getByRole("alert").textContent).toMatch(
                /temporarily unavailable/i,
            ),
        );
        expect(screen.queryByText(/download_birefnet/i)).toBeNull();
    });

    test("a successful preparation is recorded in the kit (DEC-058)", async () => {
        prepareRequirement.mockResolvedValue(prepared());
        renderUpload();
        drop(image());
        await waitFor(() => expect(screen.getByText("Ready")).toBeTruthy());

        const kit = getKit("rbi-assistant-panel-year-2025");
        expect(kit?.requirements.candidate_signature.jobId).toBe("job_1");
        expect(kit?.kitId).toMatch(/^kit_/);
    });

    test("the kit id travels with the request so the package can gather it", async () => {
        prepareRequirement.mockResolvedValue(prepared());
        renderUpload();
        drop(image());
        await waitFor(() => expect(prepareRequirement).toHaveBeenCalled());
        const call = prepareRequirement.mock.calls[0][0];
        expect(call.kitId).toMatch(/^kit_/);
        expect(call.examId).toBe("rbi-assistant-panel-year-2025");
        expect(call.requirementId).toBe("candidate_signature");
    });

    test("an oversized file is refused before it reaches the network", async () => {
        const huge = new File([new Uint8Array(6 * 1024 * 1024)], "big.jpg", {
            type: "image/jpeg",
        });
        renderUpload();
        drop(huge);
        await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
        expect(prepareRequirement).not.toHaveBeenCalled();
    });
});

describe("the outcome view", () => {
    test("clean output is never exposed as an unpaid preview", () => {
        render(
            <OutcomeResult
                result={prepared({ output_url: "/v1/jobs/job_1/output" })}
                requirementName="Signature"
                onReplace={() => {}}
            />,
        );
        expect(screen.queryByRole("img")).toBeNull();
        expect(
            screen.getByText(/protected preview is not available/i),
        ).toBeTruthy();
    });
    test("the preview is labelled as watermarked until purchase", () => {
        render(
            <OutcomeResult
                result={prepared({
                    preview_url: "/v1/jobs/job_1/preview",
                    preview_watermarked: true,
                })}
                requirementName="Candidate signature"
                onReplace={() => {}}
            />,
        );
        expect(screen.getByText(/watermarked until you buy it/i)).toBeTruthy();
    });

    test("size and dimensions are shown so the candidate can check them", () => {
        render(
            <OutcomeResult
                result={prepared({ width: 140, height: 60, byte_size: 14000 })}
                requirementName="Candidate signature"
                onReplace={() => {}}
            />,
        );
        expect(screen.getByText(/140 × 60 px · 14 KB/)).toBeTruthy();
    });
});

describe("routine normalisation is not a caveat", () => {
    test("a file whose only findings are normalisation notes reads as clean", () => {
        // The API reports any non-empty findings as prepared_with_findings, so an
        // ordinary JPEG arrives carrying INPUT_METADATA_REMOVED. If that showed
        // the amber badge, almost every file would, and the state would stop
        // meaning anything for the findings that matter.
        render(
            <OutcomeResult
                result={prepared({
                    outcome: "prepared_with_findings",
                    findings: [
                        "INPUT_METADATA_REMOVED",
                        "INPUT_COLOUR_MODE_CONVERTED",
                    ],
                })}
                requirementName="Candidate signature"
                onReplace={() => {}}
            />,
        );
        expect(screen.getByText("Ready")).toBeTruthy();
        expect(
            screen.queryByText(/worth checking before you submit/i),
        ).toBeNull();
    });

    test("routine notes are still shown, in the candidate's words", () => {
        render(
            <OutcomeResult
                result={prepared({
                    outcome: "prepared_with_findings",
                    findings: ["INPUT_METADATA_REMOVED"],
                })}
                requirementName="Candidate signature"
                onReplace={() => {}}
            />,
        );
        expect(screen.getByText(/what we changed \(1\)/i)).toBeTruthy();
        expect(screen.getByText(/removed hidden camera data/i)).toBeTruthy();
        // Never the raw code.
        expect(screen.queryByText("INPUT_METADATA_REMOVED")).toBeNull();
    });

    test("a substantive finding still raises the caveat state", () => {
        render(
            <OutcomeResult
                result={prepared({
                    outcome: "prepared_with_findings",
                    findings: [
                        "INPUT_METADATA_REMOVED",
                        "The published minimum of 10000 bytes cannot be reached at the published dimensions.",
                    ],
                })}
                requirementName="Candidate signature"
                onReplace={() => {}}
            />,
        );
        expect(
            screen.getByText(/ready — with something to check/i),
        ).toBeTruthy();
        expect(
            screen.getByText(/published minimum of 10000 bytes/i),
        ).toBeTruthy();
    });

    test("an unrecognised code stays a caveat rather than being hidden", () => {
        // Fail-safe: a code this list has not learned must not be demoted.
        render(
            <OutcomeResult
                result={prepared({
                    outcome: "prepared_with_findings",
                    findings: ["SOME_FUTURE_ENGINE_CODE"],
                })}
                requirementName="Candidate signature"
                onReplace={() => {}}
            />,
        );
        expect(
            screen.getByText(/ready — with something to check/i),
        ).toBeTruthy();
    });
});
