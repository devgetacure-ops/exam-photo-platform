"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import type { SearchEntry } from "../../lib/types";
import { useExamPicker } from "../../lib/use-exam-picker";
import { readRecent, rememberExam, type RecentExam } from "../../lib/recent-exams";
import { TOP_EXAMS } from "../../lib/top-exams";
import { ExamResults } from "../exam-results";

/**
 * Search, on a phone, is a screen of its own.
 *
 * A dropdown squeezed under a hero loses half of itself to the keyboard the
 * moment the field takes focus. Here the field sits at the top of an empty
 * screen, the results fill everything above the keyboard, and before anything
 * is typed the screen offers what a thumb can use without typing at all: the
 * examinations this browser opened before, and the short forms most people
 * come for.
 *
 * Two things about how it opens are load-bearing:
 *
 * - It opens from inside the tap's own handler (`openPhoneSearch`), not from
 *   an effect after a render. iOS raises the keyboard only for a focus that
 *   happens during the user's gesture; one frame later the field is focused
 *   and the keyboard stays down.
 * - Opening pushes a history entry, so Android's back button closes the
 *   search instead of leaving the page. Choosing an examination *replaces*
 *   that entry rather than pushing past it, so back from the examination
 *   lands on the page the candidate searched from, not on a search that has
 *   already closed.
 */

export const PHONE_SEARCH_ID = "euk-msearch";
const OPEN_EVENT = "euk-msearch-open";

type Index = { exams: SearchEntry[]; unavailable: SearchEntry[] };

const EMPTY: SearchEntry[] = [];

function isSearchEntry(state: unknown): boolean {
    return Boolean((state as { eukSearch?: boolean } | null)?.eukSearch);
}

/** Call from a click handler, never from an effect. */
export function openPhoneSearch(): void {
    const el = document.getElementById(PHONE_SEARCH_ID) as HTMLDialogElement | null;
    if (!el || el.hasAttribute("open")) return;
    // iOS 15.0–15.3 shipped <dialog> without its modal methods; there it opens
    // as a plain element, which still covers the screen.
    if (typeof el.showModal === "function") el.showModal();
    else el.setAttribute("open", "");
    el.querySelector<HTMLInputElement>("input")?.focus();
    window.history.pushState({ eukSearch: true }, "");
    el.dispatchEvent(new Event(OPEN_EVENT));
}

export function PhoneSearch() {
    const ref = useRef<HTMLDialogElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const router = useRouter();
    const [index, setIndex] = useState<Index | null>(null);
    const [failed, setFailed] = useState(false);
    const [recent, setRecent] = useState<RecentExam[]>([]);

    const shut = useCallback(() => {
        const el = ref.current;
        if (!el) return;
        if (el.open && typeof el.close === "function") el.close();
        el.removeAttribute("open");
    }, []);

    /** Close the way the back button would, so history stays in step. */
    const dismiss = useCallback(() => {
        if (isSearchEntry(window.history.state)) window.history.back();
        else shut();
    }, [shut]);

    const picker = useExamPicker(index?.exams ?? EMPTY, index?.unavailable ?? EMPTY, shut, {
        onPick: (entry) => setRecent(rememberExam({ id: entry.id, name: entry.name })),
        replace: true,
    });

    useEffect(() => {
        const onPop = (event: PopStateEvent) => {
            if (!isSearchEntry(event.state)) shut();
        };
        window.addEventListener("popstate", onPop);
        return () => window.removeEventListener("popstate", onPop);
    }, [shut]);

    useEffect(() => {
        const el = ref.current;
        if (!el) return;
        const onOpen = () => {
            setRecent(readRecent());
            if (index) return;
            setFailed(false);
            fetch("/search-index.json")
                .then((response) => {
                    if (!response.ok) throw new Error(String(response.status));
                    return response.json();
                })
                .then((data: Index) => setIndex(data))
                .catch(() => setFailed(true));
        };
        el.addEventListener(OPEN_EVENT, onOpen);
        return () => el.removeEventListener(OPEN_EVENT, onOpen);
    }, [index]);

    /** A link that leaves the search in place of its history entry. */
    const leaveTo = (href: string) => (event: React.MouseEvent<HTMLAnchorElement>) => {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return;
        event.preventDefault();
        shut();
        router.replace(href);
    };

    const known = (id: string) => !index || index.exams.some((exam) => exam.id === id);
    const recentShown = recent.filter((row) => known(row.id));
    const shortcuts = index
        ? TOP_EXAMS.filter((pick) => index.exams.some((exam) => exam.id === pick.id))
        : [];
    const waiting = picker.asking && !index;

    return (
        <dialog
            ref={ref}
            id={PHONE_SEARCH_ID}
            className="euk euk-msearch"
            aria-label="Search for your examination"
            onCancel={(event) => {
                event.preventDefault();
                dismiss();
            }}
        >
            <div className="euk-msearch-head">
                <button
                    type="button"
                    className="euk-msearch-back"
                    aria-label="Close search"
                    onClick={dismiss}
                >
                    <svg width="11" height="18" viewBox="0 0 11 18" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <path d="M9 1 L2 9 L9 17" />
                    </svg>
                </button>
                <div className="euk-msearch-field">
                    <input
                        ref={inputRef}
                        type="search"
                        enterKeyHint="search"
                        className="euk-searchfield euk-msearch-input"
                        value={picker.query}
                        placeholder="SSC CGL, NEET UG, IBPS PO…"
                        aria-label="Search for your examination"
                        role="combobox"
                        aria-autocomplete="list"
                        aria-controls={picker.listId}
                        aria-expanded={picker.asking && !waiting}
                        aria-activedescendant={
                            picker.available[picker.active]
                                ? `${picker.listId}-${picker.active}`
                                : undefined
                        }
                        autoComplete="off"
                        spellCheck={false}
                        onChange={(event) => picker.type(event.target.value)}
                        onKeyDown={(event) => {
                            if (event.key === "Escape") {
                                event.preventDefault();
                                dismiss();
                                return;
                            }
                            picker.onKeyDown(event);
                        }}
                    />
                    {picker.query && (
                        <button
                            type="button"
                            className="euk-msearch-clear"
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
            </div>

            <div className="euk-msearch-body">
                {picker.asking ? (
                    waiting ? (
                        <p className="euk-msearch-wait">
                            {failed
                                ? "The list of examinations didn’t load. Check your connection and try again."
                                : "Loading examinations…"}
                        </p>
                    ) : (
                        <ExamResults picker={picker} className="euk-msearch-results" />
                    )
                ) : (
                    <>
                        {recentShown.length > 0 && (
                            <section aria-labelledby="msearch-recent">
                                <h2 id="msearch-recent" className="euk-msearch-label">
                                    Opened before
                                </h2>
                                <ul className="euk-msearch-recent">
                                    {recentShown.map((row) => (
                                        <li key={row.id}>
                                            <a href={`/exam/${row.id}`} onClick={leaveTo(`/exam/${row.id}`)}>
                                                {row.name}
                                            </a>
                                        </li>
                                    ))}
                                </ul>
                            </section>
                        )}

                        {shortcuts.length > 0 && (
                            <section aria-labelledby="msearch-short">
                                <h2 id="msearch-short" className="euk-msearch-label">
                                    Straight to one of these
                                </h2>
                                <ul className="euk-msearch-chips">
                                    {shortcuts.map((pick) => (
                                        <li key={pick.id}>
                                            <a href={`/exam/${pick.id}`} onClick={leaveTo(`/exam/${pick.id}`)}>
                                                {pick.label}
                                            </a>
                                        </li>
                                    ))}
                                </ul>
                            </section>
                        )}

                        {failed && (
                            <p className="euk-msearch-wait">
                                The list of examinations didn&rsquo;t load. Check your
                                connection, or browse them all.
                            </p>
                        )}
                    </>
                )}

                <div className="euk-msearch-foot">
                    <a
                        href={picker.asking ? picker.requestHref : "/exam-request"}
                        onClick={leaveTo(picker.asking ? picker.requestHref : "/exam-request")}
                    >
                        Not on the list? Tell us which one
                    </a>
                    {/* A plain anchor on purpose, like the one above: leaveTo
                        closes the dialog before it navigates. The lint rule
                        began to notice this one once /exams gained pages
                        beneath it (DEC-096). */}
                    {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
                    <a href="/exams" onClick={leaveTo("/exams")}>
                        Browse every examination, A to Z
                    </a>
                </div>
            </div>
        </dialog>
    );
}
