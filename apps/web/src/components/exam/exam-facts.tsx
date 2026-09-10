"use client";
import { useEffect, useState } from "react";

export interface ExamFact {
    kind: string;
    text: string;
    source: string;
}

export function ExamFacts({
    facts,
    examName,
}: {
    facts: ExamFact[];
    examName: string;
}) {
    const [index, setIndex] = useState(0);
    const [playing, setPlaying] = useState(false);
    const [hovering, setHovering] = useState(false);
    useEffect(() => {
        if (
            !playing ||
            hovering ||
            facts.length < 2 ||
            matchMedia("(prefers-reduced-motion: reduce)").matches
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
            className="exam-facts"
            aria-label={`Useful details for ${examName}`}
            onMouseEnter={() => setHovering(true)}
            onMouseLeave={() => setHovering(false)}
            onFocusCapture={() => setHovering(true)}
            onBlurCapture={(event) => {
                if (!event.currentTarget.contains(event.relatedTarget))
                    setHovering(false);
            }}
        >
            <div className="facts-heading">
                <h2>Worth knowing before you upload.</h2>
                <span>From this exam’s sources</span>
            </div>
            <div
                aria-live={playing ? "off" : "polite"}
                aria-atomic="true"
                className="fact-body"
            >
                <p>{fact.text}</p>
            </div>
            <div className="facts-footer">
                <details>
                    <summary>Read the source</summary>
                    <p>{fact.source}</p>
                    {url && (
                        <a href={url} target="_blank" rel="noreferrer">
                            Open source ↗
                        </a>
                    )}
                </details>
                {facts.length > 1 && (
                    <div className="fact-controls">
                        <button
                            type="button"
                            aria-label="Previous exam fact"
                            onClick={() =>
                                setIndex(
                                    (index + facts.length - 1) % facts.length,
                                )
                            }
                        >
                            ←
                        </button>
                        <span>
                            {index + 1} / {facts.length}
                        </span>
                        <button
                            type="button"
                            aria-label="Next exam fact"
                            onClick={() => setIndex((index + 1) % facts.length)}
                        >
                            →
                        </button>
                        <button
                            type="button"
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
