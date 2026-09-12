"use client";

import { useRef, useState } from "react";

/**
 * A search over the support answers, on a phone.
 *
 * The answers are already on the page, collapsed, grouped under three
 * headings; nine questions is a screen and a half of thumbing on a phone to
 * find the one that is yours. This filters them where they stand: a question
 * that does not mention what was typed is hidden, and a group left with
 * nothing in it goes too. It adds no wrapper to the page, so the desktop
 * layout is untouched, and it works on the answers' own text, so it can never
 * describe a question differently from how the page does.
 */
export function AnswerSearch({ scope }: { scope: string }) {
    const [query, setQuery] = useState("");
    const [shown, setShown] = useState<number | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const filter = (value: string) => {
        setQuery(value);
        const root = document.querySelector(scope);
        if (!root) return;
        const needle = value.trim().toLowerCase();
        let matches = 0;
        root.querySelectorAll<HTMLDetailsElement>("details.euk-answer").forEach((answer) => {
            const hit = !needle || (answer.textContent ?? "").toLowerCase().includes(needle);
            answer.hidden = !hit;
            if (hit) matches += 1;
        });
        root.querySelectorAll<HTMLElement>("section.euk-answers").forEach((group) => {
            group.hidden = !group.querySelector("details.euk-answer:not([hidden])");
        });
        setShown(needle ? matches : null);
    };

    return (
        <div className="euk-m-only euk-manswers">
            <label className="euk-mfilter">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
                    <circle cx="11" cy="11" r="7" />
                    <path d="m20.5 20.5-4.2-4.2" />
                </svg>
                <span className="sr-only">Search the answers</span>
                <input
                    ref={inputRef}
                    type="search"
                    enterKeyHint="search"
                    className="euk-searchfield"
                    value={query}
                    placeholder="Search: payment, refund, email…"
                    autoComplete="off"
                    onChange={(event) => filter(event.target.value)}
                />
            </label>
            {shown === 0 && (
                <p className="euk-manswers-none" role="status">
                    None of these answers mention &ldquo;{query.trim()}&rdquo;.{" "}
                    <a href="#write">Write to us</a>, and it stays private.
                </p>
            )}
            {shown !== null && shown > 0 && (
                <p className="sr-only" role="status">
                    {shown} answer{shown === 1 ? "" : "s"} match.
                </p>
            )}
        </div>
    );
}
