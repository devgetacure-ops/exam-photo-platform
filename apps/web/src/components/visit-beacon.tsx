"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";
import { campaignFrom, currentKit, deviceOf, referrerHost, send, sessionId, tracked } from "../lib/visit-beacon";

/**
 * Counts a page view on every route change and the seconds the page was
 * actually visible (DEC-110). Draws nothing.
 */
export function VisitBeacon() {
    const pathname = usePathname() ?? "/";
    const first = useRef(true);
    const visible = useRef(0);

    useEffect(() => {
        if (!tracked(pathname)) return;
        const { device, browser } = deviceOf(navigator.userAgent, window.innerWidth);
        const connection = (navigator as Navigator & { connection?: { effectiveType?: string } }).connection?.effectiveType;
        send([
            {
                session_id: sessionId(),
                type: "view",
                path: pathname,
                kit_id: currentKit(),
                device,
                browser,
                connection,
                ...(first.current
                    ? { referrer_host: referrerHost(document.referrer, window.location.host), ...campaignFrom(window.location.search) }
                    : {}),
            },
        ]);
        first.current = false;
    }, [pathname]);

    useEffect(() => {
        if (!tracked(pathname)) return;
        const flush = (beacon: boolean) => {
            const seconds = Math.round(visible.current);
            if (seconds < 1) return;
            visible.current = 0;
            send([{ session_id: sessionId(), type: "ping", seconds, kit_id: currentKit() }], beacon);
        };
        const tick = window.setInterval(() => {
            if (document.visibilityState === "visible") visible.current += 5;
            if (visible.current >= 30) flush(false);
        }, 5000);
        const hide = () => {
            if (document.visibilityState === "hidden") flush(true);
        };
        const leave = () => flush(true);
        document.addEventListener("visibilitychange", hide);
        window.addEventListener("pagehide", leave);
        return () => {
            window.clearInterval(tick);
            document.removeEventListener("visibilitychange", hide);
            window.removeEventListener("pagehide", leave);
            flush(true);
        };
    }, [pathname]);

    return null;
}
