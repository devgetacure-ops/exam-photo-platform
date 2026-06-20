import React from "react";
import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { RulePreviewCard } from "../components/admin/rule-preview-card";
import { RuleValidationPanel } from "../components/admin/rule-validation-panel";
import { RuleJsonPanel } from "../components/admin/rule-json-panel";
import { RuleEditor } from "../components/admin/rule-editor";
import { setNestedValue } from "../lib/rule-editor-state";

// Mock the validateRule API call globally for components that use it,
// but we will test the actual function directly using vi.importActual.
vi.mock("../lib/rule-admin-api", () => ({
  validateRule: vi.fn(),
}));

describe("Rules Admin Console & Dashboard Components", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  test("admin route locked when NEXT_PUBLIC_ENABLE_RULE_ADMIN is not true", () => {
    render(<RuleEditor apiGateEnabled={false} />);
    
    expect(screen.getByText("Admin Console Gated")).toBeDefined();
    expect(screen.getByText(/NEXT_PUBLIC_ENABLE_RULE_ADMIN=true/i)).toBeDefined();
    expect(screen.getByText(/This flag is only a local accidental-exposure guard. It is not authentication./i)).toBeDefined();
  });

  test("admin route warning renders when enabled", () => {
    render(<RuleEditor apiGateEnabled={true} />);

    expect(screen.getByText("Local Development Rule Configuration Console Active")).toBeDefined();
    expect(screen.getByText(/Do not expose this admin route publicly/i)).toBeDefined();
    expect(screen.queryByText("Admin Console Gated")).toBeNull();
  });

  test("rule editor updates dimension fields", () => {
    const mockRule = {
      schema_version: "1.0",
      rule_id: "rule-test",
      image_requirements: {
        dimensions: {
          mode: "exact",
          width_px: 300,
          height_px: 400,
          aspect_ratio: "3:4",
        },
      },
    };

    const updated = setNestedValue(mockRule, "image_requirements.dimensions.width_px", 350);
    expect(updated.image_requirements.dimensions.width_px).toBe(350);
    expect(mockRule.image_requirements.dimensions.width_px).toBe(300); // verify original copy untouched
  });

  test("rule preview renders exact dimensions", () => {
    const exactRule = {
      status: "official",
      exam: { exam_name: "Exact Exam", conducting_body: "Conduct Board", application_cycle: "2026-A" },
      image_requirements: {
        dimensions: {
          mode: "exact",
          width_px: 600,
          height_px: 600,
          aspect_ratio: "1:1",
        },
      },
    };

    render(<RulePreviewCard rule={exactRule} />);

    expect(screen.getByText("Exact Exam")).toBeDefined();
    expect(screen.getByText(/600 × 600 px/i)).toBeDefined();
    expect(screen.getByText(/Exact aspect: 1:1/i)).toBeDefined();
  });

  test("rule preview renders range dimensions", () => {
    const rangeRule = {
      status: "provisional",
      exam: { exam_name: "Range Exam", conducting_body: "Conduct Board", application_cycle: "2026" },
      image_requirements: {
        dimensions: {
          mode: "range",
          min_width_px: 200,
          max_width_px: 400,
          min_height_px: 300,
          max_height_px: 500,
        },
      },
    };

    render(<RulePreviewCard rule={rangeRule} />);

    expect(screen.getByText("Range Exam")).toBeDefined();
    expect(screen.getByText(/Width: 200-400 px, Height: 300-500 px/i)).toBeDefined();
  });

  test("validation panel renders field-path errors", () => {
    const errors = [
      {
        severity: "error" as const,
        error_code: "RULE_VALIDATION_ERROR",
        field_path: "image_requirements.dimensions.width_px",
        message: "Width is required for exact dimension rules.",
        suggested_resolution: "Provide width_px.",
      },
    ];

    render(<RuleValidationPanel errors={errors} isValid={false} isValidating={false} />);

    expect(screen.getByText("image_requirements.dimensions.width_px")).toBeDefined();
    expect(screen.getByText("Width is required for exact dimension rules.")).toBeDefined();
    expect(screen.getByText("Tip: Provide width_px.")).toBeDefined();
  });

  test("rule JSON export triggers download", () => {
    const ruleObj = { rule_id: "test-rule-id", val: 123 };
    
    // Assign mocks directly for JSDOM
    const createMock = vi.fn().mockReturnValue("blob:mock-url");
    const revokeMock = vi.fn();
    global.URL.createObjectURL = createMock;
    global.URL.revokeObjectURL = revokeMock;

    render(
      <RuleJsonPanel
        rule={ruleObj}
        onImport={vi.fn()}
        isDirty={true}
        validationStatus="unvalidated"
      />
    );

    const downloadButton = screen.getByRole("button", { name: /Export \/ Download JSON/i });
    fireEvent.click(downloadButton);

    expect(createMock).toHaveBeenCalled();
    expect(revokeMock).toHaveBeenCalled();
  });

  test("rule admin API sends POST /v1/rules/validate", async () => {
    const mockValResponse = {
      is_valid: true,
      error_count: 0,
      errors: [],
    };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockValResponse,
    });
    vi.stubGlobal("fetch", fetchMock);

    // Import actual module to test real fetch parameters
    const { validateRule: realValidateRule } = await vi.importActual<
      typeof import("../lib/rule-admin-api")
    >("../lib/rule-admin-api");

    const res = await realValidateRule({ some: "rule" });

    expect(res.is_valid).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toContain("/v1/rules/validate");
    expect(options.method).toBe("POST");
    expect(options.body).toBe(JSON.stringify({ rule: { some: "rule" } }));
  });

  test("Reset/Revert draft behavior functions correctly", async () => {
    const sampleRule = {
      rule_id: "sample-exact-rule",
      schema_version: "1.0",
      image_requirements: {
        dimensions: { mode: "exact", width_px: 300, height_px: 400 },
      },
    };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => sampleRule,
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<RuleEditor apiGateEnabled={true} />);

    // Load sample
    const select = screen.getByRole("combobox");
    await act(async () => {
      fireEvent.change(select, { target: { value: "exact_300x400" } });
    });

    // Verify sample loaded width input
    const widthInput = screen.getByLabelText("Width (pixels)") as HTMLInputElement;
    expect(widthInput.value).toBe("300");
    
    // Change input
    await act(async () => {
      fireEvent.change(widthInput, { target: { value: "350" } });
    });

    // Revert button should be enabled
    const revertBtn = screen.getByRole("button", { name: /Revert Changes/i }) as HTMLButtonElement;
    expect(revertBtn.disabled).toBe(false);

    // Click Revert
    await act(async () => {
      fireEvent.click(revertBtn);
    });

    // Verify reset back to 300
    expect((widthInput as HTMLInputElement).value).toBe("300");
    expect(revertBtn.disabled).toBe(true);
  });
});
