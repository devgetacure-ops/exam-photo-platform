"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";

/**
 * The request slip, shared by the missing-examination page and support.
 *
 * It is drawn as the one form on the site a candidate fills in for us rather
 * than for their examination, and it has four designed states, because each
 * is a moment a candidate is deciding whether we can be trusted: filling it
 * in, waiting on it, a failure that keeps every answer they typed, and a
 * receipt that shows exactly what was saved and under which reference.
 *
 * Nothing is reported as saved until the server returns a reference for it.
 */
type Kind = "exam" | "support";
type State = "idle" | "sending" | "error" | "done";

interface Receipt {
    reference: string;
    exam: string;
    email: string;
}

interface Failure {
    title: string;
    body: string;
}

const COPY = {
    exam: {
        bar: "Request for an examination",
        examLabel: "The examination",
        examHint: "As its notice writes it. Add the year if you know it.",
        examPlaceholder: "Its full name",
        messageLabel: "A link to its official notice",
        messageHint: "Optional. It saves us a search.",
        messagePlaceholder: "https://",
        consent:
            "Keep my email to tell me when this examination is ready, and delete it after 30 days either way.",
        submit: "Put it on the list",
        sending: "Putting it on the list",
        stamp: "On the list",
        doneTitle: ["Noted.", "Back to your preparation."],
        emailRow: "We’ll write to",
        doneNote:
            "Keep the reference. If you ever write to us about this request, it is how we find it.",
        again: "Request another examination",
    },
    support: {
        bar: "A message to support",
        examLabel: "Examination or order reference",
        examHint: "Optional. Either one helps us find what went wrong.",
        examPlaceholder: "For example, SSC CGL 2026",
        messageLabel: "What happened",
        messageHint:
            "Please don’t include photographs, passwords, Aadhaar numbers or card details.",
        messagePlaceholder: "Tell us what you expected and what you saw instead.",
        consent:
            "Use these details to look into my request and reply to me, and delete them after 30 days.",
        submit: "Send it",
        sending: "Sending",
        stamp: "Received",
        doneTitle: ["Received.", "We’ll reply by email."],
        emailRow: "We’ll reply to",
        doneNote:
            "Keep the reference. Quote it if you write again, so your messages stay together.",
        again: "Send another message",
    },
} as const;

const OFFLINE: Failure = {
    title: "We couldn’t reach our server.",
    body: "Check your connection and try again. Everything you typed is still here.",
};

const TIMEOUT: Failure = {
    title: "That took too long.",
    body: "Our server didn’t answer in time. Everything you typed is still here, so try again in a moment.",
};

function failureFor(status: number, message: string | undefined): Failure {
    if (status === 422) {
        return {
            title: "One detail needs another look.",
            body: message ?? "Check your email address and the tick box.",
        };
    }
    return {
        title: "That didn’t go through.",
        body:
            message ??
            "Something went wrong on our side. Everything you typed is still here, so try again in a minute.",
    };
}

function CrossBox() {
    return (
        <svg
            viewBox="0 0 22 22"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.4"
            strokeLinecap="round"
            aria-hidden="true"
        >
            <rect x="1.5" y="1.5" width="19" height="19" />
            <path d="M7 7 L15 15 M15 7 L7 15" />
        </svg>
    );
}

export function RequestForm({
    kind,
    initialExam = "",
    examCount,
}: {
    kind: Kind;
    initialExam?: string;
    /** When given, the receipt offers the directory by its real size. */
    examCount?: number;
}) {
    const copy = COPY[kind];
    const [state, setState] = useState<State>("idle");
    const [failure, setFailure] = useState<Failure | null>(null);
    const [receipt, setReceipt] = useState<Receipt | null>(null);
    const [copied, setCopied] = useState(false);
    // Bumped to remount the form empty for a second request.
    const [round, setRound] = useState(0);
    const errorRef = useRef<HTMLDivElement>(null);
    const doneRef = useRef<HTMLHeadingElement>(null);

    // Focus follows the outcome, so a screen reader or keyboard user lands on
    // what changed instead of on a button that no longer means anything.
    useEffect(() => {
        if (state === "error") errorRef.current?.focus();
        if (state === "done") doneRef.current?.focus();
    }, [state]);

    async function submit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (state === "sending") return;
        const data = new FormData(event.currentTarget);
        setState("sending");
        setFailure(null);

        let response: Response;
        try {
            response = await fetch("/api/requests", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    kind,
                    exam: data.get("exam"),
                    email: data.get("email"),
                    message: data.get("message"),
                    consent: data.get("consent") === "on",
                    website: data.get("website"),
                }),
                signal: AbortSignal.timeout(15000),
            });
        } catch (error) {
            setFailure(
                error instanceof DOMException && error.name === "TimeoutError"
                    ? TIMEOUT
                    : OFFLINE,
            );
            setState("error");
            return;
        }

        const body = (await response.json().catch(() => null)) as {
            reference?: string;
            error?: string;
        } | null;

        if (!response.ok || !body?.reference) {
            setFailure(failureFor(response.status, body?.error));
            setState("error");
            return;
        }

        setReceipt({
            reference: body.reference,
            exam: String(data.get("exam") ?? "").trim(),
            email: String(data.get("email") ?? "").trim(),
        });
        setState("done");
    }

    if (state === "done" && receipt) {
        return (
            <div className="euk-slip euk-slip--done">
                <p className="euk-slip-bar">{copy.bar}</p>
                <div className="euk-slip-body">
                    <p className="euk-slip-stamp" aria-hidden="true">
                        {copy.stamp}
                    </p>
                    <h2
                        ref={doneRef}
                        tabIndex={-1}
                        className="euk-display euk-receipt-title"
                    >
                        {copy.doneTitle[0]}
                        <br />
                        {copy.doneTitle[1]}
                    </h2>
                    <dl className="euk-receipt">
                        {receipt.exam && (
                            <div>
                                <dt>
                                    {kind === "exam"
                                        ? "Examination"
                                        : "About"}
                                </dt>
                                <dd>{receipt.exam}</dd>
                            </div>
                        )}
                        <div>
                            <dt>{copy.emailRow}</dt>
                            <dd>{receipt.email}</dd>
                        </div>
                        <div>
                            <dt>Reference</dt>
                            <dd className="euk-receipt-ref">
                                <span>{receipt.reference}</span>
                                <button
                                    type="button"
                                    className="euk-receipt-copy"
                                    onClick={async () => {
                                        try {
                                            await navigator.clipboard.writeText(
                                                receipt.reference,
                                            );
                                            setCopied(true);
                                            setTimeout(
                                                () => setCopied(false),
                                                1800,
                                            );
                                        } catch {
                                            /* The reference stays on screen to copy by hand. */
                                        }
                                    }}
                                >
                                    {copied ? "Copied" : "Copy"}
                                </button>
                            </dd>
                        </div>
                    </dl>
                    <p className="euk-slip-note">{copy.doneNote}</p>
                    <div className="euk-slip-actions">
                        <Link href="/exams" className="primary-button">
                            {examCount
                                ? `See the ${examCount} we prepare now`
                                : "See the examinations we prepare"}
                        </Link>
                        <button
                            type="button"
                            className="quiet-link"
                            onClick={() => {
                                setReceipt(null);
                                setState("idle");
                                setRound((n) => n + 1);
                            }}
                        >
                            {copy.again}
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    const sending = state === "sending";

    return (
        <form
            key={round}
            className="euk-slip"
            onSubmit={submit}
            aria-busy={sending}
        >
            <p className="euk-slip-bar">{copy.bar}</p>
            <div className="euk-slip-body">
                <div className="euk-field">
                    <label htmlFor="request-exam" className="euk-field-label">
                        {copy.examLabel}
                    </label>
                    <p id="request-exam-hint" className="euk-field-hint">
                        {copy.examHint}
                    </p>
                    <input
                        id="request-exam"
                        name="exam"
                        type="text"
                        defaultValue={round === 0 ? initialExam : ""}
                        required={kind === "exam"}
                        maxLength={200}
                        placeholder={copy.examPlaceholder}
                        aria-describedby="request-exam-hint"
                    />
                </div>

                <div className="euk-field">
                    <label htmlFor="request-email" className="euk-field-label">
                        Your email address
                    </label>
                    <input
                        id="request-email"
                        name="email"
                        type="email"
                        inputMode="email"
                        autoComplete="email"
                        required
                        maxLength={254}
                        placeholder="you@example.com"
                    />
                </div>

                <div className="euk-field">
                    <label
                        htmlFor="request-message"
                        className="euk-field-label"
                    >
                        {copy.messageLabel}
                    </label>
                    <p id="request-message-hint" className="euk-field-hint">
                        {copy.messageHint}
                    </p>
                    <textarea
                        id="request-message"
                        name="message"
                        required={kind === "support"}
                        maxLength={3000}
                        rows={kind === "exam" ? 2 : 5}
                        placeholder={copy.messagePlaceholder}
                        aria-describedby="request-message-hint"
                    />
                </div>

                <div className="request-trap" aria-hidden="true">
                    <label>
                        Leave blank
                        <input name="website" tabIndex={-1} autoComplete="off" />
                    </label>
                </div>

                <label className="euk-consent">
                    <input name="consent" type="checkbox" required />
                    <span>{copy.consent}</span>
                </label>

                {state === "error" && failure && (
                    <div
                        ref={errorRef}
                        tabIndex={-1}
                        role="alert"
                        className="euk-slip-error"
                    >
                        <CrossBox />
                        <p className="euk-slip-error-title">{failure.title}</p>
                        <p>{failure.body}</p>
                    </div>
                )}

                <button
                    className="primary-button euk-slip-submit"
                    type="submit"
                    aria-disabled={sending}
                >
                    {sending
                        ? `${copy.sending}…`
                        : state === "error"
                          ? "Try again"
                          : copy.submit}
                </button>
            </div>
        </form>
    );
}
