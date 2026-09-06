"use client";
import Image from "next/image";
import { useState } from "react";

const photoExamples = [
    {
        src: "/examples/portrait-studio.png",
        title: "Clear, even lighting",
        detail: "Face the camera with your whole head visible. Check your exam’s appearance rules alongside.",
        good: true,
    },
    {
        src: "/examples/portrait-blurred.jpg",
        title: "Blurred photo",
        detail: "Blur can hide facial detail. A sharper source gives a better result.",
        good: false,
    },
    {
        src: "/examples/portrait-looking-away.jpg",
        title: "Looking away",
        detail: "Face the camera directly unless your exam’s official instructions say otherwise.",
        good: false,
    },
];
export function VisualGuide({ type }: { type: string }) {
    const [index, setIndex] = useState(0);
    const photo = type === "photograph";
    const examples = photo
        ? photoExamples
        : type === "signature"
          ? [
                {
                    src: "/examples/signature-good.jpg",
                    title: "Keep the full signature visible",
                    detail: "Use the pen colour and signing instructions your exam specifies.",
                    good: true,
                },
                {
                    src: "/examples/signature-clipped.jpg",
                    title: "Don’t cut off the strokes",
                    detail: "Leave a little paper around every edge of your signature.",
                    good: false,
                },
            ]
          : type === "thumb_impression"
            ? [
                  {
                      src: "/examples/thumb-guide.png",
                      title: "A clear, complete impression",
                      detail: "Keep the whole mark visible. Use the thumb and ink colour specified by your exam.",
                      good: true,
                  },
              ]
            : [
                  {
                      src: "/examples/declaration-guide.png",
                      title: "Keep the entire page visible",
                      detail: "This is an example of framing only. Use your own document and your exam’s exact instructions.",
                      good: true,
                  },
              ];
    const current = examples[index] ?? examples[0];
    return (
        <section
            className={`visual-guide ${photo ? "portrait-guide" : "paper-guide"}`}
            aria-label="Visual upload guidance"
        >
            <div className="example-caption">
                {current.good ? <span className="example-good">{photo ? "Good lighting" : "Good example"}</span> : <button type="button" className="example-caution" onClick={() => setIndex(0)}>Back to the good example</button>}
                <span>
                    Visual guide · {index + 1}/{examples.length}
                </span>
            </div>
            <figure>
                <Image
                    width={600}
                    height={600}
                    src={current.src}
                    alt={current.title}
                    className="guide-image"
                    loading={photo && index === 0 ? "eager" : "lazy"}
                />
                <figcaption>
                    <strong>{current.title}</strong>
                    <p>{current.detail}</p>
                </figcaption>
            </figure>
            {photo && <p className="avoid-heading">Avoid these</p>}
            {examples.length > 1 && (
                <div
                    className="example-thumbnails"
                    aria-label="Choose a guidance example"
                >
                    {examples.map((item, i) => (
                        <button
                            key={item.src}
                            type="button"
                            aria-pressed={i === index}
                            onClick={() => setIndex(i)}
                        >
                            <Image
                                width={120}
                                height={90}
                                src={item.src}
                                alt=""
                            />
                            <span>
                                {i === 0
                                    ? photo
                                        ? "Good lighting"
                                        : "Full signature"
                                    : item.title}
                            </span>
                        </button>
                    ))}
                </div>
            )}
            <p className="example-disclaimer">
                Guidance example. Your exam’s rules determine acceptance.
            </p>
        </section>
    );
}
