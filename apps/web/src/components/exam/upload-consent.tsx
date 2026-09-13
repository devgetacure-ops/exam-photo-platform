"use client";

import { type ReactNode, useState, useSyncExternalStore } from "react";

import {
    consentNeeds,
    consentReady,
    giveConsent,
    readConsent,
    subscribeConsent,
    type ConsentNeeds,
    type ConsentState,
} from "../../lib/consent";

/**
 * The agreements asked for above an upload, before the first file (DEC-086).
 *
 * Only what the law needs, and nothing else written into the flow: one tick
 * for the terms and the privacy policy with both pages linked, a parent's or
 * guardian's where the candidate can be under 18, and one for a thumb
 * impression. Once ticked they are remembered in this browser, so the boxes
 * do not show again for the next file.
 */

const UNKNOWN = "unknown";

function snapshot(examId: string): string {
    const state = readConsent(examId);
    return `${Number(state.terms)}${Number(state.guardian)}${Number(state.thumb)}`;
}

function parse(value: string): ConsentState | null {
    if (value === UNKNOWN) return null;
    return { terms: value[0] === "1", guardian: value[1] === "1", thumb: value[2] === "1" };
}

export interface UploadConsent {
    ready: boolean;
    /** Ask before a file is taken: false, with the boxes flagged, when it may not be. */
    allow: () => boolean;
    panel: ReactNode;
}

export function useUploadConsent(examId: string, requirementType: string): UploadConsent {
    const needs = consentNeeds(examId, requirementType);
    // The server cannot know what this browser agreed to, so it renders no
    // boxes; the browser decides once it can read its storage.
    const state = parse(useSyncExternalStore(subscribeConsent, () => snapshot(examId), () => UNKNOWN));
    const ready = state !== null && consentReady(state, needs);

    // Shown once something is known to be missing, and kept on screen while
    // the candidate ticks, so a box never disappears under their finger.
    const [asked, setAsked] = useState(false);
    const [nudge, setNudge] = useState(false);
    if (state !== null && !ready && !asked) setAsked(true);

    const allow = () => {
        if (ready) return true;
        setAsked(true);
        setNudge(true);
        return false;
    };

    const panel =
        asked && state ? (
            <ConsentPanel examId={examId} needs={needs} state={state} nudge={nudge && !ready} />
        ) : null;

    return { ready, allow, panel };
}

function ConsentPanel({
    examId,
    needs,
    state,
    nudge,
}: {
    examId: string;
    needs: ConsentNeeds;
    state: ConsentState;
    nudge: boolean;
}) {
    const missing =
        Number(!state.terms) +
        Number(Boolean(needs.guardian) && !state.guardian) +
        Number(needs.thumb && !state.thumb);

    return (
        <div className="euk-upload-consent" data-nudge={nudge || undefined}>
            <label className="euk-consent">
                <input
                    type="checkbox"
                    checked={state.terms}
                    onChange={(event) => giveConsent(examId, "terms", event.target.checked)}
                />
                <span>
                    I have read the{" "}
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

            {needs.guardian && (
                <label className="euk-consent">
                    <input
                        type="checkbox"
                        checked={state.guardian}
                        onChange={(event) => giveConsent(examId, "guardian", event.target.checked)}
                    />
                    <span>
                        {needs.guardian === "child"
                            ? "I am the candidate’s parent or guardian, or they are with me and agree to these files being prepared."
                            : "I am 18 or older, or my parent or guardian agrees to these files being prepared."}
                    </span>
                </label>
            )}

            {needs.thumb && (
                <label className="euk-consent">
                    <input
                        type="checkbox"
                        checked={state.thumb}
                        onChange={(event) => giveConsent(examId, "thumb", event.target.checked)}
                    />
                    <span>
                        I agree to the thumb impression being used only to prepare
                        this file.
                    </span>
                </label>
            )}

            {nudge && (
                <p className="euk-upload-consent-nudge" role="alert">
                    Tick {missing === 1 ? "this" : "these"} first, then add your file.
                </p>
            )}
        </div>
    );
}
