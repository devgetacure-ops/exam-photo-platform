"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { SearchEntry } from "../lib/types";
import { ExamSearch } from "./exam-search";

/**
 * The search that lives in the header.
 *
 * Two jobs, one control. On the landing page the search *is* the page, so the
 * header stays out of the way until that one scrolls off — then this takes its
 * place, moving up into the bar rather than appearing from nowhere. On an
 * examination page there is no search on the page at all, so it is simply
 * there, wearing the examination's name and sized to it.
 *
 * The index is not in this page. It is fetched once, the first time somebody
 * opens the panel, because the alternative is putting the whole catalogue into
 * 415 documents for the few candidates who search from here.
 */
interface Props {
    /** Shown in the closed control on an examination page. */
    examName?: string;
    /**
     * Id of the element this replaces — the control appears only once that
     * one has scrolled out of sight. Omit and it is always there.
     */
    takesOverFrom?: string;
}

type Index = { exams: SearchEntry[]; unavailable: SearchEntry[] };

export function HeaderSearch({ examName, takesOverFrom }: Props) {
    const [shown, setShown] = useState(!takesOverFrom);
    const [open, setOpen] = useState(false);
    const [index, setIndex] = useState<Index | null>(null);
    const [failed, setFailed] = useState(false);
    const panelRef = useRef<HTMLDivElement>(null);
    const buttonRef = useRef<HTMLButtonElement>(null);

    // Appear only once the page's own search has gone.
    useEffect(() => {
        if (!takesOverFrom) return;
        const target = document.getElementById(takesOverFrom);
        if (!target || typeof IntersectionObserver === "undefined") {
            // No anchor to watch, so the header keeps the search rather than
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

    const show = useCallback(() => {
        load();
        setOpen(true);
    }, [load]);

    const close = useCallback(() => {
        setOpen(false);
        buttonRef.current?.focus();
    }, []);

    useEffect(() => {
        if (!open) return;
        const onKey = (event: KeyboardEvent) => {
            if (event.key === "Escape") close();
        };
        const onDown = (event: MouseEvent) => {
            const target = event.target as Node;
            if (
                !panelRef.current?.contains(target) &&
                !buttonRef.current?.contains(target)
            ) {
                setOpen(false);
            }
        };
        document.addEventListener("keydown", onKey);
        document.addEventListener("mousedown", onDown);
        return () => {
            document.removeEventListener("keydown", onKey);
            document.removeEventListener("mousedown", onDown);
        };
    }, [open, close]);

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
            show();
        };
        document.addEventListener("keydown", onKey);
        return () => document.removeEventListener("keydown", onKey);
    }, [show]);

    return (
        <div className="euk-topsearch" data-shown={shown} data-open={open}>
            <button
                ref={buttonRef}
                type="button"
                className="euk-topsearch-open"
                onClick={show}
                onMouseEnter={load}
                aria-expanded={open}
                aria-haspopup="dialog"
                inert={!shown ? true : undefined}
            >
                <svg
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
                <span className="euk-topsearch-label">
                    {examName ?? "Search your examination"}
                </span>
                <kbd className="euk-topsearch-key" aria-hidden="true">
                    /
                </kbd>
            </button>

            {open && (
                <div
                    ref={panelRef}
                    className="euk-topsearch-panel"
                    role="dialog"
                    aria-label="Search for your examination"
                >
                    <div
                        className="euk-wrap euk-topsearch-panel-inner"
                        /* Choosing a result navigates; the panel has done its
                           job and should not still be over the page that
                           arrives. Closing on the choice itself beats watching
                           the route for a change we already know about. */
                        onClickCapture={(event) => {
                            const el = event.target as HTMLElement;
                            if (el.closest('a,[role="option"]')) setOpen(false);
                        }}
                    >
                        {index ? (
                            <ExamSearch
                                exams={index.exams}
                                unavailable={index.unavailable}
                                autoFocus
                            />
                        ) : (
                            <p className="euk-topsearch-wait">
                                {failed
                                    ? "The list of examinations didn’t load. Reload the page, or browse them all."
                                    : "Loading examinations…"}
                            </p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
