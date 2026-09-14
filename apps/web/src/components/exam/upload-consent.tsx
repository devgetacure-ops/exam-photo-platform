"use client";

import { type ReactNode, useState, useSyncExternalStore } from "react";

import { giveTermsConsent, readTermsAccepted, subscribeConsent } from "../../lib/consent";

/**
 * The one agreement asked above an upload, before the first file (DEC-086,
 * amended 2026-09-14): the terms and the privacy policy, both linked. Once
 * ticked it is remembered in this browser, so the box does not show again.
 */

const UNKNOWN = "unknown";

export interface UploadConsent {
    ready: boolean;
    /** Ask before a file is taken: false, with the box flagged, when it may not be. */
    allow: () => boolean;
    panel: ReactNode;
}

export function useUploadConsent(): UploadConsent {
    // The server cannot know what this browser agreed to, so it renders no
    // box; the browser decides once it can read its storage.
    const snapshot = useSyncExternalStore(
        subscribeConsent,
        () => (readTermsAccepted() ? "1" : "0"),
        () => UNKNOWN,
    );
    const known = snapshot !== UNKNOWN;
    const accepted = snapshot === "1";

    // Shown once it is known to be missing, and kept on screen while the
    // candidate ticks, so the box never disappears under their finger.
    const [asked, setAsked] = useState(false);
    const [nudge, setNudge] = useState(false);
    if (known && !accepted && !asked) setAsked(true);

    const allow = () => {
        if (accepted) return true;
        setAsked(true);
        setNudge(true);
        return false;
    };

    const panel =
        asked && known ? (
            <div className="euk-upload-consent" data-nudge={(nudge && !accepted) || undefined}>
                <label className="euk-consent">
                    <input
                        type="checkbox"
                        checked={accepted}
                        onChange={(event) => giveTermsConsent(event.target.checked)}
                    />
                    <span>
                        I have read and agree to the{" "}
                        <a href="/terms" target="_blank" rel="noreferrer">
                            terms and conditions
                        </a>{" "}
                        and the{" "}
                        <a href="/privacy" target="_blank" rel="noreferrer">
                            privacy policy
                        </a>
                        .
                    </span>
                </label>
                {nudge && !accepted && (
                    <p className="euk-upload-consent-nudge" role="alert">
                        Tick this first, then add your file.
                    </p>
                )}
            </div>
        ) : null;

    return { ready: accepted, allow, panel };
}
