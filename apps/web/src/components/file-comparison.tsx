"use client";
import { useId, useRef, useState } from "react";
import { BILLING_ENABLED } from "../billing/config";
import { useTr } from "./locale-context";

/**
 * The upload beside its prepared preview, compared by dragging anywhere on the
 * picture (testing note 6).
 *
 * The old version put an unstyled range input under the picture, so only a
 * thin strip at its top ever took a drag. Now the frame itself follows the
 * pointer: a horizontal drag moves the divider, a vertical one still scrolls
 * the page (`touch-action: pan-y`), and the range input stays for the
 * keyboard, visually hidden but focusable.
 */
export function FileComparison({
    before,
    after,
    illustration = false,
}: {
    before: string;
    after: string;
    illustration?: boolean;
}) {
    const tr = useTr();
    const [position, setPosition] = useState(50);
    // A 150 x 200 photograph drawn three times its size looks soft, and was
    // read as a poor result (owner's testing, 1 October). Said plainly when
    // the preview is being shown well above the file's own size.
    const [enlarged, setEnlarged] = useState<{ width: number; height: number } | null>(null);
    const frameRef = useRef<HTMLDivElement>(null);
    const id = useId();

    const follow = (clientX: number) => {
        const frame = frameRef.current;
        if (!frame) return;
        const box = frame.getBoundingClientRect();
        if (box.width <= 0) return;
        const pct = ((clientX - box.left) / box.width) * 100;
        setPosition(Math.round(Math.min(100, Math.max(0, pct))));
    };

    return (
        <figure
            className={`file-comparison ${illustration ? "illustrated-comparison" : ""}`}
        >
            <div
                ref={frameRef}
                className="comparison-images"
                data-testid="comparison-frame"
                onPointerDown={(event) => {
                    event.currentTarget.setPointerCapture?.(event.pointerId);
                    follow(event.clientX);
                }}
                onPointerMove={(event) => {
                    const frame = event.currentTarget;
                    if (frame.hasPointerCapture && !frame.hasPointerCapture(event.pointerId)) return;
                    follow(event.clientX);
                }}
            >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                    src={after}
                    alt={
                        illustration
                            ? "Illustrated file preparation example"
                            : BILLING_ENABLED
                              ? "Prepared watermarked preview"
                              : tr("Prepared file preview", "तैयार फ़ाइल का प्रीव्यू")
                    }
                    draggable={false}
                    onLoad={(event) => {
                        const image = event.currentTarget;
                        const shown = image.getBoundingClientRect().width;
                        setEnlarged(
                            !illustration && image.naturalWidth > 0 && shown > image.naturalWidth * 1.5
                                ? { width: image.naturalWidth, height: image.naturalHeight }
                                : null,
                        );
                    }}
                />
                <div
                    className="comparison-before"
                    style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }}
                >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                        src={before}
                        alt={
                            illustration
                                ? "Illustration with simulated poor exposure"
                                : tr("Your original upload", "आपकी असली अपलोड")
                        }
                        draggable={false}
                    />
                </div>
                <span
                    className="comparison-divider"
                    style={{ left: `${position}%` }}
                    aria-hidden="true"
                >
                    <span className="comparison-handle">↔</span>
                </span>
                <div className="comparison-labels" aria-hidden="true">
                    <span>
                        {illustration ? "The starting point" : tr("Original", "असली")}
                    </span>
                    <span>{illustration ? "The possibility" : tr("Preview", "प्रीव्यू")}</span>
                </div>
                <input
                    id={id}
                    className="comparison-range"
                    type="range"
                    min="0"
                    max="100"
                    value={position}
                    onChange={(e) => setPosition(Number(e.target.value))}
                    aria-label={tr("Compare original and prepared preview", "असली और तैयार फ़ाइल की तुलना करें")}
                    aria-valuetext={tr(`${position}% original visible`, `${position}% असली दिख रही है`)}
                />
            </div>
            <figcaption>
                <label htmlFor={id}>{tr("Drag across the picture, or use the arrow keys", "तस्वीर पर खींचें, या तीर वाली कुंजियाँ दबाएँ")}</label>
                {/* Two buttons that look like buttons, the one in view marked:
                    as plain words nobody knew they could be tapped (owner's
                    testing, 1 October). */}
                <div className="comparison-actions" role="group" aria-label={tr("Show", "दिखाएँ")}>
                    <button
                        type="button"
                        aria-pressed={position >= 50}
                        onClick={() => setPosition(100)}
                    >
                        {tr("Original", "असली")}
                    </button>
                    <button
                        type="button"
                        aria-pressed={position < 50}
                        onClick={() => setPosition(0)}
                    >
                        {tr("Preview", "प्रीव्यू")}
                    </button>
                </div>
                <span>
                    {illustration
                        ? "Illustration only · not an engine result"
                        : BILLING_ENABLED
                          ? "Watermarked preview · your download is the full, unmarked file"
                          : tr("Preview · your download is the full-size file", "प्रीव्यू · डाउनलोड में पूरी साइज़ की फ़ाइल मिलेगी")}
                </span>
                {enlarged && (
                    <span>
                        {tr(
                            `Shown enlarged. The file is ${enlarged.width} × ${enlarged.height} px, the size this examination asks for, so it looks softer here than it is.`,
                            `बड़ा करके दिखाया गया है। फ़ाइल ${enlarged.width} × ${enlarged.height} px की है, जितनी यह परीक्षा माँगती है, इसलिए यहाँ थोड़ी धुंधली लगती है।`,
                        )}
                    </span>
                )}
            </figcaption>
        </figure>
    );
}
