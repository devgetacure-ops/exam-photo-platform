"use client";
import { useId, useState } from "react";

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
    const id = useId();
    return (
        <figure
            className={`file-comparison ${illustration ? "illustrated-comparison" : ""}`}
        >
            <div className="comparison-images">
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
                    <span>↔</span>
                </span>
                <div className="comparison-labels" aria-hidden="true">
                    <span>
                        {illustration ? "The starting point" : "Original"}
                    </span>
                    <span>{illustration ? "The possibility" : "Preview"}</span>
                </div>
                <input
                    id={id}
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
                <label htmlFor={id}>Drag or use arrow keys to compare</label>
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
                        : "Reduced-resolution, watermarked preview · clean file after payment"}
                </span>
            </figcaption>
        </figure>
    );
}
