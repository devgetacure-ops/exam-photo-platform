import {
  ProcessImageResponse,
  JobStatusResponse,
  PipelineReport,
  ExamList,
  ExamDetail,
  PrepareRequirementResponse,
  RequirementNotServed,
  RequirementNotServedError,
  DocumentPlan,
  DocumentPage,
  KitPackage,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_EXAM_PHOTO_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * Gets the configured base URL for the local processing API.
 */
export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

/**
 * Submits a candidate photo and rule JSON to the API for synchronous processing.
 */
export async function processImage({
  image,
  ruleJson,
  allowInvalidOutput = false,
}: {
  image: File;
  ruleJson: object;
  allowInvalidOutput?: boolean;
}): Promise<ProcessImageResponse> {
  const formData = new FormData();
  // The FastAPI endpoint expects "file" and "rule"
  formData.append("file", image);
  formData.append("rule", JSON.stringify(ruleJson));

  const url = new URL("/v1/process", API_BASE_URL);
  url.searchParams.append("allow_invalid_output", String(allowInvalidOutput));

  try {
    const response = await fetch(url.toString(), {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      let errorDetail = `Server error (${response.status})`;
      try {
        const errJson = await response.json();
        if (errJson && errJson.detail) {
          errorDetail = errJson.detail;
        }
      } catch {
        // Fallback to HTTP status text
      }
      throw new Error(errorDetail);
    }

    return await response.json();
  } catch (error) {
    const err = error as Error;
    if (err instanceof TypeError && err.message.includes("fetch")) {
      throw new Error(
        "The processing API is not reachable. Start it with: python -m exam_photo serve-api --host 127.0.0.1 --port 8000"
      );
    }
    throw new Error(err.message || "An unknown error occurred during image submission.");
  }
}

/**
 * Queries job status and metadata.
 */
export async function getJob(jobId: string): Promise<JobStatusResponse> {
  const url = new URL(`/v1/jobs/${jobId}`, API_BASE_URL);

  try {
    const response = await fetch(url.toString());
    if (!response.ok) {
      let errorDetail = `Job query failed (${response.status})`;
      try {
        const errJson = await response.json();
        if (errJson && errJson.detail) {
          errorDetail = errJson.detail;
        }
      } catch {
        // ignore
      }
      throw new Error(errorDetail);
    }
    return await response.json();
  } catch (error) {
    const err = error as Error;
    throw new Error(err.message || "Could not retrieve job status.");
  }
}

/**
 * Retrieves the full pipeline validation report.
 */
export async function getReport(jobId: string): Promise<PipelineReport> {
  const url = new URL(`/v1/jobs/${jobId}/report`, API_BASE_URL);

  try {
    const response = await fetch(url.toString());
    if (!response.ok) {
      let errorDetail = `Report query failed (${response.status})`;
      try {
        const errJson = await response.json();
        if (errJson && errJson.detail) {
          errorDetail = errJson.detail;
        }
      } catch {
        // ignore
      }
      throw new Error(errorDetail);
    }
    return await response.json();
  } catch (error) {
    const err = error as Error;
    throw new Error(err.message || "Could not retrieve validation report.");
  }
}

/**
 * Streams the final processed JPEG output candidate as a blob.
 */
export async function getOutputBlob(jobId: string): Promise<Blob> {
  const url = new URL(`/v1/jobs/${jobId}/output`, API_BASE_URL);

  try {
    const response = await fetch(url.toString());
    if (!response.ok) {
      let errorDetail = `Output download failed (${response.status})`;
      try {
        const errJson = await response.json();
        if (errJson && errJson.detail) {
          errorDetail = errJson.detail;
        }
      } catch {
        // ignore
      }
      throw new Error(errorDetail);
    }
    return await response.blob();
  } catch (error) {
    const err = error as Error;
    throw new Error(err.message || "Could not retrieve output image.");
  }
}

// --- Exam catalogue and kit (DEC-055) --------------------------------------

/**
 * Reads `detail` off an error body, tolerating a plain-text or empty response.
 * Kept private so the catalogue calls do not each re-implement it; the older
 * functions above are left as they were.
 */
async function errorDetail(response: Response, fallback: string): Promise<string> {
  try {
    const body = await response.json();
    if (body && typeof body.detail === "string") return body.detail;
    if (body && body.detail && typeof body.detail.detail === "string") {
      return body.detail.detail;
    }
  } catch {
    // no JSON body
  }
  return `${fallback} (${response.status})`;
}

function unreachableApiMessage(err: unknown): Error {
  const e = err as Error;
  if (e instanceof TypeError && e.message.includes("fetch")) {
    // A blocked cross-origin request and a dead server are the same TypeError
    // to the browser, and the service ships with CORS off by default -- so
    // naming only the server sends whoever reads this to restart something
    // that is already running. Both causes are named, in the order they bite.
    return new Error(
      "Could not reach the processing service. Either it is not running " +
        "(start it with: python -m exam_photo serve-api --host 127.0.0.1 --port 8000), " +
        "or it is running without browser access enabled " +
        "(set EXAM_PHOTO_LOCAL_CORS_ENABLED=true before starting it)."
    );
  }
  return new Error(e.message || "An unknown error occurred.");
}

/** Every examination the platform holds a rule for, plus the ones it does not (DEC-056). */
export async function listExams(): Promise<ExamList> {
  const url = new URL("/v1/exams", API_BASE_URL);
  try {
    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error(await errorDetail(response, "Could not load the examination list"));
    }
    return await response.json();
  } catch (error) {
    throw unreachableApiMessage(error);
  }
}

/** One examination with its full inventory and photograph specification. */
export async function getExam(examId: string): Promise<ExamDetail> {
  const url = new URL(`/v1/exams/${encodeURIComponent(examId)}`, API_BASE_URL);
  try {
    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error(await errorDetail(response, "Could not load the examination"));
    }
    return await response.json();
  } catch (error) {
    throw unreachableApiMessage(error);
  }
}

/**
 * Prepare one requirement of one examination. Throws {@link RequirementNotServedError}
 * when the support gate refuses (HTTP 409) so the caller can tell the candidate
 * what to do instead rather than surfacing a bare failure (DEC-056).
 */
export async function prepareRequirement({
  examId,
  requirementId,
  file,
  kitId,
  allowInvalidOutput = false,
  qualityMode = "balanced",
}: {
  examId: string;
  requirementId: string;
  file: File;
  kitId?: string;
  allowInvalidOutput?: boolean;
  qualityMode?: string;
}): Promise<PrepareRequirementResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (kitId) formData.append("kit_id", kitId);

  const url = new URL(
    `/v1/exams/${encodeURIComponent(examId)}/requirements/${encodeURIComponent(
      requirementId
    )}/prepare`,
    API_BASE_URL
  );
  url.searchParams.append("allow_invalid_output", String(allowInvalidOutput));
  url.searchParams.append("quality_mode", qualityMode);

  try {
    const response = await fetch(url.toString(), { method: "POST", body: formData });
    if (response.status === 409) {
      const body = await response.json().catch(() => null);
      const info = body?.detail as RequirementNotServed | undefined;
      if (info && info.platform_support) throw new RequirementNotServedError(info);
    }
    if (!response.ok) {
      throw new Error(await errorDetail(response, "Preparation failed"));
    }
    return await response.json();
  } catch (error) {
    if (error instanceof RequirementNotServedError) throw error;
    throw unreachableApiMessage(error);
  }
}

/**
 * First half of the document pair (DEC-053): upload a set of files and get back
 * the pages they contain, for the candidate to arrange.
 */
export async function planDocument({
  examId,
  requirementId,
  files,
  kitId,
}: {
  examId: string;
  requirementId: string;
  files: File[];
  kitId?: string;
}): Promise<DocumentPlan> {
  const formData = new FormData();
  for (const file of files) formData.append("files", file);
  if (kitId) formData.append("kit_id", kitId);

  const url = new URL(
    `/v1/exams/${encodeURIComponent(examId)}/requirements/${encodeURIComponent(
      requirementId
    )}/documents`,
    API_BASE_URL
  );

  try {
    const response = await fetch(url.toString(), { method: "POST", body: formData });
    if (response.status === 409) {
      const body = await response.json().catch(() => null);
      const info = body?.detail as RequirementNotServed | undefined;
      if (info && info.platform_support) throw new RequirementNotServedError(info);
    }
    if (!response.ok) {
      throw new Error(await errorDetail(response, "Could not read the uploads"));
    }
    return await response.json();
  } catch (error) {
    if (error instanceof RequirementNotServedError) throw error;
    throw unreachableApiMessage(error);
  }
}

/**
 * Second half of the document pair: assemble a planned document. `order` omitted
 * means "every page as it arrived"; a page left out is omitted and a page listed
 * twice is repeated (DEC-053).
 */
export async function assembleDocument(
  jobId: string,
  order?: DocumentPage[]
): Promise<PrepareRequirementResponse> {
  const url = new URL(
    `/v1/documents/${encodeURIComponent(jobId)}/assemble`,
    API_BASE_URL
  );
  try {
    const response = await fetch(url.toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order: order ?? null }),
    });
    if (!response.ok) {
      throw new Error(await errorDetail(response, "Assembly failed"));
    }
    return await response.json();
  } catch (error) {
    throw unreachableApiMessage(error);
  }
}

/** The checklist for a kit, without downloading the archive (DEC-057). */
export async function getKitPackage(kitId: string): Promise<KitPackage> {
  const url = new URL(
    `/v1/kits/${encodeURIComponent(kitId)}/package`,
    API_BASE_URL
  );
  try {
    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error(await errorDetail(response, "Could not build the package"));
    }
    return await response.json();
  } catch (error) {
    throw unreachableApiMessage(error);
  }
}

/** Absolute URL for the kit ZIP. The browser navigates to it; there is no body to stream. */
export function kitPackageDownloadUrl(kitId: string): string {
  return new URL(
    `/v1/kits/${encodeURIComponent(kitId)}/package/download`,
    API_BASE_URL
  ).toString();
}

/** Absolute URL for a produced file, resolving the relative `output_url` the API returns. */
export function jobOutputUrl(jobId: string): string {
  return new URL(`/v1/jobs/${encodeURIComponent(jobId)}/output`, API_BASE_URL).toString();
}

/**
 * Triggers backend deletion of job folder and registry tracking.
 */
export async function deleteJob(jobId: string): Promise<void> {
  const url = new URL(`/v1/jobs/${jobId}`, API_BASE_URL);

  try {
    const response = await fetch(url.toString(), {
      method: "DELETE",
    });

    if (!response.ok) {
      let errorDetail = `Deletion failed (${response.status})`;
      try {
        const errJson = await response.json();
        if (errJson && errJson.detail) {
          errorDetail = errJson.detail;
        }
      } catch {
        // ignore
      }
      throw new Error(errorDetail);
    }
  } catch (error) {
    const err = error as Error;
    throw new Error(err.message || "An error occurred while deleting job resources.");
  }
}
