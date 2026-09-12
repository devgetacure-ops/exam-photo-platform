"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

/**
 * The phone's top bar: back, where you are, and nothing else.
 *
 * It gets out of the way as you read — hiding on a downward scroll and
 * returning the moment you scroll up — because 48px of a 640px screen is worth
 * having back, and because the way out should never be more than one upward
 * flick away. It does not hide while a flow is at its first screen, where the
 * back control is the only way out.
 */
export function AppBar({
    title,
    backHref,
    onBack,
    pinned = false,
    right,
}: {
    title: string;
    backHref?: string;
    onBack?: () => void;
    /** Keep it visible whatever the scroll does. */
    pinned?: boolean;
    right?: React.ReactNode;
}) {
    const [hidden, setHidden] = useState(false);
    const lastY = useRef(0);

    useEffect(() => {
        if (pinned) return;
        lastY.current = window.scrollY;
        let frame = 0;
        const onScroll = () => {
            if (frame) return;
            frame = requestAnimationFrame(() => {
                frame = 0;
                const y = window.scrollY;
                const down = y > lastY.current;
                // Past the bar's own height, so a short page never hides it.
                setHidden(down && y > 64);
                lastY.current = y;
            });
        };
        window.addEventListener("scroll", onScroll, { passive: true });
        return () => {
            window.removeEventListener("scroll", onScroll);
            if (frame) cancelAnimationFrame(frame);
        };
    }, [pinned]);

    const back = backHref ? (
        <Link href={backHref} className="euk-appbar-back" aria-label="Back">
            <Chevron />
        </Link>
    ) : onBack ? (
        <button type="button" className="euk-appbar-back" aria-label="Back" onClick={onBack}>
            <Chevron />
        </button>
    ) : null;

    return (
        <header className="euk-appbar" data-hidden={hidden || undefined}>
            {back}
            <h1 className="euk-appbar-title">{title}</h1>
            {right ? <div className="euk-appbar-right">{right}</div> : null}
        </header>
    );
}

function Chevron() {
    return (
        <svg
            width="11"
            height="18"
            viewBox="0 0 11 18"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            <path d="M9 1 L2 9 L9 17" />
        </svg>
    );
}
