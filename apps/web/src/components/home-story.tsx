import Link from "next/link";
import type { CSSProperties } from "react";
import { WipeDemo } from "./euk/wipe-demo";
import { Reveal } from "./euk/reveal";
import {
    CertificateDrawing,
    DeclarationDrawing,
    PhotoDrawing,
    SignatureDrawing,
    ThumbDrawing,
} from "./euk/doodles";
import {
    EstimateMark,
    ForgetsMark,
    NoPretenceMark,
    UntouchedMark,
} from "./euk/principle-marks";

/**
 * The long argument: what we do, how, the problem, why it exists, that it
 * is free, and the decisions behind it.
 *
 * On a desktop it follows the hero on the landing page. On a phone the home is
 * short and this lives at `/about`, one link away, because it is several
 * screens a candidate pays for in scroll and rarely reads before searching.
 * One component in both places, so the two cannot drift apart.
 *
 * It renders as a fragment, never inside a wrapper: `.euk-hero + .euk-section`
 * sets the seam under the hero and needs the sections to stay its siblings.
 */

const SSC_NOTICE = "https://ssc.nic.in/SSCFileServer/PortalManagement/UploadedFiles/notice_rhqladakh_23052022.pdf";

const KIT = [
    {
        name: "Photograph",
        Drawing: PhotoDrawing,
        body: "Cropped to your examination's frame, on a plain background, under the file limit. Your face is left alone.",
    },
    {
        name: "Signature",
        Drawing: SignatureDrawing,
        body: "The page cleared around your strokes and the ink made firm. Never stretched.",
    },
    {
        name: "Thumb impression",
        Drawing: ThumbDrawing,
        body: "Lighting evened and cropped close, never masked, so every ridge survives.",
    },
    {
        name: "Declaration",
        Drawing: DeclarationDrawing,
        body: "Your handwritten sheet straightened so it reads clearly. The page stays whole.",
    },
    {
        name: "Certificates and ID",
        Drawing: CertificateDrawing,
        body: "A scan turned into a clean PDF, or an existing PDF put in order.",
    },
];

const TOOL_TABS = ["resize", "remove bg", "compress", "convert", "rename"];

/**
 * Six frames, drawn as a measured sheet.
 *
 * Every box is given the same area rather than the same scale — at true scale a
 * 1200px square would swallow a 150×200 one and the row would say nothing. What
 * the row is for is the shape: no two examinations want the same one. The
 * figures on each box are the examination's own pixel dimensions, so the
 * proportions you see are real even though the sizes are not.
 */
const FRAMES = [
    { w: 112, h: 129, px: "200 × 230" },
    { w: 120, h: 120, px: "1200 × 1200" },
    { w: 104, h: 139, px: "150 × 200" },
    { w: 137, h: 105, px: "413 × 319" },
];

const FREE_TOOLS = [
    "Image to PDF",
    "PDF to image",
    "Merge PDFs",
    "Reorder pages",
    "Remove pages",
    "Rotate pages",
    "Compress to the size limit",
    "Named as the portal asks",
];

const ELSEWHERE = [
    "a background remover",
    "a resizer",
    "a compressor",
    "a format converter",
    "a renamer",
    "a PDF merger",
];

/**
 * Representational before-and-after pairs for the landing band.
 *
 * Generated people and invented signatures: no candidate's photograph or
 * signature appears anywhere on this site, and these particular pairs were
 * made to show the difference rather than produced by the engine. The band
 * says so under the frames.
 */
export const PHOTO_PAIRS = ["a1", "a2", "a3", "a4"].map((id) => ({
    id,
    before: `/examples/band/photo-${id}-uploaded.jpg`,
    after: `/examples/band/photo-${id}-prepared.jpg`,
    alt: "A photograph taken at home, and the same photograph prepared for an application",
}));

export const SIGNATURE_PAIRS = ["s1", "s2", "s3"].map((id) => ({
    id,
    before: `/examples/band/sign-${id}-uploaded.jpg`,
    after: `/examples/band/sign-${id}-prepared.jpg`,
    alt: "A signature photographed on paper, and the same signature prepared for an application",
}));

const PHOTO_CHECKS = [
    { label: "Background", before: "Your room, your wall", after: "Plain and even" },
    { label: "Light", before: "Warm, one side brighter", after: "Even across the face" },
    {
        label: "Framing",
        before: "Small and off to one side",
        after: "Centred, head at the size they ask for",
    },
    {
        label: "The file",
        before: "Whatever your phone saved",
        after: "The pixels, the KB and the name the form wants",
    },
];

const SIGNATURE_CHECKS = [
    {
        label: "Paper",
        before: "Table, shadow, taken at an angle",
        after: "Clean white, square to the page",
    },
    { label: "Ink", before: "Thin and patchy", after: "Firm and even" },
    { label: "Crop", before: "Lost in a big empty page", after: "Tight around the strokes" },
    {
        label: "The file",
        before: "Whatever your phone saved",
        after: "The pixels, the KB and the name the form wants",
    },
];

const PRINCIPLES = [
    {
        Mark: UntouchedMark,
        title: "It never changes your face.",
        body: "Exposure and contrast, yes. Whitening or reshaping, never.",
    },
    {
        Mark: EstimateMark,
        title: "It never guesses a rule.",
        body: "Where an examination didn't publish a number, ours is marked est.",
    },
    {
        Mark: NoPretenceMark,
        title: "It never pretends.",
        body: "When we can't prepare a file, the page says so, and there's no upload button.",
    },
    {
        Mark: ForgetsMark,
        title: "It forgets you.",
        body: "No account. Your files are deleted within 30 minutes, or within an hour if you ask.",
    },
];

export function HomeStory({ examCount }: { examCount: number }) {
    const steps = [
        {
            whose: "Yours",
            title: "Find your examination",
            body: `Search by name or short form. ${examCount} examinations are on file.`,
        },
        {
            whose: "Yours",
            title: "Keep what you need",
            body: "The full kit is already ticked. Untick what your form doesn't ask for.",
        },
        {
            whose: "Ours",
            title: "We prepare it",
            body: "Each file is made to your examination's own specification.",
        },
        {
            whose: "Yours",
            title: "Check the result",
            body: "See the prepared file before you download it.",
        },
        {
            whose: "Yours",
            title: "Download, free",
            body: "Download them or have them emailed. Deleted within 30 minutes, or an hour if you ask.",
        },
    ];

    return (
        <>
            {/* ---- what we do ------------------------------------------ */}
            <section className="euk-section" id="what">
                <div className="euk-wrap">
                    <Reveal>
                        <h2 className="euk-display euk-h2">
                            Everything the form
                            {" "}
                            <br />
                            asks you to attach.
                        </h2>
                        <p className="euk-lede">
                            An application is rarely one photograph. Every file has its own pixel size and limit, and we prepare all of them.
                        </p>
                    </Reveal>

                    <div className="euk-kit-grid">
                        {KIT.map(({ name, Drawing, body }, i) => (
                            <Reveal
                                key={name}
                                delay={i * 90}
                                className="euk-kit-card"
                            >
                                <Drawing className="euk-kit-drawing" />
                                <h3>{name}</h3>
                                <p>{body}</p>
                            </Reveal>
                        ))}
                    </div>

                    <WipeDemo
                        photos={PHOTO_PAIRS}
                        photoChecks={PHOTO_CHECKS}
                        signatures={SIGNATURE_PAIRS}
                        signatureChecks={SIGNATURE_CHECKS}
                    />
                </div>
            </section>

            {/* ---- how we do it ---------------------------------------- */}
            <section className="euk-section euk-section--alt" id="how">
                <div className="euk-wrap">
                    <Reveal>
                        <h2 className="euk-display euk-h2">
                            You choose. We prepare.
                            {" "}
                            <br />
                            You keep.
                        </h2>
                        <p className="euk-lede">
                            No account and nothing to install. You won&rsquo;t need to know what a kilobyte is.
                        </p>
                    </Reveal>
                    <ol className="euk-steps">
                        {steps.map((step, i) => (
                            <li
                                key={step.title}
                                className={`euk-step ${step.whose === "Ours" ? "euk-step--ours" : ""}`}
                            >
                                <Reveal delay={i * 110}>
                                    <h3>
                                        {step.title}{" "}
                                        <span className="euk-whose">
                                            {step.whose}
                                        </span>
                                    </h3>
                                    <p>{step.body}</p>
                                </Reveal>
                            </li>
                        ))}
                    </ol>
                </div>
            </section>

            {/* ---- the problem ----------------------------------------- */}
            <section className="euk-invert euk-section" id="problem">
                <div className="euk-wrap euk-problem">
                    <Reveal className="euk-problem-head">
                        <h2 className="euk-display euk-h2">
                            Six tabs. Four tools.
                            {" "}
                            <br />
                            And the photo is{" "}
                            <span className="euk-mark">still wrong.</span>
                        </h2>
                        <p className="euk-lede">
                            It was never your photograph. It was the
                            specification.
                        </p>
                    </Reveal>
                    <div className="euk-problem-body">
                        <Reveal className="euk-browser">
                            <div className="euk-browser-bar">
                                <ul className="euk-browser-tabs">
                                    {TOOL_TABS.map((t, i) => (
                                        <li
                                            key={t}
                                            className="euk-browser-tab"
                                            style={{
                                                transitionDelay: `${i * 90 + 200}ms`,
                                            }}
                                        >
                                            <span
                                                className="euk-browser-fav"
                                                aria-hidden="true"
                                            />
                                            <span className="euk-browser-label">
                                                {t}
                                            </span>
                                            <span
                                                className="euk-browser-x"
                                                aria-hidden="true"
                                            >
                                                ×
                                            </span>
                                        </li>
                                    ))}
                                    <li
                                        className="euk-browser-tab euk-browser-tab--live"
                                        style={{ transitionDelay: "720ms" }}
                                    >
                                        <span
                                            className="euk-browser-fav"
                                            aria-hidden="true"
                                        />
                                        <span className="euk-browser-label">
                                            still wrong
                                        </span>
                                        <span
                                            className="euk-browser-x"
                                            aria-hidden="true"
                                        >
                                            ×
                                        </span>
                                    </li>
                                </ul>
                            </div>
                            <div className="euk-browser-address" aria-hidden="true">
                                <span className="euk-browser-dot" />
                                <span>another-free-tool.example/upload</span>
                            </div>
                            <div className="euk-browser-page">
                                <p>
                                    Resize on one site, remove the background on another, compress somewhere else, rename it yourself. Then the background was never actually removed, and you start again.
                                </p>
                                <p className="euk-problem-turn">
                                    None of those tools has read your examination&rsquo;s rules. That is the only thing we do.
                                </p>
                            </div>
                        </Reveal>
                        <Reveal delay={160} className="euk-ledger">
                            <h3 className="euk-ledger-title">
                                What &ldquo;ready&rdquo; usually leaves out
                            </h3>
                            <ul>
                                <li>
                                    <span className="euk-ledger-claim">Background removed</span>
                                    <span className="euk-ledger-truth">
                                        Not resized, not under the limit, not named.
                                    </span>
                                </li>
                                <li>
                                    <span className="euk-ledger-claim">Cropped</span>
                                    <span className="euk-ledger-truth">
                                        With no idea how much of the frame your face should fill.
                                    </span>
                                </li>
                                <li>
                                    <span className="euk-ledger-claim">Ready to upload</span>
                                    <span className="euk-ledger-truth">
                                        Nothing checked if it&rsquo;s blurred or too dark.
                                    </span>
                                </li>
                                <li>
                                    <span className="euk-ledger-claim">Just ask an AI</span>
                                    <span className="euk-ledger-truth">
                                        Then write the prompt that gets all of this right.{" "}
                                        <Link href="/we-vs-ai">We vs AI</Link>
                                    </span>
                                </li>
                            </ul>
                        </Reveal>
                    </div>
                </div>
            </section>

            <section className="euk-gridded euk-plate">
                <div className="euk-wrap">
                    <Reveal className="euk-plate-head">
                        <h2 className="euk-display euk-plate-title">
                            One face.
                            {" "}
                            <br />
                            Six examinations.
                        </h2>
                        <p>
                            No preset fits all six. Each one is read from
                            what that examination actually published.
                        </p>
                    </Reveal>

                    <Reveal delay={120} className="euk-plate-body">
                        <div className="euk-plate-row">
                            {FRAMES.map((f) => (
                                <figure
                                    key={f.px}
                                    className="euk-frame"
                                    style={
                                        {
                                            "--fw": `${f.w}px`,
                                            "--fh": `${f.h}px`,
                                        } as CSSProperties
                                    }
                                >
                                    <span className="euk-frame-rise" aria-hidden="true" />
                                    <div className="euk-frame-box">
                                        <svg
                                            viewBox="0 0 40 48"
                                            className="euk-frame-face"
                                            aria-hidden="true"
                                            fill="var(--ink-40)"
                                        >
                                            <ellipse cx="20" cy="15" rx="9" ry="11" />
                                            <path d="M20 28 C 9 28, 3 38, 2 48 L 38 48 C 37 38, 31 28, 20 28 Z" />
                                        </svg>
                                    </div>
                                    <figcaption className="euk-frame-dim">
                                        {f.px}
                                    </figcaption>
                                </figure>
                            ))}

                            <figure className="euk-frame euk-frame--band">
                                <span className="euk-frame-rise" aria-hidden="true" />
                                <div className="euk-frame-box">
                                    <svg
                                        viewBox="0 0 40 48"
                                        className="euk-frame-face"
                                        aria-hidden="true"
                                        fill="var(--ink-40)"
                                    >
                                        <ellipse cx="20" cy="15" rx="9" ry="11" />
                                        <path d="M20 28 C 9 28, 3 38, 2 48 L 38 48 C 37 38, 31 28, 20 28 Z" />
                                    </svg>
                                    <span className="euk-frame-strip">
                                        name + date
                                    </span>
                                </div>
                                <figcaption className="euk-frame-dim euk-frame-dim--band">
                                    printed on the photo
                                </figcaption>
                            </figure>

                            <figure className="euk-frame euk-frame--live">
                                <span className="euk-frame-rise" aria-hidden="true" />
                                <div className="euk-frame-box">
                                    <span className="euk-frame-live">
                                        taken live
                                    </span>
                                </div>
                                <figcaption className="euk-frame-dim euk-frame-dim--band">
                                    not ours to prepare
                                </figcaption>
                            </figure>
                        </div>

                        <div className="euk-plate-datum" aria-hidden="true" />

                        <dl className="euk-plate-block">
                            <div>
                                <dt>Requirements read</dt>
                                <dd>418</dd>
                            </div>
                            <div>
                                <dt>Examinations</dt>
                                <dd>{examCount}</dd>
                            </div>
                            <div>
                                <dt>Drawn</dt>
                                <dd>to equal area, not to scale</dd>
                            </div>
                        </dl>
                    </Reveal>
                </div>
            </section>

            {/* ---- why we built it ------------------------------------- */}
            <section className="euk-section" id="why">
                <div className="euk-wrap euk-why">
                    <Reveal className="euk-scale" >
                        <span className="euk-scale-big euk-scale-big--small">
                            Free
                        </span>
                        <span className="euk-scale-small">against</span>
                        <span className="euk-scale-big">
                            the years you prepared
                        </span>
                    </Reveal>
                    <Reveal delay={120} className="euk-why-copy">
                        <h2 className="euk-display euk-h2">
                            The smallest part of your application
                            {" "}
                            <br />
                            shouldn&rsquo;t cost you the biggest.
                        </h2>
                        <p>
                            Years of preparation meet a form that is strict about kilobytes. SSC&rsquo;s 2022 notice for its Ladakh
                            selection posts lists unclear photographs and
                            illegible signatures among its grounds for
                            rejection.
                        </p>
                        <p>
                            <a
                                href={SSC_NOTICE}
                                className="euk-link"
                                target="_blank"
                                rel="noreferrer"
                            >
                                Read the notice
                            </a>
                        </p>
                    </Reveal>
                </div>
            </section>

            {/* ---- free ------------------------------------------------ */}
            <section className="euk-section euk-section--alt" id="free">
                <div className="euk-wrap">
                    <Reveal>
                        <h2 className="euk-display euk-h2">
                            Every file is free.
                            {" "}
                            <br />
                            However many your exam asks for.
                        </h2>
                        <p className="euk-lede">
                            No account, no payment, no watermark.
                        </p>
                    </Reveal>

                    <Link href="/exams" className="primary-button">
                        Find your examination
                    </Link>

                    <div className="euk-value">
                        <Reveal className="euk-free">
                            <h3>Every PDF job, free too</h3>
                            <ul className="euk-chips">
                                {FREE_TOOLS.map((tool) => (
                                    <li key={tool} className="euk-chip">
                                        {tool}
                                    </li>
                                ))}
                            </ul>
                            <p>
                                PDF to image runs in your browser.{" "}
                                <Link href="/pdf">See the PDF work</Link>
                            </p>
                        </Reveal>
                        <Reveal delay={120} className="euk-elsewhere">
                            <h3>Or, somewhere else</h3>
                            <ul className="euk-chips">
                                {ELSEWHERE.map((tool) => (
                                    <li
                                        key={tool}
                                        className="euk-chip euk-chip--gone"
                                    >
                                        {tool}
                                    </li>
                                ))}
                            </ul>
                        </Reveal>
                    </div>

                    <p className="euk-retention">
                        Files are deleted within 30 minutes, or within an
                        hour if you ask us to keep them, so download them
                        when they&rsquo;re ready.
                    </p>
                </div>
            </section>

            {/* ---- our story ------------------------------------------- */}
            <section className="euk-section" id="story">
                <div className="euk-wrap">
                    <Reveal>
                        <h2 className="euk-display euk-h2">
                            Why it&rsquo;s built
                            {" "}
                            <br />
                            the way it is.
                        </h2>
                        <p className="euk-lede">
                            A handful of decisions shape everything here, and
                            none of them was the easy option.
                        </p>
                    </Reveal>
                    <div className="euk-principles">
                        {PRINCIPLES.map((p, i) => (
                            <Reveal
                                key={p.title}
                                delay={i * 90}
                                className="euk-principle"
                            >
                                <p.Mark className="euk-principle-mark" />
                                <div className="euk-principle-say">
                                    <h3 className="euk-display">
                                        {p.title}
                                    </h3>
                                    <p>{p.body}</p>
                                </div>
                            </Reveal>
                        ))}
                    </div>
                </div>
            </section>
        </>
    );
}
