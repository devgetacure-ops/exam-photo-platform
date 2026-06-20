import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import { processImage, getJob, deleteJob } from "../lib/api-client";

describe("API Client Wrapper", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test("processImage builds multipart request correctly", async () => {
    const mockResponse = {
      job_id: "job_xyz123",
      status: "SUCCEEDED",
      is_valid: true,
      issue_codes: [],
    };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });
    vi.stubGlobal("fetch", fetchMock);

    const imageFile = new File(["test-image-data"], "photo.jpg", { type: "image/jpeg" });
    const ruleObj = { schema_version: "1.0", image_requirements: {} };

    const result = await processImage({
      image: imageFile,
      ruleJson: ruleObj,
      allowInvalidOutput: true,
    });

    expect(result.job_id).toBe("job_xyz123");
    expect(result.status).toBe("SUCCEEDED");

    // Inspect the mock call parameters
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [calledUrl, calledOptions] = fetchMock.mock.calls[0];

    expect(calledUrl).toContain("/v1/process");
    expect(calledUrl).toContain("allow_invalid_output=true");
    expect(calledOptions.method).toBe("POST");
    expect(calledOptions.body).toBeInstanceOf(FormData);

    const formData = calledOptions.body as FormData;
    expect(formData.get("file")).toBe(imageFile);
    expect(formData.get("rule")).toBe(JSON.stringify(ruleObj));
  });

  test("processImage handles non-200 responses", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: "Invalid rule schema validation failed" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const imageFile = new File([""], "photo.jpg", { type: "image/jpeg" });
    const ruleObj = { schema_version: "1.0", image_requirements: {} };

    await expect(
      processImage({ image: imageFile, ruleJson: ruleObj })
    ).rejects.toThrow("Invalid rule schema validation failed");
  });

  test("getJob fetches metadata correctly", async () => {
    const mockJob = {
      job_id: "job_xyz123",
      status: "PROCESSING",
      created_at: "2026-06-20",
      updated_at: "2026-06-20",
    };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockJob,
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getJob("job_xyz123");
    expect(result.status).toBe("PROCESSING");
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/v1/jobs/job_xyz123"));
  });

  test("deleteJob sends DELETE request", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
    });
    vi.stubGlobal("fetch", fetchMock);

    await deleteJob("job_xyz123");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/v1/jobs/job_xyz123"),
      expect.objectContaining({ method: "DELETE" })
    );
  });
});
