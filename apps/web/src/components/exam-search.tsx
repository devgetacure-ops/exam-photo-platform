"use client";

import { useMemo, useRef, useState, useId } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { SearchEntry } from "../lib/types";

/**
 * The picker. A candidate arrives knowing one thing — the name of their
 * examination — so search is the whole interaction: no categories, no browse
 * tree, no filters.
 *
 * The whole index is in memory (39 records and their aliases, a few KB), so
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

/** A match, plus how good it was, so exact and prefix hits outrank substrings. */
interface Ranked {
  entry: SearchEntry;
  score: number;
  /** The alias that matched, when it was not the name. Shown so the candidate
   *  sees *why* a row came back for "CAT". */
  via: string | null;
}

function normalise(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

/**
 * The same string with every separator removed.
 *
 * Examination names are written inconsistently in the wild -- "MHT-CET" and
 * "MHT CET", "R.B.I." and "RBI", "CUET-UG" and "CUET UG" -- and a candidate
 * types whichever they saw. Comparing the compact forms as well as the spaced
 * ones makes all of those spellings find the same exam.
 */
function compact(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function escapeForRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * How well one haystack answers the query, 0 for not at all.
 *
 * Ranked rather than boolean so an exact or leading match outranks a substring
 * buried mid-string: typing "gate" should surface GATE, not every examination
 * whose description happens to contain "postgraduate".
 */
function rateOne(haystack: string, q: string): number {
  if (!haystack || !q) return 0;
  if (haystack === q) return 100;
  if (haystack.startsWith(q)) return 80;
  if (new RegExp(`\\b${escapeForRegExp(q)}`).test(haystack)) return 60;
  if (haystack.includes(q)) return 30;
  return 0;
}

/** Best score across the spaced and compact spellings of both sides. */
function rate(raw: string, query: string): number {
  const words = normalise(raw).split(" ");
  const tokens = normalise(query).split(" ");
  let position = -1;
  const orderedMatch = tokens.length > 1 && tokens.every(token => {
    position = words.findIndex((word, index) => index > position && word.startsWith(token));
    return position >= 0;
  });
  return Math.max(
    rateOne(normalise(raw), normalise(query)),
    rateOne(compact(raw), compact(query)),
    orderedMatch ? 45 : 0
  );
}

/**
 * Score one entry against the query.
 *
 * Abbreviations and full forms both have to work, and in this catalogue the
 * abbreviation usually lives in `aliases` ("CAT 2025") while the full form is
 * the name ("Common Admission Test 2025"). Both are searched, and a hit on
 * either is a hit.
 */
function score(entry: SearchEntry, query: string): Ranked | null {
  if (!normalise(query)) return null;

  let best = rate(entry.name, query);
  let via: string | null = null;

  for (const alias of entry.aliases) {
    const aliasScore = rate(alias, query);
    // The bonus applies only to an alias that actually matched. Adding it
    // unconditionally would give every examination a non-zero score for every
    // query, turning a search for "ssc" into a list of everything.
    if (aliasScore > 0 && aliasScore + 5 > best) {
      best = aliasScore + 5;
      via = alias;
    }
  }

  // The conducting body is searchable but weighted down: "Reserve Bank of
  // India" should find RBI Assistant, without every IIM exam ranking on
  // "Institutes".
  const bodyScore = rate(entry.body, query) * 0.5;
  if (bodyScore > best) {
    best = bodyScore;
    via = entry.body;
  }

  if (best <= 0) return null;
  return { entry, score: best, via };
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
    if (!query.trim()) return { available: [], blocked: [] as Ranked[] };

    const rank = (rows: SearchEntry[]) =>
      rows
        .map((entry) => score(entry, query))
        .filter((row): row is Ranked => row !== null)
        .sort((a, b) => b.score - a.score || a.entry.name.localeCompare(b.entry.name));

    return { available: rank(exams).slice(0, 7), blocked: rank(unavailable).slice(0, 4) };
  }, [query, exams, unavailable]);

  // Only selectable rows take part in keyboard navigation. An unavailable
  // examination is shown, never selected — arrowing onto it and pressing
  // Enter would imply it leads somewhere (DEC-056).
  const navigable = available;
  const hasResults = available.length > 0 || blocked.length > 0;

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
      }
    } else if (event.key === "Escape") {
      setQuery("");
    }
  };

  return (
    <div className="w-full">
      <div
        className="group flex items-center gap-3 border-[3px] border-[var(--ink)] bg-[var(--paper)]
                   px-5 py-4 shadow-card transition-colors
                   focus-within:border-[var(--signal)]"
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
          placeholder="Search your exam — SSC, CAT, IBPS PO, NEET…"
          aria-label="Search for your examination"
          aria-autocomplete="list"
          aria-controls={listId}
          aria-activedescendant={available[active] ? `${listId}-${active}` : undefined}
          aria-expanded={hasResults}
          role="combobox"
          autoComplete="off"
          spellCheck={false}
          className="w-full bg-transparent text-lg text-[var(--ink)] outline-none
                     placeholder:text-muted
                     [&::-webkit-search-cancel-button]:appearance-none"
        />
        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery("");
              inputRef.current?.focus();
            }}
            className="label shrink-0 rounded px-1.5 py-1 hover:text-ink"
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
          {!hasResults && (
            <p className="px-4 py-6 text-sm text-ink-soft">
              Nothing matches <span className="font-medium text-ink">“{query}”</span>.
              We cover {exams.length} examinations so far — if yours is missing,{" "}
              try its full name or a different abbreviation.
            </p>
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
                <span className="block truncate font-medium text-ink">
                  {row.entry.name}
                </span>
                <span className="mt-0.5 block truncate text-xs text-muted">
                  {row.entry.body}
                  {row.via && (
                    <>
                      {" · also "}
                      <span className="text-ink-soft">{row.via}</span>
                    </>
                  )}
                </span>
              </span>
              <span className="spec shrink-0 text-xs text-ink-soft">
                {row.entry.prepares} file{row.entry.prepares === 1 ? "" : "s"}
              </span>
              <svg
                className="size-4 shrink-0 text-muted"
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
              <p className="label px-4 pt-3 pb-1.5">Not yet available</p>
              {blocked.map((row) => (
                <div
                  key={row.entry.name}
                  className="border-b-2 border-[var(--hairline)] px-4 py-3 last:border-b-0"
                >
                  <p className="text-sm font-medium text-ink-soft">{row.entry.name}</p>
                  <p className="mt-0.5 text-xs text-muted">
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
      <div className="euk-label flex flex-wrap gap-4 px-4 py-3 text-[10px] [&_a]:text-[var(--ink-55)] [&_a]:underline [&_a]:underline-offset-4 [&_a:hover]:text-[var(--signal-deep)]">{showBrowseLink && <Link href="/exams">Browse all {exams.length} exams ↗</Link>}{query.trim() && <Link href={`/exam-request?exam=${encodeURIComponent(query)}`}>Can’t find yours? Request it ↗</Link>}</div>
    </div>
  );
}
