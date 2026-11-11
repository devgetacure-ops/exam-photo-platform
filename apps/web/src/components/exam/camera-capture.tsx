"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { useTr } from "../locale-context";

/**
 * The camera, inside the page (DEC-131).
 *
 * "Take a photo now" used to hand the phone its own camera app through a
 * `capture` file input. While that app is open Android often discards the
 * browser tab to free memory, so the page reloads on return and the photograph
 * never arrives (owner's testing, 11 November: "after taking photo, nothing is
 * being shown"). Here the page itself shows the camera, so it never leaves the
 * screen and nothing can be lost.
 *
 * Where the browser cannot do this (no `getUserMedia`, which also means any
 * plain-HTTP address) the caller keeps the old input; `inPageCameraAvailable`
 * says which. A refused permission offers the camera app from inside here.
 */

export function inPageCameraAvailable(): boolean {
    return (
        typeof window !== "undefined" &&
        window.isSecureContext !== false &&
        typeof navigator !== "undefined" &&
        typeof navigator.mediaDevices?.getUserMedia === "function"
    );
}

type State = "starting" | "live" | "taken" | "error";

export function CameraCapture({
    facing,
    onCapture,
    onClose,
    onUseCameraApp,
}: {
    /** "user" for a photograph of yourself, "environment" for paper. */
    facing: "user" | "environment";
    onCapture: (file: File) => void;
    onClose: () => void;
    /** Opens the phone's camera app instead; called from a tap. */
    onUseCameraApp: () => void;
}) {
    const tr = useTr();
    const video = useRef<HTMLVideoElement>(null);
    const stream = useRef<MediaStream | null>(null);
    const [state, setState] = useState<State>("starting");
    const [refused, setRefused] = useState(false);
    const [still, setStill] = useState<{ url: string; blob: Blob } | null>(null);
    const [mounted, setMounted] = useState(false);

    const stop = useCallback(() => {
        stream.current?.getTracks().forEach((track) => track.stop());
        stream.current = null;
    }, []);

    const start = useCallback(async () => {
        stop();
        setState("starting");
        try {
            const media = await navigator.mediaDevices.getUserMedia({
                audio: false,
                video: {
                    facingMode: facing,
                    width: { ideal: 1920 },
                    height: { ideal: 1920 },
                },
            });
            stream.current = media;
            if (video.current) {
                video.current.srcObject = media;
                await video.current.play().catch(() => undefined);
            }
            setState("live");
        } catch (error) {
            const name = error instanceof DOMException ? error.name : "";
            setRefused(name === "NotAllowedError" || name === "SecurityError");
            setState("error");
        }
    }, [facing, stop]);

    useEffect(() => {
        const begin = setTimeout(() => {
            setMounted(true);
            void start();
        }, 0);
        const scroll = document.body.style.overflow;
        document.body.style.overflow = "hidden";
        return () => {
            clearTimeout(begin);
            document.body.style.overflow = scroll;
            stop();
        };
    }, [start, stop]);

    useEffect(
        () => () => {
            if (still) URL.revokeObjectURL(still.url);
        },
        [still],
    );

    const take = () => {
        const element = video.current;
        if (!element || !element.videoWidth) return;
        const canvas = document.createElement("canvas");
        canvas.width = element.videoWidth;
        canvas.height = element.videoHeight;
        const context = canvas.getContext("2d");
        if (!context) return;
        // The picture as the camera saw it, never mirrored: the preview is
        // mirrored only so that moving left looks like moving left.
        context.drawImage(element, 0, 0);
        canvas.toBlob(
            (blob) => {
                if (!blob) return;
                stop();
                setStill({ url: URL.createObjectURL(blob), blob });
                setState("taken");
            },
            "image/jpeg",
            0.95,
        );
    };

    const retake = () => {
        setStill(null);
        void start();
    };

    const use = () => {
        if (!still) return;
        onCapture(new File([still.blob], "camera-photo.jpg", { type: "image/jpeg" }));
    };

    if (!mounted) return null;

    return createPortal(
        <div
            className="euk euk-camera"
            role="dialog"
            aria-modal="true"
            aria-label={tr("Camera", "कैमरा")}
            data-facing={facing}
        >
            <div className="euk-camera-stage">
                <video
                    ref={video}
                    className="euk-camera-video"
                    playsInline
                    muted
                    autoPlay
                    hidden={state === "taken" || state === "error"}
                />
                {still && state === "taken" && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img className="euk-camera-still" src={still.url} alt={tr("The photo you took", "आपकी खींची फ़ोटो")} />
                )}
                {facing === "user" && state === "live" && (
                    <div className="euk-camera-guide" aria-hidden="true" />
                )}
                {state === "starting" && (
                    <p className="euk-camera-note" role="status">
                        {tr("Opening the camera…", "कैमरा खुल रहा है…")}
                    </p>
                )}
                {state === "error" && (
                    <div className="euk-camera-note" role="alert">
                        <p>
                            {refused
                                ? tr(
                                      "The camera wasn’t allowed. Allow it for this site in your browser, or use your phone’s camera app.",
                                      "कैमरे की अनुमति नहीं मिली। ब्राउज़र में इस साइट को अनुमति दें, या फ़ोन का कैमरा ऐप इस्तेमाल करें।",
                                  )
                                : tr(
                                      "The camera couldn’t start here. Use your phone’s camera app instead.",
                                      "कैमरा यहाँ शुरू नहीं हो सका। फ़ोन का कैमरा ऐप इस्तेमाल करें।",
                                  )}
                        </p>
                        <button type="button" className="secondary-button" onClick={onUseCameraApp}>
                            {tr("Use the camera app", "कैमरा ऐप इस्तेमाल करें")}
                        </button>
                    </div>
                )}
            </div>
            {state === "live" && facing === "user" && (
                <p className="euk-camera-tip">
                    {tr(
                        "Face the light, look straight in, and fit your head inside the outline.",
                        "रोशनी की ओर मुँह करें, सीधे देखें, और सिर को घेरे के अंदर रखें।",
                    )}
                </p>
            )}
            <div className="euk-camera-actions" data-state={state}>
                {state === "taken" ? (
                    <>
                        <button type="button" className="secondary-button" onClick={retake}>
                            {tr("Retake", "फिर से खींचें")}
                        </button>
                        <button type="button" className="primary-button" onClick={use}>
                            {tr("Use this photo", "यही फ़ोटो लें")}
                        </button>
                    </>
                ) : (
                    <>
                        <button type="button" className="secondary-button" onClick={onClose}>
                            {tr("Cancel", "रद्द करें")}
                        </button>
                        {state !== "error" && (
                            <button
                                type="button"
                                className="euk-camera-shutter"
                                onClick={take}
                                disabled={state !== "live"}
                                aria-label={tr("Take the photo", "फ़ोटो खींचें")}
                            />
                        )}
                    </>
                )}
            </div>
        </div>,
        document.body,
    );
}
