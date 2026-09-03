import Image from "next/image";

/**
 * What a good one looks like, and what the common wrong ones look like.
 *
 * Real photographs, not diagrams. A candidate is judging their own photo
 * against a standard, and an abstract head-in-a-box cannot tell them whether
 * *theirs* is cropped too tight. Every wrong example is derived from the same
 * source frame by `scripts/generate_guidance_examples.py`, so the framing is
 * the only thing that differs between them.
 *
 * The source is public domain and licence-tracked in `tests/fixtures/`. No
 * candidate photograph is ever used (AGENTS.md).
 */

interface Example {
  src: string;
  label: string;
  good?: boolean;
}

const PHOTO: Example[] = [
  { src: "/examples/photo-good.jpg", label: "Like this", good: true },
  { src: "/examples/photo-too-far.jpg", label: "Too far away" },
  { src: "/examples/photo-too-tight.jpg", label: "Cropped too tight" },
  { src: "/examples/photo-blurred.jpg", label: "Blurred" },
  { src: "/examples/photo-too-dark.jpg", label: "Too dark" },
  { src: "/examples/photo-shadow.jpg", label: "Shadow on the face" },
];

const SIGNATURE: Example[] = [
  { src: "/examples/signature-good.jpg", label: "Like this", good: true },
  { src: "/examples/signature-clipped.jpg", label: "Running off the paper" },
];

const BY_TYPE: Record<string, Example[]> = {
  photograph: PHOTO,
  signature: SIGNATURE,
  // A thumb impression and a declaration are photographed sheets: the
  // signature pair teaches the same lesson (keep the whole mark inside the
  // frame), and inventing separate examples we have no source for would be
  // decoration rather than guidance.
  thumb_impression: SIGNATURE,
  handwritten_declaration: SIGNATURE,
};

export function ExampleStrip({ requirementType }: { requirementType: string }) {
  const examples = BY_TYPE[requirementType];
  if (!examples) return null;

  const isPhoto = requirementType === "photograph";

  return (
    <div className="mt-5">
      <p className="label mb-2">What works, and what gets sent back</p>
      <div className="flex flex-wrap gap-2">
        {examples.map((example) => (
          <figure key={example.src} className="shrink-0">
            <div
              className={`overflow-hidden rounded-md border-2 ${
                example.good ? "border-ready" : "border-line"
              }`}
            >
              <Image
                src={example.src}
                alt={example.label}
                width={isPhoto ? 240 : 420}
                height={isPhoto ? 300 : 170}
                className={isPhoto ? "h-28 w-auto" : "h-28 w-auto bg-white"}
                unoptimized
              />
            </div>
            <figcaption
              className={`mt-1 text-center text-xs ${
                example.good ? "text-ready" : "text-muted"
              }`}
            >
              {example.label}
            </figcaption>
          </figure>
        ))}
      </div>
    </div>
  );
}
