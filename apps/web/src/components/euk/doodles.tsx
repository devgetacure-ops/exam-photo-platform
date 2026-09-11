/**
 * The drawings.
 *
 * Every one of these stands for a file the product actually prepares, which is
 * the test each had to pass: a drawing that carries no information does not
 * ship. They are inline SVG in the system's ink — stroke only, round caps, one
 * signal accent each — so they cost no request, recolour with the theme, and
 * stay sharp at any size.
 *
 * Every stroke declares `pathLength={1}`. That is what lets CSS draw each one
 * on as its block is revealed with a single dash rule, regardless of how long
 * the real path is. A stroke without it would render as a dotted line.
 */
type StrokeProps = { d: string; accent?: boolean };

function S({ d, accent = false }: StrokeProps) {
    return (
        <path
            d={d}
            pathLength={1}
            className={accent ? "euk-draw-accent" : undefined}
        />
    );
}

function Drawing({
    viewBox,
    label,
    className = "",
    children,
}: {
    viewBox: string;
    label?: string;
    className?: string;
    children: React.ReactNode;
}) {
    return (
        <svg
            viewBox={viewBox}
            className={`euk-draw ${className}`}
            fill="none"
            stroke="currentColor"
            strokeWidth={2.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            role={label ? "img" : undefined}
            aria-label={label}
            aria-hidden={label ? undefined : true}
        >
            {children}
        </svg>
    );
}

export function PhotoDrawing({ className }: { className?: string }) {
    return (
        <Drawing viewBox="0 0 120 140" className={className}>
            <S d="M12 12 H108 V128 H12 Z" />
            <S d="M60 34 C 74 34, 80 46, 80 58 C 80 72, 71 82, 60 82 C 49 82, 40 72, 40 58 C 40 46, 46 34, 60 34 Z" />
            <S d="M24 128 C 28 104, 42 94, 60 94 C 78 94, 92 104, 96 128" />
            <S accent d="M4 24 V4 H24" />
            <S accent d="M96 4 H116 V24" />
            <S accent d="M4 116 V136 H24" />
            <S accent d="M116 116 V136 H96" />
        </Drawing>
    );
}

export function SignatureDrawing({ className }: { className?: string }) {
    return (
        <Drawing viewBox="0 0 160 72" className={className}>
            <S d="M14 44 C 22 16, 34 16, 30 40 C 27 58, 40 30, 50 26 C 58 23, 52 48, 60 44 C 70 38, 72 22, 80 30 C 86 36, 82 50, 92 44 C 104 36, 110 20, 118 28 C 124 34, 118 46, 130 42 C 138 39, 142 34, 150 30" />
            <S accent d="M8 60 H152" />
        </Drawing>
    );
}

export function ThumbDrawing({ className }: { className?: string }) {
    return (
        <Drawing viewBox="0 0 100 124" className={className}>
            <S d="M50 12 C 26 12, 14 36, 14 60 C 14 90, 30 110, 50 110 C 70 110, 86 90, 86 60 C 86 36, 74 12, 50 12" />
            <S d="M50 25 C 32 25, 25 42, 25 60 C 25 83, 36 98, 50 98 C 64 98, 75 83, 75 60 C 75 42, 68 25, 50 25" />
            <S d="M50 38 C 39 38, 36 50, 36 62 C 36 77, 43 87, 50 87 C 57 87, 64 77, 64 62" />
            <S accent d="M50 51 C 45 51, 46 59, 46 65 C 46 72, 49 76, 53 76" />
        </Drawing>
    );
}

export function DeclarationDrawing({ className }: { className?: string }) {
    return (
        <Drawing viewBox="0 0 110 140" className={className}>
            <S d="M14 8 H78 L96 26 V132 H14 Z" />
            <S d="M78 8 V26 H96" />
            <S d="M26 46 C 36 42, 46 50, 56 44 C 64 40, 72 48, 82 44" />
            <S d="M26 64 C 38 60, 50 68, 62 62 C 70 59, 78 65, 84 62" />
            <S d="M26 82 C 34 78, 44 86, 56 80 C 64 77, 70 83, 74 80" />
            <S accent d="M52 114 C 58 102, 64 106, 62 116 C 60 124, 70 110, 78 112 C 84 114, 88 108, 92 106" />
        </Drawing>
    );
}

export function CertificateDrawing({ className }: { className?: string }) {
    return (
        <Drawing viewBox="0 0 130 112" className={className}>
            <S d="M8 8 H122 V104 H8 Z" />
            <S d="M17 17 H113 V95 H17 Z" />
            <S d="M38 34 H92" />
            <S d="M30 50 H100" />
            <S d="M30 61 H84" />
            <S accent d="M92 78 A 12 12 0 1 0 116 78 A 12 12 0 1 0 92 78" />
            <S accent d="M99 88 L95 102 L102 97 L107 103 L109 89" />
        </Drawing>
    );
}

export function ArrowDrawing({ className }: { className?: string }) {
    return (
        <Drawing viewBox="0 0 84 32" className={className}>
            <S d="M4 20 C 22 6, 50 6, 74 15" />
            <S d="M63 6 L76 15 L64 24" />
        </Drawing>
    );
}

/** A request joining a list: two entries ticked, the new one not yet. */
export function ListDrawing({ className }: { className?: string }) {
    return (
        <Drawing viewBox="0 0 110 130" className={className}>
            <S d="M14 18 H96 V124 H14 Z" />
            <S d="M40 10 H70 V26 H40 Z" />
            <S d="M26 44 H38 V56 H26 Z" />
            <S d="M29 50 L32 53 L36 47" />
            <S d="M48 50 H84" />
            <S d="M26 68 H38 V80 H26 Z" />
            <S d="M29 74 L32 77 L36 71" />
            <S d="M48 74 H80" />
            <S accent d="M26 92 H38 V104 H26 Z" />
            <S accent d="M48 98 H78" />
        </Drawing>
    );
}

/** An examination's published notice, being read for its upload rules. */
export function NoticeDrawing({ className }: { className?: string }) {
    return (
        <Drawing viewBox="0 0 112 128" className={className}>
            <S d="M10 8 H74 L92 26 V122 H10 Z" />
            <S d="M74 8 V26 H92" />
            <S d="M22 42 H78" />
            <S d="M22 56 H70" />
            <S d="M22 70 H52" />
            <S accent d="M58 88 A 18 18 0 1 0 94 88 A 18 18 0 1 0 58 88" />
            <S accent d="M89 101 L106 118" />
        </Drawing>
    );
}

/** The one email a request earns. */
export function EnvelopeDrawing({ className }: { className?: string }) {
    return (
        <Drawing viewBox="0 0 130 96" className={className}>
            <S d="M8 14 H122 V88 H8 Z" />
            <S d="M8 14 L65 56 L122 14" />
            <S d="M8 88 L50 46" />
            <S d="M122 88 L80 46" />
            <S accent d="M58 56 A 7 7 0 1 0 72 56 A 7 7 0 1 0 58 56" />
        </Drawing>
    );
}

/** A signature that writes itself on the footer's declaration line. */
export function SignatureStroke({ className }: { className?: string }) {
    return (
        <Drawing viewBox="0 0 240 70" className={`euk-sign ${className ?? ""}`}>
            <S d="M10 52 C 18 20, 30 14, 30 34 C 30 56, 20 58, 26 44 C 34 26, 46 22, 52 36 C 56 46, 50 54, 60 48 C 72 40, 76 20, 84 26 C 92 32, 84 50, 96 46 C 110 40, 118 18, 128 24 C 136 30, 126 48, 140 46 C 152 44, 156 30, 166 32 C 178 34, 170 50, 186 48 C 200 46, 210 36, 230 34" />
        </Drawing>
    );
}
