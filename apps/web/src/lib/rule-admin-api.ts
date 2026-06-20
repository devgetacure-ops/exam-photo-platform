import { RuleValidationResponse } from "./types";
import { getApiBaseUrl } from "./api-client";

/**
 * Validates a rule JSON object against the backend schema and validation engine.
 */
export async function validateRule(rule: object): Promise<RuleValidationResponse> {
  const apiBaseUrl = getApiBaseUrl();
  const url = new URL("/v1/rules/validate", apiBaseUrl);

  try {
    const response = await fetch(url.toString(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ rule }),
    });

    if (!response.ok) {
      let errorDetail = `Server error (${response.status})`;
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
    if (err instanceof TypeError && err.message.includes("fetch")) {
      throw new Error(
        "The processing API is not reachable. Start it with: python -m exam_photo serve-api --host 127.0.0.1 --port 8000"
      );
    }
    throw new Error(err.message || "An unknown error occurred during rule validation.");
  }
}
