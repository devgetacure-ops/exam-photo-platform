const MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB
const ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"];

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

/**
 * Validates candidate image properties before submission.
 */
export function validateImageFile(file: File, maxSizeBytes = MAX_IMAGE_SIZE_BYTES): ValidationResult {
  if (!ALLOWED_MIME_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: `Unsupported file type (${file.type}). Allowed formats: JPEG, PNG, WebP.`,
    };
  }

  if (file.size > maxSizeBytes) {
    const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
    const maxMb = (maxSizeBytes / (1024 * 1024)).toFixed(0);
    return {
      valid: false,
      error: `File size is too large (${sizeMb} MB). Maximum allowed size is ${maxMb} MB.`,
    };
  }

  return { valid: true };
}

/**
 * Validates custom rule JSON structure.
 */
export function validateRuleJson(jsonText: string): { valid: boolean; error?: string; data?: unknown } {
  let data: unknown;
  try {
    data = JSON.parse(jsonText);
  } catch {
    return {
      valid: false,
      error: "Invalid JSON format: Failed to parse.",
    };
  }

  if (!data || typeof data !== "object") {
    return {
      valid: false,
      error: "Invalid rule: Schema root must be a JSON object.",
    };
  }

  const obj = data as Record<string, unknown>;

  if (!obj.schema_version) {
    return {
      valid: false,
      error: "Missing required rule property: 'schema_version'.",
    };
  }

  if (!obj.image_requirements || typeof obj.image_requirements !== "object") {
    return {
      valid: false,
      error: "Missing required rule section: 'image_requirements'.",
    };
  }

  return { valid: true, data: obj };
}
