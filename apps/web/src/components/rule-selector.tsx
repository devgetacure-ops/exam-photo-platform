import React, { useState } from "react";
import { validateRuleJson } from "../lib/file-validation";

interface RuleSelectorProps {
  onRuleSelected: (ruleJson: object | null, name: string) => void;
  selectedName: string;
}

export function RuleSelector({ onRuleSelected, selectedName }: RuleSelectorProps) {
  const [activeTab, setActiveTab] = useState<"bundled" | "custom">("bundled");
  const [selectedSample, setSelectedSample] = useState<string>("");
  const [customError, setCustomError] = useState<string | null>(null);
  const [customFileName, setCustomFileName] = useState<string | null>(null);

  const samples = [
    {
      id: "exact_300x400",
      label: "Fictional Exact 300x400 White BG Exam",
      path: "/rules/sample_exact_300x400_50kb_white_bg.json",
    },
    {
      id: "range_200_300",
      label: "Fictional Range Dimensions White BG Exam",
      path: "/rules/sample_range_200_300_width_230_400_height_50kb_white_bg.json",
    },
  ];

  // Fetch sample rule on selection
  const handleSampleChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedSample(val);
    if (!val) {
      onRuleSelected(null, "");
      return;
    }

    const matched = samples.find((s) => s.id === val);
    if (matched) {
      try {
        const response = await fetch(matched.path);
        if (!response.ok) {
          throw new Error("Failed to load sample rule file");
        }
        const data = await response.json();
        onRuleSelected(data, matched.label);
      } catch (err) {
        onRuleSelected(null, "");
        const error = err as Error;
        alert(`Error loading sample rule: ${error.message}`);
      }
    }
  };

  const handleCustomUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setCustomFileName(file.name);
    setCustomError(null);

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      const res = validateRuleJson(text);
      if (res.valid) {
        onRuleSelected(res.data as object, file.name);
      } else {
        setCustomError(res.error || "Invalid rule file");
        onRuleSelected(null, "");
      }
    };
    reader.onerror = () => {
      setCustomError("Failed to read file.");
      onRuleSelected(null, "");
    };
    reader.readAsText(file);
  };

  const handleTabChange = (tab: "bundled" | "custom") => {
    setActiveTab(tab);
    setCustomError(null);
    setCustomFileName(null);
    setSelectedSample("");
    onRuleSelected(null, "");
  };

  return (
    <div className="bg-white dark:bg-zinc-950 border border-slate-200 dark:border-zinc-800 rounded-lg p-5 shadow-sm space-y-4">
      <div>
        <h2 className="text-base font-semibold text-slate-900 dark:text-white">
          Step 1: Select Examination Rules
        </h2>
        <p className="text-xs text-slate-500 dark:text-zinc-400 mt-0.5">
          Choose a pre-defined sample rule cycle or upload your own exam compliance JSON rule.
        </p>
      </div>

      <div className="flex border-b border-slate-200 dark:border-zinc-800 text-sm">
        <button
          type="button"
          onClick={() => handleTabChange("bundled")}
          className={`pb-2 px-4 font-medium transition-all ${
            activeTab === "bundled"
              ? "border-b-2 border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400"
              : "text-slate-500 hover:text-slate-800 dark:text-zinc-400 dark:hover:text-zinc-200"
          }`}
        >
          Sample Rules
        </button>
        <button
          type="button"
          onClick={() => handleTabChange("custom")}
          className={`pb-2 px-4 font-medium transition-all ${
            activeTab === "custom"
              ? "border-b-2 border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400"
              : "text-slate-500 hover:text-slate-800 dark:text-zinc-400 dark:hover:text-zinc-200"
          }`}
        >
          Custom Rule JSON
        </button>
      </div>

      {activeTab === "bundled" ? (
        <div className="space-y-2">
          <label
            htmlFor="sample-rules-dropdown"
            className="block text-xs font-semibold text-slate-700 dark:text-zinc-300"
          >
            Bundled Exam Configurations
          </label>
          <select
            id="sample-rules-dropdown"
            value={selectedSample}
            onChange={handleSampleChange}
            className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white text-sm rounded-md border border-slate-200 dark:border-zinc-800 p-2.5 outline-none focus:ring-2 focus:ring-indigo-500/20"
          >
            <option value="">-- Choose an exam rule --</option>
            {samples.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex flex-col items-center justify-center border-2 border-dashed border-slate-200 dark:border-zinc-800 rounded-lg p-5 bg-slate-50 dark:bg-zinc-900 transition-colors">
            <svg
              className="w-8 h-8 text-slate-400 dark:text-zinc-500 mb-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <label
              htmlFor="custom-rule-file-input"
              className="cursor-pointer bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 hover:bg-slate-50 dark:hover:bg-zinc-750 text-slate-800 dark:text-white font-medium text-xs py-1.5 px-3 rounded shadow-sm transition-colors"
            >
              Upload Rule JSON
            </label>
            <input
              id="custom-rule-file-input"
              type="file"
              accept=".json"
              onChange={handleCustomUpload}
              className="hidden"
            />
            {customFileName && (
              <p className="text-xs text-slate-600 dark:text-zinc-350 mt-2 font-mono">
                {customFileName}
              </p>
            )}
          </div>

          {customError && (
            <div className="text-xs text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/30 rounded p-2.5">
              {customError}
            </div>
          )}
        </div>
      )}

      {selectedName && (
        <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-450 bg-emerald-50 dark:bg-emerald-950/10 border border-emerald-100 dark:border-emerald-900/20 rounded p-2">
          <svg
            className="w-4 h-4 shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span className="truncate">
            Active Rule: <strong>{selectedName}</strong>
          </span>
        </div>
      )}
    </div>
  );
}
