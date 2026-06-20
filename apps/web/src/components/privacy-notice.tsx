import React from "react";

export function PrivacyNotice() {
  return (
    <div className="bg-slate-50 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 rounded-lg p-5 text-sm text-slate-700 dark:text-zinc-300 shadow-sm leading-relaxed max-w-full">
      <div className="flex items-start gap-3">
        <div className="text-amber-600 dark:text-amber-500 mt-0.5" aria-hidden="true">
          <svg
            className="w-5 h-5"
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
        </div>
        <div className="flex-1 space-y-2">
          <h2 className="font-semibold text-slate-900 dark:text-white">
            Compliance & Privacy Information
          </h2>
          <p>
            Your photo is sensitive personal data. This MVP application operates within a strict local privacy boundary, transmitting uploaded images exclusively to your configured local API.
          </p>
          <p className="font-medium text-slate-800 dark:text-zinc-200">
            Important Notices:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li>
              This tool helps format an exam photo based on structured rules, but it{" "}
              <strong>cannot guarantee acceptance</strong> by any exam authority.
            </li>
            <li>
              Photos are processed through the configured local processing API. Delete the job after downloading your formatted output.
            </li>
            <li>
              Do not expose the local API publicly without authentication, SSL/TLS encryption, and rate limiting controls.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
