import { describe, test, expect } from "vitest";
import {
  formatBytes,
  describeFileSize,
  describeDimensions,
  describeFormats,
  describeBackground,
  requirementSpecRows,
  photographSpecRows,
  estimateCount,
} from "../lib/spec-format";
import {
  appearanceGuidance,
  liveCaptureStance,
  requiresLiveCapture,
} from "../lib/appearance-rules";
import type { ExamDetail, RequirementSummary } from "../lib/types";

describe("formatting a specification", () => {
  test("bytes become the units a person writes", () => {
    expect(formatBytes(20000)).toBe("20 KB");
    expect(formatBytes(1_000_000)).toBe("1 MB");
    expect(formatBytes(1_500_000)).toBe("1.5 MB");
    expect(formatBytes(0)).toBe("—");
  });

  test("the published figure wins over our byte conversion", () => {
    // The record carries both; the candidate compares against the exam's page.
    expect(
      describeFileSize({
        maximum_bytes: 20000,
        minimum_bytes: 10000,
        published_minimum: 10,
        published_maximum: 20,
        size_unit_as_published: "KB",
      })
    ).toBe("10–20 KB");
  });

  test("a published unit is normalised for display, not the figure", () => {
    // Records transcribe the notification's own casing: "kb" appears alongside
    // "KB" across the catalogue, and showing both looks like sloppiness.
    expect(
      describeFileSize({
        published_minimum: 20,
        published_maximum: 50,
        size_unit_as_published: "kb",
      })
    ).toBe("20–50 KB");
  });

  test("without a published form it falls back to converted bytes", () => {
    expect(describeFileSize({ maximum_bytes: 400000 })).toBe("up to 400 KB");
    expect(describeFileSize({ minimum_bytes: 5000 })).toBe("at least 5 KB");
    expect(describeFileSize(undefined)).toBeNull();
  });

  test("exact dimensions read as exact", () => {
    expect(describeDimensions({ mode: "exact", width_px: 1200, height_px: 1200 })).toBe(
      "1200 × 1200 px"
    );
  });

  test("a preferred size is shown rather than dropped", () => {
    // Several bodies publish a preferred pixel size without mandating it. That
    // is a real published figure and the size we aim for.
    expect(
      describeDimensions({
        mode: "unspecified",
        preferred_width_px: 200,
        preferred_height_px: 230,
      })
    ).toBe("200 × 230 px preferred");
  });

  test("a range reads as a range", () => {
    expect(
      describeDimensions({
        mode: "range",
        min_width_px: 100,
        max_width_px: 200,
        min_height_px: 100,
        max_height_px: 200,
      })
    ).toBe("100–200 × 100–200 px");
  });

  test("jpg and jpeg are one format, not two", () => {
    expect(describeFormats({ allowed_formats: ["jpg", "jpeg"] })).toBe("JPEG");
    expect(describeFormats({ allowed_formats: ["jpg", "png"] })).toBe("JPEG or PNG");
  });

  test("background modes read as instructions", () => {
    expect(describeBackground({ mode: "plain_light" })).toBe("Plain, light");
    expect(
      describeBackground({ mode: "exact_colour", required_colour: "#FFFFFF" })
    ).toBe("Plain #FFFFFF");
  });
});

describe("marking platform estimates (DEC-057)", () => {
  const requirement: RequirementSummary = {
    requirement_id: "signature",
    requirement_name: "Candidate signature",
    requirement_type: "signature",
    submission_method: "file_upload",
    requirement_status: "mandatory",
    platform_support: "supported",
    rejection_conditions: [],
    file_spec: { file_size: { maximum_bytes: 20000, minimum_bytes: 10000 } },
  };

  test("an interim default is flagged", () => {
    const rows = requirementSpecRows(requirement, 1, {
      "requirements[1].file_spec.file_size.maximum_bytes": { type: "interim_default" },
    });
    expect(rows.find((row) => row.term === "File size")?.estimated).toBe(true);
  });

  test("an official value is not flagged", () => {
    const rows = requirementSpecRows(requirement, 1, {
      "requirements[1].file_spec.file_size.maximum_bytes": { type: "official" },
    });
    expect(rows.find((row) => row.term === "File size")?.estimated).toBe(false);
  });

  test("provenance for a different requirement does not leak across", () => {
    const rows = requirementSpecRows(requirement, 1, {
      "requirements[2].file_spec.file_size.maximum_bytes": { type: "interim_default" },
    });
    expect(rows.find((row) => row.term === "File size")?.estimated).toBe(false);
  });

  test("half an estimated range still marks the row", () => {
    // A displayed phrase is assembled from several fields; showing "10-20 KB"
    // unmarked when the maximum was invented is the failure DEC-057 prevents.
    const rows = requirementSpecRows(requirement, 0, {
      "requirements[0].file_spec.file_size.minimum_bytes": { type: "interim_default" },
    });
    expect(rows.find((row) => row.term === "File size")?.estimated).toBe(true);
  });
});

function examWith(overrides: Partial<ExamDetail>): ExamDetail {
  return {
    exam_id: "x",
    exam_name: "X",
    conducting_body: "Y",
    examination_year: 2026,
    application_cycle: "2026",
    aliases: [],
    status: "verified",
    rule_id: "r",
    rule_version: "1",
    requirements: [],
    requirement_counts: {},
    image_requirements: {},
    provenance: {},
    source_evidence: [],
    verification_status: "verified",
    application_rejection_conditions: [],
    ...overrides,
  };
}

describe("the photograph specification", () => {
  test("is read from image_requirements, not a file_spec (DEC-047)", () => {
    const exam = examWith({
      image_requirements: {
        dimensions: { mode: "exact", width_px: 1200, height_px: 1200 },
        file_size: { maximum_bytes: 1_000_000 },
        formats: { allowed_formats: ["jpg"] },
        background: { mode: "plain_light" },
      },
    });
    const rows = photographSpecRows(exam);
    expect(rows.map((row) => row.term)).toEqual([
      "Dimensions",
      "File size",
      "Format",
      "Background",
    ]);
    expect(rows[0].value).toBe("1200 × 1200 px");
  });

  test("estimates across the record are counted", () => {
    const exam = examWith({
      provenance: {
        a: { type: "interim_default" },
        b: { type: "official" },
        c: { type: "interim_default" },
      },
    });
    expect(estimateCount(exam)).toBe(2);
  });
});

describe("live capture is not the same as no upload", () => {
  const liveOnly = { appearance: { live_capture_required: true } };

  test("the flag is read as set", () => {
    expect(requiresLiveCapture(liveOnly)).toBe(true);
    expect(requiresLiveCapture({})).toBe(false);
  });

  test("with a photograph we prepare, the live capture is ADDITIONAL", () => {
    // 16 of 39 exams set this flag and still require an uploaded photograph.
    // Telling those candidates there is nothing to upload would have them skip
    // the file we prepare.
    expect(liveCaptureStance(liveOnly, true)).toBe("additional");
  });

  test("with no photograph we prepare, it replaces the upload", () => {
    expect(liveCaptureStance(liveOnly, false)).toBe("instead");
  });

  test("without the flag there is nothing to say", () => {
    expect(liveCaptureStance({}, true)).toBe("none");
    expect(liveCaptureStance({}, false)).toBe("none");
  });
});

describe("photograph guidance from the exam's own record", () => {
  test("a conditional headwear rule keeps its condition in full", () => {
    const items = appearanceGuidance({
      appearance: {
        headwear: {
          policy: "conditional",
          condition:
            "Prohibited except for religious reasons; full facial features must remain visible.",
          source_wording: "except for religious reasons",
        },
      },
    });
    const headwear = items.find((item) => item.id === "headwear");
    expect(headwear?.verdict).toBe("conditional");
    expect(headwear?.detail).toContain("religious reasons");
    expect(headwear?.sourceWording).toBe("except for religious reasons");
  });

  test("nothing is invented when the record is silent", () => {
    expect(appearanceGuidance({})).toEqual([]);
  });

  test("a required imprint says plainly that we cannot add it", () => {
    const items = appearanceGuidance({
      appearance: {
        imprint: {
          policy: "required",
          fields: ["candidate_name", "photograph_date"],
          position: "bottom",
        },
      },
    });
    const imprint = items.find((item) => item.id === "imprint");
    expect(imprint?.detail).toContain("your name");
    expect(imprint?.detail).toContain("We cannot add that");
  });

  test("rules are ordered by what gets you rejected first", () => {
    const items = appearanceGuidance({
      appearance: {
        recency_maximum_days: 180,
        face_mask: { policy: "prohibited" },
        spectacles: { policy: "conditional", condition: "No glare." },
      },
    });
    expect(items.map((item) => item.verdict)).toEqual([
      "prohibited",
      "conditional",
      "required",
    ]);
  });

  test("recency is translated into months as well as days", () => {
    const items = appearanceGuidance({ appearance: { recency_maximum_days: 180 } });
    expect(items[0].detail).toContain("180 days");
    expect(items[0].detail).toContain("6 months");
  });
});
