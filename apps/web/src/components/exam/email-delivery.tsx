"use client";

import { useEffect, useRef, useState } from "react";
import { emailKit } from "../../lib/journey-client";

/**
 * A copy of the files for the candidate's inbox, which outlives our deletion.
 *
 * The address can be entered at review, before paying, and the files are sent
 * the moment payment is confirmed. That means the address has to survive the
 * review screen giving way to the delivery screen, which remounts this form.
 * It is held in memory for that, and only for that: never in browser storage,
 * gone on reload, and cleared once the email is sent.
 */
interface Draft {
    address: string;
    consent: boolean;
    attempted: string;
}

const drafts = new Map<string, Draft>();

function Envelope() {
    return (
        <svg viewBox="0 0 40 30" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <rect x="2" y="3" width="36" height="24" />
            <path d="M2 3 L 20 17 L 38 3" />
        </svg>
    );
}

export function EmailDelivery({
    kitId,
    jobIds,
    released,
}: {
    kitId: string;
    jobIds: string[];
    released: boolean;
}) {
    const saved = drafts.get(kitId);
    const [address, setAddress] = useState(saved?.address ?? "");
    const [consent, setConsent] = useState(saved?.consent ?? false);
    const [state, setState] = useState<"idle" | "sending" | "sent" | "error">(
        "idle",
    );
    const [message, setMessage] = useState("");
    const attempted = useRef(saved?.attempted ?? "");
    const signature = [...jobIds].sort().join(",");

    const remember = (patch: Partial<Draft>) => {
        const current = drafts.get(kitId) ?? {
            address: "",
            consent: false,
            attempted: "",
        };
        drafts.set(kitId, { ...current, ...patch });
    };

    async function send() {
        if (!released || !consent || !address || state === "sending") return;
        attempted.current = `${signature}:${address}`;
        remember({ attempted: attempted.current });
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
            drafts.delete(kitId);
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
            className="euk-email"
            data-state={state}
            onSubmit={(event) => {
                event.preventDefault();
                void send();
            }}
        >
            <div className="euk-email-head">
                <Envelope />
                <div className="min-w-0">
                    <h3>
                        {released
                            ? "A copy for your inbox"
                            : "Email them to yourself as well"}
                    </h3>
                    <p>
                        {released
                            ? "Keep the files after ours are deleted."
                            : "Leave your address and they are sent the moment payment is confirmed."}
                    </p>
                </div>
            </div>
            <label htmlFor="delivery-email" className="euk-email-label">
                Email address <span>(optional)</span>
            </label>
            <div className="euk-email-row">
                <input
                    id="delivery-email"
                    type="email"
                    inputMode="email"
                    value={address}
                    maxLength={254}
                    autoComplete="email"
                    disabled={state === "sending"}
                    onChange={(event) => {
                        setAddress(event.target.value);
                        setConsent(false);
                        remember({ address: event.target.value, consent: false });
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
            <label className="euk-consent">
                <input
                    type="checkbox"
                    checked={consent}
                    disabled={!address || state === "sending"}
                    onChange={(event) => {
                        setConsent(event.target.checked);
                        remember({ consent: event.target.checked });
                    }}
                />
                <span>
                    Email these files to me once they are released. Keep this
                    page open for sending; this address is not saved in my
                    browser.
                </span>
            </label>
            {message && (
                <p
                    className="euk-email-message"
                    role={state === "error" ? "alert" : "status"}
                >
                    {message}
                </p>
            )}
        </form>
    );
}
