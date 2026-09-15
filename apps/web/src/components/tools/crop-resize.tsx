"use client";

import { useEffect, useRef, useState } from "react";

import { formatBytes } from "../../lib/spec-format";
import { MAX_SOURCE_BYTES, compressAtSize, type Encoder } from "../../lib/compress-to-size";
import { MAX_ZOOM, centreOf, frameRect, resizedFilename, type Rect } from "../../lib/crop-frame";

/**
 * A photograph at an exact published pixel size (DEC-098), in the browser.
 *
 * The frame has the published shape, so the result is never stretched; the
 * candidate moves the photograph under it with a finger or the arrow keys and
 * zooms with the slider. The engine's automatic framing, background and
 * naming stay on the examination pages; this is the free, manual way to the
 * size itself.
 */

interface Loaded {
    bitmap: ImageBitmap;
    name: string;
}

/** The framed part of the photograph, drawn at any size and saved as a JPEG on white. */
function frameEncoder(bitmap: ImageBitmap, rect: Rect): { encode: Encoder; release: () => void } {
    const canvas = document.createElement("canvas");
    return {
        encode: async (outWidth, outHeight, quality) => {
            canvas.width = outWidth;
            canvas.height = outHeight;
            const context = canvas.getContext("2d");
            if (!context) throw new Error("No canvas context");
            context.fillStyle = "#ffffff";
            context.fillRect(0, 0, outWidth, outHeight);
            context.imageSmoothingQuality = "high";
            context.drawImage(bitmap, rect.x, rect.y, rect.w, rect.h, 0, 0, outWidth, outHeight);
            const blob = await new Promise<Blob | null>((resolve) =>
                canvas.toBlob(resolve, "image/jpeg", quality),
            );
            if (!blob) throw new Error("Could not encode the photo");
            return blob;
        },
        release: () => {
            canvas.width = 0;
            canvas.height = 0;
        },
    };
}

interface Result {
    url: string;
    bytes: number;
    filename: string;
}

export function CropResize({
    width,
    height,
    noun = "photo",
}: {
    width: number;
    height: number;
    noun?: string;
}) {
    const aspect = width / height;
    const [loaded, setLoaded] = useState<Loaded | null>(null);
    const [zoom, setZoom] = useState(1);
    const [centre, setCentre] = useState({ x: 0, y: 0 });
    const [kb, setKb] = useState("");
    const [working, setWorking] = useState(false);
    const [result, setResult] = useState<Result | null>(null);
    const [error, setError] = useState<string | null>(null);
    const input = useRef<HTMLInputElement>(null);
    const view = useRef<HTMLCanvasElement>(null);
    const drag = useRef<{ id: number; x: number; y: number } | null>(null);
    const url = useRef<string | null>(null);

    useEffect(
        () => () => {
            if (url.current) URL.revokeObjectURL(url.current);
            loaded?.bitmap.close();
        },
        [loaded],
    );

    const rect: Rect | null = loaded
        ? frameRect(loaded.bitmap.width, loaded.bitmap.height, aspect, zoom, centre.x, centre.y)
        : null;

    useEffect(() => {
        const canvas = view.current;
        if (!canvas || !loaded || !rect) return;
        const scale = window.devicePixelRatio || 1;
        canvas.width = Math.round(canvas.clientWidth * scale);
        canvas.height = Math.round((canvas.clientWidth / aspect) * scale);
        const context = canvas.getContext("2d");
        if (!context) return;
        context.imageSmoothingQuality = "high";
        context.drawImage(loaded.bitmap, rect.x, rect.y, rect.w, rect.h, 0, 0, canvas.width, canvas.height);
    }, [loaded, rect, aspect]);

    async function open(file: File) {
        setError(null);
        setResult(null);
        if (file.size > MAX_SOURCE_BYTES) {
            setError(`That file is ${formatBytes(file.size)}. Choose one under 25 MB.`);
            return;
        }
        try {
            const bitmap = await createImageBitmap(file);
            setLoaded({ bitmap, name: file.name });
            setZoom(1);
            setCentre({ x: bitmap.width / 2, y: bitmap.height / 2 });
        } catch {
            setError(
                "This photo couldn’t be opened in your browser. If it is an iPhone HEIC photo, save it as a JPEG first, then choose it again.",
            );
        }
    }

    function move(dxDisplay: number, dyDisplay: number) {
        const canvas = view.current;
        if (!rect || !canvas || canvas.clientWidth === 0) return;
        // A finger moving right drags the photograph right, so the frame's
        // centre moves left over it; frameRect keeps it inside the photograph.
        const perPixel = rect.w / canvas.clientWidth;
        const here = centreOf(rect);
        const moved = frameRect(
            loaded!.bitmap.width,
            loaded!.bitmap.height,
            aspect,
            zoom,
            here.x - dxDisplay * perPixel,
            here.y - dyDisplay * perPixel,
        );
        setCentre(centreOf(moved));
        setResult(null);
    }

    async function save() {
        if (!loaded || !rect) return;
        setWorking(true);
        setError(null);
        const { encode, release } = frameEncoder(loaded.bitmap, rect);
        try {
            const limit = Math.round(Number(kb));
            let blob: Blob;
            if (limit >= 1) {
                const outcome = await compressAtSize(width, height, limit, encode);
                if (!outcome.ok) {
                    setError(`At ${width} × ${height} px this ${noun} stays above ${limit} KB. Choose a larger limit.`);
                    return;
                }
                blob = outcome.result.blob;
            } else {
                blob = await encode(width, height, 0.92);
            }
            if (url.current) URL.revokeObjectURL(url.current);
            url.current = URL.createObjectURL(blob);
            setResult({ url: url.current, bytes: blob.size, filename: resizedFilename(loaded.name, width, height) });
        } catch {
            setError(`The ${noun} couldn’t be saved. Try again.`);
        } finally {
            setWorking(false);
            release();
        }
    }

    return (
        <div className="euk-cmp-form">
            <p className="euk-cmp-label">1. Your {noun}</p>
            <button
                type="button"
                className="primary-button euk-cmp-choose"
                onClick={() => input.current?.click()}
                disabled={working}
            >
                {loaded ? `Choose another ${noun}` : `Choose a ${noun}`}
            </button>
            <input
                ref={input}
                type="file"
                // No HEIC, as in the compress tool: iPhone Safari then converts
                // the photo to JPEG itself.
                accept="image/jpeg,image/png,image/webp"
                className="sr-only"
                aria-label={`${noun} to resize`}
                onChange={(event) => {
                    const next = event.target.files?.[0];
                    if (next) void open(next);
                    event.target.value = "";
                }}
            />
            <p className="euk-cmp-privacy">It stays on this device. Nothing is uploaded.</p>
            {error && (
                <p role="alert" className="euk-cmp-error">
                    {error}
                </p>
            )}

            {loaded && (
                <>
                    <p className="euk-cmp-label euk-cmp-step">2. Place it in the frame</p>
                    <canvas
                        ref={view}
                        className="euk-crop-view"
                        style={{
                            aspectRatio: `${width} / ${height}`,
                            // Narrower for a tall frame, so it fits a phone's
                            // screen without its shape being squeezed.
                            maxWidth: `min(100%, 360px, calc(60vh * ${aspect.toFixed(4)}))`,
                        }}
                        tabIndex={0}
                        role="img"
                        aria-label={`The part of your ${noun} that will be kept, ${width} by ${height} pixels. Drag, or use the arrow keys, to move it.`}
                        onPointerDown={(event) => {
                            event.currentTarget.setPointerCapture(event.pointerId);
                            drag.current = { id: event.pointerId, x: event.clientX, y: event.clientY };
                        }}
                        onPointerMove={(event) => {
                            const last = drag.current;
                            if (!last || last.id !== event.pointerId) return;
                            move(event.clientX - last.x, event.clientY - last.y);
                            drag.current = { id: event.pointerId, x: event.clientX, y: event.clientY };
                        }}
                        onPointerUp={() => {
                            drag.current = null;
                        }}
                        onPointerCancel={() => {
                            drag.current = null;
                        }}
                        onKeyDown={(event) => {
                            const step = 12;
                            const keys: Record<string, [number, number]> = {
                                ArrowLeft: [step, 0],
                                ArrowRight: [-step, 0],
                                ArrowUp: [0, step],
                                ArrowDown: [0, -step],
                            };
                            const delta = keys[event.key];
                            if (!delta) return;
                            event.preventDefault();
                            move(delta[0], delta[1]);
                        }}
                    />
                    <label className="euk-crop-zoom">
                        <span>Zoom</span>
                        <input
                            type="range"
                            min={1}
                            max={MAX_ZOOM}
                            step={0.01}
                            value={zoom}
                            onChange={(event) => {
                                setZoom(Number(event.target.value));
                                setResult(null);
                            }}
                        />
                    </label>

                    <p className="euk-cmp-label euk-cmp-step">3. Size limit, if your form has one</p>
                    <label className="euk-cmp-custom">
                        <span>Keep it under</span>
                        <input
                            type="number"
                            inputMode="numeric"
                            min={1}
                            max={5000}
                            value={kb}
                            placeholder="KB"
                            onChange={(event) => {
                                setKb(event.target.value);
                                setResult(null);
                            }}
                        />
                        <span aria-hidden="true">KB</span>
                    </label>

                    <button
                        type="button"
                        className="primary-button euk-cmp-choose"
                        onClick={() => void save()}
                        disabled={working}
                    >
                        {working ? "Saving…" : `Make it ${width} × ${height} px`}
                    </button>
                </>
            )}

            <p role="status" className="euk-cmp-status">
                {result ? `${formatBytes(result.bytes)} · ${width} × ${height} px · JPEG` : ""}
            </p>
            {result && (
                <div className="euk-cmp-result">
                    {/* eslint-disable-next-line @next/next/no-img-element -- a local object URL, never optimised */}
                    <img className="euk-cmp-preview" src={result.url} alt={`Your ${noun} at ${width} by ${height} pixels`} />
                    <a className="primary-button euk-cmp-download" href={result.url} download={result.filename}>
                        Download {result.filename}
                    </a>
                </div>
            )}
        </div>
    );
}
