"use client";

import Image from "next/image";
import { type CSSProperties, useCallback, useEffect, useRef, useState } from "react";

/**
 * The before-and-after band: a photograph and a signature, two equal frames.
 *
 * The motion is one continuous conveyor (the owner's testing note 2). The
 * first version swept to the prepared file, snapped the partition back and
 * faded the next example in over it, which read as a broken frame between
 * examples. Now the same partition carries the handover:
 *
 * - it sweeps across, and the upload becomes the prepared file;
 * - it rests there, long enough to be read;
 * - it sweeps back, and this time what it uncovers is the **next** upload,
 *   laid over the prepared file it is replacing;
 * - at the far edge the next upload covers the whole frame, so the prepared
 *   file underneath is swapped for the next one with nothing visible changing,
 *   and the next sweep begins.
 *
 * Every other rule stands: taking the handle of one frame holds only that one,
 * and it picks itself up three seconds after the last touch; the control
 * pauses and plays both (WCAG 2.2.2); nothing moves under
 * prefers-reduced-motion or while the band is off screen.
 *
 * The sweep writes a CSS custom property on the frame rather than React state,
 * so the loop re-renders nothing except at the two phase changes of a cycle.
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

/** One example: across, a rest on the result, back with the next upload. */
const PERIOD_MS = 7600;
/** End of the sweep to the prepared file, as a share of the period. */
const ARRIVE = 0.38;
/** Start of the sweep that brings in the next upload. */
const DEPART = 0.56;
/** End of that sweep. The remainder rests on the next upload before the swap. */
const RETURN = 0.94;
/** The partition's travel: the whole frame, so each handover is invisible. */
const UPLOAD = 100;
const PREPARED = 0;
const START = 50;
/** How long after the last touch a frame picks itself up again. */
const RESUME_AFTER_MS = 3000;

const ease = (x: number) => 0.5 - 0.5 * Math.cos(Math.PI * Math.min(1, Math.max(0, x)));

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
    /** True while the sweep back is uncovering the next upload. */
    const [incoming, setIncoming] = useState(false);
    const [held, setHeld] = useState(false);
    const [passed, setPassed] = useState(0);

    const frameRef = useRef<HTMLDivElement>(null);
    const sliderRef = useRef<HTMLDivElement>(null);
    const pctRef = useRef(START);
    const passedRef = useRef(0);
    const resumeRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const apply = useCallback(
        (next: number) => {
            const pct = Math.min(100, Math.max(0, next));
            pctRef.current = pct;
            frameRef.current?.style.setProperty("--wipe", pct.toFixed(2));
            sliderRef.current?.setAttribute("aria-valuenow", String(Math.round(pct)));
            // Counted from the prepared side, which is the side that grows: a
            // check is ticked once the prepared file has covered its place.
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

    /** Any touch holds this frame, on the example it is showing now. */
    const hold = useCallback(() => {
        setHeld(true);
        setIncoming(false);
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
        let origin = 0;
        let started = false;
        let lastCycle = 0;
        let lastIncoming = false;
        const tick = (now: number) => {
            if (!started) {
                // Pick the sweep up where the handle rests, so starting never
                // throws the partition across the frame.
                const travelled = (UPLOAD - pctRef.current) / (UPLOAD - PREPARED);
                const done = Math.acos(1 - 2 * Math.min(1, Math.max(0, travelled))) / Math.PI;
                origin = now - done * ARRIVE * PERIOD_MS;
                started = true;
            }
            const elapsed = (now - origin) / PERIOD_MS;
            const cycle = Math.floor(elapsed);
            const t = elapsed - cycle;

            // Counted rather than watched for: a dropped frame can step over
            // a narrow window, and on a slow phone that would stall the band.
            if (cycle !== lastCycle) {
                lastCycle = cycle;
                lastIncoming = false;
                if (pairs.length > 1) {
                    // The next upload already covers the whole frame, so
                    // swapping the prepared file beneath it shows nothing.
                    setIndex((i) => (i + 1) % pairs.length);
                }
                setIncoming(false);
            }

            const bringing = t >= DEPART;
            if (bringing !== lastIncoming) {
                // Swapped while the partition sits at the prepared edge, where
                // the upload layer is fully hidden.
                lastIncoming = bringing;
                setIncoming(bringing);
            }

            if (t < ARRIVE) apply(UPLOAD - ease(t / ARRIVE) * (UPLOAD - PREPARED));
            else if (t < DEPART) apply(PREPARED);
            else if (t < RETURN) apply(PREPARED + ease((t - DEPART) / (RETURN - DEPART)) * (UPLOAD - PREPARED));
            else apply(UPLOAD);

            frame = requestAnimationFrame(tick);
        };
        frame = requestAnimationFrame(tick);
        return () => cancelAnimationFrame(frame);
    }, [running, pairs.length, apply]);

    // Fetch the next pair before it is wanted, so a handover never shows a gap.
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
    const upload = incoming ? pairs[(index + 1) % pairs.length] : pair;
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
                                if (i !== index) setIndex(i);
                            }}
                        />
                    ))}
                </div>
            </div>

            <div
                ref={frameRef}
                className="euk-wipe-frame"
                style={{ "--wipe-ratio": `${width} / ${height}` } as CSSProperties}
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
                        src={upload.before}
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

            {/* Two equal frames and one line beneath them (testing note 1):
                the photograph and the signature at the same size, so neither
                dwarfs the other, and the note as a caption rather than a
                column of its own. */}
            <div className="euk-band-body">
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
                    generated, not photographs of candidates, and these pairs
                    were made to show the difference rather than produced by our
                    engine. Your own file is prepared to your
                    examination&rsquo;s published rules, and you see it before
                    you pay.
                </p>
            </div>
        </div>
    );
}
