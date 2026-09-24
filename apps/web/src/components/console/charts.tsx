"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

/**
 * The console's charts (DEC-113): one series each, one axis, a hover label on
 * every bar, and the peak drawn in the brand colour with the rest softer.
 * Colours come from the theme's tokens, so light and dark both hold.
 */

export interface Point {
    label: string;
    value: number;
    display: string;
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { payload: Point }[] }) {
    if (!active || !payload?.length) return null;
    const point = payload[0].payload;
    return (
        <div className="rounded-lg border border-[var(--op-border)] bg-[var(--op-card)] px-3 py-2 text-xs shadow-[var(--op-shadow-lg)]">
            <div className="font-semibold">{point.label}</div>
            <div className="text-[var(--op-muted)]">{point.display}</div>
        </div>
    );
}

export function BarSeries({
    points,
    height = 240,
    tickEvery,
    tickPrefix = "",
    highlightPeak = true,
    ariaLabel,
}: {
    points: Point[];
    height?: number;
    tickEvery?: number;
    /** Shown before each axis value, e.g. "₹". Text, because a function cannot come from the server. */
    tickPrefix?: string;
    highlightPeak?: boolean;
    ariaLabel: string;
}) {
    const peak = points.reduce((best, point, index) => (point.value > (points[best]?.value ?? -1) ? index : best), 0);
    const interval = tickEvery ?? Math.max(0, Math.ceil(points.length / 8) - 1);
    return (
        <div role="img" aria-label={ariaLabel} style={{ width: "100%", height }}>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={points} margin={{ top: 8, right: 4, left: -12, bottom: 0 }} barCategoryGap="18%">
                    <CartesianGrid vertical={false} strokeDasharray="3 3" />
                    <XAxis dataKey="label" tickLine={false} axisLine={false} interval={interval} tickMargin={8} />
                    <YAxis tickLine={false} axisLine={false} width={48} allowDecimals={false} tickFormatter={(value: number) => `${tickPrefix}${value}`} />
                    <Tooltip cursor={{ fill: "var(--op-hover)" }} content={<ChartTooltip />} />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={36}>
                        {points.map((point, index) => (
                            <Cell
                                key={point.label + index}
                                fill={highlightPeak && index === peak && point.value > 0 ? "var(--op-chart-1)" : highlightPeak ? "var(--op-chart-2)" : "var(--op-chart-1)"}
                            />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}

/** Horizontal bars for a funnel or a ranking: label left, value right. */
export function RankBars({ rows }: { rows: { label: string; value: number; display: string; tone?: "accent" | "muted" }[] }) {
    const max = Math.max(1, ...rows.map((row) => row.value));
    return (
        <ul className="m-0 flex list-none flex-col gap-2 p-0">
            {rows.map((row) => (
                <li key={row.label} className="relative overflow-hidden rounded-lg border border-[var(--op-border)] px-3 py-2.5">
                    <span
                        aria-hidden="true"
                        className="absolute inset-y-0 left-0"
                        style={{ width: `${Math.max(2, (row.value / max) * 100)}%`, background: row.tone === "muted" ? "var(--op-muted-bg)" : "var(--op-accent-soft)" }}
                    />
                    <span className="relative flex items-center gap-3 text-sm">
                        <span className="flex-1 font-medium">{row.label}</span>
                        <span className="op-num text-[var(--op-muted)]">{row.display}</span>
                    </span>
                </li>
            ))}
        </ul>
    );
}
