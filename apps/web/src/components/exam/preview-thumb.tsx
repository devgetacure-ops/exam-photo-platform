"use client";

import { useEffect, useRef, useState } from "react";
import { BILLING_ENABLED } from "../../billing/config";

/**
 * A prepared file's watermarked preview, small in the review, larger on a tap
 * (testing note 7). The pop-up is a modal dialog, centred, closed by its
 * button, Escape, or a tap outside the picture.
 */
export function PreviewThumb({ src, name }: { src: string; name: string }) {
    const [open, setOpen] = useState(false);
    const ref = useRef<HTMLDialogElement>(null);

    useEffect(() => {
        const dialog = ref.current;
        if (!dialog) return;
        if (open && !dialog.open) {
            if (typeof dialog.showModal === "function") dialog.showModal();
            else dialog.setAttribute("open", "");
        } else if (!open && dialog.open) {
            if (typeof dialog.close === "function") dialog.close();
            else dialog.removeAttribute("open");
        }
    }, [open]);

    return (
        <>
            <button
                type="button"
                className="euk-order-thumb"
                onClick={() => setOpen(true)}
                aria-label={`See the ${name} preview larger`}
            >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={src} alt="" draggable={false} />
            </button>
            <dialog
                ref={ref}
                className="euk-order-zoom"
                aria-label={`${name} preview`}
                onClose={() => setOpen(false)}
                onCancel={() => setOpen(false)}
                onClick={(event) => {
                    if (event.target === event.currentTarget) setOpen(false);
                }}
            >
                {open && (
                    <>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                            src={src}
                            alt={BILLING_ENABLED ? `${name}, watermarked preview` : `${name}, preview`}
                            draggable={false}
                        />
                        <p className="euk-order-zoom-note">
                            {BILLING_ENABLED
                                ? "Watermarked preview. Your download is the full, unmarked file."
                                : "Preview. Your download is the full-size file."}
                        </p>
                        <button
                            type="button"
                            className="secondary-button"
                            onClick={() => setOpen(false)}
                        >
                            Close
                        </button>
                    </>
                )}
            </dialog>
        </>
    );
}
