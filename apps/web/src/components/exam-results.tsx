"use client";

import Link from "next/link";
import type { ExamPicker } from "../lib/use-exam-picker";

/**
 * What the picker found, drawn once for both places it is shown.
 *
 * The page's search puts this under a large framed field; the top bar hangs it
 * from the bar as a dropdown. Same rows, same rules, same wording — the only
 * difference is the box around it.
 */
export function ExamResults({
    picker,
    className = "",
}: {
    picker: ExamPicker;
    className?: string;
}) {
    const {
        available,
        blocked,
        hasResults,
        active,
        setActive,
        go,
        listId,
        query,
        requestHref,
    } = picker;

    return (
        <div
            id={listId}
            role="listbox"
            aria-label="Matching examinations"
            className={`euk-results ${className}`}
        >
            {/*
              An empty result is where a candidate decides we do not have their
              examination, so it hands them the next step rather than a shrug.
            */}
            {!hasResults && (
                <div className="euk-results-none">
                    <p>
                        Nothing matches{" "}
                        <span className="euk-results-said">
                            &ldquo;{query.trim()}&rdquo;
                        </span>
                        . Try its full name or its short form. If it still
                        isn&rsquo;t here, we don&rsquo;t prepare it yet.
                    </p>
                    <Link href={requestHref} className="euk-link">
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
                    className="euk-results-row"
                    data-active={index === active}
                >
                    <span className="euk-results-name">
                        <span>{row.entry.name}</span>
                        <span className="euk-results-body">
                            {row.entry.body}
                            {row.via && (
                                <>
                                    {" · also "}
                                    <span className="euk-results-via">
                                        {row.via}
                                    </span>
                                </>
                            )}
                        </span>
                    </span>
                    <span className="euk-results-count">
                        {row.entry.prepares} file
                        {row.entry.prepares === 1 ? "" : "s"}
                    </span>
                    <svg
                        className="euk-results-go"
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
                <div className="euk-results-blocked">
                    <p className="euk-label">Not yet available</p>
                    {blocked.map((row) => (
                        <div key={row.entry.name}>
                            <p className="euk-results-blocked-name">
                                {row.entry.name}
                            </p>
                            <p className="euk-results-blocked-why">
                                {row.entry.unavailable?.reason ===
                                "live capture only"
                                    ? "The portal photographs you directly, so there is no photo for us to prepare."
                                    : "We have not confirmed this exam's published specification yet."}
                                {(row.entry.unavailable?.deliverables ?? 0) >
                                    0 && (
                                    <>
                                        {" "}
                                        Its other{" "}
                                        {row.entry.unavailable?.deliverables}{" "}
                                        upload
                                        {row.entry.unavailable?.deliverables ===
                                        1
                                            ? ""
                                            : "s"}{" "}
                                        are on our list.
                                    </>
                                )}
                            </p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
