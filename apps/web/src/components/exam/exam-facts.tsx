"use client";
import { useEffect, useState } from "react";

export interface ExamFact {
    kind: string;
    text: string;
    source: string;
}

/**
 * Worth knowing: the examination's own facts, one at a time, pinned beside
 * its name.
 *
 * Every line is the source's wording, never paraphrased, with the source one
 * tap away. Nothing here restates a measurement the page already prints — the
 * filtering happens where the facts are read.
 *
 * It moves on by itself, which is what was asked for, and it stops the moment
 * it is being read: hovering it, tabbing into it, a reduced-motion preference,
 * or the pause control all hold it where it is. Auto-advancing text without a
 * way to stop it fails WCAG 2.2.2, so the control is not optional.
 */
const KIND: Record<string, string> = {
    rejection: "What gets applications rejected",
    deliverables: "What it asks for",
    file_size: "File size",
    format: "Format",
    dimensions: "Dimensions",
    capture: "On the portal",
    appearance: "Appearance",
};

function Arrow({ back = false }: { back?: boolean }) {
    return (
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d={back ? "M12.5 4 L 6.5 10 L 12.5 16" : "M7.5 4 L 13.5 10 L 7.5 16"} />
        </svg>
    );
}

export function ExamFacts({
    facts,
    examName,
}: {
    facts: ExamFact[];
    examName: string;
}) {
    const [index, setIndex] = useState(0);
    const [playing, setPlaying] = useState(true);
    const [hovering, setHovering] = useState(false);
    useEffect(() => {
        if (
            !playing ||
            hovering ||
            facts.length < 2 ||
            (typeof matchMedia === "function" &&
                matchMedia("(prefers-reduced-motion: reduce)").matches)
        )
            return;
        const timer = setInterval(
            () => setIndex((value) => (value + 1) % facts.length),
            9000,
        );
        return () => clearInterval(timer);
    }, [playing, hovering, facts.length]);
    if (!facts.length) return null;
    const fact = facts[index % facts.length];
    const url = fact.source.match(/https?:\/\/[^\s)]+/)?.[0];
    return (
        <aside
            className="euk-tip"
            aria-label={`Worth knowing about ${examName}`}
            onMouseEnter={() => setHovering(true)}
            onMouseLeave={() => setHovering(false)}
            onFocusCapture={() => setHovering(true)}
            onBlurCapture={(event) => {
                if (!event.currentTarget.contains(event.relatedTarget))
                    setHovering(false);
            }}
        >
            <svg className="euk-tip-pin" viewBox="0 0 30 38" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" aria-hidden="true">
                <circle cx="15" cy="11" r="8" fill="currentColor" />
                <path d="M15 19 V 36" />
            </svg>
            <h2 className="euk-tip-title">Worth knowing</h2>
            <div
                aria-live={playing ? "off" : "polite"}
                aria-atomic="true"
                className="euk-tip-body"
            >
                <p className="euk-tip-kind">{KIND[fact.kind] ?? "From the notice"}</p>
                <p key={index} className="euk-tip-text">
                    {fact.text}
                </p>
            </div>
            <div className="euk-tip-foot">
                {url ? (
                    <a className="euk-tip-source" href={url} target="_blank" rel="noreferrer">
                        Read it in the source ↗
                    </a>
                ) : (
                    <details className="euk-tip-source-details">
                        <summary>Where this comes from</summary>
                        <p>{fact.source}</p>
                    </details>
                )}
                {facts.length > 1 && (
                    <div className="euk-tip-controls">
                        <button
                            type="button"
                            aria-label="Previous exam fact"
                            onClick={() =>
                                setIndex((index + facts.length - 1) % facts.length)
                            }
                        >
                            <Arrow back />
                        </button>
                        <span className="euk-tip-count">
                            {index + 1} of {facts.length}
                        </span>
                        <button
                            type="button"
                            aria-label="Next exam fact"
                            onClick={() => setIndex((index + 1) % facts.length)}
                        >
                            <Arrow />
                        </button>
                        <button
                            type="button"
                            className="euk-tip-play"
                            aria-pressed={playing}
                            onClick={() => setPlaying(!playing)}
                        >
                            {playing ? "Pause" : "Play"}
                        </button>
                    </div>
                )}
            </div>
        </aside>
    );
}
