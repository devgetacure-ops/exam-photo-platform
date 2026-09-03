"use client";

import { useMemo, useState } from "react";

import type { ExamDetail, RequirementSummary } from "../../lib/types";
import { RequirementPanel } from "./requirement-panel";
import { useKit } from "./use-kit";

/**
 * One examination's files, as a workspace rather than a page to scroll.
 *
 * The earlier version stacked every requirement fully expanded — diagrams,
 * specification, published rejection causes and an upload box, four times over
 * — which came to roughly six screens for four files. A candidate could not see
 * how much was left, could not compare two files, and had to scroll past three
 * they had already done to reach the fourth.
 *
 * So the list holds still on the left and only the selected file's detail
 * changes on the right. The list is the whole job at a glance: what is done,
 * what is left, and what is not ours. Nothing collapses or reflows as you work.
 */

interface Props {
  exam: ExamDetail;
}

type Row = { requirement: RequirementSummary; index: number };

function statusDot(state: string): string {
  switch (state) {
    case "ready":
      return "bg-ready";
    case "caveat":
      return "bg-caveat";
    case "blocked":
      return "bg-blocked";
    case "self":
      return "bg-self";
    default:
      return "bg-line-strong";
  }
}

export function KitWorkspace({ exam }: Props) {
  const { entries } = useKit(exam.exam_id);

  const { ours, theirs } = useMemo(() => {
    const rows: Row[] = (exam.requirements ?? []).map((requirement, index) => ({
      requirement,
      index,
    }));
    return {
      ours: rows.filter(
        ({ requirement }) =>
          requirement.platform_support === "supported" ||
          requirement.platform_support === "partially_supported"
      ),
      theirs: rows.filter(
        ({ requirement }) =>
          requirement.platform_support !== "supported" &&
          requirement.platform_support !== "partially_supported"
      ),
    };
  }, [exam.requirements]);

  const [selectedId, setSelectedId] = useState<string>(
    ours[0]?.requirement.requirement_id ?? theirs[0]?.requirement.requirement_id ?? ""
  );

  const selected =
    [...ours, ...theirs].find(
      (row) => row.requirement.requirement_id === selectedId
    ) ?? ours[0];

  const stateOf = (requirement: RequirementSummary): string => {
    if (
      requirement.platform_support !== "supported" &&
      requirement.platform_support !== "partially_supported"
    ) {
      return "self";
    }
    const entry = entries[requirement.requirement_id];
    if (!entry) return "todo";
    if (entry.outcome === "blocked" || entry.outcome === "not_produced") return "blocked";
    if (entry.outcome === "prepared_with_findings") return "caveat";
    return "ready";
  };

  const done = ours.filter(
    ({ requirement }) => entries[requirement.requirement_id]
  ).length;

  return (
    <div className="grid min-h-0 flex-1 grid-cols-[300px_1fr]">
      {/* --- The job, held still ------------------------------------------ */}
      <aside className="flex flex-col border-r border-line bg-sunk">
        <div className="border-b border-line px-5 py-4">
          <div className="flex items-baseline justify-between">
            <span className="label">Your files</span>
            <span className="spec text-sm text-ink">
              {done}/{ours.length}
            </span>
          </div>
          <div className="mt-2 flex h-1 gap-0.5 overflow-hidden rounded-full bg-line">
            {ours.map(({ requirement }) => (
              <span
                key={requirement.requirement_id}
                className={`h-full flex-1 ${
                  entries[requirement.requirement_id] ? "bg-ready" : "bg-transparent"
                }`}
              />
            ))}
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto p-2">
          {ours.map(({ requirement }) => {
            const state = stateOf(requirement);
            const active = requirement.requirement_id === selectedId;
            return (
              <button
                key={requirement.requirement_id}
                type="button"
                onClick={() => setSelectedId(requirement.requirement_id)}
                aria-current={active}
                className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-left ${
                  active ? "bg-surface shadow-card" : "hover:bg-surface/60"
                }`}
              >
                <span className={`size-2 shrink-0 rounded-full ${statusDot(state)}`} />
                <span
                  className={`min-w-0 flex-1 truncate text-sm ${
                    active ? "font-medium text-ink" : "text-ink-soft"
                  }`}
                >
                  {requirement.requirement_name}
                </span>
              </button>
            );
          })}

          {theirs.length > 0 && (
            <>
              <p className="label mt-4 px-3 pb-1 text-self">You do these</p>
              {theirs.map(({ requirement }) => {
                const active = requirement.requirement_id === selectedId;
                return (
                  <button
                    key={requirement.requirement_id}
                    type="button"
                    onClick={() => setSelectedId(requirement.requirement_id)}
                    aria-current={active}
                    className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-left ${
                      active ? "bg-surface shadow-card" : "hover:bg-surface/60"
                    }`}
                  >
                    <span className="size-2 shrink-0 rounded-full bg-self" />
                    <span className="min-w-0 flex-1 truncate text-sm text-self">
                      {requirement.requirement_name}
                    </span>
                  </button>
                );
              })}
            </>
          )}
        </nav>

        <div className="border-t border-line px-5 py-4">
          <div className="flex items-baseline justify-between">
            <span className="text-sm text-ink-soft">
              {ours.length > 1 ? "All files" : "This file"}
            </span>
            <span className="text-xl font-semibold">
              ₹{ours.length > 1 ? 8 : 4}
            </span>
          </div>
          <button
            type="button"
            disabled={done === 0}
            className="mt-3 w-full rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-on-accent
                       disabled:cursor-not-allowed disabled:bg-line-strong disabled:text-muted"
          >
            {done === 0
              ? "Add a file to continue"
              : done < ours.length
                ? `Get ${done} now`
                : "Get all files"}
          </button>
          <p className="mt-2 text-xs text-muted">
            Final price. Deleted after 30 minutes.
          </p>
        </div>
      </aside>

      {/* --- One file at a time ------------------------------------------- */}
      <section className="min-w-0 overflow-y-auto">
        {selected && (
          <RequirementPanel
            key={selected.requirement.requirement_id}
            requirement={selected.requirement}
            index={selected.index}
            exam={exam}
          />
        )}
      </section>
    </div>
  );
}
