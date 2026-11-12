"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { byVolume, deadlineStatus, isOpen, opensSoon, type Deadline } from "../../lib/deadlines";
import { useDeadlines } from "../../lib/use-deadlines";
import { useToday } from "../../lib/use-today";
import { DeadlineStamp } from "./deadline-stamp";

const MAX_SLIDES = 6;
const EVERY_MS = 5000;

/**
 * Open and soon-opening examinations, one at a time, under the header
 * (DEC-135 option B; a carousel since DEC-137).
 *
 * The biggest examinations come first (candidates last cycle), then the most
 * urgent. It moves on every few seconds, stops while a pointer, finger or
 * keyboard is on it, and never moves on its own for anyone who asked for
 * reduced motion. Nothing at all when no examination is open or opening.
 */
export function ClosingSoonBanner({ builtOn }: { builtOn: string }) {
    const today = useToday(builtOn);
    const entries = useDeadlines();
    const slides = [...entries]
        .filter((entry) => {
            const status = deadlineStatus(entry, today);
            return isOpen(status) || opensSoon(status);
        })
        .sort(byVolume(today))
        .slice(0, MAX_SLIDES);
    const count = slides.length;

    const [index, setIndex] = useState(0);
    const [held, setHeld] = useState(false);
    const [paused, setPaused] = useState(false);
    const [still, setStill] = useState(false);
    const touchX = useRef<number | null>(null);
    const current = count ? index % count : 0;

    useEffect(() => {
        const query = window.matchMedia("(prefers-reduced-motion: reduce)");
        const update = () => setStill(query.matches);
        update();
        query.addEventListener("change", update);
        return () => query.removeEventListener("change", update);
    }, []);

    useEffect(() => {
        if (count < 2 || held || paused || still) return;
        const timer = window.setInterval(() => {
            if (document.visibilityState === "visible") setIndex((i) => (i + 1) % count);
        }, EVERY_MS);
        return () => window.clearInterval(timer);
    }, [count, held, paused, still]);

    if (!count) return null;
    const go = (to: number) => setIndex(((to % count) + count) % count);

    return (
        <aside
            className="euk euk-invert euk-dbanner"
            aria-label="Application deadlines"
            aria-roledescription={count > 1 ? "carousel" : undefined}
            onMouseEnter={() => setHeld(true)}
            onMouseLeave={() => setHeld(false)}
            onFocus={() => setHeld(true)}
            onBlur={(event) => {
                if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setHeld(false);
            }}
            onTouchStart={(event) => {
                setHeld(true);
                touchX.current = event.touches[0]?.clientX ?? null;
            }}
            onTouchEnd={(event) => {
                const start = touchX.current;
                const end = event.changedTouches[0]?.clientX;
                touchX.current = null;
                if (start != null && end != null && Math.abs(end - start) > 40) go(current + (end < start ? 1 : -1));
            }}
        >
            <div className="euk-wrap euk-dbanner-inner">
                <div className="euk-dbanner-track">
                    {slides.map((entry, i) => (
                        <Slide key={entry.examId} entry={entry} today={today} active={i === current} label={`${i + 1} of ${count}`} many={count > 1} />
                    ))}
                </div>
                {count > 1 && (
                    <div className="euk-dbanner-nav">
                        {slides.map((entry, i) => (
                            <button
                                key={entry.examId}
                                type="button"
                                className="euk-dbanner-dot"
                                aria-label={`Show ${entry.shortName ?? entry.examName}`}
                                aria-current={i === current ? "true" : undefined}
                                onClick={() => go(i)}
                            />
                        ))}
                        {!still && (
                            <button type="button" className="euk-dbanner-pause" onClick={() => setPaused((p) => !p)} aria-label={paused ? "Play" : "Pause"}>
                                <span aria-hidden="true">{paused ? "▶" : "❚❚"}</span>
                            </button>
                        )}
                    </div>
                )}
            </div>
        </aside>
    );
}

function Slide({ entry, today, active, label, many }: { entry: Deadline; today: string; active: boolean; label: string; many: boolean }) {
    const status = deadlineStatus(entry, today);
    const name = entry.shortName ?? entry.examName;
    return (
        <div
            className="euk-dbanner-slide"
            data-active={active ? "true" : undefined}
            role={many ? "group" : undefined}
            aria-roledescription={many ? "slide" : undefined}
            aria-label={many ? label : undefined}
            aria-hidden={active ? undefined : true}
            inert={!active}
        >
            <DeadlineStamp entry={entry} today={today} />
            <p className="euk-dbanner-text">
                <strong>{name}</strong>
                {status.state === "opening"
                    ? " applications open soon. Get your photo and signature ready."
                    : " is taking applications. Get your photo and signature ready."}
            </p>
            <Link className="euk-dbanner-go" href={`/exam/${entry.examId}`}>
                Prepare files <span aria-hidden="true">→</span>
            </Link>
        </div>
    );
}
