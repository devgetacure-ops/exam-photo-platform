/**
 * The four refusals, drawn.
 *
 * Each principle on the landing page is a thing the product will not do, and a
 * paragraph is a weak way to say that. So each one carries a small drawing
 * that performs its own refusal: a retouching wand passes over a face and the
 * face is unchanged; a missing figure fills with `est.` instead of a number;
 * an upload closes itself rather than pretend; a file is swept off the sheet.
 *
 * They play once as the block is revealed and again on hover or keyboard
 * focus. Everything that moves is a transform or an opacity, and the whole set
 * holds still under `prefers-reduced-motion` — the drawings still read at rest,
 * which is the test each one had to pass before it was allowed to move.
 */
type MarkProps = { className?: string };

function Mark({
    children,
    className = "",
    viewBox = "0 0 132 84",
}: {
    children: React.ReactNode;
    className?: string;
    viewBox?: string;
}) {
    return (
        <svg
            viewBox={viewBox}
            className={`euk-draw euk-vow ${className}`}
            fill="none"
            stroke="currentColor"
            strokeWidth={2.4}
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            {children}
        </svg>
    );
}

function Face({ x }: { x: number }) {
    return (
        <g transform={`translate(${x} 0)`}>
            <path d="M0 6 H44 V72 H0 Z" pathLength={1} />
            <path
                d="M22 20 C 31 20, 35 27, 35 34 C 35 43, 29 49, 22 49 C 15 49, 9 43, 9 34 C 9 27, 13 20, 22 20 Z"
                pathLength={1}
            />
            <path d="M6 72 C 9 60, 15 55, 22 55 C 29 55, 35 60, 38 72" pathLength={1} />
        </g>
    );
}

/** It never changes your face: the wand passes, the two stay identical. */
export function UntouchedMark({ className }: MarkProps) {
    return (
        <Mark className={className} viewBox="0 0 152 84">
            <Face x={4} />
            <Face x={88} />
            <g className="euk-vow-eq">
                <path d="M60 34 H76" pathLength={1} />
                <path d="M60 44 H76" pathLength={1} />
            </g>
            <g className="euk-vow-wand">
                <path
                    className="euk-draw-accent"
                    d="M141 50 L150 62"
                    pathLength={1}
                />
                <path
                    className="euk-draw-accent"
                    d="M136 44 L141 50 L135 54 L131 47 Z"
                    pathLength={1}
                />
            </g>
        </Mark>
    );
}

/** It never guesses a rule: the blank takes a tag, never a number. */
export function EstimateMark({ className }: MarkProps) {
    return (
        <Mark className={className}>
            <path d="M8 10 H124" pathLength={1} />
            <path d="M8 26 H78" pathLength={1} />
            <path d="M8 42 H54" pathLength={1} />
            {/* the figure the examination never published */}
            <path d="M8 54 H76 V78 H8 Z" pathLength={1} />
            <g className="euk-vow-tag">
                <path
                    className="euk-draw-accent"
                    d="M16 59 H68 V73 H16 Z"
                    pathLength={1}
                />
                <path className="euk-draw-accent" d="M26 66 H58" pathLength={1} />
            </g>
        </Mark>
    );
}

/** It never pretends: the tray shuts rather than take a file it can't use. */
export function NoPretenceMark({ className }: MarkProps) {
    return (
        <Mark className={className}>
            <path d="M18 52 V74 H114 V52" pathLength={1} />
            <g className="euk-vow-arrow">
                <path d="M66 8 V44" pathLength={1} />
                <path d="M54 32 L66 44 L78 32" pathLength={1} />
            </g>
            <path
                className="euk-vow-shut euk-draw-accent"
                d="M18 52 H114"
                pathLength={1}
            />
        </Mark>
    );
}

/** It forgets you: the sheet is swept, and what was on it is gone. */
export function ForgetsMark({ className }: MarkProps) {
    return (
        <Mark className={className}>
            <path d="M16 8 H92 L116 30 V76 H16 Z" pathLength={1} />
            <path d="M92 8 V30 H116" pathLength={1} />
            <g className="euk-vow-lines">
                <path d="M30 44 H100" pathLength={1} />
                <path d="M30 56 H100" pathLength={1} />
                <path d="M30 66 H74" pathLength={1} />
            </g>
            <path
                className="euk-vow-sweep euk-draw-accent"
                d="M8 36 V80"
                pathLength={1}
            />
        </Mark>
    );
}
