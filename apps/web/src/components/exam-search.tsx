"use client";

import { useRef } from "react";
import Link from "next/link";
import type { SearchEntry } from "../lib/types";
import { useExamPicker } from "../lib/use-exam-picker";
import { ExamResults } from "./exam-results";

/**
 * The picker, as the page carries it. A candidate arrives knowing one thing —
 * the name of their examination — so search is the whole interaction: no
 * categories, no browse tree, no filters.
 *
 * The frame around the field carries focus itself. The site's focus ring would
 * draw a second rectangle inside this one, which is a box in a box, so the
 * field opts out of it by name in system.css — a Tailwind utility cannot do it,
 * because unlayered CSS beats layered utilities whatever the specificity says.
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
    const picker = useExamPicker(exams, unavailable);
    const inputRef = useRef<HTMLInputElement>(null);

    return (
        <div className="euk-picker">
            <div className="euk-picker-field">
                <svg
                    className="euk-picker-glass"
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
                    className="euk-searchfield euk-picker-input"
                    value={picker.query}
                    onChange={(event) => picker.type(event.target.value)}
                    onKeyDown={picker.onKeyDown}
                    autoFocus={autoFocus}
                    placeholder="Search your exam: SSC, CAT, IBPS PO, NEET…"
                    aria-label="Search for your examination"
                    aria-autocomplete="list"
                    aria-controls={picker.listId}
                    aria-activedescendant={
                        picker.available[picker.active]
                            ? `${picker.listId}-${picker.active}`
                            : undefined
                    }
                    aria-expanded={picker.hasResults}
                    role="combobox"
                    autoComplete="off"
                    spellCheck={false}
                />
                {picker.query && (
                    <button
                        type="button"
                        onClick={() => {
                            picker.clear();
                            inputRef.current?.focus();
                        }}
                        className="euk-label euk-picker-clear"
                        aria-label="Clear search"
                    >
                        Clear
                    </button>
                )}
            </div>

            {picker.asking && (
                <ExamResults picker={picker} className="euk-results--page" />
            )}

            <div className="euk-picker-foot euk-label">
                {showBrowseLink && (
                    <Link href="/exams">Browse all {exams.length} exams ↗</Link>
                )}
                {picker.asking && picker.hasResults && (
                    <Link href={picker.requestHref}>
                        Not the one? Ask us to add it ↗
                    </Link>
                )}
            </div>
        </div>
    );
}
