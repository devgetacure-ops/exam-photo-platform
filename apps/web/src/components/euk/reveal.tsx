"use client";

import { useEffect, useRef, type CSSProperties, type ReactNode } from "react";

/**
 * Brings a block in as it enters the viewport.
 *
 * Nothing is hidden by default. The first version hid every block in CSS the
 * moment the page loaded and relied on this script to show them again — so on
 * a slow connection, or if the script failed to load at all, everything below
 * the hero stayed invisible. Verified: in a viewport tall enough to hold the
 * whole page, none of the 33 blocks were ever shown, and the design detector,
 * running its own browser, read that content at 1:1 contrast.
 *
 * Now a block is only held back once this script is actually running, and only
 * if it is still below the fold at that moment — so the candidate never sees
 * it disappear. No JavaScript, a failed bundle, reduced motion, or a browser
 * without IntersectionObserver all leave every block exactly where it is,
 * fully visible.
 *
 * One observer for the page, each element released once shown, nothing
 * replays on scroll-up.
 */
let shared: IntersectionObserver | null = null;
const onShow = new WeakMap<Element, () => void>();

function observer(): IntersectionObserver {
    if (shared) return shared;
    shared = new IntersectionObserver(
        (entries) => {
            for (const entry of entries) {
                if (!entry.isIntersecting) continue;
                onShow.get(entry.target)?.();
                onShow.delete(entry.target);
                shared?.unobserve(entry.target);
            }
        },
        { rootMargin: "0px 0px -8% 0px", threshold: 0.12 },
    );
    return shared;
}

export function Reveal({
    children,
    className = "",
    delay = 0,
}: {
    children: ReactNode;
    className?: string;
    delay?: number;
}) {
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const el = ref.current;
        if (!el || typeof IntersectionObserver === "undefined") return;
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            return;
        }
        // Already on screen: leave it. Arming it now would make a block the
        // candidate is looking at blink out and back in.
        if (el.getBoundingClientRect().top < window.innerHeight) return;

        const show = () => {
            el.setAttribute("data-shown", "");
            el.removeEventListener("focusin", show);
        };
        el.setAttribute("data-armed", "");
        // A keyboard user can tab into a block before it has scrolled far
        // enough to trigger, and would land focus on something invisible.
        el.addEventListener("focusin", show);
        onShow.set(el, show);
        observer().observe(el);
        return () => {
            el.removeEventListener("focusin", show);
            onShow.delete(el);
            shared?.unobserve(el);
        };
    }, []);

    const style = delay
        ? ({ "--reveal-delay": `${delay}ms` } as CSSProperties)
        : undefined;

    return (
        <div ref={ref} data-reveal="" className={className} style={style}>
            {children}
        </div>
    );
}
