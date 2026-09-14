"use client";

import { useEffect, useRef, useState } from "react";

/**
 * The test payment sheet (DEC-089).
 *
 * Opens where Razorpay's window would, on a machine running the engine's
 * payment simulator, so the whole checkout — paying, confirming, the delivered
 * screen — can be tried without a payment account. It is labelled as a test
 * on its first line and never looks like a real payment page: nothing is
 * charged, and the live site never shows it.
 */
export function SimulatedCheckout({
    amount,
    examName,
    onPay,
    onFail,
    onClose,
}: {
    amount: string;
    examName: string;
    onPay: () => Promise<void>;
    onFail: () => void;
    onClose: () => void;
}) {
    const ref = useRef<HTMLDialogElement>(null);
    const [paying, setPaying] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        const dialog = ref.current;
        if (!dialog || dialog.open) return;
        if (typeof dialog.showModal === "function") dialog.showModal();
        else dialog.setAttribute("open", "");
    }, []);

    const pay = async () => {
        setPaying(true);
        setError("");
        try {
            await onPay();
        } catch {
            setError("The test payment could not be settled. Is the engine running?");
            setPaying(false);
        }
    };

    return (
        <dialog
            ref={ref}
            className="euk-simpay"
            aria-labelledby="simpay-title"
            onCancel={(event) => {
                event.preventDefault();
                onClose();
            }}
        >
            <p className="euk-simpay-flag">Test payment · nothing is charged</p>
            <h2 id="simpay-title" className="euk-simpay-title">
                {amount}
            </h2>
            <p className="euk-simpay-for">ExamUploadKit · {examName}</p>
            <p className="euk-simpay-note">
                This stands in for Razorpay on a test machine. The live site
                opens Razorpay here.
            </p>
            {error && (
                <p className="euk-simpay-error" role="alert">
                    {error}
                </p>
            )}
            <div className="euk-simpay-actions">
                <button type="button" className="primary-button" disabled={paying} onClick={() => void pay()}>
                    {paying ? "Paying…" : `Pay ${amount}`}
                </button>
                <button type="button" className="secondary-button" disabled={paying} onClick={onFail}>
                    Simulate a failed payment
                </button>
                <button type="button" className="quiet-link" disabled={paying} onClick={onClose}>
                    Close without paying
                </button>
            </div>
        </dialog>
    );
}
