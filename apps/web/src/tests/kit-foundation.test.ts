import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import {
  listExams,
  getExam,
  prepareRequirement,
  planDocument,
  getKitPackage,
  kitPackageDownloadUrl,
} from "../lib/api-client";
import { RequirementNotServedError } from "../lib/types";
import {
  startKit,
  getKit,
  recordPreparation,
  forgetRequirement,
  clearKit,
  isValidKitId,
} from "../lib/kit-state";
import type { PrepareRequirementResponse } from "../lib/types";

describe("catalogue + kit API client", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test("listExams reads /v1/exams", async () => {
    const body = { exams: [], total: 0, unavailable: [], unreadable: {} };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => body }));
    const result = await listExams();
    expect(result.total).toBe(0);
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/v1/exams"));
  });

  test("getExam encodes the id and hits the detail route", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ exam_id: "ssc-cgl-2026" }) })
    );
    await getExam("ssc-cgl-2026");
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/v1/exams/ssc-cgl-2026"));
  });

  test("prepareRequirement sends multipart with the kit id and quality mode", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ job_id: "job_1", outcome: "prepared" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const file = new File(["x"], "sig.png", { type: "image/png" });
    await prepareRequirement({
      examId: "e1",
      requirementId: "signature",
      file,
      kitId: "kit_abc",
    });

    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toContain("/v1/exams/e1/requirements/signature/prepare");
    expect(url).toContain("quality_mode=balanced");
    const form = opts.body as FormData;
    expect(form.get("file")).toBe(file);
    expect(form.get("kit_id")).toBe("kit_abc");
  });

  test("prepareRequirement throws RequirementNotServedError on a 409 gate refusal", async () => {
    const info = {
      detail: "This requirement is completed at the exam centre.",
      exam_id: "e1",
      requirement_id: "live_capture",
      requirement_name: "Live photograph",
      requirement_type: "photograph",
      submission_method: "official_live_capture",
      platform_support: "guidance_only",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 409, json: async () => ({ detail: info }) })
    );

    await expect(
      prepareRequirement({
        examId: "e1",
        requirementId: "live_capture",
        file: new File(["x"], "p.jpg"),
      })
    ).rejects.toBeInstanceOf(RequirementNotServedError);
  });

  test("planDocument appends every file under the 'files' field", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ job_id: "job_2", pages: [], unreadable: {} }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await planDocument({
      examId: "e1",
      requirementId: "certificate",
      files: [new File(["a"], "1.pdf"), new File(["b"], "2.pdf")],
    });

    const form = fetchMock.mock.calls[0][1].body as FormData;
    expect(form.getAll("files")).toHaveLength(2);
  });

  test("getKitPackage and the download URL target the kit routes", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ kit_id: "kit_z", items: [] }) })
    );
    await getKitPackage("kit_z");
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/v1/kits/kit_z/package"));
    expect(kitPackageDownloadUrl("kit_z")).toContain("/v1/kits/kit_z/package/download");
  });
});

describe("kit-state (localStorage)", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  const preparedResponse = (
    requirementId: string,
    outcome: PrepareRequirementResponse["outcome"] = "prepared"
  ): PrepareRequirementResponse => ({
    job_id: `job_${requirementId}`,
    exam_id: "e1",
    requirement_id: requirementId,
    requirement_type: "signature",
    platform_support: "supported",
    status: "SUCCEEDED",
    outcome,
    output_filename: `${requirementId}.png`,
    output_url: `/v1/jobs/job_${requirementId}/output`,
    report_url: `/v1/jobs/job_${requirementId}/report`,
    findings: outcome === "prepared_with_findings" ? ["ceiling was an estimate"] : [],
    issue_codes: [],
  });

  test("startKit mints a valid kit id and is idempotent per exam", () => {
    const first = startKit("e1", "Exam One");
    expect(isValidKitId(first.kitId)).toBe(true);
    const second = startKit("e1");
    expect(second.kitId).toBe(first.kitId);
  });

  test("recordPreparation persists a requirement entry across reads", () => {
    startKit("e1", "Exam One");
    recordPreparation("e1", preparedResponse("signature"));
    const kit = getKit("e1");
    expect(kit?.requirements.signature.jobId).toBe("job_signature");
    expect(kit?.requirements.signature.outcome).toBe("prepared");
  });

  test("a second preparation for the same requirement replaces the first", () => {
    startKit("e1");
    recordPreparation("e1", preparedResponse("signature"));
    const retried = { ...preparedResponse("signature", "prepared_with_findings"), job_id: "job_retry" };
    recordPreparation("e1", retried);
    const kit = getKit("e1");
    expect(kit?.requirements.signature.jobId).toBe("job_retry");
    expect(kit?.requirements.signature.findings).toContain("ceiling was an estimate");
  });

  test("forgetRequirement drops one entry, clearKit drops the kit", () => {
    startKit("e1");
    recordPreparation("e1", preparedResponse("signature"));
    recordPreparation("e1", preparedResponse("photo"));
    forgetRequirement("e1", "signature");
    expect(getKit("e1")?.requirements.signature).toBeUndefined();
    expect(getKit("e1")?.requirements.photo).toBeDefined();
    clearKit("e1");
    expect(getKit("e1")).toBeNull();
  });

  test("a corrupt store reads as empty rather than throwing", () => {
    window.localStorage.setItem("exam-photo:kits:v1", "{not json");
    expect(getKit("e1")).toBeNull();
    expect(() => startKit("e1")).not.toThrow();
  });
});
