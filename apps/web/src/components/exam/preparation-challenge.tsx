"use client";
import Script from "next/script";
import { useEffect, useRef, useState } from "react";

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
                },
            ) => string;
            remove: (id: string) => void;
        };
    }
}
export function PreparationChallenge({
    siteKey,
    onToken,
}: {
    siteKey: string;
    onToken: (token: string) => void;
}) {
    const element = useRef<HTMLDivElement>(null);
    const [ready, setReady] = useState(false);
    const [error, setError] = useState(false);
    useEffect(() => {
        if (!ready || !element.current || !window.turnstile) return;
        const id = window.turnstile.render(element.current, {
            sitekey: siteKey,
            callback: onToken,
            "expired-callback": () => onToken(""),
            "error-callback": () => {
                onToken("");
                setError(true);
            },
        });
        return () => {
            window.turnstile?.remove(id);
            onToken("");
        };
    }, [ready, siteKey, onToken]);
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
                    Verification couldn’t load. Refresh this page to try again.
                </p>
            )}
        </div>
    );
}
