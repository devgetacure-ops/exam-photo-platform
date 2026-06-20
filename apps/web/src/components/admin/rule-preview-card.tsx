import React from "react";
import { RuleDocument } from "../../lib/types";

interface RulePreviewCardProps {
  rule: RuleDocument | null;
}

export function RulePreviewCard({ rule }: RulePreviewCardProps) {
  if (!rule) {
    return (
      <div className="p-8 bg-slate-50 dark:bg-zinc-900/50 border border-slate-200 dark:border-zinc-800 rounded-lg text-center text-xs text-slate-500">
        No rule active. Load a sample or upload a file.
      </div>
    );
  }

  const examName = rule.exam?.exam_name || "Unnamed Exam";
  const conductingBody = rule.exam?.conducting_body || "Unknown Conducting Body";
  const cycle = rule.exam?.application_cycle || "Unknown Cycle";
  const status = rule.status || "provisional";

  // Dimensions
  const dims = rule.image_requirements?.dimensions || {};
  const dimMode = dims.mode || "unspecified";
  let dimSummary = "Unspecified Dimensions";
  if (dimMode === "exact") {
    dimSummary = `${dims.width_px || "N/A"} × ${dims.height_px || "N/A"} px (Exact aspect: ${
      dims.aspect_ratio || "N/A"
    })`;
  } else if (dimMode === "range") {
    dimSummary = `Width: ${dims.min_width_px || "N/A"}-${
      dims.max_width_px || "N/A"
    } px, Height: ${dims.min_height_px || "N/A"}-${dims.max_height_px || "N/A"} px`;
  }

  // File size
  const fs = rule.image_requirements?.file_size || {};
  const minKb = fs.minimum_bytes ? (fs.minimum_bytes / 1024).toFixed(1) : "N/A";
  const maxKb = fs.maximum_bytes ? (fs.maximum_bytes / 1024).toFixed(1) : "N/A";
  const sizeSummary = `${minKb} KB to ${maxKb} KB`;

  // Format
  const formats = rule.image_requirements?.formats || {};
  const allowedFormats = formats.allowed_formats
    ? formats.allowed_formats.join(", ").toUpperCase()
    : "N/A";
  const preferredFormat = formats.preferred_format ? formats.preferred_format.toUpperCase() : "N/A";

  // Background
  const bg = rule.image_requirements?.background || {};
  const bgSummary = bg.plain_background_required
    ? `Plain solid color required (Mode: ${bg.mode || "N/A"}${
        bg.required_colour ? `, Color: ${bg.required_colour}` : ""
      })`
    : "No background restriction";

  // Filename
  const fn = rule.image_requirements?.filename || {};
  const fnMode = fn.mode || "unspecified";
  let fnSummary = "Unspecified naming";
  if (fnMode === "exact") {
    fnSummary = `Exact file name: "${fn.exact_filename || "N/A"}"`;
  } else if (fnMode === "pattern") {
    fnSummary = `Pattern required: "${fn.filename_pattern || "N/A"}"`;
  } else if (fnMode === "unspecified") {
    fnSummary = "No filename renaming requirement";
  }

  // Exceptional details
  const ex = rule.image_requirements?.exceptional_instructions || {};
  const hasExceptions =
    ex.printed_name ||
    ex.printed_date ||
    ex.signature_inclusion ||
    ex.spectacles_restriction ||
    ex.headwear_restriction;

  return (
    <div className="bg-gradient-to-br from-indigo-50/10 to-slate-50/50 dark:from-zinc-900/50 dark:to-zinc-950 border border-slate-200 dark:border-zinc-800 rounded-lg p-5 shadow-sm space-y-4 text-left">
      <div className="border-b border-slate-150 dark:border-zinc-850 pb-3">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white leading-tight">
              {examName}
            </h3>
            <p className="text-[11px] text-slate-500 dark:text-zinc-400 mt-0.5">
              {conductingBody} • Cycle: {cycle}
            </p>
          </div>
          <span
            className={`text-[9px] font-semibold uppercase px-2 py-0.5 rounded-full border ${
              status === "official"
                ? "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/20 dark:text-emerald-450 dark:border-emerald-900/30"
                : "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/20 dark:text-amber-450 dark:border-amber-900/30"
            }`}
          >
            {status}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        <div className="space-y-1">
          <p className="text-slate-400 dark:text-zinc-500 font-semibold text-[10px] uppercase tracking-wider">
            Dimensions Check
          </p>
          <p className="font-semibold text-slate-850 dark:text-zinc-200">{dimSummary}</p>
          <p className="text-[10px] text-slate-450 dark:text-zinc-400">
            Mode: <span className="capitalize">{dimMode}</span>
          </p>
        </div>

        <div className="space-y-1">
          <p className="text-slate-400 dark:text-zinc-500 font-semibold text-[10px] uppercase tracking-wider">
            File Size Limits
          </p>
          <p className="font-semibold text-slate-850 dark:text-zinc-200">{sizeSummary}</p>
          <p className="text-[10px] text-slate-450 dark:text-zinc-400">
            Published limits: {fs.published_minimum || "N/A"} - {fs.published_maximum || "N/A"}{" "}
            {fs.size_unit_as_published || "KB"}
          </p>
        </div>

        <div className="space-y-1">
          <p className="text-slate-400 dark:text-zinc-500 font-semibold text-[10px] uppercase tracking-wider">
            Image format
          </p>
          <p className="font-semibold text-slate-850 dark:text-zinc-200">
            Preferred: {preferredFormat}
          </p>
          <p className="text-[10px] text-slate-450 dark:text-zinc-400">Allowed: {allowedFormats}</p>
        </div>

        <div className="space-y-1">
          <p className="text-slate-400 dark:text-zinc-500 font-semibold text-[10px] uppercase tracking-wider">
            Background
          </p>
          <p className="font-semibold text-slate-855 dark:text-zinc-200 truncate" title={bgSummary}>
            {bgSummary}
          </p>
          <p className="text-[10px] text-slate-450 dark:text-zinc-400 truncate">
            {bg.instructions || "Plain background required."}
          </p>
        </div>

        <div className="space-y-1">
          <p className="text-slate-400 dark:text-zinc-500 font-semibold text-[10px] uppercase tracking-wider">
            Rename / Output format
          </p>
          <p className="font-semibold text-slate-880 dark:text-zinc-200">{fnSummary}</p>
          <p className="text-[10px] text-slate-455 dark:text-zinc-400">
            Extension: {fn.extension_required ? "Required" : "Optional"}
          </p>
        </div>

        <div className="space-y-1">
          <p className="text-slate-400 dark:text-zinc-500 font-semibold text-[10px] uppercase tracking-wider">
            Restrictions & Info
          </p>
          <p className="font-semibold text-slate-880 dark:text-zinc-200 truncate">
            {hasExceptions ? "Specific exceptions active" : "Standard rules apply"}
          </p>
          <div className="flex flex-wrap gap-1 mt-0.5">
            {ex.spectacles_restriction && (
              <span className="bg-slate-100 dark:bg-zinc-800 text-[9px] px-1 rounded text-slate-600 dark:text-zinc-400">
                Spectacles restricted
              </span>
            )}
            {ex.headwear_restriction && (
              <span className="bg-slate-100 dark:bg-zinc-800 text-[9px] px-1 rounded text-slate-600 dark:text-zinc-400">
                Headwear restricted
              </span>
            )}
            {ex.signature_inclusion && (
              <span className="bg-slate-100 dark:bg-zinc-800 text-[9px] px-1 rounded text-slate-600 dark:text-zinc-400">
                Signature required
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
