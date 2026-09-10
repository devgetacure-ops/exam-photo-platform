"use client";

import { useEffect, useRef, useState } from "react";
import { emailKit } from "../../lib/journey-client";

export function EmailDelivery({
    kitId,
    jobIds,
    released,
}: {
    kitId: string;
    jobIds: string[];
    released: boolean;
}) {
    const [address, setAddress] = useState("");
    const [consent, setConsent] = useState(false);
    const [state, setState] = useState<"idle" | "sending" | "sent" | "error">(
        "idle",
    );
    const [message, setMessage] = useState("");
    const attempted = useRef("");
    const signature = [...jobIds].sort().join(",");
    async function send() {
        if (!released || !consent || !address || state === "sending") return;
        attempted.current = `${signature}:${address}`;
        setState("sending");
        try {
            const receipt = await emailKit(kitId, address, jobIds);
            if (!receipt.sent)
                throw new Error(
                    "Email was not sent. Your downloads are still available.",
                );
            setMessage(
                `Sent ${receipt.filenames.length} file${receipt.filenames.length === 1 ? "" : "s"} to ${receipt.masked_address}. Check your inbox and spam folder.`,
            );
            setState("sent");
        } catch (error) {
            setState("error");
            setMessage(
                error instanceof Error
                    ? error.message
                    : "Email could not be sent. Please download your files.",
            );
        }
    }
    // This is an explicitly consented, one-attempt convenience while the page is open.
    // A failed request never retries silently (its provider outcome may be uncertain).
    const sendRef = useRef(send);
    useEffect(() => {
        sendRef.current = send;
    });
    useEffect(() => {
        if (
            !released ||
            !consent ||
            !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(address)
        )
            return;
        if (attempted.current === `${signature}:${address}`) return;
        const timer = setTimeout(() => void sendRef.current(), 0);
        return () => clearTimeout(timer);
    }, [released, consent, address, signature]);

    return (
        <form
            className="email-delivery"
            onSubmit={(event) => {
                event.preventDefault();
                void send();
            }}
        >
            <div>
                <h3>A copy for your inbox.</h3>
                <p>Keep your attachments after our temporary files expire.</p>
            </div>
            <label htmlFor="delivery-email">
                Email address <span>(optional)</span>
            </label>
            <div className="form-inline">
                <input
                    id="delivery-email"
                    type="email"
                    value={address}
                    maxLength={254}
                    autoComplete="email"
                    disabled={state === "sending"}
                    onChange={(event) => {
                        setAddress(event.target.value);
                        setConsent(false);
                        setState("idle");
                        setMessage("");
                    }}
                    placeholder="you@example.com"
                />
                {released && (
                    <button
                        type="submit"
                        className="secondary-button"
                        disabled={!consent || !address || state === "sending"}
                    >
                        {state === "sending"
                            ? "Sending…"
                            : state === "error"
                              ? "Try email again"
                              : "Email my files"}
                    </button>
                )}
            </div>
            <label className="review-ack">
                <input
                    type="checkbox"
                    checked={consent}
                    disabled={!address || state === "sending"}
                    onChange={(event) => setConsent(event.target.checked)}
                />
                <span>
                    Email these files to me once they are released. Keep this
                    page open for sending; this address is not saved in my
                    browser.
                </span>
            </label>
            {message && (
                <p role={state === "error" ? "alert" : "status"}>{message}</p>
            )}
        </form>
    );
}
