"use client";

import { useEffect, type RefObject } from "react";

import { markInstallMoment } from "../../lib/install";

/**
 * The moment the files are the candidate's.
 *
 * The landing page promised "You prepare for the exam. We'll prepare the
 * files." This is where that promise is kept, so the words turn it round. An
 * admit card is drawn in, a tick writes itself across it, and ALL THE BEST is
 * stamped on it: one wish, set where the candidate's eye already is, rather
 * than confetti over the downloads they still need to take.
 *
 * Choreographed once, never looped: the title rises, the card settles, the
 * stamp lands, the tick draws, three sparks draw in a quick stagger. About a
 * second in all. Reduced motion shows the finished card with nothing moving.
 */
export function KitSuccess({
    examName,
    titleRef,
}: {
    examName: string;
    titleRef: RefObject<HTMLHeadingElement | null>;
}) {
    // The files are the candidate's: the strongest moment there is to offer
    // the site a place on the home screen.
    useEffect(() => {
        markInstallMoment();
    }, []);

    return (
        <div className="euk-done">
            <div className="euk-done-art" aria-hidden="true">
                <svg
                    viewBox="0 0 240 190"
                    className="euk-done-svg"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                >
                    <g className="euk-done-card">
                        <rect className="euk-done-paper" x="20" y="42" width="184" height="132" />
                        <path d="M20 66 H 204" />
                        <path d="M34 54 H 96" />
                        <rect x="34" y="80" width="42" height="52" />
                        <path d="M55 90 C 62 90, 65 96, 65 102 C 65 109, 60 114, 55 114 C 50 114, 45 109, 45 102 C 45 96, 48 90, 55 90 Z" />
                        <path d="M38 132 C 40 124, 47 119, 55 119 C 63 119, 70 124, 72 132" />
                        <path d="M90 88 H 180 M90 102 H 168 M90 116 H 150" />
                        <path d="M92 152 C 98 142, 104 144, 102 152 C 100 158, 110 148, 118 150 C 124 152, 128 146, 134 144" />
                    </g>
                    <path className="euk-done-tick" pathLength={1} d="M150 138 L 166 154 L 198 114" />
                    <path className="euk-done-spark euk-done-spark--1" pathLength={1} d="M216 16 V 36 M206 26 H 226" />
                    <path className="euk-done-spark euk-done-spark--2" pathLength={1} d="M14 18 V 32 M7 25 H 21" />
                    <path className="euk-done-spark euk-done-spark--3" pathLength={1} d="M226 86 V 100 M219 93 H 233" />
                </svg>
                <p className="euk-done-stamp">All the best</p>
            </div>

            <div className="euk-done-copy">
                <h2
                    id="done-title"
                    ref={titleRef}
                    tabIndex={-1}
                    className="euk-display euk-done-title"
                >
                    We’ve prepared the files.
                    <br />
                    <span className="euk-mark">Now it’s your exam.</span>
                </h2>
                <p className="euk-done-lede">
                    All the best for {examName}. The part we could do is
                    finished. The part that decides it is the preparation, and
                    that was always yours.
                </p>
            </div>
        </div>
    );
}
