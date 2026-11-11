"use client";

import { useEffect, useRef } from "react";
import { ADSENSE_CLIENT, adSlotId } from "../lib/ads";

declare global {
    interface Window {
        adsbygoogle?: unknown[];
    }
}

/**
 * One labelled ad unit (DEC-127). Renders nothing until the site has an
 * AdSense publisher id and this slot an id, so pages stay exactly as they
 * are before approval. Space is reserved so the page does not jump when the
 * ad arrives. Never placed next to an upload or download control.
 */
export function AdSlot({ name, className }: { name: string; className?: string }) {
    const slot = adSlotId(name);
    const pushed = useRef(false);
    useEffect(() => {
        if (!slot || pushed.current) return;
        pushed.current = true;
        try {
            (window.adsbygoogle = window.adsbygoogle || []).push({});
        } catch {
            /* An ad that fails to load leaves the reserved space empty. */
        }
    }, [slot]);
    if (!slot) return null;
    return (
        <aside className={`euk-ad${className ? ` ${className}` : ""}`} aria-label="Advertisement">
            <span className="euk-ad-label">Advertisement</span>
            <ins
                className="adsbygoogle euk-ad-unit"
                style={{ display: "block" }}
                data-ad-client={ADSENSE_CLIENT}
                data-ad-slot={slot}
                data-ad-format="auto"
                data-full-width-responsive="true"
            />
        </aside>
    );
}
