"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

/**
 * The site asks for its ads to be allowed (DEC-134, the owner's decision).
 *
 * The service is free and every preparation costs money; ads are the only
 * income. When an ad blocker is detected, the whole site is covered by one
 * message and a Refresh button until it is turned off.
 *
 * Mounted only when AdSense is configured (`adsEnabled()` in the layout):
 * before approval no ad loads for anyone, and every visitor would look
 * blocked. Crawlers are never shown it, so search results see the pages.
 *
 * Detection, two ways, either one enough:
 * - a request for AdSense's own script fails (network-level blockers);
 * - a bait element with ad-like class names is hidden (cosmetic blockers).
 * An offline visitor would also fail the request; they could not use the
 * site anyway, and Refresh is the right advice for them too.
 */

const ADSENSE_URL = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js";
const BOT = /bot|crawler|spider|crawling|googlebot|bingbot|adsbot|mediapartners|lighthouse|headless/i;

async function requestBlocked(): Promise<boolean> {
    try {
        await fetch(ADSENSE_URL, { method: "HEAD", mode: "no-cors", cache: "no-store" });
        return false;
    } catch {
        return true;
    }
}

function baitHidden(): Promise<boolean> {
    return new Promise((resolve) => {
        const bait = document.createElement("div");
        bait.className = "adsbox ad-banner textads banner-ads ad-placement";
        bait.setAttribute("aria-hidden", "true");
        bait.style.cssText = "position:absolute;left:-9999px;top:-9999px;width:2px;height:2px;";
        bait.innerHTML = "&nbsp;";
        document.body.appendChild(bait);
        window.setTimeout(() => {
            const style = window.getComputedStyle(bait);
            const hidden =
                bait.offsetHeight === 0 ||
                bait.offsetParent === null ||
                style.display === "none" ||
                style.visibility === "hidden";
            bait.remove();
            resolve(hidden);
        }, 300);
    });
}

export function AdblockGate() {
    const [blocked, setBlocked] = useState(false);
    const hindi = (usePathname() ?? "").startsWith("/hi");

    useEffect(() => {
        if (typeof navigator !== "undefined" && BOT.test(navigator.userAgent)) return;
        let cancelled = false;
        const start = window.setTimeout(async () => {
            const [network, cosmetic] = await Promise.all([requestBlocked(), baitHidden()]);
            if (!cancelled && (network || cosmetic)) setBlocked(true);
        }, 1200);
        return () => {
            cancelled = true;
            window.clearTimeout(start);
        };
    }, []);

    // Everything behind the message is unreachable: no scrolling, no focus.
    useEffect(() => {
        if (!blocked) return;
        const siblings = Array.from(document.body.children).filter(
            (el) => !el.classList.contains("euk-adgate"),
        );
        siblings.forEach((el) => el.setAttribute("inert", ""));
        const overflow = document.body.style.overflow;
        document.body.style.overflow = "hidden";
        return () => {
            siblings.forEach((el) => el.removeAttribute("inert"));
            document.body.style.overflow = overflow;
        };
    }, [blocked]);

    if (!blocked) return null;

    return (
        <div className="euk euk-adgate" role="dialog" aria-modal="true" aria-labelledby="adgate-title">
            <div className="euk-adgate-card">
                <h2 id="adgate-title" className="euk-display euk-adgate-title">
                    {hindi ? "कृपया अपना ऐड ब्लॉकर रोकें" : "Please pause your ad blocker"}
                </h2>
                <p>
                    {hindi
                        ? "ExamUploadKit मुफ़्त है। हर फ़ाइल तैयार करने का ख़र्च हम उठाते हैं, और विज्ञापन ही इसका एकमात्र सहारा हैं।"
                        : "ExamUploadKit is free. Every file we prepare costs us money, and ads are the only thing that pays for it."}
                </p>
                <p className="euk-adgate-how">
                    {hindi
                        ? "पता बार के पास ऐड ब्लॉकर या शील्ड के निशान पर टैप करें, इस साइट के लिए उसे बंद करें, फिर रीफ़्रेश करें।"
                        : "Tap the ad blocker or shield icon near the address bar, turn it off for this site, then refresh."}
                </p>
                <button
                    type="button"
                    className="primary-button euk-adgate-refresh"
                    onClick={() => window.location.reload()}
                >
                    {hindi ? "मैंने बंद कर दिया, रीफ़्रेश करें" : "I’ve turned it off, refresh"}
                </button>
            </div>
        </div>
    );
}
