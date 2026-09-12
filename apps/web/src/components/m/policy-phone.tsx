"use client";

import Link from "next/link";
import { useState } from "react";

/**
 * A policy, on a phone.
 *
 * A candidate opens a policy with one worry — what happens to my photograph,
 * will I get my money back — and a wall of legal text on a phone is read by
 * nobody. So the sections are collapsed to their headings, which on a phone
 * is the table of contents, and a search opens every section that mentions
 * what was typed. The text is the same text as the desktop page, passed in,
 * never rewritten here.
 */
export function PhonePolicy({ sections }: { sections: { title: string; text: string }[] }) {
    const [query, setQuery] = useState("");
    const needle = query.trim().toLowerCase();
    const shown = sections.filter(
        (section) => !needle || `${section.title} ${section.text}`.toLowerCase().includes(needle),
    );

    return (
        <div className="euk-m-only euk-mpolicy">
            <label className="euk-mfilter">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
                    <circle cx="11" cy="11" r="7" />
                    <path d="m20.5 20.5-4.2-4.2" />
                </svg>
                <span className="sr-only">Search this policy</span>
                <input
                    type="search"
                    enterKeyHint="search"
                    className="euk-searchfield"
                    value={query}
                    placeholder="Search this policy"
                    autoComplete="off"
                    onChange={(event) => setQuery(event.target.value)}
                />
            </label>

            {shown.length === 0 ? (
                <p className="euk-mpolicy-none" role="status">
                    Nothing in this policy mentions &ldquo;{query.trim()}&rdquo;.{" "}
                    <Link href="/support">Ask us</Link>, and it stays private.
                </p>
            ) : (
                <div className="euk-mpolicy-list">
                    {shown.map((section) => (
                        <details
                            key={section.title}
                            className="euk-mpolicy-item"
                            open={needle ? true : undefined}
                        >
                            <summary>{section.title}</summary>
                            <p>{section.text}</p>
                        </details>
                    ))}
                </div>
            )}
        </div>
    );
}
