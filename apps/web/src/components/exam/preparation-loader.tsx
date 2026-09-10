"use client";
import { useEffect, useState } from "react";
import {
    journeyRequest,
    type PreparationProgress,
} from "../../lib/journey-client";

export function PreparationLoader({
    sourceUrl,
    progressToken,
}: {
    sourceUrl?: string | null;
    progressToken?: string;
}) {
    const [seconds, setSeconds] = useState(0);
    const [progress, setProgress] = useState<PreparationProgress | null>(null);
    useEffect(() => {
        if (!progressToken) return;
        const controller = new AbortController();
        let timer: ReturnType<typeof setTimeout>;
        let errors = 0;
        async function poll() {
            try {
                const state = await journeyRequest<PreparationProgress>(
                    `/v1/progress/${encodeURIComponent(progressToken!)}`,
                    undefined,
                    AbortSignal.any([
                        controller.signal,
                        AbortSignal.timeout(5000),
                    ]),
                );
                if (controller.signal.aborted) return;
                setProgress(state);
                errors = 0;
                if (state.finished) return;
            } catch {
                if (controller.signal.aborted) return;
                errors++;
                setProgress(null);
            }
            timer = setTimeout(
                () => void poll(),
                Math.min(1000 * (errors + 1), 5000),
            );
        }
        timer = setTimeout(() => void poll(), 500);
        return () => {
            controller.abort();
            clearTimeout(timer);
        };
    }, [progressToken]);
    useEffect(() => {
        const timer = setInterval(() => setSeconds((s) => s + 1), 1000);
        return () => clearInterval(timer);
    }, []);
    return (
        <div className="preparation-loader">
            {sourceUrl && (
                <>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                        className="preparation-source"
                        src={sourceUrl}
                        alt="Your original upload while preparation is in progress"
                    />
                </>
            )}
            <div className="loader-heading" role="status">
                <span className="progress-spinner" aria-hidden="true" />
                <strong>
                    {progress?.failed
                        ? "Preparation interrupted"
                        : progress?.label || "Preparing your file…"}
                </strong>
            </div>
            <p>
                We’re preparing it to your exam’s specifications. Keep this page
                open.
            </p>
            {progress && !progress.failed && (
                <div className="live-progress">
                    <progress
                        aria-label="File preparation"
                        max={1}
                        value={Math.max(
                            0,
                            Math.min(
                                progress.fraction,
                                progress.finished ? 1 : 0.99,
                            ),
                        )}
                    />
                    <span>
                        {Math.round(
                            Math.max(
                                0,
                                Math.min(
                                    progress.fraction,
                                    progress.finished ? 1 : 0.99,
                                ),
                            ) * 100,
                        )}
                        %
                    </span>
                </div>
            )}
            <p>
                Photographs usually take around 10 seconds; a cold start can
                take longer. Your preview appears when the file is ready.
            </p>
            <span className="elapsed">{seconds}s elapsed</span>
            {seconds >= 25 && (
                <p role="status">
                    This is taking a little longer. Your request is still in
                    progress. If the connection fails, we’ll show a retry
                    option.
                </p>
            )}
        </div>
    );
}
