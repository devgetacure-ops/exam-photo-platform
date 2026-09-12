"use client";

import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";

/**
 * The before-and-after band, set the way an application form is set.
 *
 * A form gives you a photograph box and, beneath it, a signature strip of the
 * same width. Arranging the two comparisons that way fixes the layout problem
 * the side-by-side version had — a tall portrait next to a short landscape,
 * ragged along the bottom — and it is the thing the candidate is filling in.
 *
 * The motion rules, in one place:
 *
 * - The sweep runs one way only, from the upload to the prepared file, and
 *   both frames run it together. Travelling back the other way said
 *   "prepared becomes your phone photograph", which is the story backwards.
 * - It rests on the prepared file at the end of each run, long enough to be
 *   read, then dissolves into the next example and starts again.
 * - Each frame is its own in every other way: taking the handle of one holds
 *   only that one, and it picks itself up three seconds after the last touch.
 * - At the end of each sweep a frame moves to its next example, so everything
 *   on offer is seen without anybody clicking.
 * - The control pauses and plays both, for anyone who wants it still
 *   (WCAG 2.2.2). Nothing moves under prefers-reduced-motion, or while the
 *   band is off screen.
 *
 * The sweep writes a CSS custom property on the frame rather than React
 * state, so the loop re-renders nothing; the only state that changes during a
 * sweep is how many of the checks the partition has passed.
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

/** One example: the sweep across, then a rest on the prepared file. */
const PERIOD_MS = 7000;
const SWEEP_SHARE = 0.72;
/** The partition's travel. It starts on the upload and ends on the result. */
const FROM = 96;
const TO = 4;
const START = 50;
/** How long after the last touch a frame picks itself up again. */
const RESUME_AFTER_MS = 3000;

interface SetProps {
    title: string;
    pairs: WipePair[];
    checks: WipeCheck[];
    width: number;
    height: number;
    /** The band's control says yes, and the band is on screen. */
    allowed: boolean;
}

function WipeSet({ title, pairs, checks, width, height, allowed }: SetProps) {
    const [index, setIndex] = useState(0);
    const [previous, setPrevious] = useState<number | null>(null);
    const [held, setHeld] = useState(false);
    const [passed, setPassed] = useState(0);

    const frameRef = useRef<HTMLDivElement>(null);
    const sliderRef = useRef<HTMLDivElement>(null);
    const pctRef = useRef(START);
    const passedRef = useRef(0);
    const indexRef = useRef(0);
    const resumeRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        indexRef.current = index;
    }, [index]);

    const apply = useCallback(
        (next: number) => {
            const pct = Math.min(100, Math.max(0, next));
            pctRef.current = pct;
            frameRef.current?.style.setProperty("--wipe", pct.toFixed(2));
            sliderRef.current?.setAttribute("aria-valuenow", String(Math.round(pct)));
            // Counted from the prepared side, which is the side that grows:
            // a check is ticked once the prepared file has covered the place
            // it sits. Counting from the upload had all four ticked while the
            // frame still showed the phone photograph.
            const covered = 100 - pct;
            const crossed = checks.filter(
                (_, i) => covered >= ((i + 1) / (checks.length + 1)) * 100,
            ).length;
            if (crossed !== passedRef.current) {
                passedRef.current = crossed;
                setPassed(crossed);
            }
        },
        [checks],
    );

    useEffect(() => {
        apply(pctRef.current);
    }, [apply]);

    /** Any touch holds this frame; it lets go again after a quiet spell. */
    const hold = useCallback(() => {
        setHeld(true);
        if (resumeRef.current) clearTimeout(resumeRef.current);
        resumeRef.current = setTimeout(() => setHeld(false), RESUME_AFTER_MS);
    }, []);

    useEffect(
        () => () => {
            if (resumeRef.current) clearTimeout(resumeRef.current);
        },
        [],
    );

    const running = allowed && !held;

    useEffect(() => {
        if (!running) return;
        let frame = 0;
        let started = false;
        let origin = 0;
        let lastCycle = 0;
        const tick = (now: number) => {
            if (!started) {
                // Pick the sweep up where the handle rests, so starting it
                // never throws the partition across the frame.
                const travelled = Math.min(
                    1,
                    Math.max(0, (FROM - pctRef.current) / (FROM - TO)),
                );
                const done = Math.acos(1 - 2 * travelled) / Math.PI;
                origin = now - done * SWEEP_SHARE * PERIOD_MS;
                lastCycle = 0;
                started = true;
            }
            const elapsed = (now - origin) / PERIOD_MS;
            const t = elapsed % 1;
            // Across, then a rest on the result. One direction: the upload
            // becomes the prepared file, never the other way about.
            const travel = Math.min(1, t / SWEEP_SHARE);
            const eased = 0.5 - 0.5 * Math.cos(Math.PI * travel);
            apply(FROM - eased * (FROM - TO));
            // On to the next example once a whole run has played. Counted
            // rather than watched for: a dropped frame can step clean over a
            // narrow window, and on a slow phone that means a frame that
            // quietly stops changing example.
            const cycle = Math.floor(elapsed);
            if (cycle !== lastCycle && pairs.length > 1) {
                lastCycle = cycle;
                setPrevious(indexRef.current);
                setIndex((i) => (i + 1) % pairs.length);
            }
            frame = requestAnimationFrame(tick);
        };
        frame = requestAnimationFrame(tick);
        return () => cancelAnimationFrame(frame);
    }, [running, pairs.length, apply]);

    useEffect(() => {
        if (previous === null) return;
        const timer = setTimeout(() => setPrevious(null), 420);
        return () => clearTimeout(timer);
    }, [previous]);

    // Fetch the next pair before it is wanted, so a change never shows a gap.
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
    const latest = passed > 0 ? checks[passed - 1] : null;

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
                                hold();
                                if (i === index) return;
                                setPrevious(index);
                                setIndex(i);
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
                    hold();
                    fromClientX(event.clientX);
                }}
                onPointerMove={(event) => {
                    if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
                    hold();
                    fromClientX(event.clientX);
                }}
                onPointerUp={hold}
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
                    aria-valuenow={START}
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
                        hold();
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
                <ul className="euk-wipe-ticks">
                    {checks.map((check, i) => (
                        <li key={check.label} data-done={i < passed ? "true" : undefined}>
                            <span className="euk-wipe-tickbox" aria-hidden="true">
                                {i < passed ? (
                                    <svg width="9" height="8" viewBox="0 0 11 9" fill="none" stroke="var(--signal-ink)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M1 4.5 L4 7.5 L10 1.5" />
                                    </svg>
                                ) : null}
                            </span>
                            {check.label}
                        </li>
                    ))}
                </ul>
                <p className="euk-wipe-caption">
                    {latest ? (
                        <>
                            <span className="euk-wipe-was">{latest.before}</span>
                            {" → "}
                            <span className="euk-wipe-now">{latest.after}</span>
                        </>
                    ) : (
                        "Drag the handle, or leave it running."
                    )}
                </p>
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
        // Any part of it showing counts: the sheet is taller than a phone
        // viewport, so a fractional threshold would never be met there.
        const observer = new IntersectionObserver(([entry]) =>
            setOnScreen(entry.isIntersecting),
        );
        observer.observe(el);
        return () => observer.disconnect();
    }, []);

    const allowed = playing && onScreen;

    return (
        <div className="euk-band" ref={bandRef}>
            <div className="euk-band-head">
                <div className="euk-band-copy">
                    <h3 className="euk-display">
                        Watch it, or take the handle.
                    </h3>
                    <p>
                        What you gave us on one side, what came back on the
                        other. Each frame works through its examples on its own;
                        drag either and it stays where you put it, then picks
                        itself up three seconds later.
                    </p>
                </div>
                <button
                    type="button"
                    className="euk-band-toggle"
                    aria-pressed={playing}
                    onClick={() => setPlaying((value) => !value)}
                >
                    <span aria-hidden="true">{playing ? "❚❚" : "▶"}</span>
                    {playing ? "Pause both" : "Play both"}
                </button>
            </div>

            <div className="euk-band-pair">
                <WipeSet
                    title="Photograph"
                    pairs={photos}
                    checks={photoChecks}
                    width={720}
                    height={960}
                    allowed={allowed}
                />
                <WipeSet
                    title="Signature"
                    pairs={signatures}
                    checks={signatureChecks}
                    width={960}
                    height={720}
                    allowed={allowed}
                />
            </div>

            <p className="euk-band-note">
                Representational examples. The faces and the signatures are
                generated, not photographs of candidates, and these pairs were
                made to show the difference rather than produced by our engine.
                Your own file is prepared to your examination&rsquo;s published
                rules, and you see it before you pay.
            </p>
        </div>
    );
}
