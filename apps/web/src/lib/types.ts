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

export interface StageReport {
  stage: string;
  status: "success" | "failure" | "skipped";
  details?: Record<string, unknown>;
  error?: string;
}

export interface PipelineReport {
  is_valid: boolean;
  issue_codes: string[];
  selected_crop_mode?: string | null;
  final_width?: number | null;
  final_height?: number | null;
  final_format?: string | null;
  final_bytes?: number | null;
  final_quality?: number | null;
  stage_reports?: StageReport[];
  [key: string]: unknown; // Allow collapsible raw JSON properties
}
