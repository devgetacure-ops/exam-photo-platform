import type { ReactNode } from "react";
import type { Specimen, SpecimenId } from "../../lib/specimens";

/**
 * The specimen sheet: one accepted example, then the ones that are not.
 *
 * Every specimen is the same drawn subject with one thing changed, so the eye
 * reads the difference and nothing else. Stroke only, in the page's ink, so a
 * sheet costs no image request and inverts with the theme. Two specimens use
 * fixed colours on purpose: "too dark" has to stay dark in dark mode.
 */

const HEAD =
    "M60 36 C 76 36, 84 48, 84 64 C 84 84, 73 96, 60 96 C 47 96, 36 84, 36 64 C 36 48, 44 36, 60 36 Z";
const NECK = "M52 95 V 110 M68 95 V 110";
const SHOULDERS = "M16 150 C 20 124, 38 110, 60 110 C 82 110, 100 124, 104 150";
const EYES = "M48 62 H 56 M64 62 H 72";
const NOSE = "M60 66 V 74 L 57 76";
const MOUTH = "M53 84 Q 60 88 67 84";

const SIGNATURE =
    "M14 58 C 22 30, 34 30, 30 54 C 27 72, 40 44, 50 40 C 58 37, 52 62, 60 58 C 70 52, 72 36, 80 44 C 86 50, 82 64, 92 58 C 104 50, 110 34, 118 42 C 124 48, 118 60, 130 56 C 138 53, 142 48, 150 44";

function Portrait({
    eyes = true,
    mouth = true,
    className,
    transform,
}: {
    eyes?: boolean;
    mouth?: boolean;
    className?: string;
    transform?: string;
}) {
    return (
        <g className={className} transform={transform}>
            <path d={HEAD} vectorEffect="non-scaling-stroke" />
            <path d={NECK} vectorEffect="non-scaling-stroke" />
            <path d={SHOULDERS} vectorEffect="non-scaling-stroke" />
            {eyes && <path d={EYES} vectorEffect="non-scaling-stroke" />}
            <path d={NOSE} vectorEffect="non-scaling-stroke" />
            {mouth && <path d={MOUTH} vectorEffect="non-scaling-stroke" />}
        </g>
    );
}

const Frames = () => (
    <>
        <rect x="43" y="56" width="15" height="12" />
        <rect x="62" y="56" width="15" height="12" />
        <path d="M58 61 H 62" />
    </>
);

function Paper({ width, height }: { width: number; height: number }) {
    return (
        <rect
            className="euk-spec-paper"
            x="5"
            y="7"
            width={width - 10}
            height={height - 14}
        />
    );
}

const VIEWBOX: Record<string, string> = {
    portrait: "0 0 120 150",
    signature: "0 0 160 96",
    thumb: "0 0 100 124",
    declaration: "0 0 110 140",
    document: "0 0 130 112",
};

export function familyOf(id: SpecimenId): string {
    return id.split("-")[0];
}

function art(id: SpecimenId): ReactNode {
    switch (id) {
        case "portrait-ok":
            return <Portrait />;
        case "portrait-cap":
            return (
                <>
                    <Portrait />
                    <path
                        className="euk-spec-fill"
                        d="M35 54 C 35 30, 85 30, 85 54 Z"
                    />
                    <path d="M26 54 H 94" />
                </>
            );
        case "portrait-dark-glasses":
            return (
                <>
                    <Portrait eyes={false} />
                    <rect className="euk-spec-fill" x="43" y="56" width="15" height="12" />
                    <rect className="euk-spec-fill" x="62" y="56" width="15" height="12" />
                    <path d="M58 61 H 62" />
                </>
            );
        case "portrait-spectacles":
            return (
                <>
                    <Portrait />
                    <Frames />
                </>
            );
        case "portrait-glare":
            return (
                <>
                    <Portrait eyes={false} />
                    <Frames />
                    <path
                        className="euk-spec-accent"
                        d="M45 67 L 56 57 M64 67 L 75 57"
                    />
                </>
            );
        case "portrait-mask":
            return (
                <>
                    <Portrait mouth={false} />
                    <path
                        className="euk-spec-fill-soft"
                        d="M41 71 C 50 69, 70 69, 79 71 L 77 87 C 70 94, 50 94, 43 87 Z"
                    />
                    <path d="M41 73 L 35 64 M79 73 L 85 64" />
                </>
            );
        case "portrait-shadow":
            return (
                <>
                    <Portrait />
                    <path
                        className="euk-spec-hatch"
                        d="M62 42 L 82 58 M62 52 L 84 70 M62 62 L 83 80 M62 72 L 78 86 M62 82 L 71 90"
                    />
                </>
            );
        case "portrait-side":
            return (
                <g>
                    <path d="M54 36 C 70 36, 80 48, 82 60 L 91 70 L 83 74 C 83 86, 73 96, 60 96 C 46 96, 38 84, 38 66 C 38 48, 42 36, 54 36 Z" />
                    <path d="M46 60 C 40 60, 40 72, 46 72" />
                    <path d="M70 62 H 77" />
                    <path d="M71 85 Q 75 87 79 85" />
                    <path d="M54 95 V 110 M70 95 V 110" />
                    <path d={SHOULDERS} />
                </g>
            );
        case "portrait-eyes-closed":
            return (
                <>
                    <Portrait eyes={false} />
                    <path d="M48 62 Q 52 66 56 62 M64 62 Q 68 66 72 62" />
                </>
            );
        case "portrait-far":
            return (
                <Portrait transform="translate(60 100) scale(0.42) translate(-60 -100)" />
            );
        case "portrait-clipped":
            return (
                <Portrait transform="translate(0 -40) translate(60 60) scale(1.3) translate(-60 -60)" />
            );
        case "portrait-blur":
            return (
                <>
                    <Portrait className="euk-spec-ghost" transform="translate(3 2)" />
                    <Portrait className="euk-spec-ghost" transform="translate(-2 1)" />
                    <Portrait />
                </>
            );
        case "portrait-dark":
            return (
                <>
                    <rect className="euk-spec-night" x="0" y="0" width="120" height="150" />
                    <Portrait className="euk-spec-dim" />
                </>
            );

        case "signature-ok":
            return (
                <>
                    <Paper width={160} height={96} />
                    <path d={SIGNATURE} />
                </>
            );
        case "signature-capitals":
            return (
                <>
                    <Paper width={160} height={96} />
                    <path d="M18 64 L 30 30 L 42 64 M23 51 H 37" />
                    <path d="M52 30 V 64 M52 30 H 62 C 72 30, 72 46, 62 47 H 52 M62 47 C 74 48, 74 64, 62 64 H 52" />
                    <path d="M104 36 C 96 28, 82 30, 82 47 C 82 64, 96 66, 104 58" />
                    <path d="M116 30 V 64 H 136" />
                </>
            );
        case "signature-clipped":
            return (
                <>
                    <Paper width={160} height={96} />
                    <path d={SIGNATURE} transform="translate(52 -6) scale(1.1)" />
                </>
            );
        case "signature-faint":
            return (
                <>
                    <Paper width={160} height={96} />
                    <path className="euk-spec-faint" d={SIGNATURE} />
                </>
            );

        case "thumb-ok":
        case "thumb-smudged": {
            const smudged = id === "thumb-smudged";
            const whorls = (
                <g transform="translate(50 62) scale(0.8) translate(-50 -62)">
                    <path d="M50 12 C 26 12, 14 36, 14 60 C 14 90, 30 110, 50 110 C 70 110, 86 90, 86 60 C 86 36, 74 12, 50 12" />
                    <path d="M50 25 C 32 25, 25 42, 25 60 C 25 83, 36 98, 50 98 C 64 98, 75 83, 75 60 C 75 42, 68 25, 50 25" />
                    <path d="M50 38 C 39 38, 36 50, 36 62 C 36 77, 43 87, 50 87 C 57 87, 64 77, 64 62" />
                    <path d="M50 51 C 45 51, 46 59, 46 65 C 46 72, 49 76, 53 76" />
                </g>
            );
            return (
                <>
                    <Paper width={100} height={124} />
                    {smudged && (
                        <>
                            <g className="euk-spec-ghost" transform="translate(5 4)">
                                {whorls}
                            </g>
                            <ellipse
                                className="euk-spec-fill-soft"
                                cx="60"
                                cy="72"
                                rx="24"
                                ry="18"
                            />
                        </>
                    )}
                    {whorls}
                </>
            );
        }

        case "declaration-ok":
        case "declaration-capitals":
        case "declaration-cropped": {
            const page = (
                <>
                    <path className="euk-spec-paper" d="M14 8 H 78 L 96 26 V 132 H 14 Z" />
                    <path d="M78 8 V 26 H 96" />
                </>
            );
            if (id === "declaration-capitals") {
                return (
                    <>
                        {page}
                        <text className="euk-spec-text" x="24" y="50">I HEREBY</text>
                        <text className="euk-spec-text" x="24" y="68">DECLARE THAT</text>
                        <text className="euk-spec-text" x="24" y="86">THE ABOVE IS</text>
                        <path d="M52 114 C 58 102, 64 106, 62 116 C 60 124, 70 110, 78 112" />
                    </>
                );
            }
            const writing = (
                <>
                    <path d="M26 46 C 36 42, 46 50, 56 44 C 64 40, 72 48, 82 44" />
                    <path d="M26 64 C 38 60, 50 68, 62 62 C 70 59, 78 65, 84 62" />
                    <path d="M26 82 C 34 78, 44 86, 56 80 C 64 77, 70 83, 74 80" />
                    <path d="M52 114 C 58 102, 64 106, 62 116 C 60 124, 70 110, 78 112 C 84 114, 88 108, 92 106" />
                </>
            );
            return id === "declaration-cropped" ? (
                <g transform="translate(26 22)">
                    {page}
                    {writing}
                </g>
            ) : (
                <>
                    {page}
                    {writing}
                </>
            );
        }

        case "document-ok":
        case "document-cut": {
            const certificate = (
                <>
                    <rect className="euk-spec-paper" x="8" y="8" width="114" height="96" />
                    <path d="M17 17 H 113 V 95 H 17 Z" />
                    <path d="M38 34 H 92 M30 50 H 100 M30 61 H 84" />
                    <path d="M92 78 A 12 12 0 1 0 116 78 A 12 12 0 1 0 92 78" />
                </>
            );
            return id === "document-cut" ? (
                <g transform="translate(65 56) rotate(-10) scale(1.22) translate(-65 -56)">
                    {certificate}
                </g>
            ) : (
                certificate
            );
        }
    }
}

export function Tick() {
    return (
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M4 10.5 L 8.5 15 L 16 5.5" />
        </svg>
    );
}

export function Cross() {
    return (
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round" aria-hidden="true">
            <path d="M5 5 L 15 15 M15 5 L 5 15" />
        </svg>
    );
}

export function SpecimenSheet({
    specimens,
    note,
}: {
    specimens: Specimen[];
    note: string;
}) {
    return (
        <figure className="euk-specimens">
            <ul className="euk-specimen-list">
                {specimens.map((specimen) => {
                    const family = familyOf(specimen.id);
                    return (
                        <li
                            key={specimen.id}
                            className={`euk-specimen ${specimen.ok ? "euk-specimen--ok" : "euk-specimen--no"}`}
                            data-family={family}
                        >
                            <div className="euk-specimen-art">
                                <svg
                                    viewBox={VIEWBOX[family]}
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth={2.2}
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    aria-hidden="true"
                                >
                                    {art(specimen.id)}
                                </svg>
                                <span className="euk-specimen-mark" aria-hidden="true">
                                    {specimen.ok ? <Tick /> : <Cross />}
                                </span>
                            </div>
                            <p className="euk-specimen-caption">
                                <span className="sr-only">
                                    {specimen.ok ? "Accepted: " : "Not accepted: "}
                                </span>
                                {specimen.caption}
                            </p>
                        </li>
                    );
                })}
            </ul>
            <figcaption className="euk-specimens-note">{note}</figcaption>
        </figure>
    );
}
