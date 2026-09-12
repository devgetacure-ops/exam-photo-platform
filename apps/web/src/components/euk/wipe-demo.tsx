"use client";

import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";

/**
 * The before-and-after band: a photograph and a signature, side by side.
 *
 * It drags itself. A candidate who never touches it still sees what the
 * product does, and one who does touch it takes the handle mid-sweep — the
 * first drag stops the motion everywhere and the control reads Play.
 *
 * The sweep writes a CSS custom property on the frame rather than React state,
 * so a 60fps loop re-renders nothing; the only state that changes during a
 * sweep is how many checks have been passed, which moves a handful of times.
 * Motion stops when the band scrolls out of view, and never starts at all
 * under prefers-reduced-motion.
 *
 * The examples are representational: generated photographs and signatures,
 * not files this site prepared and not any candidate's. The band says so.
 */

export interface WipePair {
    id: string;
    before: string;
    after: string;
    alt: string;
}

export interface WipeCheck {
    label: string;
    before: string;
    after: string;
}

interface SetProps {
    title: string;
    pairs: WipePair[];
    checks: WipeCheck[];
    width: number;
    height: number;
    running: boolean;
    /** Where this frame's handle rests, so the two never move in lockstep. */
    start: number;
    onTakeover: () => void;
}

/** A full sweep, out and back. Slow enough to read the checks as they turn. */
const PERIOD_MS = 8200;
const LOW = 4;
const HIGH = 96;

function WipeSet({
    title,
    pairs,
    checks,
    width,
    height,
    running,
    start,
    onTakeover,
}: SetProps) {
    const [index, setIndex] = useState(0);
    const [previous, setPrevious] = useState<number | null>(null);
    const [pinned, setPinned] = useState(false);
    const [done, setDone] = useState(0);

    const frameRef = useRef<HTMLDivElement>(null);
    const sliderRef = useRef<HTMLDivElement>(null);
    const pctRef = useRef(start);
    const doneRef = useRef(0);
    const indexRef = useRef(0);

    useEffect(() => {
        indexRef.current = index;
    }, [index]);

    const apply = useCallback(
        (next: number) => {
            const pct = Math.min(100, Math.max(0, next));
            pctRef.current = pct;
            frameRef.current?.style.setProperty("--wipe", pct.toFixed(2));
            sliderRef.current?.setAttribute("aria-valuenow", String(Math.round(pct)));
            const passed = checks.filter(
                (_, i) => pct >= ((i + 1) / (checks.length + 1)) * 100,
            ).length;
            if (passed !== doneRef.current) {
                doneRef.current = passed;
                setDone(passed);
            }
        },
        [checks],
    );

    useEffect(() => {
        apply(pctRef.current);
    }, [apply]);

    useEffect(() => {
        if (!running) return;
        let frame = 0;
        let started = false;
        let origin = 0;
        let lastTriangle = 1;
        const tick = (now: number) => {
            if (!started) {
                // Pick up the sweep where the handle already rests, so
                // starting it never throws the partition across the frame.
                const norm = Math.min(
                    1,
                    Math.max(0, (pctRef.current - LOW) / (HIGH - LOW)),
                );
                const from = Math.acos(1 - 2 * norm) / Math.PI;
                origin = now - (from / 2) * PERIOD_MS;
                lastTriangle = from;
                started = true;
            }
            const t = ((now - origin) / PERIOD_MS) % 1;
            // Out and back, eased at both ends so it never snaps around.
            const triangle = t < 0.5 ? t * 2 : (1 - t) * 2;
            const eased = 0.5 - 0.5 * Math.cos(Math.PI * triangle);
            apply(LOW + eased * (HIGH - LOW));
            // Change example at the far end of the sweep, where the prepared
            // file fills the frame and the swap reads as one picture becoming
            // another rather than as a jump.
            if (triangle < 0.02 && lastTriangle >= 0.02 && !pinned && pairs.length > 1) {
                setPrevious(indexRef.current);
                setIndex((i) => (i + 1) % pairs.length);
            }
            lastTriangle = triangle;
            frame = requestAnimationFrame(tick);
        };
        frame = requestAnimationFrame(tick);
        return () => cancelAnimationFrame(frame);
    }, [running, pinned, pairs.length, apply]);

    // Clear the outgoing layer once its fade has run.
    useEffect(() => {
        if (previous === null) return;
        const timer = setTimeout(() => setPrevious(null), 360);
        return () => clearTimeout(timer);
    }, [previous]);

    // Fetch the next pair before it is needed, so a swap never shows a gap.
    useEffect(() => {
        const next = pairs[(index + 1) % pairs.length];
        if (!next || typeof window === "undefined") return;
        for (const src of [next.before, next.after]) {
            const image = new window.Image();
            image.src = src;
        }
    }, [index, pairs]);

    const fromClientX = useCallback(
        (clientX: number) => {
            const el = frameRef.current;
            if (!el) return;
            const box = el.getBoundingClientRect();
            if (box.width === 0) return;
            apply(((clientX - box.left) / box.width) * 100);
        },
        [apply],
    );

    const pair = pairs[index];
    const outgoing = previous !== null && previous !== index ? pairs[previous] : null;

    return (
        <figure className="euk-wipe">
            <div className="euk-wipe-head">
                <h4 className="euk-label euk-wipe-title">{title}</h4>
                <div
                    className="euk-wipe-dots"
                    role="group"
                    aria-label={`Choose a ${title.toLowerCase()} example`}
                >
                    {pairs.map((item, i) => (
                        <button
                            key={item.id}
                            type="button"
                            className="euk-wipe-dot"
                            aria-label={`Example ${i + 1} of ${pairs.length}`}
                            aria-pressed={i === index}
                            onClick={() => {
                                if (i === index) return;
                                setPrevious(index);
                                setIndex(i);
                                setPinned(true);
                            }}
                        />
                    ))}
                </div>
            </div>

            <div
                ref={frameRef}
                className="euk-wipe-frame"
                style={{ aspectRatio: `${width} / ${height}` }}
                onPointerDown={(event) => {
                    event.currentTarget.setPointerCapture(event.pointerId);
                    onTakeover();
                    setPinned(true);
                    fromClientX(event.clientX);
                }}
                onPointerMove={(event) => {
                    if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
                    fromClientX(event.clientX);
                }}
            >
                {outgoing && (
                    <Image
                        key={outgoing.id}
                        className="euk-wipe-img euk-wipe-prev"
                        src={outgoing.after}
                        alt=""
                        width={width}
                        height={height}
                        aria-hidden="true"
                        draggable={false}
                    />
                )}
                <Image
                    className="euk-wipe-img"
                    src={pair.after}
                    alt={pair.alt}
                    width={width}
                    height={height}
                    priority={index === 0}
                    draggable={false}
                />
                <div className="euk-wipe-clip" aria-hidden="true">
                    <Image
                        className="euk-wipe-img"
                        src={pair.before}
                        alt=""
                        width={width}
                        height={height}
                        priority={index === 0}
                        draggable={false}
                    />
                </div>
                <div className="euk-wipe-line" aria-hidden="true" />
                <div
                    ref={sliderRef}
                    role="slider"
                    tabIndex={0}
                    aria-label={`Drag to compare the ${title.toLowerCase()} as uploaded with the prepared file`}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={55}
                    aria-valuetext="Part of the uploaded file shown"
                    className="euk-wipe-handle"
                    onKeyDown={(event) => {
                        const step = event.shiftKey ? 10 : 2;
                        const moves: Record<string, number> = {
                            ArrowLeft: -step,
                            ArrowRight: step,
                            Home: -100,
                            End: 100,
                        };
                        const delta = moves[event.key];
                        if (delta === undefined) return;
                        event.preventDefault();
                        onTakeover();
                        setPinned(true);
                        apply(pctRef.current + delta);
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
                <span className="euk-label euk-wipe-tag euk-wipe-tag--before">
                    As uploaded
                </span>
                <span className="euk-label euk-wipe-tag euk-wipe-tag--after">
                    Prepared
                </span>
            </div>

            <figcaption>
                <ol className="euk-wipe-checks">
                    {checks.map((check, i) => (
                        <li
                            key={check.label}
                            className="euk-wipe-check"
                            data-done={i < done ? "true" : undefined}
                        >
                            <span className="euk-wipe-check-mark" aria-hidden="true">
                                {i < done ? (
                                    <svg width="11" height="9" viewBox="0 0 11 9" fill="none" stroke="var(--signal-ink)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M1 4.5 L4 7.5 L10 1.5" />
                                    </svg>
                                ) : null}
                            </span>
                            <span className="euk-label euk-wipe-check-label">
                                {check.label}
                            </span>
                            <span className="euk-wipe-check-text">
                                <span className={i < done ? "euk-wipe-was" : undefined}>
                                    {check.before}
                                </span>
                                {i < done && (
                                    <span className="euk-wipe-now">
                                        {" → "}
                                        {check.after}
                                    </span>
                                )}
                            </span>
                        </li>
                    ))}
                </ol>
            </figcaption>
        </figure>
    );
}

export function WipeDemo({
    photos,
    photoChecks,
    signatures,
    signatureChecks,
}: {
    photos: WipePair[];
    photoChecks: WipeCheck[];
    signatures: WipePair[];
    signatureChecks: WipeCheck[];
}) {
    const [playing, setPlaying] = useState(false);
    const [onScreen, setOnScreen] = useState(false);
    const bandRef = useRef<HTMLDivElement>(null);

    // Motion is opt-out for everyone else and opt-in here: it starts only
    // after the browser says it is wanted (WCAG 2.3.3), and the control
    // stays for anyone who wants it the other way.
    useEffect(() => {
        const query = window.matchMedia("(prefers-reduced-motion: reduce)");
        const sync = () => setPlaying(!query.matches);
        sync();
        query.addEventListener("change", sync);
        return () => query.removeEventListener("change", sync);
    }, []);

    useEffect(() => {
        const el = bandRef.current;
        if (!el || typeof IntersectionObserver === "undefined") {
            setOnScreen(true);
            return;
        }
        // Any part of it showing counts: the band is taller than a phone
        // viewport, so a fractional threshold would never be met on the
        // screen it matters most on.
        const observer = new IntersectionObserver(([entry]) =>
            setOnScreen(entry.isIntersecting),
        );
        observer.observe(el);
        return () => observer.disconnect();
    }, []);

    const running = playing && onScreen;

    return (
        <div className="euk-wipes" ref={bandRef}>
            <div className="euk-wipes-head">
                <div>
                    <h3 className="euk-display">
                        Watch it, or
                        <br />
                        take the handle.
                    </h3>
                    <p>
                        This is the comparison you get after you upload: what you
                        gave us on one side, what came back on the other. Each
                        problem is checked off as the line passes it.
                    </p>
                </div>
                <button
                    type="button"
                    className="euk-wipes-toggle"
                    aria-pressed={playing}
                    onClick={() => setPlaying((value) => !value)}
                >
                    <span aria-hidden="true">{playing ? "❚❚" : "▶"}</span>
                    {playing ? "Pause" : "Play"}
                </button>
            </div>

            <div className="euk-wipes-grid">
                <WipeSet
                    title="Photograph"
                    pairs={photos}
                    checks={photoChecks}
                    width={720}
                    height={960}
                    running={running}
                    start={55}
                    onTakeover={() => setPlaying(false)}
                />
                <WipeSet
                    title="Signature"
                    pairs={signatures}
                    checks={signatureChecks}
                    width={960}
                    height={720}
                    running={running}
                    start={30}
                    onTakeover={() => setPlaying(false)}
                />
            </div>

            <p className="euk-wipes-note">
                Representational examples. The faces and the signatures are
                generated, not photographs of candidates, and these particular
                pairs were made to show the difference rather than produced by
                our engine. Your own file is prepared to your examination&rsquo;s
                published rules, and you see it before you pay.
            </p>
        </div>
    );
}
