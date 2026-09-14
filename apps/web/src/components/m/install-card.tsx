"use client";

import { useEffect, useState, useSyncExternalStore, type CSSProperties } from "react";

import {
    INSTALL_MOMENT,
    INSTALL_READY,
    installMode,
    promptInstall,
    recentlyDismissed,
    rememberDismissal,
    type InstallMode,
} from "../../lib/install";

/**
 * The invitation to put the site on the home screen, and the menu's way to do
 * it at any time. The rules are in `lib/install.ts`; this is what a candidate
 * sees of them.
 *
 * The card is not a dialog. It rises from the foot of the screen above any
 * bottom bar, after a useful moment, and waits there; it never moves by itself
 * after arriving and never covers the action the candidate came for.
 */

function subscribe(onChange: () => void): () => void {
    window.addEventListener(INSTALL_READY, onChange);
    window.addEventListener("appinstalled", onChange);
    return () => {
        window.removeEventListener(INSTALL_READY, onChange);
        window.removeEventListener("appinstalled", onChange);
    };
}

function useInstallMode(): InstallMode {
    return useSyncExternalStore(subscribe, installMode, () => null);
}

function ShareIcon() {
    return (
        <svg width="16" height="19" viewBox="0 0 16 19" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M8 12 V1 M4 5 L8 1 L12 5" />
            <path d="M5 8 H2 V18 H14 V8 H11" />
        </svg>
    );
}

export function InstallCard() {
    const mode = useInstallMode();
    const [shown, setShown] = useState(false);
    const [offset, setOffset] = useState(0);

    useEffect(() => {
        const onMoment = () => {
            if (recentlyDismissed() || installMode() === null) return;
            // Above the bottom bar, where one is showing, so the action the
            // candidate came for is never covered.
            const bar = document.querySelector<HTMLElement>(".euk-actionbar");
            setOffset(bar ? bar.offsetHeight : 0);
            setShown(true);
        };
        window.addEventListener(INSTALL_MOMENT, onMoment);
        return () => window.removeEventListener(INSTALL_MOMENT, onMoment);
    }, []);

    if (!shown || mode === null) return null;

    const notNow = () => {
        rememberDismissal();
        setShown(false);
    };

    return (
        <div
            className="euk euk-m-only euk-install"
            style={{ "--install-offset": `${offset}px` } as CSSProperties}
        >
            <aside className="euk-install-card" aria-labelledby="install-title" aria-live="polite">
                <p id="install-title" className="euk-install-title">
                    Keep ExamUploadKit on your home screen
                </p>
                {mode === "prompt" ? (
                    <>
                        <p className="euk-install-body">
                            Back to your files, and to your next examination, in one
                            tap. It opens like an app, with nothing to download from a
                            store.
                        </p>
                        <div className="euk-install-actions">
                            <button
                                type="button"
                                className="primary-button"
                                onClick={async () => {
                                    const outcome = await promptInstall();
                                    if (outcome !== "accepted") rememberDismissal();
                                    setShown(false);
                                }}
                            >
                                Add to home screen
                            </button>
                            <button type="button" className="euk-install-later" onClick={notNow}>
                                Not now
                            </button>
                        </div>
                    </>
                ) : (
                    <>
                        <p className="euk-install-body">
                            Tap <ShareIcon /> <strong>Share</strong>, then{" "}
                            <strong>Add to Home Screen</strong>. It opens like an app,
                            with nothing to download from a store.
                        </p>
                        <div className="euk-install-actions">
                            <button type="button" className="euk-install-later" onClick={notNow}>
                                Got it
                            </button>
                        </div>
                    </>
                )}
                <p className="euk-install-note">It still needs the internet, as the site does.</p>
            </aside>
        </div>
    );
}

/** In the phone's menu: install at any time, where installing can work. */
export function InstallMenuItem() {
    const mode = useInstallMode();
    const [steps, setSteps] = useState(false);

    if (mode === null) return null;

    return (
        <div className="euk-mmenu-install">
            {mode === "prompt" ? (
                <button type="button" className="secondary-button" onClick={() => void promptInstall()}>
                    Install the app
                </button>
            ) : (
                <>
                    <button
                        type="button"
                        className="secondary-button"
                        aria-expanded={steps}
                        onClick={() => setSteps((value) => !value)}
                    >
                        Install the app
                    </button>
                    {steps && (
                        <p>
                            Tap <ShareIcon /> <strong>Share</strong>, then{" "}
                            <strong>Add to Home Screen</strong>.
                        </p>
                    )}
                </>
            )}
        </div>
    );
}
