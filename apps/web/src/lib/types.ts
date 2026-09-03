export type ApiJobStatus =
  | "RECEIVED"
  | "PROCESSING"
  | "SUCCEEDED"
  | "FAILED"
  | "DELETED";

export interface ProcessImageResponse {
  job_id: string;
  status: ApiJobStatus;
  is_valid?: boolean | null;
  output_filename?: string | null;
  report_url?: string | null;
  output_url?: string | null;
  expires_at?: string | null;
  issue_codes?: string[];
}

export interface JobStatusResponse {
  job_id: string;
  status: ApiJobStatus;
  created_at: string;
  updated_at: string;
  expires_at?: string | null;
  is_valid?: boolean | null;
  issue_codes?: string[];
  output_filename?: string | null;
  report_url?: string | null;
  output_url?: string | null;
}

export type StageStatus = "not_started" | "passed" | "warning" | "failed" | "skipped";

export interface StageReport {
  stage: string;
  status: StageStatus;
  details?: Record<string, unknown>;
  error?: string;
}

export interface PipelineReport {
  is_valid: boolean;
  rule_compliant: boolean;
  visual_quality_acceptable: boolean;
  issue_codes: string[];
  selected_crop_mode?: string | null;
  final_width?: number | null;
  final_height?: number | null;
  final_format?: string | null;
  final_bytes?: number | null;
  final_quality?: number | null;
  quality_mode?: string | null;
  diagnostic_artifacts_available?: boolean | null;
  portrait_quality_report?: Record<string, unknown> | null;
  matte_quality_report?: Record<string, unknown> | null;
  stage_reports?: StageReport[];
  [key: string]: unknown; // Allow collapsible raw JSON properties
}


// --- Exam catalogue (DEC-055) ------------------------------------------------

/**
 * The five states a requirement can sit in relative to the platform. Carried as
 * the string it is and never reduced to a boolean anywhere in the client
 * (DEC-056): `supported` and `partially_supported` mean the platform prepares a
 * file, `guidance_only` and `physical_stage` mean the candidate does it
 * themselves, `not_yet_supported` means it is coming.
 */
export type PlatformSupport =
  | "supported"
  | "partially_supported"
  | "guidance_only"
  | "physical_stage"
  | "not_yet_supported";

export type RequirementType =
  | "photograph"
  | "signature"
  | "thumb_impression"
  | "handwritten_declaration"
  | "certificate_scan"
  | "identity_document"
  | "portal_declaration"
  | "other";

export type SubmissionMethod =
  | "file_upload"
  | "handwritten_then_uploaded"
  | "document_scan_upload"
  | "official_live_capture"
  | "external_identity_verification"
  | "typed_or_selected_declaration"
  | "physical_stage_requirement";

export type RequirementStatus =
  | "mandatory"
  | "conditional"
  | "optional"
  | "portal_dependent";

/** Present for every `platform_support` value, zeros included. */
export type RequirementCounts = Partial<Record<PlatformSupport, number>>;

export interface ExamSummary {
  exam_id: string;
  exam_name: string;
  conducting_body: string;
  examination_year: number;
  application_cycle: string;
  application_stage?: string | null;
  category?: string | null;
  aliases: string[];
  status: string;
  requirement_counts: RequirementCounts;
  requirement_total: number;
}

/**
 * An examination the research covers that the catalogue does not encode. Shown
 * in the picker as a non-selectable row rather than omitted (DEC-056).
 */
export interface UnavailableExam {
  exam_name: string;
  reason: string;
  detail: string;
  non_photograph_deliverables: number;
}

export interface ExamList {
  exams: ExamSummary[];
  total: number;
  unavailable: UnavailableExam[];
  unreadable: Record<string, string>;
}

export interface RequirementSummary {
  requirement_id: string;
  requirement_name: string;
  requirement_type: RequirementType;
  submission_method: SubmissionMethod;
  requirement_status: RequirementStatus;
  platform_support: PlatformSupport;
  applicability?: string | null;
  content_instructions?: string | null;
  rejection_conditions: string[];
  notes?: string | null;
  /** The published output spec. `null` for a photograph (see `image_requirements`). */
  file_spec?: Record<string, unknown> | null;
}

/**
 * Where a rule came from. `official_source` is load-bearing and is never
 * assumed: 7 of the 39 examinations rest on secondary references — one of them
 * a forum reproduction of the notification — and presenting that as an official
 * citation would be a false claim about evidence.
 */
export interface SourceEvidence {
  source_type: string;
  official_source: boolean;
  captured_wording?: string | null;
  source_url?: string | null;
  document_title?: string | null;
}

export interface ExamDetail {
  exam_id: string;
  exam_name: string;
  conducting_body: string;
  examination_year: number;
  application_cycle: string;
  application_stage?: string | null;
  jurisdiction?: string | null;
  category?: string | null;
  aliases: string[];
  status: string;
  rule_id: string;
  rule_version: string;
  notes?: string | null;
  /** `null` when deliverable research has not been done — never "photo only". */
  requirements?: RequirementSummary[] | null;
  requirement_counts: RequirementCounts;
  image_requirements: Record<string, unknown>;
  /** Per-field provenance; `type === "interim_default"` marks a platform estimate. */
  provenance: Record<string, { type?: string; [k: string]: unknown }>;
  source_evidence: SourceEvidence[];
  /** `verified` | `verified_with_ambiguity` | `provisional`. */
  verification_status: string | null;
  /**
   * Published causes of rejection that concern the whole application rather
   * than any single upload. Conditions naming a deliverable live on that
   * requirement instead, so this list stays short.
   */
  application_rejection_conditions: string[];
}

// --- Preparation (DEC-055, DEC-056) -----------------------------------------

/**
 * The outcome states a preparation attempt lands in. `prepared_with_findings`
 * is a first-class state, not a flavour of success: a blank page, an
 * unreachable published minimum, an invented ceiling and an oversized document
 * are all reported about a file that exists (DEC-041, DEC-056).
 */
export type PreparationOutcome =
  | "prepared"
  | "prepared_with_findings"
  | "blocked"
  | "not_produced";

export interface PrepareRequirementResponse {
  job_id: string;
  kit_id?: string | null;
  exam_id: string;
  requirement_id: string;
  requirement_type: RequirementType;
  platform_support: PlatformSupport;
  status: ApiJobStatus;
  outcome: PreparationOutcome;
  expires_at?: string | null;

  output_url?: string | null;
  output_filename?: string | null;
  output_media_type?: string | null;
  report_url?: string | null;
  byte_size?: number | null;
  width?: number | null;
  height?: number | null;

  findings: string[];
  is_blank?: boolean | null;
  ceiling_was_unpublished?: boolean | null;
  exceeds_ceiling?: boolean | null;

  // Photograph path only.
  is_valid?: boolean | null;
  issue_codes: string[];
  rule_compliant?: boolean | null;
  visual_quality_acceptable?: boolean | null;
}

/**
 * Returned with HTTP 409 when the platform will not act on a requirement.
 * Carries the requirement's own vocabulary so the client can say what the
 * candidate must do instead, not just report a failure.
 */
export interface RequirementNotServed {
  detail: string;
  exam_id: string;
  requirement_id: string;
  requirement_name: string;
  requirement_type: RequirementType;
  submission_method: SubmissionMethod;
  platform_support: PlatformSupport;
  content_instructions?: string | null;
  applicability?: string | null;
}

/** Thrown by the client when a prepare call is refused at the support gate. */
export class RequirementNotServedError extends Error {
  readonly info: RequirementNotServed;
  constructor(info: RequirementNotServed) {
    super(info.detail);
    this.name = "RequirementNotServedError";
    this.info = info;
  }
}

// --- Multi-page documents (DEC-053) ----------------------------------------

export interface DocumentPage {
  source_index: number;
  page_index: number;
  /** `photograph` | `document_scan` | `document_text`. A text page is never re-rendered. */
  origin: string;
  rotation: number;
}

export interface DocumentPlan {
  job_id: string;
  kit_id?: string | null;
  exam_id: string;
  requirement_id: string;
  expires_at?: string | null;
  pages: DocumentPage[];
  /** Uploads that could not be read, by index, with the reason. */
  unreadable: Record<string, string>;
}

// --- Kit package (DEC-055 step 4, DEC-057) --------------------------------

export interface KitPackageItem {
  requirement_id?: string | null;
  requirement_type?: string | null;
  platform_support?: string | null;
  outcome?: string | null;
  included: boolean;
  filename?: string | null;
  byte_size?: number | null;
  findings: string[];
}

export interface KitPackage {
  kit_id: string;
  exam_id?: string | null;
  exam_name?: string | null;
  files_included: number;
  package_url?: string | null;
  requirements: Record<string, unknown>[];
  items: KitPackageItem[];
}

export interface RuleValidationError {
  severity: "error" | "warning";
  error_code: string;
  field_path: string;
  message: string;
  suggested_resolution?: string | null;
}

export interface RuleValidationResponse {
  is_valid: boolean;
  error_count: number;
  errors: RuleValidationError[];
}

export interface RuleDocument {
  schema_version?: string;
  rule_id?: string;
  rule_version?: string;
  status?: string;
  exam?: {
    exam_id?: string;
    exam_name?: string;
    conducting_body?: string;
    examination_year?: number;
    application_cycle?: string;
    aliases?: string[];
  };
  image_requirements?: {
    dimensions?: {
      mode?: string;
      width_px?: number;
      height_px?: number;
      aspect_ratio?: string;
      min_width_px?: number;
      max_width_px?: number;
      min_height_px?: number;
      max_height_px?: number;
    };
    file_size?: {
      minimum_bytes?: number;
      maximum_bytes?: number;
      published_minimum?: number;
      published_maximum?: number;
      size_unit_as_published?: string;
      target_ceiling_ratio?: number;
      safety_margin_bytes?: number;
    };
    formats?: {
      preferred_format?: string;
      allowed_formats?: string[];
      preserve_transparency?: boolean;
      strip_metadata?: boolean;
      colour_space?: string;
      extension_policy?: string;
    };
    background?: {
      mode?: string;
      required_colour?: string;
      tolerance?: number;
      plain_background_required?: boolean;
      shadows_allowed?: boolean;
      gradient_allowed?: boolean;
      instructions?: string;
    };
    composition?: {
      face_coverage_target?: number;
      face_coverage_minimum?: number;
      face_coverage_maximum?: number;
      coverage_is_strict?: boolean;
      complete_hair_visible?: boolean;
      ears_visible?: boolean;
      chin_visible?: boolean;
      beard_boundary_visible?: boolean;
      face_centred?: boolean;
      frontal_pose?: boolean;
      eye_visibility?: boolean;
      spectacles_policy?: string;
    };
    filename?: {
      mode?: string;
      exact_filename?: string;
      filename_pattern?: string;
      case_sensitive?: boolean;
      extension_required?: boolean;
      fallback_basename?: string;
    };
    exceptional_instructions?: {
      printed_name?: boolean;
      printed_date?: boolean;
      signature_inclusion?: boolean;
      black_and_white_restriction?: boolean;
      recent_photo_requirement?: boolean;
      spectacles_restriction?: boolean;
      headwear_restriction?: boolean;
      processing_support_status?: string;
    };
  };
  [key: string]: unknown;
}

// --- Picker search index (built at build time, shipped to the client) -------

/**
 * One row of the client-side search index. Deliberately small: the whole
 * catalogue ships with the landing page so predictive search costs no network
 * round trip, and every field here is paid for 50 times over.
 *
 * Lives here rather than beside the build-time reader because the picker is a
 * client component and must not import from a `server-only` module.
 */
export interface SearchEntry {
  id: string;
  name: string;
  body: string;
  year: number;
  aliases: string[];
  /** How many requirements the platform actually prepares. Drives the row summary. */
  prepares: number;
  total: number;
  /** Present only on rows that cannot be selected (DEC-056). */
  unavailable?: { reason: string; detail: string; deliverables: number };
}
