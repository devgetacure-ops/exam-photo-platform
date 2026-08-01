import React, { useState } from "react";
import { PipelineReport, StageReport } from "../lib/types";

interface ValidationReportProps {
  report: PipelineReport;
}

export function ValidationReport({ report }: ValidationReportProps) {
  const [showJson, setShowJson] = useState(false);

  // Clean the report object to ensure encoded_bytes is not displayed or serialized
  const getCleanJson = (data: PipelineReport) => {
    const copy = { ...data };
    delete copy.encoded_bytes;
    return JSON.stringify(copy, null, 2);
  };

  const {
    is_valid,
    issue_codes = [],
    selected_crop_mode,
    final_width,
    final_height,
    final_format,
    final_bytes,
    final_quality,
    stage_reports = [],
  } = report;

  const formatSize = (bytes?: number | null) => {
    if (bytes == null) return "Unknown";
    return (bytes / 1024).toFixed(2) + " KB";
  };

  const isCompliant = is_valid && report.visual_quality_acceptable !== false;

  const technicalStages = ["rule_validation", "input_normalization", "crop_selection", "output_preparation", "output_compression", "final_decode_validation", "final_rule_validation", "filename_generation"];
  const compositionStages = ["face_detection", "head_estimation", "crop_planning"];
  const backgroundStages = ["subject_segmentation", "mask_refinement", "background_composition"];

  const techReports = stage_reports.filter(s => technicalStages.includes(s.stage));
  const compReports = stage_reports.filter(s => compositionStages.includes(s.stage));
  const bgReports = stage_reports.filter(s => backgroundStages.includes(s.stage));

  const renderStageRow = (stage: StageReport) => {
    let dotColor = "bg-slate-400 dark:bg-zinc-650";
    let textColor = "text-slate-450 dark:text-zinc-500";

    if (stage.status === "passed") {
      dotColor = "bg-emerald-500";
      textColor = "text-emerald-600 dark:text-emerald-450";
    } else if (stage.status === "warning") {
      dotColor = "bg-amber-500";
      textColor = "text-amber-600 dark:text-amber-450";
    } else if (stage.status === "failed") {
      dotColor = "bg-rose-500";
      textColor = "text-rose-600 dark:text-rose-455";
    }

    const displayName = stage.stage
      .split("_")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");

    return (
      <div
        key={stage.stage}
        className="flex items-center justify-between p-3 bg-white dark:bg-zinc-950 hover:bg-slate-50/50 dark:hover:bg-zinc-900/10 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${dotColor}`}
            aria-hidden="true"
          />
          <span className="font-semibold text-slate-700 dark:text-zinc-300">
            {displayName}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {stage.error && (
            <span className="text-[10px] text-rose-600 dark:text-rose-455 font-mono max-w-[150px] sm:max-w-[250px] truncate">
              {stage.error}
            </span>
          )}
          <span
            className={`font-semibold uppercase text-[10px] ${textColor}`}
          >
            {stage.status}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white dark:bg-zinc-950 border border-slate-200 dark:border-zinc-800 rounded-lg p-5 shadow-sm space-y-5">
      {/* 1. Header / Overall Status */}
      <div className="flex items-center justify-between border-b border-slate-150 dark:border-zinc-850 pb-3">
        <div>
          <h2 className="text-base font-semibold text-slate-900 dark:text-white">
            Compliance Validation Report
          </h2>
          <p className="text-xs text-slate-500 dark:text-zinc-400 mt-0.5">
            Results of the automated formatting checks.
          </p>
        </div>
        <div
          className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold uppercase ${
            isCompliant
              ? "bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-450 border border-emerald-200 dark:border-emerald-900/30"
              : "bg-rose-50 dark:bg-rose-950/20 text-rose-700 dark:text-rose-455 border border-rose-200 dark:border-rose-900/30"
          }`}
        >
          <span
            className={`w-2 h-2 rounded-full ${isCompliant ? "bg-emerald-500" : "bg-rose-500"}`}
            aria-hidden="true"
          />
          {isCompliant ? "Compliant" : "Non-Compliant"}
        </div>
      </div>

      {/* 2. Issue Codes (if invalid) */}
      {!isCompliant && issue_codes.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-rose-700 dark:text-rose-400">
            Detected Issues:
          </p>
          <div className="flex flex-wrap gap-1.5">
            {issue_codes.map((code) => (
              <span
                key={code}
                className="px-2 py-0.5 bg-rose-50 dark:bg-rose-950/30 border border-rose-100 dark:border-rose-900/40 text-[10px] font-semibold font-mono text-rose-700 dark:text-rose-400 rounded"
              >
                {code}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 3. Output Metadata Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 bg-slate-50 dark:bg-zinc-900/50 p-3 rounded-lg border border-slate-100 dark:border-zinc-900 text-xs">
        <div>
          <p className="text-slate-500 dark:text-zinc-400 font-medium">Dimensions</p>
          <p className="font-semibold text-slate-800 dark:text-white mt-0.5">
            {final_width != null && final_height != null
              ? `${final_width} × ${final_height} px`
              : "N/A"}
          </p>
        </div>
        <div>
          <p className="text-slate-500 dark:text-zinc-400 font-medium">File Size</p>
          <p className="font-semibold text-slate-800 dark:text-white mt-0.5">
            {formatSize(final_bytes)}
          </p>
        </div>
        <div>
          <p className="text-slate-500 dark:text-zinc-400 font-medium">Output Format</p>
          <p className="font-semibold text-slate-800 dark:text-white mt-0.5 uppercase">
            {final_format || "N/A"}
          </p>
        </div>
        <div>
          <p className="text-slate-500 dark:text-zinc-400 font-medium">Crop Mode</p>
          <p className="font-semibold text-slate-800 dark:text-white mt-0.5">
            {selected_crop_mode || "N/A"}
          </p>
        </div>
        <div>
          <p className="text-slate-500 dark:text-zinc-400 font-medium">Quality</p>
          <p className="font-semibold text-slate-800 dark:text-white mt-0.5">
            {final_quality != null ? `${final_quality}%` : "N/A"}
          </p>
        </div>
      </div>

      {/* 4. Stage Reports Grouped */}
      <div className="space-y-4">
        {techReports.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-slate-700 dark:text-zinc-300">
              Technical Rule Checks
            </h3>
            <div className="border border-slate-150 dark:border-zinc-850 rounded-lg overflow-hidden divide-y divide-slate-150 dark:divide-zinc-850 text-xs">
              {techReports.map(renderStageRow)}
            </div>
          </div>
        )}

        {compReports.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-slate-700 dark:text-zinc-305">
              Portrait Composition Quality
            </h3>
            <div className="border border-slate-150 dark:border-zinc-850 rounded-lg overflow-hidden divide-y divide-slate-150 dark:divide-zinc-850 text-xs">
              {compReports.map(renderStageRow)}
            </div>
          </div>
        )}

        {bgReports.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-slate-700 dark:text-zinc-305">
              Background & Edge Quality
            </h3>
            <div className="border border-slate-150 dark:border-zinc-850 rounded-lg overflow-hidden divide-y divide-slate-150 dark:divide-zinc-850 text-xs">
              {bgReports.map(renderStageRow)}
            </div>
          </div>
        )}
      </div>


      {/* 5. Collapsible Raw JSON Explorer */}
      <div className="pt-2 border-t border-slate-150 dark:border-zinc-850 space-y-2">
        <button
          type="button"
          onClick={() => setShowJson(!showJson)}
          className="flex items-center gap-1 text-slate-500 dark:text-zinc-400 hover:text-indigo-650 dark:hover:text-indigo-400 transition-colors text-xs font-semibold focus:outline-none"
        >
          <svg
            className={`w-4 h-4 transition-transform duration-200 ${showJson ? "rotate-90" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
          </svg>
          {showJson ? "Hide Diagnostic Raw JSON" : "Show Diagnostic Raw JSON"}
        </button>

        {showJson && (
          <pre className="p-3 bg-slate-55 dark:bg-zinc-900/80 border border-slate-200 dark:border-zinc-800 rounded-lg text-[10px] font-mono text-slate-700 dark:text-zinc-300 overflow-x-auto max-h-72">
            {getCleanJson(report)}
          </pre>
        )}
      </div>
    </div>
  );
}
