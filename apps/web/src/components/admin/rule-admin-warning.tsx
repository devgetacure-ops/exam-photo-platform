import React from "react";

interface RuleAdminWarningProps {
  enabled: boolean;
}

export function RuleAdminWarning({ enabled }: RuleAdminWarningProps) {
  if (!enabled) {
    return (
      <div className="max-w-md mx-auto my-12 p-6 bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/30 rounded-lg text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-rose-100 dark:bg-rose-900/40 text-rose-600 dark:text-rose-455 flex items-center justify-center mx-auto">
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
        </div>
        <h2 className="text-base font-bold text-rose-900 dark:text-rose-350">Admin Console Gated</h2>
        <p className="text-xs text-rose-700 dark:text-rose-400 leading-relaxed">
          The local rules configuration console is locked. To enable this development tool, set the environment variable:
        </p>
        <pre className="p-2.5 bg-slate-900 text-rose-400 rounded text-[10px] font-mono select-all overflow-x-auto text-left">
          NEXT_PUBLIC_ENABLE_RULE_ADMIN=true
        </pre>
        <p className="text-[10px] text-rose-500 dark:text-rose-455 italic">
          This flag is only a local accidental-exposure guard. It is not authentication.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-amber-50/20 dark:bg-amber-950/10 border border-amber-200/50 dark:border-amber-900/20 rounded-lg p-3 text-xs text-amber-700 dark:text-amber-450 flex items-start gap-2.5">
      <svg
        className="w-4 h-4 shrink-0 mt-0.5 text-amber-500"
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
      <div className="space-y-0.5">
        <p className="font-semibold">Local Development Rule Configuration Console Active</p>
        <p className="leading-relaxed opacity-90">
          This is a local development utility. Do not expose this admin route publicly. It lacks authentication, authorization, and audit logs. This flag is only a local accidental-exposure guard. It is not authentication.
        </p>
      </div>
    </div>
  );
}
