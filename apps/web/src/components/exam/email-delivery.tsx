"use client";

import { useEffect, useRef, useState } from "react";
import { emailKit } from "../../lib/journey-client";
import { getReadiness } from "../../lib/api-client";

/**
 * A copy of the files for the candidate's inbox, which outlives our deletion.
 *
 * The address can be entered at review, before paying, and the files are sent
 * the moment payment is confirmed. That means the address has to survive the
 * review screen giving way to the delivery screen, which remounts this form.
 * It is held in memory for that, and only for that: never in browser storage,
 * gone on reload, and cleared once the email is sent.
 *
 * Typing an address into a box that says what it is for is the consent; there
 * is no tick (owner, 16 September 2026). The tick also said "I have finished
 * typing", and that job is kept by where the address was typed. Before
 * payment, it is sent by itself once payment is confirmed: by then the
 * candidate has gone to pay. After payment, only the button sends it, so a
 * half-typed address that already looks valid ("name@gmail.co") never goes.
 */
const LOOKS_LIKE_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface Draft {
    address: string;
    /** Typed before payment, so it is sent by itself once payment is confirmed. */
    auto: boolean;
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
    const [auto, setAuto] = useState(saved?.auto ?? false);
    const [state, setState] = useState<"idle" | "sending" | "sent" | "error">(
        "idle",
    );
    const [message, setMessage] = useState("");
    const attempted = useRef(saved?.attempted ?? "");
    const signature = [...jobIds].sort().join(",");
    const trimmed = address.trim();
    const valid = LOOKS_LIKE_EMAIL.test(trimmed);
    // Offered only where this host can actually send (testing note 18): a
    // form that always fails, and then blames the address, is worse than no
    // form. Unknown -- the engine unreachable or silent -- keeps the form.
    const [unavailable, setUnavailable] = useState(false);
    useEffect(() => {
        let live = true;
        void getReadiness().then((ready) => {
            if (live && ready?.email === "not_configured") setUnavailable(true);
        });
        return () => {
            live = false;
        };
    }, []);

    const remember = (patch: Partial<Draft>) => {
        const current = drafts.get(kitId) ?? {
            address: "",
            auto: false,
            attempted: "",
        };
        drafts.set(kitId, { ...current, ...patch });
    };

    async function send() {
        if (!released || !valid || state === "sending") return;
        attempted.current = `${signature}:${trimmed}`;
        remember({ attempted: attempted.current });
        setState("sending");
        try {
            const receipt = await emailKit(kitId, trimmed, jobIds);
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
    // One attempt, only for an address given before payment, while the page is
    // open. A failed request never retries silently (its provider outcome may
    // be uncertain).
    const sendRef = useRef(send);
    useEffect(() => {
        sendRef.current = send;
    });
    useEffect(() => {
        if (!released || !auto || !valid) return;
        if (attempted.current === `${signature}:${trimmed}`) return;
        const timer = setTimeout(() => void sendRef.current(), 0);
        return () => clearTimeout(timer);
    }, [released, auto, valid, trimmed, signature]);

    if (unavailable) return null;

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
                            : "Leave your address and they are sent the moment payment is confirmed on this page."}
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
                        // Before payment the address waits for confirmation;
                        // after it, only the button sends.
                        setAuto(!released);
                        remember({ address: event.target.value, auto: !released });
                        setState("idle");
                        setMessage("");
                    }}
                    placeholder="you@example.com"
                />
                {released && (
                    <button
                        type="submit"
                        className="secondary-button"
                        // Sent stays sent until the address changes: a second
                        // tap sent the same files twice (owner's inbox, 16
                        // September).
                        disabled={!valid || state === "sending" || state === "sent"}
                    >
                        {state === "sending"
                            ? "Sending…"
                            : state === "sent"
                              ? "Sent"
                              : state === "error"
                                ? "Try email again"
                                : "Email my files"}
                    </button>
                )}
            </div>
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
