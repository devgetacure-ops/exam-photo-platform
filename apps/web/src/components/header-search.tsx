"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { SearchEntry } from "../lib/types";
import { useExamPicker } from "../lib/use-exam-picker";
import { ExamResults } from "./exam-results";

/**
 * The search that lives in the bar.
 *
 * It is the search, not a door to one. Click it and type: the predictive list
 * drops straight out of the bar. An earlier version opened a panel with a
 * second field inside it, which made every candidate type in a box that was
 * not the box they clicked.
 *
 * Two jobs, one field. On the landing page and the directory the search *is*
 * the page, so this one appears only once that has scrolled off — and is out
 * of the tab order until then. On an examination page there is no search on
 * the page at all, so it is there from the start, wearing that examination's
 * name as its placeholder.
 *
 * The index is not in this page. It is fetched once, on first focus, because
 * the alternative is putting the whole catalogue into 415 documents for the
 * few candidates who search from here. Focus is early enough that it has
 * arrived by the second keystroke; if it somehow has not, the list says it is
 * loading rather than claiming nothing matches.
 */
interface Props {
    /** Placeholder on an examination page. */
    examName?: string;
    /**
     * Id of the element this replaces — the field appears only once that one
     * has scrolled out of sight. Omit and it is always there.
     */
    takesOverFrom?: string;
}

type Index = { exams: SearchEntry[]; unavailable: SearchEntry[] };

const EMPTY: SearchEntry[] = [];

export function HeaderSearch({ examName, takesOverFrom }: Props) {
    const [shown, setShown] = useState(!takesOverFrom);
    const [index, setIndex] = useState<Index | null>(null);
    const [failed, setFailed] = useState(false);
    const [dropped, setDropped] = useState(false);
    const boxRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const picker = useExamPicker(
        index?.exams ?? EMPTY,
        index?.unavailable ?? EMPTY,
        () => setDropped(false),
    );

    // Appear only once the page's own search has gone.
    useEffect(() => {
        if (!takesOverFrom) return;
        const target = document.getElementById(takesOverFrom);
        if (!target || typeof IntersectionObserver === "undefined") {
            // No anchor to watch, so the bar keeps the search rather than
            // leaving a candidate with no way to look anything up.
            const frame = requestAnimationFrame(() => setShown(true));
            return () => cancelAnimationFrame(frame);
        }
        const observer = new IntersectionObserver(
            ([entry]) => setShown(!entry.isIntersecting),
            { rootMargin: "-72px 0px 0px 0px" },
        );
        observer.observe(target);
        return () => observer.disconnect();
    }, [takesOverFrom]);

    const load = useCallback(() => {
        if (index) return;
        fetch("/search-index.json")
            .then((response) => {
                if (!response.ok) throw new Error(String(response.status));
                return response.json();
            })
            .then((data: Index) => setIndex(data))
            .catch(() => setFailed(true));
    }, [index]);

    // Clicking away puts the list down without clearing what was typed.
    useEffect(() => {
        if (!dropped) return;
        const onDown = (event: MouseEvent) => {
            if (!boxRef.current?.contains(event.target as Node)) {
                setDropped(false);
            }
        };
        document.addEventListener("mousedown", onDown);
        return () => document.removeEventListener("mousedown", onDown);
    }, [dropped]);

    // The shortcut every search field on the web has. Never while the
    // candidate is typing into something else.
    useEffect(() => {
        const onKey = (event: KeyboardEvent) => {
            if (event.key !== "/" || event.metaKey || event.ctrlKey) return;
            const el = document.activeElement;
            if (
                el instanceof HTMLInputElement ||
                el instanceof HTMLTextAreaElement ||
                (el instanceof HTMLElement && el.isContentEditable)
            ) {
                return;
            }
            event.preventDefault();
            load();
            inputRef.current?.focus();
        };
        document.addEventListener("keydown", onKey);
        return () => document.removeEventListener("keydown", onKey);
    }, [load]);

    const waiting = picker.asking && !index;
    const open = dropped && (picker.asking || waiting);

    return (
        <div
            ref={boxRef}
            className="euk-topsearch"
            data-shown={shown}
            data-open={open}
        >
            <div className="euk-topsearch-field">
                <svg
                    className="euk-topsearch-glass"
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
                    className="euk-searchfield euk-topsearch-input"
                    value={picker.query}
                    placeholder={examName ?? "Search your examination"}
                    aria-label="Search for your examination"
                    aria-autocomplete="list"
                    aria-controls={picker.listId}
                    aria-activedescendant={
                        picker.available[picker.active]
                            ? `${picker.listId}-${picker.active}`
                            : undefined
                    }
                    aria-expanded={open}
                    role="combobox"
                    autoComplete="off"
                    spellCheck={false}
                    inert={!shown ? true : undefined}
                    onMouseEnter={load}
                    onFocus={() => {
                        load();
                        setDropped(true);
                    }}
                    onChange={(event) => {
                        picker.type(event.target.value);
                        setDropped(true);
                    }}
                    onKeyDown={picker.onKeyDown}
                />
                {picker.query && (
                    <button
                        type="button"
                        className="euk-label euk-topsearch-clear"
                        aria-label="Clear search"
                        onClick={() => {
                            picker.clear();
                            inputRef.current?.focus();
                        }}
                    >
                        Clear
                    </button>
                )}
            </div>

            {open && (
                <div className="euk-topsearch-drop">
                    {waiting ? (
                        <p className="euk-topsearch-wait">
                            {failed
                                ? "The list of examinations didn’t load. Reload the page, or browse them all."
                                : "Loading examinations…"}
                        </p>
                    ) : (
                        <ExamResults picker={picker} />
                    )}
                </div>
            )}
        </div>
    );
}
