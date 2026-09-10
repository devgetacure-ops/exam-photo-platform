"use client";
import { useState } from "react";

export function RequestForm({
    kind,
    initialExam = "",
}: {
    kind: "exam" | "support";
    initialExam?: string;
}) {
    const [state, setState] = useState<"idle" | "sending" | "done" | "error">(
        "idle",
    );
    const [message, setMessage] = useState("");
    return (
        <form
            className="request-form"
            onSubmit={async (event) => {
                event.preventDefault();
                const data = new FormData(event.currentTarget);
                setState("sending");
                setMessage("");
                try {
                    const response = await fetch("/api/requests", {
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
                    const receipt = await response.json();
                    if (!response.ok)
                        throw new Error(
                            receipt.error ?? "Your request could not be saved.",
                        );
                    setState("done");
                    setMessage(
                        `Your request is saved. Reference: ${receipt.reference}. Keep this reference for follow-up.`,
                    );
                } catch (error) {
                    setState("error");
                    setMessage(
                        error instanceof Error
                            ? error.message
                            : "Please try again.",
                    );
                }
            }}
        >
            <label htmlFor="request-exam">
                {kind === "exam"
                    ? "Exam name"
                    : "Exam or order reference (optional)"}
            </label>
            <input
                id="request-exam"
                name="exam"
                defaultValue={initialExam}
                required={kind === "exam"}
                maxLength={200}
                placeholder="For example, your exam name and year"
            />
            <label htmlFor="request-email">Your email address</label>
            <input
                id="request-email"
                name="email"
                type="email"
                autoComplete="email"
                required
                maxLength={254}
                placeholder="you@example.com"
            />
            <label htmlFor="request-message">
                {kind === "exam"
                    ? "Official link or details (optional)"
                    : "How can we help?"}
            </label>
            <textarea
                id="request-message"
                name="message"
                required={kind === "support"}
                maxLength={3000}
                rows={5}
                placeholder={
                    kind === "exam"
                        ? "A link to the notification helps us research the right rules."
                        : "Tell us what happened. Please do not include photographs, passwords, Aadhaar numbers or card details."
                }
            />
            <div className="request-trap" aria-hidden="true">
                <label>
                    Leave blank
                    <input name="website" tabIndex={-1} autoComplete="off" />
                </label>
            </div>
            <label className="review-ack">
                <input name="consent" type="checkbox" required />
                <span>
                    {kind === "exam"
                        ? "Use these details to review my exam request and contact me about its availability."
                        : "Use these details to review and respond to my request."}
                </span>
            </label>
            <button
                className="primary-button"
                type="submit"
                disabled={state === "sending" || state === "done"}
            >
                {state === "sending"
                    ? "Saving your request…"
                    : state === "done"
                      ? "Request saved"
                      : kind === "exam"
                        ? "Request this exam ↗"
                        : "Send my request ↗"}
            </button>
            {message && (
                <p
                    role={state === "error" ? "alert" : "status"}
                    className="form-message"
                >
                    {message}
                </p>
            )}
        </form>
    );
}
