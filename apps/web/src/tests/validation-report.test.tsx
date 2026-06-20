import React from "react";
import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ValidationReport } from "../components/validation-report";
import { PipelineReport } from "../lib/types";

describe("ValidationReport Component", () => {
  test("does not render encoded_bytes in HTML output", () => {
    const report: PipelineReport = {
      is_valid: true,
      issue_codes: [],
      final_width: 300,
      final_height: 400,
      final_format: "JPEG",
      final_bytes: 12345,
      selected_crop_mode: "CropModeA",
      stage_reports: [],
      encoded_bytes: "sensitive_base64_data_here",
    };

    const { container } = render(<ValidationReport report={report} />);

    // Verify basic compliant text renders
    expect(screen.getByText("Compliant")).toBeDefined();

    // Verify encoded_bytes string is not present in the HTML output
    expect(container.innerHTML).not.toContain("sensitive_base64_data_here");
    expect(container.innerHTML).not.toContain("encoded_bytes");
  });

  test("correctly renders various stage report statuses", () => {
    const report: PipelineReport = {
      is_valid: false,
      issue_codes: ["ERR_1"],
      stage_reports: [
        { stage: "Stage A", status: "passed" },
        { stage: "Stage B", status: "warning" },
        { stage: "Stage C", status: "failed", error: "Stage C failed" },
        { stage: "Stage D", status: "skipped" },
        { stage: "Stage E", status: "not_started" },
      ],
    };

    render(<ValidationReport report={report} />);

    expect(screen.getByText("Stage A")).toBeDefined();
    expect(screen.getByText("passed")).toBeDefined();

    expect(screen.getByText("Stage B")).toBeDefined();
    expect(screen.getByText("warning")).toBeDefined();

    expect(screen.getByText("Stage C")).toBeDefined();
    expect(screen.getByText("failed")).toBeDefined();
    expect(screen.getByText("Stage C failed")).toBeDefined();

    expect(screen.getByText("Stage D")).toBeDefined();
    expect(screen.getByText("skipped")).toBeDefined();

    expect(screen.getByText("Stage E")).toBeDefined();
    expect(screen.getByText("not_started")).toBeDefined();
  });
});
