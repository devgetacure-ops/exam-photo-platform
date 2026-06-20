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
});
