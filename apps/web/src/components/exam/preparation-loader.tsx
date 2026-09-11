"use client";
import { useEffect, useState } from "react";
import {
    journeyRequest,
    type PreparationProgress,
} from "../../lib/journey-client";
import { FileTypeDrawing } from "../euk/doodles";

/**
 * The wait, made visible.
 *
 * The candidate's own photograph sits in the frame, blurred and grey, and
 * sharpens and takes its colour back as the work completes; the frame's edge
 * fills with the same fraction; the steps tick as the engine reports them.
 * Every one of those is driven by the engine's real progress (DEC-075), never
 * by a timer. When progress cannot be read, the frame says so honestly: the
 * photograph stays blurred and the edge circles instead of filling.
 */

const PHOTO_STEPS: { stages: string[]; text: string }[] = [
    {
        stages: ["input_normalization", "suitability_evaluation"],
        text: "Opening it and checking it can be used",
    },
    { stages: ["face_detection", "head_estimation"], text: "Finding your face" },
    {
        stages: ["subject_segmentation", "mask_refinement", "foreground_decontamination"],
        text: "Separating you from the background",
    },
    {
        stages: ["crop_selection", "crop_planning", "background_composition", "portrait_composition"],
        text: "Framing you and laying the background",
    },
    {
        stages: ["output_preparation", "output_compression"],
        text: "Sizing and compressing to the rules",
    },
    {
        stages: ["final_decode_validation", "final_rule_validation", "filename_generation"],
        text: "Checking every rule again",
    },
];

export function PreparationLoader({
    sourceUrl,
    progressToken,
    requirementType,
}: {
    sourceUrl?: string | null;
    progressToken?: string;
    requirementType?: string;
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

    const fraction =
        progress && !progress.failed
            ? Math.max(0, Math.min(progress.fraction, progress.finished ? 1 : 0.99))
            : null;
    const indeterminate = fraction === null;
    const photo = requirementType === "photograph";
    const completed = progress?.completed_stages ?? [];
    const latest = PHOTO_STEPS.reduce(
        (found, step, i) =>
            step.stages.some((stage) => completed.includes(stage)) ? i : found,
        -1,
    );
    const done = (i: number) =>
        !!progress?.finished ||
        i < latest ||
        (i === latest &&
            PHOTO_STEPS[i].stages.every((stage) => completed.includes(stage)));
    const current = PHOTO_STEPS.findIndex((_, i) => !done(i));

    return (
        <div className="euk-prep" data-indeterminate={indeterminate}>
            <div className="euk-prep-frame">
                {sourceUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                        className="euk-prep-source"
                        src={sourceUrl}
                        alt="Your original upload while preparation is in progress"
                        style={
                            indeterminate
                                ? undefined
                                : {
                                      filter: `blur(${((1 - fraction) * 9).toFixed(1)}px) grayscale(${(1 - fraction).toFixed(2)})`,
                                  }
                        }
                    />
                ) : (
                    <FileTypeDrawing
                        type={requirementType ?? "certificate_scan"}
                        className="euk-prep-art"
                    />
                )}
                <span className="euk-prep-scan" aria-hidden="true" />
                <svg
                    className="euk-prep-ring"
                    viewBox="0 0 100 125"
                    preserveAspectRatio="none"
                    aria-hidden="true"
                >
                    <rect
                        x="1"
                        y="1"
                        width="98"
                        height="123"
                        pathLength={1}
                        style={indeterminate ? undefined : { strokeDashoffset: 1 - fraction }}
                    />
                </svg>
            </div>

            <div className="min-w-0">
                <p className="euk-prep-label" role="status">
                    {progress?.failed
                        ? "Preparation interrupted"
                        : progress?.label || "Preparing your file…"}
                </p>
                {!indeterminate && (
                    <p className="euk-prep-pct" aria-hidden="true">
                        {Math.round(fraction * 100)}
                        <span>%</span>
                    </p>
                )}
                {progress && !progress.failed && (
                    <progress
                        className="sr-only"
                        aria-label="File preparation"
                        max={1}
                        value={fraction ?? 0}
                    />
                )}
                {photo && (
                    <ol className="euk-prep-steps">
                        {PHOTO_STEPS.map((step, i) => (
                            <li
                                key={step.text}
                                data-state={done(i) ? "done" : i === current ? "now" : "later"}
                            >
                                <svg className="euk-prep-box" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                                    <rect x="1.5" y="1.5" width="15" height="15" />
                                    <path d="M5 9.2 L 7.8 12 L 13 6" pathLength={1} />
                                </svg>
                                <span>{step.text}</span>
                            </li>
                        ))}
                    </ol>
                )}
                <p className="euk-prep-note">
                    We’re preparing it to your exam’s specifications. Keep this
                    page open.{" "}
                    {photo
                        ? "Photographs usually take around 10 seconds; a cold start can take longer."
                        : "This usually takes a few seconds."}{" "}
                    Your preview appears when the file is ready.
                </p>
                <span className="euk-prep-elapsed">{seconds}s elapsed</span>
                {seconds >= 25 && (
                    <p className="euk-prep-note" role="status">
                        This is taking a little longer. Your request is still in
                        progress. If the connection fails, we’ll show a retry
                        option.
                    </p>
                )}
            </div>
        </div>
    );
}
