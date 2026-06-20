"use client";

import React from "react";
import { RuleEditor } from "../../../components/admin/rule-editor";

export default function AdminRulesPage() {
  const apiGateEnabled = process.env.NEXT_PUBLIC_ENABLE_RULE_ADMIN === "true";

  return (
    <div className="flex-1 bg-slate-50 dark:bg-zinc-950 font-sans text-slate-800 dark:text-zinc-200 min-h-screen">
      <header className="bg-white dark:bg-zinc-900 border-b border-slate-200 dark:border-zinc-800 py-6 px-4 sm:px-8">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="space-y-0.5 text-left">
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
                Exam Rules Configuration Manager
              </h1>
              <span className="bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-450 border border-amber-100 dark:border-amber-900/30 text-[10px] font-semibold px-2 py-0.5 rounded-full">
                Developer Console
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-zinc-400">
              Create, edit, validate, and export structured JSON rules.
            </p>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto py-8 px-4 sm:px-8">
        <RuleEditor apiGateEnabled={apiGateEnabled} />
      </main>
    </div>
  );
}
