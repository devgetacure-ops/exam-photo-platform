"use client";

import Image from "next/image";
import { useCallback, useRef, useState } from "react";

/**
 * A real wipe between the photograph a candidate uploaded and the file the
 * engine returned.
 *
 * Two things make it feel like handling an object rather than operating a
 * widget. The divider tracks the pointer exactly — there is no easing on drag,
 * because a partition that lags behind your finger reads as a video of a
 * slider rather than a slider. And the whole frame is the drag target, so a
 * thumb landing anywhere near the seam grabs it; only keyboard users need to
 * find the handle itself.
 *
 * Only `clip-path` and `transform` change while dragging. Both are composited,
 * so the wipe costs no layout and no repaint on the mid-range Android this is
 * built for.
 */
export function Compare({
    beforeSrc,
    afterSrc,
    width,
    height,
    beforeLabel = "AS UPLOADED",
    afterLabel = "PREPARED",
    checks,
    placeholder = false,
    alt,
}: {
    beforeSrc: string;
    afterSrc: string;
    width: number;
    height: number;
    beforeLabel?: string;
    afterLabel?: string;
    checks: { label: string; before: string; after: string }[];
    placeholder?: boolean;
    alt: string;
}) {
    const [pct, setPct] = useState(50);
    const frameRef = useRef<HTMLDivElement>(null);

    const setFromClientX = useCallback((clientX: number) => {
        const el = frameRef.current;
        if (!el) return;
        const box = el.getBoundingClientRect();
        if (box.width === 0) return;
        const next = ((clientX - box.left) / box.width) * 100;
        setPct(Math.min(100, Math.max(0, next)));
    }, []);

    const onPointerDown = useCallback(
        (e: React.PointerEvent<HTMLDivElement>) => {
            e.currentTarget.setPointerCapture(e.pointerId);
            setFromClientX(e.clientX);
        },
        [setFromClientX],
    );

    const onPointerMove = useCallback(
        (e: React.PointerEvent<HTMLDivElement>) => {
            if (!e.currentTarget.hasPointerCapture(e.pointerId)) return;
            setFromClientX(e.clientX);
        },
        [setFromClientX],
    );

    const onKeyDown = useCallback((e: React.KeyboardEvent) => {
        const step = e.shiftKey ? 10 : 2;
        const moves: Record<string, number> = {
            ArrowLeft: -step,
            ArrowRight: step,
            Home: -100,
            End: 100,
        };
        const delta = moves[e.key];
        if (delta === undefined) return;
        e.preventDefault();
        setPct((p) => Math.min(100, Math.max(0, p + delta)));
    }, []);

    return (
        <figure className="m-0">
            <div
                ref={frameRef}
                onPointerDown={onPointerDown}
                onPointerMove={onPointerMove}
                className="euk-block euk-block--signal relative select-none overflow-hidden"
                style={{ touchAction: "pan-y", cursor: "ew-resize" }}
            >
                {/* the prepared file sits underneath and is revealed */}
                <Image
                    src={afterSrc}
                    width={width}
                    height={height}
                    alt={alt}
                    priority
                    draggable={false}
                    className="block h-auto w-full"
                />

                {/* the upload is clipped back to expose it */}
                <div
                    className="absolute inset-0"
                    style={{ clipPath: `inset(0 ${100 - pct}% 0 0)` }}
                    aria-hidden="true"
                >
                    <Image
                        src={beforeSrc}
                        width={width}
                        height={height}
                        alt=""
                        priority
                        draggable={false}
                        className="block h-auto w-full"
                    />
                </div>

                {/* the partition */}
                <div
                    className="pointer-events-none absolute inset-y-0 w-[3px] bg-[var(--signal)]"
                    style={{ left: `${pct}%`, transform: "translateX(-50%)" }}
                    aria-hidden="true"
                />

                <div
                    role="slider"
                    tabIndex={0}
                    aria-label="Drag to compare the uploaded photograph with the prepared file"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={Math.round(pct)}
                    aria-valuetext={`${Math.round(pct)}% of the uploaded photograph shown`}
                    onKeyDown={onKeyDown}
                    className="absolute top-1/2 flex h-11 w-11 items-center justify-center border-[3px] border-[var(--ink)] bg-[var(--signal-deep)]"
                    style={{
                        // Clamped so the handle never hangs half-off the frame
                        // at 0 or 100, which read as a rendering fault.
                        left: `calc(${pct}% + ${(50 - pct) * 0.46}px)`,
                        transform: "translate(-50%, -50%)",
                        cursor: "ew-resize",
                    }}
                >
                    <svg
                        width="20"
                        height="14"
                        viewBox="0 0 20 14"
                        fill="none"
                        stroke="var(--signal-ink)"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        aria-hidden="true"
                    >
                        <path d="M7 2 L2 7 L7 12" />
                        <path d="M13 2 L18 7 L13 12" />
                    </svg>
                </div>

                <span className="euk-label pointer-events-none absolute left-2 top-2 bg-[var(--ink)] px-2 py-1 text-[11px] text-[var(--paper)]">
                    {beforeLabel}
                </span>
                <span className="euk-label pointer-events-none absolute right-2 top-2 bg-[var(--signal)] px-2 py-1 text-[11px] text-[var(--signal-ink)]">
                    {afterLabel}
                </span>
            </div>

            <figcaption className="pt-4">
                <ol className="flex flex-col gap-0">
                    {checks.map((c, i) => {
                        // Each item turns over as the partition passes it, so
                        // the list is read by dragging rather than by scrolling.
                        const threshold = ((i + 1) / (checks.length + 1)) * 100;
                        const done = pct >= threshold;
                        return (
                            <li
                                key={c.label}
                                className="flex items-start gap-3 border-b-2 border-[var(--hairline)] py-2 last:border-b-0"
                            >
                                <span
                                    className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center border-2 ${done ? "border-[var(--ink)] bg-[var(--signal)]" : "border-[var(--ink-40)]"}`}
                                    aria-hidden="true"
                                >
                                    {done ? (
                                        <svg width="11" height="9" viewBox="0 0 11 9" fill="none" stroke="var(--signal-ink)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M1 4.5 L4 7.5 L10 1.5" />
                                        </svg>
                                    ) : (
                                        <svg width="9" height="9" viewBox="0 0 9 9" fill="none" stroke="var(--ink-40)" strokeWidth="2" strokeLinecap="round">
                                            <path d="M1 1 L8 8 M8 1 L1 8" />
                                        </svg>
                                    )}
                                </span>
                                <span className="euk-label w-[86px] shrink-0 pt-1 text-[11px] text-[var(--ink-55)]">
                                    {c.label}
                                </span>
                                <span className="euk-figures min-w-0 flex-1 text-[13px] leading-snug [overflow-wrap:anywhere]">
                                    <span className={done ? "text-[var(--ink-40)] line-through" : "text-[var(--ink-70)]"}>
                                        {c.before}
                                    </span>
                                    {done && (
                                        <span className="font-semibold text-[var(--ink)]">
                                            {" → "}
                                            {c.after}
                                        </span>
                                    )}
                                </span>
                            </li>
                        );
                    })}
                </ol>
                <p className="pt-3 text-[13px] text-[var(--ink-55)]">
                    Drag the handle, or use the arrow keys
                </p>
                {placeholder && (
                    <p className="mt-3 border-2 border-dashed border-[var(--notyet-line)] bg-[var(--notyet-fill)] px-3 py-2 text-[13px] leading-relaxed text-[var(--ink-55)]">
                        Placeholder pair. Both files are the same image, so the
                        figures above describe no real change. Replace
                        hero-before.jpg and hero-after.jpg and this reads true.
                    </p>
                )}
            </figcaption>
        </figure>
    );
}
