"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";
import { actionForClick, campaignFrom, currentKit, deviceOf, referrerHost, reportAction, send, sessionId, tracked } from "../lib/visit-beacon";

/**
 * Counts a page view on every route change and the seconds the page was
 * actually visible (DEC-110), and every button, link, file pick and download
 * along the way (DEC-124). Draws nothing.
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

    useEffect(() => {
        const click = (event: MouseEvent) => {
            const action = actionForClick(event.target instanceof Element ? event.target : null);
            if (action) reportAction(action.name, action.label);
        };
        const change = (event: Event) => {
            const input = event.target;
            if (!(input instanceof HTMLInputElement) || input.type !== "file" || !input.files?.length) return;
            const count = input.files.length;
            reportAction("file_chosen", `${count} file${count === 1 ? "" : "s"}`);
        };
        document.addEventListener("click", click, { capture: true });
        document.addEventListener("change", change, { capture: true });
        return () => {
            document.removeEventListener("click", click, { capture: true });
            document.removeEventListener("change", change, { capture: true });
        };
    }, []);

    return null;
}
