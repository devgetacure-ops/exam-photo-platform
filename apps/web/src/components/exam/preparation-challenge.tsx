"use client";
import Script from "next/script";
import { useEffect, useRef, useState } from "react";
import { useTr } from "../locale-context";

declare global {
    interface Window {
        turnstile?: {
            render: (
                container: HTMLElement,
                options: {
                    sitekey: string;
                    callback: (token: string) => void;
                    "expired-callback": () => void;
                    "error-callback": () => void;
                    "refresh-expired"?: "auto" | "manual" | "never";
                },
            ) => string;
            reset: (id: string) => void;
            remove: (id: string) => void;
        };
    }
}

/**
 * Cloudflare Turnstile for one upload box.
 *
 * A page has one box per file, and every box needs its own pass. The
 * script's `onReady` fires only for the first box that mounts it, so the
 * others never drew a widget and could never upload (live, 11 November).
 * Each box now waits for `window.turnstile` itself, however the script got
 * there.
 *
 * A pass is good for one preparation. `round` goes up after every attempt,
 * and the widget is reset for a fresh pass; an expired pass refreshes
 * itself.
 */
export function PreparationChallenge({
    siteKey,
    onToken,
    round = 0,
}: {
    siteKey: string;
    onToken: (token: string) => void;
    /** Increment after each preparation attempt to get a fresh pass. */
    round?: number;
}) {
    const tr = useTr();
    const element = useRef<HTMLDivElement>(null);
    const widget = useRef<string | null>(null);
    const [ready, setReady] = useState(false);
    const [error, setError] = useState(false);

    // The script may already be on the page from another box.
    useEffect(() => {
        if (ready) return;
        if (typeof window !== "undefined" && window.turnstile) {
            const start = setTimeout(() => setReady(true), 0);
            return () => clearTimeout(start);
        }
        const poll = setInterval(() => {
            if (window.turnstile) {
                setReady(true);
                clearInterval(poll);
            }
        }, 250);
        return () => clearInterval(poll);
    }, [ready]);

    useEffect(() => {
        if (!ready || !element.current || !window.turnstile) return;
        const id = window.turnstile.render(element.current, {
            sitekey: siteKey,
            callback: (token) => {
                setError(false);
                onToken(token);
            },
            "expired-callback": () => onToken(""),
            "error-callback": () => {
                onToken("");
                setError(true);
            },
            "refresh-expired": "auto",
        });
        widget.current = id;
        return () => {
            window.turnstile?.remove(id);
            widget.current = null;
            onToken("");
        };
    }, [ready, siteKey, onToken]);

    // A used pass is spent: ask for a new one after each attempt.
    useEffect(() => {
        if (round === 0 || !widget.current || !window.turnstile) return;
        onToken("");
        window.turnstile.reset(widget.current);
    }, [round, onToken]);

    return (
        <div className="preparation-challenge">
            <Script
                src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"
                strategy="afterInteractive"
                onReady={() => setReady(true)}
                onError={() => setError(true)}
            />
            <div ref={element} />
            {error && (
                <p role="alert">
                    {tr(
                        "Verification couldn’t load. Refresh this page to try again.",
                        "जाँच लोड नहीं हो सकी। पेज रीफ़्रेश करके फिर कोशिश करें।",
                    )}
                </p>
            )}
        </div>
    );
}
