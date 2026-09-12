"use client";

import { useEffect, useRef } from "react";

/**
 * A bottom sheet, for everything a candidate needs to see without losing the
 * screen they are on: this file's rules, the specimens, a source, the price
 * breakdown.
 *
 * Built on `<dialog>` rather than a div, so the browser gives us the modal
 * behaviour for free and gets it right: focus moves in and is trapped, Escape
 * closes, the page behind is inert, and the backdrop is a real ::backdrop.
 * A tap on the backdrop closes it, because on a phone that is what everybody
 * tries first.
 */
export function Sheet({
    open,
    title,
    onClose,
    children,
}: {
    open: boolean;
    title: string;
    onClose: () => void;
    children: React.ReactNode;
}) {
    const ref = useRef<HTMLDialogElement>(null);

    useEffect(() => {
        const el = ref.current;
        if (!el) return;
        // iOS 15.0–15.3 shipped <dialog> without the modal methods. There it
        // opens as a plain element: no focus trap and no backdrop, but the
        // content is reachable, which beats a button that does nothing.
        if (open && !el.open) {
            if (typeof el.showModal === "function") el.showModal();
            else el.setAttribute("open", "");
        }
        if (!open && el.open) {
            if (typeof el.close === "function") el.close();
            else el.removeAttribute("open");
        }
    }, [open]);

    return (
        <dialog
            ref={ref}
            className="euk-sheet"
            aria-label={title}
            onClose={onClose}
            onCancel={onClose}
            onClick={(event) => {
                // The backdrop's clicks land on the dialog itself.
                if (event.target === ref.current) onClose();
            }}
        >
            <div className="euk-sheet-grip" aria-hidden="true" />
            <div className="euk-sheet-head">
                <h2>{title}</h2>
                <button
                    type="button"
                    className="euk-sheet-close"
                    onClick={onClose}
                    aria-label="Close"
                >
                    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
                        <path d="M2 2 L13 13 M13 2 L2 13" />
                    </svg>
                </button>
            </div>
            <div className="euk-sheet-body">{children}</div>
        </dialog>
    );
}
