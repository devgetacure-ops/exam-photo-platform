import type { ReactNode } from "react";

/**
 * The shell for a page that exists because something didn't go to plan.
 *
 * Each one gets its own drawing and its own words, set the way the rest of the
 * site sets a headline, so an error reads as a page we meant to show rather
 * than a browser default. The drawing is the one piece of motion: it draws
 * itself once on arrival and stays still.
 */
export function StatePage({
    art,
    title,
    mark,
    lede,
    children,
}: {
    art: ReactNode;
    title: string;
    mark: string;
    lede: ReactNode;
    children?: ReactNode;
}) {
    return (
        <main className="euk euk-state" id="main-content">
            <div className="euk-wrap euk-state-grid">
                <div className="euk-state-art" aria-hidden="true">
                    {art}
                </div>
                <div className="euk-state-copy">
                    <h1 className="euk-display euk-state-title">
                        {title}
                        <br />
                        <span className="euk-mark">{mark}</span>
                    </h1>
                    <p className="euk-state-lede">{lede}</p>
                    {children}
                </div>
            </div>
        </main>
    );
}

/** A form with one page missing from the stack: the page that isn't on file. */
export function MissingPageDrawing() {
    return (
        <svg className="euk-state-svg" viewBox="0 0 220 200" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
            <path className="euk-state-stroke" pathLength={1} d="M30 40 H 130 L 150 60 V 180 H 30 Z" />
            <path className="euk-state-stroke" pathLength={1} d="M130 40 V 60 H 150" />
            <path className="euk-state-stroke" pathLength={1} d="M46 84 H 124 M46 100 H 116 M46 116 H 128 M46 132 H 104" />
            <path className="euk-state-stroke euk-state-dash" pathLength={1} d="M78 20 H 178 L 198 40 V 160 H 78 Z" />
            <path className="euk-state-stroke euk-state-accent" pathLength={1} d="M122 84 C 122 70, 146 68, 146 84 C 146 96, 134 96, 134 108 M134 124 V 125" />
        </svg>
    );
}

/** A form torn at the corner and mended: something broke, the kit didn't. */
export function TornPageDrawing() {
    return (
        <svg className="euk-state-svg" viewBox="0 0 220 200" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
            <path className="euk-state-stroke" pathLength={1} d="M40 30 H 150 L 172 52 V 110 L 150 122 L 168 140 L 150 158 V 180 H 40 Z" />
            <path className="euk-state-stroke" pathLength={1} d="M150 30 V 52 H 172" />
            <path className="euk-state-stroke" pathLength={1} d="M58 72 H 140 M58 90 H 132 M58 108 H 124" />
            <path className="euk-state-stroke euk-state-accent" pathLength={1} d="M138 128 L 178 118 M140 150 L 182 138" />
            <path className="euk-state-stroke" pathLength={1} d="M58 150 C 66 138, 74 142, 72 152 C 70 160, 82 148, 90 150" />
        </svg>
    );
}
