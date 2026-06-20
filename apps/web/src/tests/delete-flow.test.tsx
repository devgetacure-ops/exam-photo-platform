import React from "react";
import { describe, test, expect, vi, beforeEach, afterEach, Mock } from "vitest";
import { render, fireEvent, screen, act } from "@testing-library/react";
import { ResultPreview } from "../components/result-preview";
import * as api from "../lib/api-client";

vi.mock("../lib/api-client", () => ({
  deleteJob: vi.fn(),
  getOutputBlob: vi.fn(),
}));

describe("Deletion Lifecycle Flow", () => {
  let createMock: Mock;
  let revokeMock: Mock;

  beforeEach(() => {
    createMock = vi.fn().mockReturnValue("blob:http://localhost:3000/preview-mock");
    revokeMock = vi.fn();
    global.URL.createObjectURL = createMock;
    global.URL.revokeObjectURL = revokeMock;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test("delete action clears preview and revokes URLs", async () => {
    const deleteSpy = vi.spyOn(api, "deleteJob").mockResolvedValue(undefined);
    const getBlobSpy = vi.spyOn(api, "getOutputBlob").mockResolvedValue(new Blob());

    const onDeleteMock = vi.fn();

    // Render component
    render(
      <ResultPreview
        jobId="job_xyz123"
        outputFilename="photo.jpg"
        isValid={true}
        onDelete={onDeleteMock}
        outputUrl="/v1/jobs/job_xyz123/output"
      />
    );

    // Wait for preview blob download to settle
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 20));
    });

    expect(getBlobSpy).toHaveBeenCalledWith("job_xyz123");
    expect(createMock).toHaveBeenCalled();

    // Trigger delete action
    const deleteButton = screen.getByRole("button", { name: /Delete Job/i });
    await act(async () => {
      fireEvent.click(deleteButton);
    });

    expect(deleteSpy).toHaveBeenCalledWith("job_xyz123");
    expect(onDeleteMock).toHaveBeenCalled();
    expect(revokeMock).toHaveBeenCalled();

    // Verify deleted state is shown
    expect(screen.getByText("Job Assets Deleted Successfully")).toBeDefined();
  });
});
