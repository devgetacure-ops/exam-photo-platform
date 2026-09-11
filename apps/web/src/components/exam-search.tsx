"use client";

import { useMemo, useRef, useState, useId } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { SearchEntry } from "../lib/types";
import { rankEntries } from "../lib/search-rank";

/**
 * The picker. A candidate arrives knowing one thing — the name of their
 * examination — so search is the whole interaction: no categories, no browse
 * tree, no filters.
 *
 * The whole index is in memory (every record and its aliases, a few KB), so
 * matching costs no round trip and results appear as fast as the candidate can
 * type. That is the difference between a search box that feels like a product
 * and one that feels like a form.
 */

interface Props {
  exams: SearchEntry[];
  unavailable: SearchEntry[];
  /** Focus on mount — on the landing page the search *is* the page. */
  autoFocus?: boolean;
  /** Off on /exams itself, where offering to browse the page you are on reads careless. */
  showBrowseLink?: boolean;
}

export function ExamSearch({
  exams,
  unavailable,
  autoFocus = false,
  showBrowseLink = true,
}: Props) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listId = useId();

  const { available, blocked } = useMemo(() => {
    if (!query.trim()) return { available: [], blocked: [] };
    return {
      available: rankEntries(exams, query).slice(0, 7),
      blocked: rankEntries(unavailable, query).slice(0, 4),
    };
  }, [query, exams, unavailable]);

  // Only selectable rows take part in keyboard navigation. An unavailable
  // examination is shown, never selected — arrowing onto it and pressing
  // Enter would imply it leads somewhere (DEC-056).
  const navigable = available;
  const hasResults = available.length > 0 || blocked.length > 0;
  const requestHref = `/exam-request?exam=${encodeURIComponent(query.trim())}`;

  const go = (entry: SearchEntry) => router.push(`/exam/${entry.id}`);

  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((i) => Math.max(0, Math.min(i + 1, navigable.length - 1)));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (event.key === "Enter") {
      const chosen = navigable[active];
      if (chosen) {
        event.preventDefault();
        go(chosen.entry);
      } else if (query.trim() && !hasResults) {
        // Nothing to select, so Enter does the one useful thing left.
        event.preventDefault();
        router.push(requestHref);
      }
    } else if (event.key === "Escape") {
      setQuery("");
    }
  };

  return (
    <div className="w-full">
      <div
        className="group flex items-center gap-3 border-[3px] border-[var(--ink)] bg-[var(--paper)]
                   px-5 py-4 shadow-[5px_5px_0_var(--ink)] transition-colors
                   focus-within:border-[var(--signal-deep)]"
      >
        <svg
          className="size-5 shrink-0 text-[var(--ink)]"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          aria-hidden="true"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m20.5 20.5-4.2-4.2" />
        </svg>
        <input
          ref={inputRef}
          type="search"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setActive(0);
          }}
          onKeyDown={onKeyDown}
          autoFocus={autoFocus}
          placeholder="Search your exam: SSC, CAT, IBPS PO, NEET…"
          aria-label="Search for your examination"
          aria-autocomplete="list"
          aria-controls={listId}
          aria-activedescendant={available[active] ? `${listId}-${active}` : undefined}
          aria-expanded={hasResults}
          role="combobox"
          autoComplete="off"
          spellCheck={false}
          className="w-full bg-transparent text-lg text-[var(--ink)] outline-none
                     placeholder:text-[var(--ink-55)]
                     [&::-webkit-search-cancel-button]:appearance-none"
        />
        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery("");
              inputRef.current?.focus();
            }}
            className="euk-label shrink-0 px-1.5 py-1 text-[11px] text-[var(--ink-55)] hover:text-[var(--ink)]"
            aria-label="Clear search"
          >
            Clear
          </button>
        )}
      </div>

      {query.trim() && (
        <div
          id={listId}
          role="listbox"
          aria-label="Matching examinations"
          className="mt-2 overflow-hidden border-[3px] border-[var(--ink)] bg-[var(--paper)] shadow-[7px_7px_0_var(--ink)]"
        >
          {/*
            An empty result is where a candidate decides we do not have their
            examination, so it hands them the next step rather than a shrug.
          */}
          {!hasResults && (
            <div className="px-4 py-5">
              <p className="text-[15px] leading-relaxed text-[var(--ink-70)]">
                Nothing matches{" "}
                <span className="font-semibold text-[var(--ink)]">“{query.trim()}”</span>.
                Try its full name or its short form. If it still isn&rsquo;t
                here, we don&rsquo;t prepare it yet.
              </p>
              <Link href={requestHref} className="euk-link mt-3 inline-block text-[15px]">
                Ask us to add it
              </Link>
            </div>
          )}

          {available.map((row, index) => (
            <button
              key={row.entry.id}
              id={`${listId}-${index}`}
              type="button"
              role="option"
              aria-selected={index === active}
              onMouseEnter={() => setActive(index)}
              onClick={() => go(row.entry)}
              className={`flex w-full items-center gap-3 border-b-2 border-[var(--hairline)] px-4 py-3
                          text-left last:border-b-0 ${
                            index === active ? "bg-[var(--partial-fill)]" : "hover:bg-[var(--paper-2)]"
                          }`}
            >
              <span className="min-w-0 flex-1">
                <span className="block truncate font-medium text-[var(--ink)]">
                  {row.entry.name}
                </span>
                <span className="mt-0.5 block truncate text-xs text-[var(--ink-55)]">
                  {row.entry.body}
                  {row.via && (
                    <>
                      {" · also "}
                      <span className="text-[var(--ink-70)]">{row.via}</span>
                    </>
                  )}
                </span>
              </span>
              <span className="euk-figures shrink-0 text-xs text-[var(--ink-70)]">
                {row.entry.prepares} file{row.entry.prepares === 1 ? "" : "s"}
              </span>
              <svg
                className="size-4 shrink-0 text-[var(--ink-55)]"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                aria-hidden="true"
              >
                <path d="m9 18 6-6-6-6" />
              </svg>
            </button>
          ))}

          {/*
            Unavailable examinations appear in the results rather than being
            filtered out. A candidate searching SSC CGL and finding nothing
            concludes the platform does not cover it; an absence discovered
            here is better than one discovered at the portal (DEC-056). They
            are visibly not selectable — no chevron, no hover affordance,
            muted ground — because the one thing worse than an absence is
            implying we can do something we cannot.
          */}
          {blocked.length > 0 && (
            <div className="border-t-2 border-[var(--ink)] bg-[var(--paper-2)]">
              <p className="euk-label px-4 pt-3 pb-1.5 text-[11px]">Not yet available</p>
              {blocked.map((row) => (
                <div
                  key={row.entry.name}
                  className="border-b-2 border-[var(--hairline)] px-4 py-3 last:border-b-0"
                >
                  <p className="text-sm font-medium text-[var(--ink-70)]">{row.entry.name}</p>
                  <p className="mt-0.5 text-xs text-[var(--ink-55)]">
                    {row.entry.unavailable?.reason === "live capture only"
                      ? "The portal photographs you directly, so there is no photo for us to prepare."
                      : "We have not confirmed this exam's published specification yet."}
                    {(row.entry.unavailable?.deliverables ?? 0) > 0 && (
                      <>
                        {" "}
                        Its other {row.entry.unavailable?.deliverables} upload
                        {row.entry.unavailable?.deliverables === 1 ? "" : "s"} are on our
                        list.
                      </>
                    )}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      <div className="euk-label flex flex-wrap gap-4 px-4 py-3 text-[11px] [&_a]:text-[var(--ink-55)] [&_a]:underline [&_a]:underline-offset-4 [&_a:hover]:text-[var(--signal-deep)]">
        {showBrowseLink && <Link href="/exams">Browse all {exams.length} exams ↗</Link>}
        {query.trim() && hasResults && <Link href={requestHref}>Not the one? Ask us to add it ↗</Link>}
      </div>
    </div>
  );
}
