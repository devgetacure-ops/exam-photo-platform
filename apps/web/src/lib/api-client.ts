import { ProcessImageResponse, JobStatusResponse, PipelineReport } from "./types";

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
