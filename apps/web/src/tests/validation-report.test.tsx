import React from "react";
import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ValidationReport } from "../components/validation-report";
import { PipelineReport } from "../lib/types";

describe("ValidationReport Component", () => {
  test("does not render encoded_bytes in HTML output", () => {
    const report: PipelineReport = {
      is_valid: true,
      rule_compliant: true,
      visual_quality_acceptable: true,
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
      rule_compliant: false,
      visual_quality_acceptable: false,
      issue_codes: ["ERR_1"],
      stage_reports: [
        { stage: "rule_validation", status: "passed" },
        { stage: "face_detection", status: "warning" },
        { stage: "subject_segmentation", status: "failed", error: "Stage C failed" },
        { stage: "output_preparation", status: "skipped" },
        { stage: "crop_planning", status: "not_started" },
      ],
    };

    render(<ValidationReport report={report} />);

    expect(screen.getByText("Rule Validation")).toBeDefined();
    expect(screen.getByText("passed")).toBeDefined();

    expect(screen.getByText("Face Detection")).toBeDefined();
    expect(screen.getByText("warning")).toBeDefined();

    expect(screen.getByText("Subject Segmentation")).toBeDefined();
    expect(screen.getByText("failed")).toBeDefined();
    expect(screen.getByText("Stage C failed")).toBeDefined();

    expect(screen.getByText("Output Preparation")).toBeDefined();
    expect(screen.getByText("skipped")).toBeDefined();

    expect(screen.getByText("Crop Planning")).toBeDefined();
    expect(screen.getByText("not_started")).toBeDefined();
  });
});
