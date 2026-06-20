import React, { useRef } from "react";
import { exportRuleJson } from "../../lib/rule-export";
import { RuleDocument } from "../../lib/types";

interface RuleJsonPanelProps {
  rule: RuleDocument | null;
  onImport: (imported: RuleDocument) => void;
  isDirty: boolean;
  validationStatus: "valid" | "invalid" | "unvalidated";
}

export function RuleJsonPanel({ rule, onImport, isDirty, validationStatus }: RuleJsonPanelProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formattedJson = rule ? JSON.stringify(rule, null, 2) : "";

  const handleCopy = () => {
    navigator.clipboard.writeText(formattedJson);
    alert("JSON copied to clipboard!");
  };

  const handleDownload = () => {
    if (!rule) return;
    const filename = rule.rule_id ? `${rule.rule_id}.json` : "exam_rule.json";
    exportRuleJson(rule, filename);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target?.result as string);
        onImport(parsed);
      } catch {
        alert("Failed to parse JSON file.");
      }
    };
    reader.readAsText(file);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="bg-white dark:bg-zinc-950 border border-slate-200 dark:border-zinc-800 rounded-lg p-5 shadow-sm flex flex-col h-full text-left space-y-4">
      <div className="flex items-center justify-between border-b border-slate-150 dark:border-zinc-850 pb-3">
        <div className="space-y-0.5">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">Raw JSON Configuration</h3>
          <p className="text-[10px] text-slate-500">Live serialized representation of the rule draft.</p>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] font-semibold">
          {/* Validation Status Badge */}
          {validationStatus === "valid" && (
            <span className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-450 px-2 py-0.5 rounded-full border border-emerald-200/30">
              Valid
            </span>
          )}
          {validationStatus === "invalid" && (
            <span className="bg-rose-50 text-rose-700 dark:bg-rose-950/20 dark:text-rose-455 px-2 py-0.5 rounded-full border border-rose-200/30">
              Invalid
            </span>
          )}
          {validationStatus === "unvalidated" && (
            <span className="bg-slate-55 text-slate-600 dark:bg-zinc-900 dark:text-zinc-400 px-2 py-0.5 rounded-full border border-slate-200 dark:border-zinc-800">
              Unchecked
            </span>
          )}

          {/* Draft/Dirty Status Badge */}
          {isDirty ? (
            <span className="bg-amber-50 text-amber-700 dark:bg-amber-950/20 dark:text-amber-450 px-2 py-0.5 rounded-full border border-amber-200/30">
              Draft
            </span>
          ) : (
            <span className="bg-slate-55 text-slate-500 dark:bg-zinc-900 dark:text-zinc-500 px-2 py-0.5 rounded-full border border-slate-200 dark:border-zinc-800">
              Saved
            </span>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={handleCopy}
          disabled={!rule}
          className="bg-slate-55 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 text-slate-800 dark:text-white font-semibold text-[10px] py-1.5 px-3 rounded shadow-sm hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Copy JSON
        </button>
        <button
          type="button"
          onClick={handleDownload}
          disabled={!rule}
          className="bg-indigo-600 text-white font-semibold text-[10px] py-1.5 px-3 rounded shadow-sm hover:bg-indigo-750 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Export / Download JSON
        </button>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="bg-slate-55 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 text-slate-850 dark:text-white font-semibold text-[10px] py-1.5 px-3 rounded shadow-sm hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors"
        >
          Import Rule JSON
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>

      <div className="flex-1 min-h-[300px] relative">
        <textarea
          readOnly
          value={formattedJson}
          className="w-full h-full min-h-[350px] p-3 bg-slate-900 text-slate-200 dark:bg-zinc-950 dark:text-zinc-300 border border-slate-200 dark:border-zinc-800 rounded-lg text-[10px] font-mono focus:outline-none resize-none leading-relaxed"
          placeholder="Rule configuration JSON will appear here..."
        />
      </div>
    </div>
  );
}
