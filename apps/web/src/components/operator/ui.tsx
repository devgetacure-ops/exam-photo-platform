import Link from "next/link";
import type { ReactNode } from "react";

/**
 * The operator page's small parts (DEC-108, DEC-109). Server components only:
 * nothing here ships JavaScript, so nothing here can leak the operator token.
 */

export function Tile({
    label,
    value,
    alarm,
    href,
}: {
    label: string;
    value: ReactNode;
    alarm?: boolean;
    href?: string;
}) {
    const body = (
        <>
            <span className="euk-label">{label}</span>
            <strong>{value}</strong>
        </>
    );
    return href ? (
        <Link href={href} className="euk-op-tile" data-alarm={alarm ? "true" : undefined}>
            {body}
        </Link>
    ) : (
        <div className="euk-op-tile" data-alarm={alarm ? "true" : undefined}>
            {body}
        </div>
    );
}

export function Fact({
    label,
    value,
    alarm,
}: {
    label: string;
    value: ReactNode;
    alarm?: boolean;
}) {
    return (
        <div data-alarm={alarm ? "true" : undefined}>
            <dt>{label}</dt>
            <dd>{value ?? "—"}</dd>
        </div>
    );
}

export function Failure({ what, error }: { what: string; error: string }) {
    return (
        <p className="euk-op-failure" role="alert">
            Could not load {what}: {error}
        </p>
    );
}

const STATE_LABEL: Record<string, string> = {
    "refund-due": "Refund due",
    delivered: "Delivered",
    paid: "Paid",
    unpaid: "Not paid",
    "payment-failed": "Payment failed",
    refunded: "Refunded",
    open: "Open",
    answered: "Answered",
    resolved: "Resolved",
    succeeded: "Prepared",
    processing: "Processing",
    error: "Error",
    busy: "Refused: busy",
    failed: "Failed",
};

/** A state, always in words; the colour only repeats what the word says. */
export function Badge({ state }: { state: string }) {
    return (
        <span className="euk-op-badge" data-state={state}>
            {STATE_LABEL[state] ?? state}
        </span>
    );
}

export interface Bar {
    label: string;
    value: number;
    display: string;
}

/**
 * One series of bars on one axis, with a hover label per bar and the same
 * numbers as a table beneath, so nothing depends on seeing the colour.
 */
export function Bars({
    title,
    bars,
    tone = "ink",
    everyNthLabel = 1,
}: {
    title: string;
    bars: Bar[];
    tone?: "ink" | "signal";
    everyNthLabel?: number;
}) {
    const width = 640;
    const height = 160;
    const axis = 18;
    const top = 14;
    const max = Math.max(1, ...bars.map((bar) => bar.value));
    const slot = width / Math.max(1, bars.length);
    const barWidth = Math.max(2, slot - 2);
    const peak = bars.reduce((best, bar) => (bar.value > best.value ? bar : best), bars[0]);
    return (
        <figure className="euk-op-chart">
            <figcaption>{title}</figcaption>
            <svg viewBox={`0 0 ${width} ${height + axis}`} role="img" aria-label={title} data-tone={tone}>
                <line x1="0" x2={width} y1={height} y2={height} className="euk-op-chart-base" />
                {bars.map((bar, index) => {
                    const h = bar.value ? Math.max(2, ((height - top) * bar.value) / max) : 0;
                    const x = index * slot + 1;
                    return (
                        <g key={bar.label}>
                            <rect x={index * slot} y={0} width={slot} height={height} className="euk-op-chart-hit">
                                <title>{`${bar.label}: ${bar.display}`}</title>
                            </rect>
                            {h > 0 && (
                                <path
                                    className="euk-op-chart-bar"
                                    d={roundedTop(x, height - h, barWidth, h, Math.min(4, barWidth / 2))}
                                    pointerEvents="none"
                                />
                            )}
                            {index % everyNthLabel === 0 && (
                                <text x={x + barWidth / 2} y={height + 13} textAnchor="middle" className="euk-op-chart-tick">
                                    {bar.label}
                                </text>
                            )}
                        </g>
                    );
                })}
                {peak && peak.value > 0 && (
                    <text
                        x={Math.min(width - 4, bars.indexOf(peak) * slot + slot / 2)}
                        y={Math.max(11, height - ((height - top) * peak.value) / max - 4)}
                        textAnchor="middle"
                        className="euk-op-chart-peak"
                    >
                        {peak.display}
                    </text>
                )}
            </svg>
            <details>
                <summary>As a table</summary>
                <table className="euk-op-table">
                    <tbody>
                        {bars.map((bar) => (
                            <tr key={bar.label}>
                                <th scope="row">{bar.label}</th>
                                <td>{bar.display}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </details>
        </figure>
    );
}

function roundedTop(x: number, y: number, w: number, h: number, r: number): string {
    const radius = Math.min(r, h);
    return [
        `M${x},${y + h}`,
        `V${y + radius}`,
        `Q${x},${y} ${x + radius},${y}`,
        `H${x + w - radius}`,
        `Q${x + w},${y} ${x + w},${y + radius}`,
        `V${y + h}`,
        "Z",
    ].join(" ");
}

/** A POST form to an operator action; the action checks Access and origin. */
export function ActionForm({
    action,
    back,
    children,
    className,
}: {
    action: string;
    back: string;
    children: ReactNode;
    className?: string;
}) {
    return (
        <form method="post" action={action} className={className ?? "euk-op-form"}>
            <input type="hidden" name="back" value={back} />
            {children}
        </form>
    );
}

export function NotesBlock({
    target,
    back,
    notes,
}: {
    target: string;
    back: string;
    notes: { at: string; actor: string; text: string }[];
}) {
    return (
        <section className="euk-op-section">
            <h2>Notes</h2>
            {notes.length === 0 && <p className="euk-op-quiet">None yet.</p>}
            <ul className="euk-op-plain">
                {notes.map((note, index) => (
                    <li key={index}>
                        <span className="euk-op-quiet">
                            {new Date(note.at).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })} · {note.actor}
                        </span>
                        <br />
                        <span className="euk-op-message">{note.text}</span>
                    </li>
                ))}
            </ul>
            <ActionForm action="/admin/actions/note" back={back}>
                <input type="hidden" name="target" value={target} />
                <label>
                    <span className="euk-label">Add a note</span>
                    <textarea name="text" rows={3} maxLength={4000} required />
                </label>
                <button type="submit" className="euk-op-button">
                    Save note
                </button>
            </ActionForm>
        </section>
    );
}
