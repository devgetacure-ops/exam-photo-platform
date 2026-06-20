import React from "react";
import { RuleValidationError } from "../../lib/types";

interface RuleValidationPanelProps {
  errors: RuleValidationError[];
  isValid: boolean | null;
  isValidating: boolean;
}

export function RuleValidationPanel({ errors, isValid, isValidating }: RuleValidationPanelProps) {
  if (isValidating) {
    return (
      <div className="p-4 bg-slate-50 dark:bg-zinc-900/50 border border-slate-200 dark:border-zinc-800 rounded-lg text-center text-xs text-slate-500">
        Validating rules with backend service...
      </div>
    );
  }

  if (isValid === null) {
    return (
      <div className="p-4 bg-slate-50 dark:bg-zinc-900/50 border border-slate-200 dark:border-zinc-800 rounded-lg text-center text-xs text-slate-500">
        Click &quot;Validate Rule&quot; to run validation routines.
      </div>
    );
  }

  if (isValid) {
    return (
      <div className="p-4 bg-emerald-50 dark:bg-emerald-950/10 border border-emerald-200 dark:border-emerald-900/20 rounded-lg flex items-start gap-2.5 text-xs text-emerald-800 dark:text-emerald-450">
        <svg
          className="w-4 h-4 shrink-0 text-emerald-500 mt-0.5"
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
        <div>
          <p className="font-semibold">Rule JSON is Valid</p>
          <p className="opacity-90 mt-0.5">
            All configuration parameters strictly comply with the canonical backend JSON Schema and
            validation constraints.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="p-3 bg-rose-50 dark:bg-rose-950/10 border border-rose-200 dark:border-rose-900/20 rounded-lg flex items-start gap-2.5 text-xs text-rose-800 dark:text-rose-455">
        <svg
          className="w-4 h-4 shrink-0 text-rose-500 mt-0.5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <div>
          <p className="font-semibold">Validation Check Failed</p>
          <p className="opacity-90 mt-0.5">
            Found {errors.length} configuration error(s) that must be resolved.
          </p>
        </div>
      </div>

      <div className="border border-slate-200 dark:border-zinc-800 rounded-lg overflow-hidden divide-y divide-slate-200 dark:divide-zinc-850 text-xs">
        {errors.map((err, idx) => (
          <div
            key={idx}
            className="p-3 bg-white dark:bg-zinc-950 hover:bg-slate-50/50 dark:hover:bg-zinc-900/10 transition-colors space-y-1 text-left"
          >
            <div className="flex items-center justify-between">
              <span
                className="font-mono text-[10px] text-indigo-650 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/30 px-1.5 py-0.5 rounded truncate max-w-[200px]"
                title={err.field_path}
              >
                {err.field_path || "(root)"}
              </span>
              <span
                className={`text-[9px] font-bold uppercase px-1 rounded ${
                  err.severity === "error"
                    ? "text-rose-600 dark:text-rose-455 bg-rose-50 dark:bg-rose-950/20"
                    : "text-amber-600 dark:text-amber-450 bg-amber-50 dark:bg-amber-950/20"
                }`}
              >
                {err.severity}
              </span>
            </div>
            <p className="text-slate-800 dark:text-zinc-200 font-medium">{err.message}</p>
            <p className="text-[10px] text-slate-450 dark:text-zinc-500 font-mono">
              Code: {err.error_code}
            </p>
            {err.suggested_resolution && (
              <p className="text-[10px] text-slate-500 dark:text-zinc-450 italic mt-0.5">
                Tip: {err.suggested_resolution}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
