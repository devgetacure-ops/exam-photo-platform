import React, { useState } from "react";
import { RuleAdminWarning } from "./rule-admin-warning";
import { RuleFormSections } from "./rule-form-sections";
import { RuleJsonPanel } from "./rule-json-panel";
import { RulePreviewCard } from "./rule-preview-card";
import { RuleValidationPanel } from "./rule-validation-panel";
import { validateRule } from "../../lib/rule-admin-api";
import { RULE_SAMPLES, fetchSampleRule } from "../../lib/rule-samples";
import { setNestedValue } from "../../lib/rule-editor-state";
import { RuleValidationError, RuleDocument } from "../../lib/types";

interface RuleEditorProps {
  apiGateEnabled: boolean;
}

export function RuleEditor({ apiGateEnabled }: RuleEditorProps) {
  const [activeRule, setActiveRule] = useState<RuleDocument | null>(null);
  const [lastLoadedRule, setLastLoadedRule] = useState<RuleDocument | null>(null);
  const [selectedSampleId, setSelectedSampleId] = useState<string>("");

  const [validationErrors, setValidationErrors] = useState<RuleValidationError[]>([]);
  const [validationStatus, setValidationStatus] = useState<"valid" | "invalid" | "unvalidated">(
    "unvalidated"
  );
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Derive dirty state
  const isDirty =
    activeRule !== null &&
    lastLoadedRule !== null &&
    JSON.stringify(activeRule) !== JSON.stringify(lastLoadedRule);

  // Handle drop-down sample rule selection
  const handleSelectSample = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedSampleId(val);
    if (!val) {
      setActiveRule(null);
      setLastLoadedRule(null);
      setValidationErrors([]);
      setValidationStatus("unvalidated");
      return;
    }

    const matched = RULE_SAMPLES.find((s) => s.id === val);
    if (matched) {
      try {
        setErrorMessage(null);
        const data = await fetchSampleRule(matched);
        setActiveRule(data);
        setLastLoadedRule(data);
        setValidationErrors([]);
        setValidationStatus("unvalidated");
      } catch (err) {
        const error = err as Error;
        setErrorMessage(`Failed to load sample: ${error.message}`);
      }
    }
  };

  // Handle custom JSON upload/import
  const handleImportJson = (imported: RuleDocument) => {
    if (!imported || typeof imported !== "object") {
      alert("Invalid JSON format.");
      return;
    }
    setActiveRule(imported);
    setLastLoadedRule(imported);
    setSelectedSampleId("");
    setValidationErrors([]);
    setValidationStatus("unvalidated");
    setErrorMessage(null);
  };

  // Revert changes back to pristine loaded rule
  const handleRevert = () => {
    if (lastLoadedRule) {
      setActiveRule(lastLoadedRule);
      setValidationErrors([]);
      setValidationStatus("unvalidated");
      setErrorMessage(null);
    }
  };

  // Form field value change updates rule draft
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleValueChange = (path: string, value: any) => {
    const updated = setNestedValue(activeRule, path, value);
    setActiveRule(updated);
    // Mark as unvalidated when edits are made
    setValidationStatus("unvalidated");
  };

  // Run backend rule validation endpoint
  const handleValidate = async () => {
    if (!activeRule) return;
    setIsValidating(true);
    setErrorMessage(null);
    try {
      const response = await validateRule(activeRule);
      setValidationErrors(response.errors);
      setValidationStatus(response.is_valid ? "valid" : "invalid");
    } catch (err) {
      const error = err as Error;
      setErrorMessage(error.message || "An unexpected error occurred during rule validation.");
      setValidationStatus("unvalidated");
    } finally {
      setIsValidating(false);
    }
  };

  if (!apiGateEnabled) {
    return (
      <div className="max-w-5xl mx-auto py-12 px-4 sm:px-8">
        <RuleAdminWarning enabled={false} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <RuleAdminWarning enabled={true} />

      {/* Header controls toolbar */}
      <div className="bg-white dark:bg-zinc-950 border border-slate-200 dark:border-zinc-800 rounded-lg p-5 shadow-sm space-y-4 text-left">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2 flex-1 max-w-md">
            <label
              htmlFor="admin-sample-dropdown"
              className="block text-xs font-semibold text-slate-700 dark:text-zinc-300"
            >
              Load Starter Rule Template
            </label>
            <select
              id="admin-sample-dropdown"
              value={selectedSampleId}
              onChange={handleSelectSample}
              className="w-full bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-white text-sm rounded-md border border-slate-200 dark:border-zinc-800 p-2 outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="">-- Select template rule --</option>
              {RULE_SAMPLES.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end gap-2.5">
            <button
              type="button"
              onClick={handleValidate}
              disabled={!activeRule || isValidating}
              className="bg-indigo-650 hover:bg-indigo-750 text-white font-semibold text-xs py-2 px-4 rounded shadow-sm transition-colors focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isValidating ? "Validating..." : "Validate Rule"}
            </button>
            <button
              type="button"
              onClick={handleRevert}
              disabled={!isDirty}
              className="bg-slate-55 dark:bg-zinc-900 border border-slate-250 dark:border-zinc-850 hover:bg-slate-100 dark:hover:bg-zinc-800 text-slate-805 dark:text-white font-semibold text-xs py-2 px-4 rounded shadow-sm transition-colors focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Revert Changes
            </button>
          </div>
        </div>

        {errorMessage && (
          <div className="text-xs text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/30 rounded p-2.5">
            {errorMessage}
          </div>
        )}
      </div>

      {activeRule && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Form Editor (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <RuleFormSections rule={activeRule} onChange={handleValueChange} />
          </div>

          {/* Right Column: JSON Preview & Validation Status (5 cols) */}
          <div className="lg:col-span-5 space-y-6 lg:sticky lg:top-6">
            <RulePreviewCard rule={activeRule} />
            <RuleValidationPanel
              errors={validationErrors}
              isValid={validationStatus === "unvalidated" ? null : validationStatus === "valid"}
              isValidating={isValidating}
            />
            <RuleJsonPanel
              rule={activeRule}
              onImport={handleImportJson}
              isDirty={isDirty}
              validationStatus={validationStatus}
            />
          </div>
        </div>
      )}
    </div>
  );
}
