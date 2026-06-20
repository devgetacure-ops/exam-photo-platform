import React from "react";

interface ProcessingStatusProps {
  status: "idle" | "sending" | "processing" | "succeeded" | "failed" | "error";
  message?: string;
}

export function ProcessingStatus({ status, message }: ProcessingStatusProps) {
  if (status === "idle") return null;

  const isSpinnerVisible = status === "sending" || status === "processing";

  return (
    <div className="bg-white dark:bg-zinc-950 border border-slate-200 dark:border-zinc-800 rounded-lg p-5 shadow-sm flex flex-col items-center justify-center space-y-4">
      {isSpinnerVisible && (
        <div className="relative w-12 h-12 flex items-center justify-center">
          <div className="absolute inset-0 rounded-full border-4 border-slate-100 dark:border-zinc-800"></div>
          <div className="absolute inset-0 rounded-full border-4 border-t-indigo-600 dark:border-t-indigo-500 animate-spin"></div>
        </div>
      )}

      {status === "error" && (
        <div className="text-rose-600 dark:text-rose-500" aria-hidden="true">
          <svg
            className="w-12 h-12"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
      )}

      <div className="text-center space-y-1">
        <p className="text-sm font-semibold text-slate-800 dark:text-white capitalize">
          {status === "sending"
            ? "Sending Data..."
            : status === "processing"
            ? "Processing Compliance Diagnostics..."
            : status === "error"
            ? "Operation Failed"
            : status}
        </p>
        {message && (
          <p className="text-xs text-slate-500 dark:text-zinc-400 max-w-md font-mono whitespace-pre-wrap leading-relaxed bg-slate-50 dark:bg-zinc-900/50 p-2.5 rounded border border-slate-100 dark:border-zinc-900">
            {message}
          </p>
        )}
      </div>
    </div>
  );
}
