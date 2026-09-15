"use client";

import { useEffect, useRef, useState } from "react";

import { formatBytes } from "../../lib/spec-format";
import {
    MAX_SOURCE_BYTES,
    PRESET_KB,
    canvasEncoder,
    compressToSize,
    compressedFilename,
} from "../../lib/compress-to-size";

/**
 * Compress a photograph to a size, in the candidate's own browser (DEC-096).
 *
 * The limit first, because it is the one thing the candidate already knows
 * from their form; then the photograph; then a JPEG just under the limit to
 * download. Nothing is uploaded, which is why it is free.
 */

interface Result {
    url: string;
    bytes: number;
    width: number;
    height: number;
    filename: string;
    targetKb: number;
}

type Failure =
    | { kind: "not-image" }
    | { kind: "too-large"; bytes: number }
    | { kind: "unreadable" }
    | { kind: "too-small"; targetKb: number };

function failureText(failure: Failure): string {
    switch (failure.kind) {
        case "not-image":
            return "That file isn’t a photo. Choose a JPEG, PNG or WebP.";
        case "too-large":
            return `That file is ${formatBytes(failure.bytes)}. Choose one under 25 MB.`;
        case "unreadable":
            return "This photo couldn’t be opened in your browser. If it is an iPhone HEIC photo, save it as a JPEG first, then choose it again.";
        case "too-small":
            return `Even at the smallest usable size this photo stays above ${failure.targetKb} KB. Choose a larger size.`;
    }
}

export function CompressImage() {
    const [targetKb, setTargetKb] = useState<number>(50);
    const [custom, setCustom] = useState("");
    const [status, setStatus] = useState<"idle" | "working" | "done" | "failed">("idle");
    const [result, setResult] = useState<Result | null>(null);
    const [failure, setFailure] = useState<Failure | null>(null);
    const [file, setFile] = useState<File | null>(null);
    const input = useRef<HTMLInputElement>(null);
    const url = useRef<string | null>(null);

    useEffect(
        () => () => {
            if (url.current) URL.revokeObjectURL(url.current);
        },
        [],
    );

    function fail(next: Failure) {
        setFailure(next);
        setResult(null);
        setStatus("failed");
    }

    async function run(source: File, kb: number) {
        const looksLikeImage =
            source.type.startsWith("image/") || /\.(jpe?g|png|webp|heic|heif)$/i.test(source.name);
        if (!looksLikeImage) return fail({ kind: "not-image" });
        if (source.size > MAX_SOURCE_BYTES) return fail({ kind: "too-large", bytes: source.size });

        setFile(source);
        setFailure(null);
        setStatus("working");

        let encoder: Awaited<ReturnType<typeof canvasEncoder>>;
        try {
            encoder = await canvasEncoder(source);
        } catch {
            return fail({ kind: "unreadable" });
        }
        try {
            const outcome = await compressToSize(encoder.width, encoder.height, kb, encoder.encode);
            if (!outcome.ok) return fail({ kind: "too-small", targetKb: kb });
            if (url.current) URL.revokeObjectURL(url.current);
            url.current = URL.createObjectURL(outcome.result.blob);
            setResult({
                url: url.current,
                bytes: outcome.result.blob.size,
                width: outcome.result.width,
                height: outcome.result.height,
                filename: compressedFilename(source.name, kb),
                targetKb: kb,
            });
            setStatus("done");
        } catch {
            fail({ kind: "unreadable" });
        } finally {
            encoder.close();
        }
    }

    function choose(kb: number) {
        setTargetKb(kb);
        setCustom("");
    }

    const working = status === "working";
    const stale = file !== null && result !== null && result.targetKb !== targetKb;

    return (
        <div className="euk-cmp-form">
            <fieldset className="euk-cmp-limit">
                <legend className="euk-cmp-label">1. Your form&rsquo;s limit</legend>
                <ul className="euk-cmp-sizes">
                    {PRESET_KB.map((kb) => (
                        <li key={kb}>
                            <button
                                type="button"
                                className="euk-cmp-size"
                                aria-pressed={targetKb === kb && custom === ""}
                                onClick={() => choose(kb)}
                                disabled={working}
                            >
                                {kb} KB
                            </button>
                        </li>
                    ))}
                </ul>
                <label className="euk-cmp-custom">
                    <span>Or another size</span>
                    <input
                        type="number"
                        inputMode="numeric"
                        min={1}
                        max={5000}
                        value={custom}
                        placeholder="KB"
                        disabled={working}
                        onChange={(event) => {
                            setCustom(event.target.value);
                            const kb = Math.round(Number(event.target.value));
                            if (kb >= 1 && kb <= 5000) setTargetKb(kb);
                        }}
                    />
                    <span aria-hidden="true">KB</span>
                </label>
            </fieldset>

            <p className="euk-cmp-label euk-cmp-step">2. Your photo</p>
            <button
                type="button"
                className="primary-button euk-cmp-choose"
                onClick={() => input.current?.click()}
                disabled={working}
            >
                {file ? "Choose another photo" : "Choose a photo"}
            </button>
            <input
                ref={input}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
                className="sr-only"
                aria-label="Photo to compress"
                onChange={(event) => {
                    const next = event.target.files?.[0];
                    if (next) void run(next, targetKb);
                    event.target.value = "";
                }}
            />
            <p className="euk-cmp-privacy">It stays on this device. Nothing is uploaded.</p>

            <p role="status" className="euk-cmp-status">
                {working
                    ? `Compressing to under ${targetKb} KB…`
                    : result
                      ? `${formatBytes(result.bytes)}, under ${result.targetKb} KB · ${result.width} × ${result.height} px · JPEG`
                      : ""}
            </p>
            {failure && (
                <p role="alert" className="euk-cmp-error">
                    {failureText(failure)}
                </p>
            )}

            {result && (
                <div className="euk-cmp-result">
                    {/* eslint-disable-next-line @next/next/no-img-element -- a local object URL, never optimised */}
                    <img className="euk-cmp-preview" src={result.url} alt="Your compressed photo" />
                    <a className="primary-button euk-cmp-download" href={result.url} download={result.filename}>
                        Download {result.filename}
                    </a>
                </div>
            )}
            {stale && file && (
                <button
                    type="button"
                    className="euk-cmp-again"
                    onClick={() => void run(file, targetKb)}
                    disabled={working}
                >
                    Compress again to under {targetKb} KB
                </button>
            )}
        </div>
    );
}
