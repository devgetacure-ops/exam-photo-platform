"use client";
import { useId, useRef, useState } from "react";

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
    const [position, setPosition] = useState(50);
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
                            : "Prepared watermarked preview"
                    }
                    draggable={false}
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
                                : "Your original upload"
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
                        {illustration ? "The starting point" : "Original"}
                    </span>
                    <span>{illustration ? "The possibility" : "Preview"}</span>
                </div>
                <input
                    id={id}
                    className="comparison-range"
                    type="range"
                    min="0"
                    max="100"
                    value={position}
                    onChange={(e) => setPosition(Number(e.target.value))}
                    aria-label="Compare original and prepared preview"
                    aria-valuetext={`${position}% original visible`}
                />
            </div>
            <figcaption>
                <label htmlFor={id}>Drag across the picture, or use the arrow keys</label>
                <div className="comparison-actions">
                    <button type="button" onClick={() => setPosition(100)}>
                        Original
                    </button>
                    <button type="button" onClick={() => setPosition(0)}>
                        Preview
                    </button>
                </div>
                <span>
                    {illustration
                        ? "Illustration only · not an engine result"
                        : "Watermarked preview · your download is the full, unmarked file"}
                </span>
            </figcaption>
        </figure>
    );
}
