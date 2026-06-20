import React from "react";
import { RuleDocument } from "../../lib/types";

interface RuleFormSectionsProps {
  rule: RuleDocument;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onChange: (path: string, value: any) => void;
}

export function RuleFormSections({ rule, onChange }: RuleFormSectionsProps) {
  if (!rule) {
    return (
      <div className="p-6 bg-slate-50 dark:bg-zinc-900/50 border border-slate-200 dark:border-zinc-800 rounded-lg text-center text-xs text-slate-500">
        Load a sample rule or import a JSON file to start editing.
      </div>
    );
  }

  // Helper to read nested paths safely in form inputs
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const getValue = (path: string, fallback: any = ""): any => {
    const parts = path.split(".");
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let current: any = rule;
    for (const part of parts) {
      if (current === undefined || current === null) return fallback;
      current = current[part];
    }
    return current !== undefined && current !== null ? current : fallback;
  };

  const renderSectionHeader = (title: string, desc: string) => (
    <div className="space-y-0.5">
      <h4 className="text-xs font-bold text-slate-800 dark:text-zinc-200">{title}</h4>
      <p className="text-[10px] text-slate-500 dark:text-zinc-500">{desc}</p>
    </div>
  );

  return (
    <div className="space-y-4">
      {/* 1. Identity */}
      <details className="group border border-slate-200 dark:border-zinc-800 rounded-lg bg-white dark:bg-zinc-950 overflow-hidden shadow-sm" open>
        <summary className="p-4 font-semibold text-slate-800 dark:text-zinc-200 hover:bg-slate-50/50 dark:hover:bg-zinc-900/10 cursor-pointer select-none list-none flex items-center justify-between border-b border-transparent group-open:border-slate-150 dark:group-open:border-zinc-850">
          {renderSectionHeader("1. Rule & Exam Identity", "Configure rule identifiers and conducted exam metadata.")}
          <span className="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
        </summary>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Schema Version</label>
            <input
              type="text"
              value={getValue("schema_version")}
              onChange={(e) => onChange("schema_version", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Rule ID</label>
            <input
              type="text"
              value={getValue("rule_id")}
              onChange={(e) => onChange("rule_id", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Rule Version</label>
            <input
              type="text"
              value={getValue("rule_version")}
              onChange={(e) => onChange("rule_version", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Status</label>
            <select
              value={getValue("status")}
              onChange={(e) => onChange("status", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="provisional">Provisional</option>
              <option value="official">Official</option>
            </select>
          </div>
          <div className="space-y-1 text-left sm:col-span-2">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Exam Name</label>
            <input
              type="text"
              value={getValue("exam.exam_name")}
              onChange={(e) => onChange("exam.exam_name", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Exam ID</label>
            <input
              type="text"
              value={getValue("exam.exam_id")}
              onChange={(e) => onChange("exam.exam_id", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Conducting Body</label>
            <input
              type="text"
              value={getValue("exam.conducting_body")}
              onChange={(e) => onChange("exam.conducting_body", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Examination Year</label>
            <input
              type="number"
              value={getValue("exam.examination_year")}
              onChange={(e) => onChange("exam.examination_year", parseInt(e.target.value) || 0)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Application Cycle</label>
            <input
              type="text"
              value={getValue("exam.application_cycle")}
              onChange={(e) => onChange("exam.application_cycle", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
        </div>
      </details>

      {/* 2. Dimensions */}
      <details className="group border border-slate-200 dark:border-zinc-800 rounded-lg bg-white dark:bg-zinc-950 overflow-hidden shadow-sm">
        <summary className="p-4 font-semibold text-slate-800 dark:text-zinc-200 hover:bg-slate-50/50 dark:hover:bg-zinc-900/10 cursor-pointer select-none list-none flex items-center justify-between border-b border-transparent group-open:border-slate-150 dark:group-open:border-zinc-850">
          {renderSectionHeader("2. Dimension Constraints", "Configure width, height, aspect ratios, and range validation modes.")}
          <span className="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
        </summary>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Dimension Mode</label>
            <select
              value={getValue("image_requirements.dimensions.mode")}
              onChange={(e) => onChange("image_requirements.dimensions.mode", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="exact">Exact dimensions</option>
              <option value="range">Dimension range</option>
              <option value="unspecified">Unspecified / Free crop</option>
            </select>
          </div>

          {getValue("image_requirements.dimensions.mode") === "exact" && (
            <>
              <div className="space-y-1 text-left">
                <label htmlFor="dim-width-px" className="font-semibold text-slate-650 dark:text-zinc-300">Width (pixels)</label>
                <input
                  id="dim-width-px"
                  type="number"
                  value={getValue("image_requirements.dimensions.width_px")}
                  onChange={(e) => onChange("image_requirements.dimensions.width_px", parseInt(e.target.value) || undefined)}
                  className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
              <div className="space-y-1 text-left">
                <label className="font-semibold text-slate-650 dark:text-zinc-300">Height (pixels)</label>
                <input
                  type="number"
                  value={getValue("image_requirements.dimensions.height_px")}
                  onChange={(e) => onChange("image_requirements.dimensions.height_px", parseInt(e.target.value) || undefined)}
                  className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
              <div className="space-y-1 text-left">
                <label className="font-semibold text-slate-650 dark:text-zinc-300">Aspect Ratio (string)</label>
                <input
                  type="text"
                  value={getValue("image_requirements.dimensions.aspect_ratio")}
                  onChange={(e) => onChange("image_requirements.dimensions.aspect_ratio", e.target.value)}
                  className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
                  placeholder="e.g. 3:4"
                />
              </div>
            </>
          )}

          {getValue("image_requirements.dimensions.mode") === "range" && (
            <>
              <div className="space-y-1 text-left">
                <label className="font-semibold text-slate-650 dark:text-zinc-300">Min Width (pixels)</label>
                <input
                  type="number"
                  value={getValue("image_requirements.dimensions.min_width_px")}
                  onChange={(e) => onChange("image_requirements.dimensions.min_width_px", parseInt(e.target.value) || undefined)}
                  className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
              <div className="space-y-1 text-left">
                <label className="font-semibold text-slate-650 dark:text-zinc-300">Max Width (pixels)</label>
                <input
                  type="number"
                  value={getValue("image_requirements.dimensions.max_width_px")}
                  onChange={(e) => onChange("image_requirements.dimensions.max_width_px", parseInt(e.target.value) || undefined)}
                  className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
              <div className="space-y-1 text-left">
                <label className="font-semibold text-slate-650 dark:text-zinc-300">Min Height (pixels)</label>
                <input
                  type="number"
                  value={getValue("image_requirements.dimensions.min_height_px")}
                  onChange={(e) => onChange("image_requirements.dimensions.min_height_px", parseInt(e.target.value) || undefined)}
                  className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
              <div className="space-y-1 text-left">
                <label className="font-semibold text-slate-650 dark:text-zinc-300">Max Height (pixels)</label>
                <input
                  type="number"
                  value={getValue("image_requirements.dimensions.max_height_px")}
                  onChange={(e) => onChange("image_requirements.dimensions.max_height_px", parseInt(e.target.value) || undefined)}
                  className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
            </>
          )}
        </div>
      </details>

      {/* 3. File Size */}
      <details className="group border border-slate-200 dark:border-zinc-800 rounded-lg bg-white dark:bg-zinc-950 overflow-hidden shadow-sm">
        <summary className="p-4 font-semibold text-slate-800 dark:text-zinc-200 hover:bg-slate-50/50 dark:hover:bg-zinc-900/10 cursor-pointer select-none list-none flex items-center justify-between border-b border-transparent group-open:border-slate-150 dark:group-open:border-zinc-850">
          {renderSectionHeader("3. File Size Parameters", "Define minimum/maximum byte sizes, unit representation, and buffers.")}
          <span className="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
        </summary>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Min Bytes (int)</label>
            <input
              type="number"
              value={getValue("image_requirements.file_size.minimum_bytes")}
              onChange={(e) => onChange("image_requirements.file_size.minimum_bytes", parseInt(e.target.value) || 0)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Max Bytes (int)</label>
            <input
              type="number"
              value={getValue("image_requirements.file_size.maximum_bytes")}
              onChange={(e) => onChange("image_requirements.file_size.maximum_bytes", parseInt(e.target.value) || 0)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Published Minimum</label>
            <input
              type="number"
              step="any"
              value={getValue("image_requirements.file_size.published_minimum")}
              onChange={(e) => onChange("image_requirements.file_size.published_minimum", parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Published Maximum</label>
            <input
              type="number"
              step="any"
              value={getValue("image_requirements.file_size.published_maximum")}
              onChange={(e) => onChange("image_requirements.file_size.published_maximum", parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Published Size Unit</label>
            <input
              type="text"
              value={getValue("image_requirements.file_size.size_unit_as_published")}
              onChange={(e) => onChange("image_requirements.file_size.size_unit_as_published", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
              placeholder="e.g. KB"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Target Ceiling Ratio</label>
            <input
              type="number"
              step="0.01"
              value={getValue("image_requirements.file_size.target_ceiling_ratio")}
              onChange={(e) => onChange("image_requirements.file_size.target_ceiling_ratio", parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-1 text-left col-span-2">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Safety Margin Bytes (int)</label>
            <input
              type="number"
              value={getValue("image_requirements.file_size.safety_margin_bytes")}
              onChange={(e) => onChange("image_requirements.file_size.safety_margin_bytes", parseInt(e.target.value) || 0)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
        </div>
      </details>

      {/* 4. Format Options */}
      <details className="group border border-slate-200 dark:border-zinc-800 rounded-lg bg-white dark:bg-zinc-950 overflow-hidden shadow-sm">
        <summary className="p-4 font-semibold text-slate-800 dark:text-zinc-200 hover:bg-slate-50/50 dark:hover:bg-zinc-900/10 cursor-pointer select-none list-none flex items-center justify-between border-b border-transparent group-open:border-slate-150 dark:group-open:border-zinc-850">
          {renderSectionHeader("4. Formats & Encoding", "Configure preferred extensions, colour space options, and transparency policies.")}
          <span className="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
        </summary>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Preferred Format</label>
            <input
              type="text"
              value={getValue("image_requirements.formats.preferred_format")}
              onChange={(e) => onChange("image_requirements.formats.preferred_format", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
              placeholder="e.g. jpeg"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Allowed Formats (comma separated list)</label>
            <input
              type="text"
              value={getValue("image_requirements.formats.allowed_formats", []).join(", ")}
              onChange={(e) => onChange("image_requirements.formats.allowed_formats", e.target.value.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean))}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
              placeholder="e.g. jpg, jpeg"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Colour Space</label>
            <input
              type="text"
              value={getValue("image_requirements.formats.colour_space")}
              onChange={(e) => onChange("image_requirements.formats.colour_space", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
              placeholder="e.g. sRGB"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Extension Mismatch Policy</label>
            <select
              value={getValue("image_requirements.formats.extension_policy")}
              onChange={(e) => onChange("image_requirements.formats.extension_policy", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="strip_and_append">Strip and append preferred</option>
              <option value="reject">Reject mismatch</option>
              <option value="warn">Warn only</option>
            </select>
          </div>
          <div className="flex items-center gap-2 mt-4 text-left">
            <input
              id="preserve-transparency-checkbox"
              type="checkbox"
              checked={getValue("image_requirements.formats.preserve_transparency", false)}
              onChange={(e) => onChange("image_requirements.formats.preserve_transparency", e.target.checked)}
              className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500/20 border-slate-350"
            />
            <label htmlFor="preserve-transparency-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
              Preserve Transparency
            </label>
          </div>
          <div className="flex items-center gap-2 mt-4 text-left">
            <input
              id="strip-metadata-checkbox"
              type="checkbox"
              checked={getValue("image_requirements.formats.strip_metadata", false)}
              onChange={(e) => onChange("image_requirements.formats.strip_metadata", e.target.checked)}
              className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500/20 border-slate-350"
            />
            <label htmlFor="strip-metadata-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
              Strip Metadata / EXIF
            </label>
          </div>
        </div>
      </details>

      {/* 5. Background */}
      <details className="group border border-slate-200 dark:border-zinc-800 rounded-lg bg-white dark:bg-zinc-950 overflow-hidden shadow-sm">
        <summary className="p-4 font-semibold text-slate-800 dark:text-zinc-200 hover:bg-slate-50/50 dark:hover:bg-zinc-900/10 cursor-pointer select-none list-none flex items-center justify-between border-b border-transparent group-open:border-slate-150 dark:group-open:border-zinc-850">
          {renderSectionHeader("5. Background Settings", "Set solid colors, plainness, gradients, and composite guidelines.")}
          <span className="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
        </summary>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Background Mode</label>
            <select
              value={getValue("image_requirements.background.mode")}
              onChange={(e) => onChange("image_requirements.background.mode", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="exact_colour">Exact Solid Colour</option>
              <option value="light_coloured">Light Coloured</option>
              <option value="plain">Plain background</option>
              <option value="unspecified">Unspecified background</option>
            </select>
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Required Solid Color (hex)</label>
            <input
              type="text"
              value={getValue("image_requirements.background.required_colour")}
              onChange={(e) => onChange("image_requirements.background.required_colour", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
              placeholder="e.g. #FFFFFF"
            />
          </div>
          <div className="space-y-1 text-left sm:col-span-2">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Instructions Description</label>
            <input
              type="text"
              value={getValue("image_requirements.background.instructions")}
              onChange={(e) => onChange("image_requirements.background.instructions", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="flex items-center gap-2 mt-2 text-left">
            <input
              id="plain-bg-checkbox"
              type="checkbox"
              checked={getValue("image_requirements.background.plain_background_required", false)}
              onChange={(e) => onChange("image_requirements.background.plain_background_required", e.target.checked)}
              className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500/20 border-slate-350"
            />
            <label htmlFor="plain-bg-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
              Plain Background Required
            </label>
          </div>
          <div className="flex items-center gap-2 mt-2 text-left">
            <input
              id="bg-shadows-checkbox"
              type="checkbox"
              checked={getValue("image_requirements.background.shadows_allowed", false)}
              onChange={(e) => onChange("image_requirements.background.shadows_allowed", e.target.checked)}
              className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500/20 border-slate-350"
            />
            <label htmlFor="bg-shadows-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
              Shadows Allowed
            </label>
          </div>
          <div className="flex items-center gap-2 mt-2 text-left col-span-2">
            <input
              id="bg-gradients-checkbox"
              type="checkbox"
              checked={getValue("image_requirements.background.gradient_allowed", false)}
              onChange={(e) => onChange("image_requirements.background.gradient_allowed", e.target.checked)}
              className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500/20 border-slate-350"
            />
            <label htmlFor="bg-gradients-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
              Gradient Background Allowed
            </label>
          </div>
        </div>
      </details>

      {/* 6. Composition */}
      <details className="group border border-slate-200 dark:border-zinc-800 rounded-lg bg-white dark:bg-zinc-950 overflow-hidden shadow-sm">
        <summary className="p-4 font-semibold text-slate-800 dark:text-zinc-200 hover:bg-slate-50/50 dark:hover:bg-zinc-900/10 cursor-pointer select-none list-none flex items-center justify-between border-b border-transparent group-open:border-slate-150 dark:group-open:border-zinc-850">
          {renderSectionHeader("6. Composition & Face coverage", "Set face target metrics, feature visibilities, and pose check toggles.")}
          <span className="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
        </summary>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Face Coverage Target %</label>
            <input
              type="number"
              step="any"
              value={getValue("image_requirements.composition.face_coverage_target")}
              onChange={(e) => onChange("image_requirements.composition.face_coverage_target", parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Face Coverage Min %</label>
            <input
              type="number"
              step="any"
              value={getValue("image_requirements.composition.face_coverage_minimum")}
              onChange={(e) => onChange("image_requirements.composition.face_coverage_minimum", parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Face Coverage Max %</label>
            <input
              type="number"
              step="any"
              value={getValue("image_requirements.composition.face_coverage_maximum")}
              onChange={(e) => onChange("image_requirements.composition.face_coverage_maximum", parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Spectacles Policy</label>
            <select
              value={getValue("image_requirements.composition.spectacles_policy")}
              onChange={(e) => onChange("image_requirements.composition.spectacles_policy", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="allowed">Allowed</option>
              <option value="prohibited_if_tinted">Prohibited if tinted / glare</option>
              <option value="prohibited">Fully prohibited</option>
            </select>
          </div>
          <div className="flex flex-col gap-2.5 sm:col-span-2 mt-2">
            <div className="flex items-center gap-2 text-left">
              <input
                id="coverage-strict-checkbox"
                type="checkbox"
                checked={getValue("image_requirements.composition.coverage_is_strict", false)}
                onChange={(e) => onChange("image_requirements.composition.coverage_is_strict", e.target.checked)}
                className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
              />
              <label htmlFor="coverage-strict-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
                Coverage is rigid constraint (Fail instead of warning)
              </label>
            </div>
            <div className="flex items-center gap-2 text-left">
              <input
                id="hair-visible-checkbox"
                type="checkbox"
                checked={getValue("image_requirements.composition.complete_hair_visible", false)}
                onChange={(e) => onChange("image_requirements.composition.complete_hair_visible", e.target.checked)}
                className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
              />
              <label htmlFor="hair-visible-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
                Complete Hair Visible
              </label>
            </div>
            <div className="flex items-center gap-2 text-left">
              <input
                id="ears-visible-checkbox"
                type="checkbox"
                checked={getValue("image_requirements.composition.ears_visible", false)}
                onChange={(e) => onChange("image_requirements.composition.ears_visible", e.target.checked)}
                className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
              />
              <label htmlFor="ears-visible-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
                Ears Visible
              </label>
            </div>
            <div className="flex items-center gap-2 text-left">
              <input
                id="chin-visible-checkbox"
                type="checkbox"
                checked={getValue("image_requirements.composition.chin_visible", false)}
                onChange={(e) => onChange("image_requirements.composition.chin_visible", e.target.checked)}
                className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
              />
              <label htmlFor="chin-visible-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
                Chin Visible
              </label>
            </div>
            <div className="flex items-center gap-2 text-left">
              <input
                id="beard-visible-checkbox"
                type="checkbox"
                checked={getValue("image_requirements.composition.beard_boundary_visible", false)}
                onChange={(e) => onChange("image_requirements.composition.beard_boundary_visible", e.target.checked)}
                className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
              />
              <label htmlFor="beard-visible-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
                Beard Boundary Checked
              </label>
            </div>
            <div className="flex items-center gap-2 text-left">
              <input
                id="face-centred-checkbox"
                type="checkbox"
                checked={getValue("image_requirements.composition.face_centred", false)}
                onChange={(e) => onChange("image_requirements.composition.face_centred", e.target.checked)}
                className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
              />
              <label htmlFor="face-centred-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
                Face Centred Required
              </label>
            </div>
            <div className="flex items-center gap-2 text-left">
              <input
                id="frontal-pose-checkbox"
                type="checkbox"
                checked={getValue("image_requirements.composition.frontal_pose", false)}
                onChange={(e) => onChange("image_requirements.composition.frontal_pose", e.target.checked)}
                className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
              />
              <label htmlFor="frontal-pose-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
                Frontal Pose Check
              </label>
            </div>
            <div className="flex items-center gap-2 text-left">
              <input
                id="eye-visible-checkbox"
                type="checkbox"
                checked={getValue("image_requirements.composition.eye_visibility", false)}
                onChange={(e) => onChange("image_requirements.composition.eye_visibility", e.target.checked)}
                className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
              />
              <label htmlFor="eye-visible-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
                Eyes Open / Visible
              </label>
            </div>
          </div>
        </div>
      </details>

      {/* 7. Filename */}
      <details className="group border border-slate-200 dark:border-zinc-800 rounded-lg bg-white dark:bg-zinc-950 overflow-hidden shadow-sm">
        <summary className="p-4 font-semibold text-slate-800 dark:text-zinc-200 hover:bg-slate-50/50 dark:hover:bg-zinc-900/10 cursor-pointer select-none list-none flex items-center justify-between border-b border-transparent group-open:border-slate-150 dark:group-open:border-zinc-850">
          {renderSectionHeader("7. Filename Policies", "Configure exact name requirements, case sensitivity, and fallback extensions.")}
          <span className="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
        </summary>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Filename Mode</label>
            <select
              value={getValue("image_requirements.filename.mode")}
              onChange={(e) => onChange("image_requirements.filename.mode", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="exact">Exact string filename</option>
              <option value="pattern">Regex pattern match</option>
              <option value="unspecified">Unspecified name</option>
            </select>
          </div>
          {getValue("image_requirements.filename.mode") === "exact" && (
            <div className="space-y-1 text-left">
              <label className="font-semibold text-slate-650 dark:text-zinc-300">Exact Name</label>
              <input
                type="text"
                value={getValue("image_requirements.filename.exact_filename")}
                onChange={(e) => onChange("image_requirements.filename.exact_filename", e.target.value)}
                className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
                placeholder="e.g. exam_photo.jpg"
              />
            </div>
          )}
          {getValue("image_requirements.filename.mode") === "pattern" && (
            <div className="space-y-1 text-left">
              <label className="font-semibold text-slate-650 dark:text-zinc-300">Regex Pattern</label>
              <input
                type="text"
                value={getValue("image_requirements.filename.filename_pattern")}
                onChange={(e) => onChange("image_requirements.filename.filename_pattern", e.target.value)}
                className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
                placeholder="e.g. ^[0-9]{10}_photo$"
              />
            </div>
          )}
          <div className="space-y-1 text-left sm:col-span-2">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Fallback Basename</label>
            <input
              type="text"
              value={getValue("image_requirements.filename.fallback_basename")}
              onChange={(e) => onChange("image_requirements.filename.fallback_basename", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <div className="flex items-center gap-2 mt-4 text-left">
            <input
              id="case-sensitive-checkbox"
              type="checkbox"
              checked={getValue("image_requirements.filename.case_sensitive", false)}
              onChange={(e) => onChange("image_requirements.filename.case_sensitive", e.target.checked)}
              className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
            />
            <label htmlFor="case-sensitive-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
              Case Sensitive
            </label>
          </div>
          <div className="flex items-center gap-2 mt-4 text-left">
            <input
              id="ext-required-checkbox"
              type="checkbox"
              checked={getValue("image_requirements.filename.extension_required", false)}
              onChange={(e) => onChange("image_requirements.filename.extension_required", e.target.checked)}
              className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
            />
            <label htmlFor="ext-required-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
              Extension Required
            </label>
          </div>
        </div>
      </details>

      {/* 8. Exceptional Instructions */}
      <details className="group border border-slate-200 dark:border-zinc-800 rounded-lg bg-white dark:bg-zinc-950 overflow-hidden shadow-sm">
        <summary className="p-4 font-semibold text-slate-800 dark:text-zinc-200 hover:bg-slate-50/50 dark:hover:bg-zinc-900/10 cursor-pointer select-none list-none flex items-center justify-between border-b border-transparent group-open:border-slate-150 dark:group-open:border-zinc-850">
          {renderSectionHeader("8. Exceptional & Additional Rules", "Define printed details constraints, B&W restrictions, and model options.")}
          <span className="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
        </summary>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="space-y-1 text-left">
            <label className="font-semibold text-slate-650 dark:text-zinc-300">Processing Support Status</label>
            <select
              value={getValue("image_requirements.exceptional_instructions.processing_support_status")}
              onChange={(e) => onChange("image_requirements.exceptional_instructions.processing_support_status", e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white rounded border border-slate-250 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="supported">Supported</option>
              <option value="partial">Partial</option>
              <option value="unsupported">Unsupported</option>
            </select>
          </div>
          <div className="flex flex-col gap-2.5 sm:col-span-2 mt-2">
            <div className="flex items-center gap-2 text-left">
              <input
                id="printed-name-checkbox"
                type="checkbox"
                checked={getValue("image_requirements.exceptional_instructions.printed_name", false)}
                onChange={(e) => onChange("image_requirements.exceptional_instructions.printed_name", e.target.checked)}
                className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
              />
              <label htmlFor="printed-name-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
                Printed Name Required in Photo
              </label>
            </div>
            <div className="flex items-center gap-2 text-left">
              <input
                id="printed-date-checkbox"
                type="checkbox"
                checked={getValue("image_requirements.exceptional_instructions.printed_date", false)}
                onChange={(e) => onChange("image_requirements.exceptional_instructions.printed_date", e.target.checked)}
                className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
              />
              <label htmlFor="printed-date-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
                Printed Capture Date Required in Photo
              </label>
            </div>
            <div className="flex items-center gap-2 text-left">
              <input
                id="signature-checkbox"
                type="checkbox"
                checked={getValue("image_requirements.exceptional_instructions.signature_inclusion", false)}
                onChange={(e) => onChange("image_requirements.exceptional_instructions.signature_inclusion", e.target.checked)}
                className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
              />
              <label htmlFor="signature-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
                Signature Attachment Required
              </label>
            </div>
            <div className="flex items-center gap-2 text-left">
              <input
                id="bw-restriction-checkbox"
                type="checkbox"
                checked={getValue("image_requirements.exceptional_instructions.black_and_white_restriction", false)}
                onChange={(e) => onChange("image_requirements.exceptional_instructions.black_and_white_restriction", e.target.checked)}
                className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
              />
              <label htmlFor="bw-restriction-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
                Black & White Photo Allowed / Restricted
              </label>
            </div>
            <div className="flex items-center gap-2 text-left">
              <input
                id="recent-photo-checkbox"
                type="checkbox"
                checked={getValue("image_requirements.exceptional_instructions.recent_photo_requirement", false)}
                onChange={(e) => onChange("image_requirements.exceptional_instructions.recent_photo_requirement", e.target.checked)}
                className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
              />
              <label htmlFor="recent-photo-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
                Recent Photo Requirement (e.g. within 3/6 months)
              </label>
            </div>
            <div className="flex items-center gap-2 text-left">
              <input
                id="spec-restriction-checkbox"
                type="checkbox"
                checked={getValue("image_requirements.exceptional_instructions.spectacles_restriction", false)}
                onChange={(e) => onChange("image_requirements.exceptional_instructions.spectacles_restriction", e.target.checked)}
                className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
              />
              <label htmlFor="spec-restriction-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
                Spectacles Restrictions Apply
              </label>
            </div>
            <div className="flex items-center gap-2 text-left">
              <input
                id="headwear-restriction-checkbox"
                type="checkbox"
                checked={getValue("image_requirements.exceptional_instructions.headwear_restriction", false)}
                onChange={(e) => onChange("image_requirements.exceptional_instructions.headwear_restriction", e.target.checked)}
                className="w-4 h-4 rounded text-indigo-660 focus:ring-indigo-500/20 border-slate-350"
              />
              <label htmlFor="headwear-restriction-checkbox" className="font-medium text-slate-700 dark:text-zinc-350 cursor-pointer">
                Headwear Restrictions Apply (Turbans/Hijabs exceptions excluded)
              </label>
            </div>
          </div>
        </div>
      </details>
    </div>
  );
}
