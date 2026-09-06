"use client";
import { useId, useRef, useState } from "react";

export function ReportIssue({
    examName,
    requirementName = "General",
    ruleId = "",
}: {
    examName: string;
    requirementName?: string;
    ruleId?: string;
}) {
    const uniqueId = useId();
    const dialog = useRef<HTMLDialogElement>(null);
    const [text, setText] = useState("");
    const [status, setStatus] = useState("");
    const address = process.env.NEXT_PUBLIC_CORRECTIONS_EMAIL;
    const body = `Exam: ${examName}\nRequirement: ${requirementName}\nRule: ${ruleId}\n\n${text}`;
    return (
        <>
            <button
                className="quiet-link"
                type="button"
                onClick={() => dialog.current?.showModal()}
            >
                Report an issue
            </button>
            <dialog
                ref={dialog}
                className="ui-dialog"
                aria-labelledby={`report-${uniqueId}`}
            >
                <form
                    onSubmit={async (e) => {
                        e.preventDefault();
                        if (address) {
                            window.location.href = `mailto:${address}?subject=${encodeURIComponent(`Rule correction: ${examName}`)}&body=${encodeURIComponent(body)}`;
                            setStatus(
                                "Your email app will open with the report. Send it there to complete your report.",
                            );
                        } else {
                            try {
                                await navigator.clipboard.writeText(body);
                                setStatus(
                                    "Report copied. Reporting is not connected yet; nothing has been sent.",
                                );
                            } catch {
                                setStatus(
                                    "Copy the report text manually. Reporting is not connected yet; nothing has been sent.",
                                );
                            }
                        }
                    }}
                >
                    <div className="dialog-heading">
                        <h2 id={`report-${uniqueId}`}>Help us get it right.</h2>
                        <button
                            className="text-button"
                            type="button"
                            onClick={() => dialog.current?.close()}
                        >
                            Close
                        </button>
                    </div>
                    <p>
                        {examName} · {requirementName}
                    </p>
                    <label htmlFor={`issue-${uniqueId}`}>
                        What needs correcting?
                    </label>
                    <textarea
                        id={`issue-${uniqueId}`}
                        required
                        minLength={8}
                        rows={5}
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Tell us which rule looks wrong. Include the official source link if you have it."
                    />
                    <p className="small-copy">
                        Please don’t include personal details or application
                        documents.
                    </p>
                    <button className="primary-button" type="submit">
                        {address ? "Open email with report" : "Copy report"}
                    </button>
                    <p role="status" className="small-copy">
                        {status}
                    </p>
                </form>
            </dialog>
        </>
    );
}
