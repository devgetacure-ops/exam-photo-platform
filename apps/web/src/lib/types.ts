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
