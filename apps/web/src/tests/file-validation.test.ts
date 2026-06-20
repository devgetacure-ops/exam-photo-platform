import { describe, test, expect } from "vitest";
import { validateImageFile, validateRuleJson } from "../lib/file-validation";

describe("File Validation Utilities", () => {
  describe("validateImageFile", () => {
    test("accepts JPEG/PNG/WebP", () => {
      const jpeg = new File([""], "test.jpg", { type: "image/jpeg" });
      const png = new File([""], "test.png", { type: "image/png" });
      const webp = new File([""], "test.webp", { type: "image/webp" });

      expect(validateImageFile(jpeg).valid).toBe(true);
      expect(validateImageFile(png).valid).toBe(true);
      expect(validateImageFile(webp).valid).toBe(true);
    });

    test("rejects non-image files", () => {
      const text = new File([""], "test.txt", { type: "text/plain" });
      const result = validateImageFile(text);

      expect(result.valid).toBe(false);
      expect(result.error).toContain("Unsupported file type");
    });

    test("rejects oversized files", () => {
      // Create a 6MB dummy file
      const dummyBuffer = new ArrayBuffer(6 * 1024 * 1024);
      const largeFile = new File([dummyBuffer], "large.jpg", { type: "image/jpeg" });

      const result = validateImageFile(largeFile, 5 * 1024 * 1024);
      expect(result.valid).toBe(false);
      expect(result.error).toContain("File size is too large");
    });
  });

  describe("validateRuleJson", () => {
    test("accepts valid rule JSON structure", () => {
      const validRule = {
        schema_version: "1.0",
        image_requirements: {
          dimensions: { mode: "exact", width_px: 300, height_px: 400 },
        },
      };

      const result = validateRuleJson(JSON.stringify(validRule));
      expect(result.valid).toBe(true);
      const data = result.data as Record<string, unknown>;
      expect(data.schema_version).toBe("1.0");
    });

    test("rejects invalid JSON string", () => {
      const result = validateRuleJson("{ bad json ");
      expect(result.valid).toBe(false);
      expect(result.error).toContain("Invalid JSON format");
    });

    test("rejects JSON without schema_version or image_requirements", () => {
      const missingVersion = {
        image_requirements: {},
      };
      const missingReqs = {
        schema_version: "1.0",
      };

      expect(validateRuleJson(JSON.stringify(missingVersion)).valid).toBe(false);
      expect(validateRuleJson(JSON.stringify(missingReqs)).valid).toBe(false);
    });
  });
});
