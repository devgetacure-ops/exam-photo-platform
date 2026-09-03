/**
 * Turning a rule record's raw specification into something a candidate reads.
 *
 * Two rules govern everything here.
 *
 * **Show the figure the examination published, not our conversion of it.** A
 * record carries both — `published_maximum: 20` with
 * `size_unit_as_published: "KB"` is what the notification said, and
 * `maximum_bytes: 20000` is what we derived so the engine can hit it. The
 * candidate is going to compare what we show against their exam's own page, so
 * we show theirs and keep ours for the pipeline.
 *
 * **A value we invented is never displayed as a published fact.** 86 values
 * across the catalogue are `interim_default` — a specification the platform
 * chose because no body published one. DEC-057 settled how to say so: a quiet
 * per-field marker in the app, explicit naming in the delivered report. Quiet,
 * because a candidate cannot act on it — they cannot research the figure and
 * ours is the best available — but never absent, because it must not read as
 * something the exam said.
 */

import type { ExamDetail, RequirementSummary } from "./types";

/** One line of a specification, as displayed. */
export interface SpecRow {
  term: string;
  value: string;
  /** True when this figure is the platform's estimate, not a published one. */
  estimated: boolean;
}

type Provenance = ExamDetail["provenance"];

/**
 * Bytes as a person writes them.
 *
 * Decimal units, because that is the reading Indian examination notifications
 * use when they say "20 KB" and the one the engine's conversion assumes.
 */
export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "—";
  if (bytes >= 1_000_000) {
    const mb = bytes / 1_000_000;
    return `${Number.isInteger(mb) ? mb : mb.toFixed(1)} MB`;
  }
  if (bytes >= 1000) return `${Math.round(bytes / 1000)} KB`;
  return `${bytes} bytes`;
}

interface FileSize {
  minimum_bytes?: number;
  maximum_bytes?: number;
  published_minimum?: number;
  published_maximum?: number;
  size_unit_as_published?: string;
}

/**
 * A file-size constraint as one phrase.
 *
 * Prefers the published figures and their published unit; falls back to
 * formatting our byte conversion when the record carries no published form.
 */
export function describeFileSize(raw: unknown): string | null {
  const size = raw as FileSize | undefined;
  if (!size) return null;

  // Records carry the unit exactly as the notification wrote it, which means
  // "kb", "Kb" and "KB" all appear across the catalogue. The figure is the
  // exam's; the casing is just transcription, and showing "20-50 kb" next to
  // another exam's "10-20 KB" reads as sloppiness on a page selling precision.
  const unit = normaliseUnit(size.size_unit_as_published);
  if (unit && size.published_maximum !== undefined) {
    const max = `${size.published_maximum} ${unit}`;
    if (size.published_minimum !== undefined) {
      return `${size.published_minimum}–${max}`;
    }
    return `up to ${max}`;
  }

  if (size.maximum_bytes !== undefined) {
    if (size.minimum_bytes !== undefined) {
      return `${formatBytes(size.minimum_bytes)}–${formatBytes(size.maximum_bytes)}`;
    }
    return `up to ${formatBytes(size.maximum_bytes)}`;
  }
  if (size.minimum_bytes !== undefined) {
    return `at least ${formatBytes(size.minimum_bytes)}`;
  }
  return null;
}

/** "kb" and "Kb" both appear in the records; the unit itself is conventional. */
function normaliseUnit(unit: string | undefined): string | undefined {
  if (!unit) return undefined;
  const known: Record<string, string> = { kb: "KB", mb: "MB", gb: "GB", b: "bytes" };
  return known[unit.toLowerCase()] ?? unit;
}

interface Dimensions {
  mode?: string;
  width_px?: number;
  height_px?: number;
  aspect_ratio?: string;
  min_width_px?: number;
  max_width_px?: number;
  min_height_px?: number;
  max_height_px?: number;
  preferred_width_px?: number;
  preferred_height_px?: number;
}

export function describeDimensions(raw: unknown): string | null {
  const dims = raw as Dimensions | undefined;
  if (!dims) return null;

  if (dims.width_px && dims.height_px) {
    return `${dims.width_px} × ${dims.height_px} px`;
  }

  // Several bodies publish a preferred pixel size without mandating it, which
  // the schema records as mode "unspecified" plus `preferred_*_px`. Dropping
  // those loses a real published figure the candidate wants to see — it is the
  // size we aim for — so it is shown, labelled as preferred rather than exact.
  if (dims.preferred_width_px && dims.preferred_height_px) {
    return `${dims.preferred_width_px} × ${dims.preferred_height_px} px preferred`;
  }
  // A range is a real mode in the schema, and the engine crops differently for
  // it (Mode B), so it is worth saying rather than flattening to "varies".
  const hasRange =
    dims.min_width_px || dims.max_width_px || dims.min_height_px || dims.max_height_px;
  if (hasRange) {
    const w =
      dims.min_width_px && dims.max_width_px
        ? `${dims.min_width_px}–${dims.max_width_px}`
        : (dims.min_width_px ?? dims.max_width_px ?? "?");
    const h =
      dims.min_height_px && dims.max_height_px
        ? `${dims.min_height_px}–${dims.max_height_px}`
        : (dims.min_height_px ?? dims.max_height_px ?? "?");
    return `${w} × ${h} px`;
  }
  if (dims.aspect_ratio) return `${dims.aspect_ratio} ratio`;
  return null;
}

const FORMAT_LABELS: Record<string, string> = {
  jpg: "JPEG",
  jpeg: "JPEG",
  png: "PNG",
  pdf: "PDF",
  webp: "WebP",
};

function labelFormat(value: string): string {
  return FORMAT_LABELS[value.toLowerCase()] ?? value.toUpperCase();
}

export function describeFormats(raw: unknown): string | null {
  const formats = raw as
    | { preferred_format?: string; allowed_formats?: string[] }
    | undefined;
  if (!formats) return null;

  const allowed = (formats.allowed_formats ?? [])
    .map(labelFormat)
    // "jpg" and "jpeg" are the same format written twice; showing both reads
    // as a distinction the candidate has to think about, and there is none.
    .filter((value, index, all) => all.indexOf(value) === index);

  if (allowed.length > 1) return allowed.join(" or ");
  if (allowed.length === 1) return allowed[0];
  if (formats.preferred_format) return labelFormat(formats.preferred_format);
  return null;
}

export function describeBackground(raw: unknown): string | null {
  const background = raw as
    { mode?: string; required_colour?: string } | undefined;
  if (!background?.mode) return null;
  switch (background.mode) {
    case "exact_colour":
      return background.required_colour
        ? `Plain ${background.required_colour}`
        : "One exact colour";
    case "plain_light":
      return "Plain, light";
    case "plain_background":
      return "Plain";
    default:
      return null;
  }
}

/** Is the value behind `key` one the platform chose rather than one published? */
function isEstimated(provenance: Provenance, key: string): boolean {
  return provenance?.[key]?.type === "interim_default";
}

/**
 * True when any provenance entry under `prefix` is an interim default.
 *
 * A single displayed phrase ("10–20 KB") is assembled from several record
 * fields, so the marker has to reflect whether *any* of them was estimated —
 * showing a range as published when half of it was invented would be the
 * precise failure DEC-057 exists to prevent.
 */
function anyEstimatedUnder(provenance: Provenance, prefix: string): boolean {
  if (!provenance) return false;
  return Object.entries(provenance).some(
    ([key, entry]) => key.startsWith(prefix) && entry?.type === "interim_default"
  );
}

/**
 * The specification rows for one non-photograph requirement.
 *
 * `index` is the requirement's position in the record, because provenance is
 * keyed positionally: `requirements[2].file_spec.file_size.maximum_bytes`.
 */
export function requirementSpecRows(
  requirement: RequirementSummary,
  index: number,
  provenance: Provenance
): SpecRow[] {
  const spec = requirement.file_spec;
  if (!spec) return [];
  const base = `requirements[${index}].file_spec`;
  const rows: SpecRow[] = [];

  const dimensions = describeDimensions(spec.dimensions);
  if (dimensions) {
    rows.push({
      term: "Dimensions",
      value: dimensions,
      estimated: anyEstimatedUnder(provenance, `${base}.dimensions`),
    });
  }

  const size = describeFileSize(spec.file_size);
  if (size) {
    rows.push({
      term: "File size",
      value: size,
      estimated: anyEstimatedUnder(provenance, `${base}.file_size`),
    });
  }

  const formats = describeFormats(spec.formats);
  if (formats) {
    rows.push({
      term: "Format",
      value: formats,
      estimated: anyEstimatedUnder(provenance, `${base}.formats`),
    });
  }

  return rows;
}

/**
 * The specification rows for the photograph.
 *
 * The photograph's specification lives in `image_requirements` rather than in
 * a `file_spec`, and is forbidden from being duplicated onto the requirement
 * (DEC-047) — so it is read from its own place here.
 */
export function photographSpecRows(exam: ExamDetail): SpecRow[] {
  const image = exam.image_requirements as Record<string, unknown>;
  const rows: SpecRow[] = [];

  const dimensions = describeDimensions(image.dimensions);
  if (dimensions) {
    rows.push({
      term: "Dimensions",
      value: dimensions,
      estimated: isEstimated(exam.provenance, "image_requirements.dimensions"),
    });
  }

  const size = describeFileSize(image.file_size);
  if (size) {
    rows.push({
      term: "File size",
      value: size,
      estimated: isEstimated(exam.provenance, "image_requirements.file_size"),
    });
  }

  const formats = describeFormats(image.formats);
  if (formats) {
    rows.push({
      term: "Format",
      value: formats,
      estimated: anyEstimatedUnder(provenanceOf(exam), "image_requirements.formats"),
    });
  }

  const background = describeBackground(image.background);
  if (background) {
    rows.push({ term: "Background", value: background, estimated: false });
  }

  return rows;
}

function provenanceOf(exam: ExamDetail): Provenance {
  return exam.provenance;
}

/** How many of an exam's displayed figures are platform estimates. */
export function estimateCount(exam: ExamDetail): number {
  if (!exam.provenance) return 0;
  return Object.values(exam.provenance).filter(
    (entry) => entry?.type === "interim_default"
  ).length;
}
