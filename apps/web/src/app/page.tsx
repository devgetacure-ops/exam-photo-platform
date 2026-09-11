import Link from "next/link";
import { ExamSearch } from "../components/exam-search";
import { SiteFooter } from "../components/site-footer";
import { SiteHeader } from "../components/site-header";
import { Note } from "../components/euk/note";
import { Compare } from "../components/euk/compare";
import { Reveal } from "../components/euk/reveal";
import {
    ArrowDrawing,
    CertificateDrawing,
    DeclarationDrawing,
    PhotoDrawing,
    SignatureDrawing,
    ThumbDrawing,
} from "../components/euk/doodles";
import { loadSearchIndex } from "../lib/catalogue.server";
import { readImageFacts, formatBytes } from "../lib/image-facts.server";

/**
 * The landing page, in the order the brief sets: the hero, then what we do,
 * how we do it, the problem, why we built it, pricing, and our story.
 *
 * Everything below the hero reveals as it scrolls in. The hero does not: it is
 * the largest contentful paint on a slow phone, and holding it back for an
 * animation would cost the one metric that decides whether a candidate stays.
 */
const SSC_NOTICE = "https://ssc.nic.in/SSCFileServer/PortalManagement/UploadedFiles/notice_rhqladakh_23052022.pdf";

const KIT = [
    {
        name: "Photograph",
        Drawing: PhotoDrawing,
        body: "Cropped to your examination's frame, with the background replaced and the file compressed under the limit and named the way the portal expects. Your face is left alone: no reshaping, no whitening.",
    },
    {
        name: "Signature",
        Drawing: SignatureDrawing,
        body: "The page cleared around your strokes and the ink made firm. Never stretched, because a stretched signature is no longer yours.",
    },
    {
        name: "Thumb impression",
        Drawing: ThumbDrawing,
        body: "Lighting evened out and cropped close, but never masked, so every ridge the authority needs to see survives.",
    },
    {
        name: "Declaration",
        Drawing: DeclarationDrawing,
        body: "We straighten your handwritten sheet so it reads clearly. The page stays whole and is never cropped down to the writing.",
    },
    {
        name: "Certificates and ID",
        Drawing: CertificateDrawing,
        body: "A scan turned into a clean PDF, or an existing PDF put in order: pages added, removed, rearranged or merged.",
    },
];

const TOOL_TABS = ["resize", "remove bg", "compress", "convert", "rename"];

const SPECS = [
    { w: 84, h: 97, label: "200×230" },
    { w: 100, h: 100, label: "1200×1200" },
    { w: 75, h: 100, label: "150×200" },
    { w: 100, h: 78, label: "413×319" },
];

const FREE_TOOLS = [
    "Image to PDF",
    "PDF to image",
    "Merge PDFs",
    "Reorder pages",
    "Remove pages",
    "Rotate pages",
    "Compress to the size limit",
];

const ELSEWHERE = [
    "a background remover",
    "a resizer",
    "a compressor",
    "a format converter",
    "a renamer",
    "a PDF merger",
];

const PRINCIPLES = [
    {
        title: "It never changes your face.",
        body: "Exposure and contrast, yes. Whitening or reshaping, never. The photograph on your admit card has to be the person who walks into the exam hall.",
    },
    {
        title: "It never guesses a rule.",
        body: "Where an examination didn't publish a number, the value we use is marked est., so you know exactly which figures to check against your notification.",
    },
    {
        title: "It never pretends.",
        body: "Some files we can't prepare. The portal might photograph you itself, or want your name printed on the image. When that happens the page says so, and there's no upload button pretending otherwise.",
    },
    {
        title: "It forgets you.",
        body: "No account and nothing to sign up for. Your files are deleted within 30 minutes, or within an hour if you ask us to keep them.",
    },
];

export default async function Home() {
    const { exams, unavailable } = await loadSearchIndex();

    // Measured from the files themselves, so the page cannot claim a number
    // the asset does not have. Swap either photograph and this updates.
    const before = readImageFacts("/examples/hero-before.jpg");
    const after = readImageFacts("/examples/hero-after.jpg");
    const checks =
        before && after
            ? [
                  {
                      label: "Background",
                      before: "Whatever was behind you",
                      after: "Plain, even, the shade they ask for",
                  },
                  {
                      label: "Dimensions",
                      before: `${before.width} × ${before.height}`,
                      after: `${after.width} × ${after.height}`,
                  },
                  {
                      label: "File size",
                      before: formatBytes(before.bytes),
                      after: formatBytes(after.bytes),
                  },
                  { label: "Format", before: before.format, after: after.format },
                  { label: "File name", before: before.name, after: after.name },
              ]
            : [];

    const steps = [
        {
            whose: "Yours",
            title: "Find your examination",
            body: `Search by its name or its short form, like SSC CGL or IBPS PO. ${exams.length} examinations are on file, each with the rules it published.`,
        },
        {
            whose: "Yours",
            title: "Keep what you need",
            body: "The full kit is already ticked. Untick anything your form doesn't ask for, and the price changes as you do.",
        },
        {
            whose: "Ours",
            title: "We prepare it",
            body: "Each file is made to your examination's own specification, and you watch it happen stage by stage.",
        },
        {
            whose: "Yours",
            title: "Check before you pay",
            body: "A watermarked preview of the real result, with a plain note of anything worth a second look.",
        },
        {
            whose: "Yours",
            title: "Pay and keep",
            body: "Download them, or have them emailed to you. Deleted within 30 minutes, or within an hour if you ask.",
        },
    ];

    return (
        <div className="euk">
            <SiteHeader />
            <main id="main-content">
                {/* ---- hero ------------------------------------------------ */}
                <section className="euk-hero">
                    <div className="euk-wrap">
                        <h1 className="euk-display euk-hero-title">
                            You prepare for the exam.
                            <br />
                            We&rsquo;ll prepare{" "}
                            <span className="euk-mark">the files.</span>
                        </h1>
                        <p className="euk-hero-sub">
                            Your photograph, signature, thumb impression, declaration and certificates. Each one made to the rules your examination published.
                        </p>
                        <div className="euk-hero-search">
                            <ExamSearch exams={exams} unavailable={unavailable} />
                        </div>
                        <p className="euk-hero-facts">
                            <span>No account</span>
                            <span>From ₹3, PDF work free</span>
                            <Link href="/exam-request">
                                Not on the list? Tell us which one
                            </Link>
                        </p>
                    </div>
                </section>

                {/* ---- what we do ------------------------------------------ */}
                <section className="euk-section" id="what">
                    <div className="euk-wrap">
                        <Reveal>
                            <h2 className="euk-display euk-h2">
                                Everything the form
                                <br />
                                asks you to attach.
                            </h2>
                            <p className="euk-lede">
                                An application is rarely one photograph. It&rsquo;s a photograph and a signature, often a thumb impression, sometimes a handwritten declaration, and a stack of certificates. Every one has its own pixel size and file limit, and we prepare all of them.
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

                        <div className="euk-demo">
                            <Reveal className="euk-demo-copy">
                                <h3 className="euk-display">
                                    Drag it.
                                    <br />
                                    Five things get fixed.
                                </h3>
                                <p>
                                    This is the comparison you see after you
                                    upload: what you gave us on one side, what
                                    came back on the other. Drag the line across
                                    and each problem is checked off as it goes.
                                </p>
                                <Note className="text-[15px]">
                                    The sizes and file names in that list are
                                    measured from the two files themselves.
                                </Note>
                            </Reveal>
                            <Reveal delay={120} className="euk-demo-frame">
                                <span className="euk-stamp" aria-hidden="true">
                                    Prepared to the
                                    <br />
                                    published rules
                                </span>
                                <Compare
                                    beforeSrc="/examples/hero-before.jpg"
                                    afterSrc="/examples/hero-after.jpg"
                                    width={before?.width ?? 240}
                                    height={before?.height ?? 320}
                                    alt="The same photograph before and after preparation"
                                    checks={checks}
                                    placeholder={
                                        before?.width === after?.width &&
                                        before?.height === after?.height
                                    }
                                />
                            </Reveal>
                        </div>
                    </div>
                </section>

                {/* ---- how we do it ---------------------------------------- */}
                <section className="euk-section euk-section--alt" id="how">
                    <div className="euk-wrap">
                        <Reveal>
                            <h2 className="euk-display euk-h2">
                                You choose. We prepare.
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
                                        {i < steps.length - 1 && (
                                            <ArrowDrawing className="euk-step-arrow" />
                                        )}
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
                            <Reveal className="euk-tabs">
                                <div className="euk-tabs-row">
                                    {TOOL_TABS.map((t, i) => (
                                        <span
                                            key={t}
                                            className="euk-tab"
                                            style={{
                                                transitionDelay: `${i * 90 + 200}ms`,
                                            }}
                                        >
                                            {t}
                                        </span>
                                    ))}
                                    <span
                                        className="euk-tab euk-tab--wrong"
                                        style={{ transitionDelay: "720ms" }}
                                    >
                                        still wrong
                                    </span>
                                </div>
                                <div className="euk-tabs-rail" />
                            </Reveal>
                            <Reveal delay={100}>
                                <p>
                                    Every year, crores of applications reach an
                                    upload screen like the one you&rsquo;re
                                    about to meet. So the routine goes: resize on one site, remove the background on another, compress somewhere else, convert the format and rename it yourself. Then you find the background was never actually removed, and you start again.
                                </p>
                                <p className="euk-problem-turn">
                                    None of those tools has ever read your
                                    examination&rsquo;s rules. That is the whole
                                    problem, and it is the only thing we do.
                                </p>
                            </Reveal>
                            <Reveal delay={160} className="euk-ledger">
                                <h3 className="euk-ledger-title">
                                    What &ldquo;ready&rdquo; usually leaves out
                                </h3>
                                <ul>
                                    <li>
                                        <span className="euk-ledger-claim">Background removed</span>
                                        <span className="euk-ledger-truth">
                                            A free AI tool does that part. It
                                            won&rsquo;t resize the photo, get it
                                            under the file limit, or name it the
                                            way the portal wants.
                                        </span>
                                    </li>
                                    <li>
                                        <span className="euk-ledger-claim">Cropped</span>
                                        <span className="euk-ledger-truth">
                                            With no idea how much of the frame
                                            your face is meant to fill.
                                        </span>
                                    </li>
                                    <li>
                                        <span className="euk-ledger-claim">Ready to upload</span>
                                        <span className="euk-ledger-truth">
                                            Nothing checked whether it&rsquo;s
                                            blurred or too dark. We flag that
                                            before you pay.
                                        </span>
                                    </li>
                                    <li>
                                        <span className="euk-ledger-claim">Just ask an AI</span>
                                        <span className="euk-ledger-truth">
                                            Then write a prompt precise enough to
                                            get every one of these right, and
                                            check its work yourself.
                                        </span>
                                    </li>
                                </ul>
                            </Reveal>
                        </div>
                    </div>
                </section>

                <section className="euk-gridded px-5 py-12 md:px-12 md:py-16">
                    <div className="euk-wrap">
                        <Reveal className="flex flex-col gap-2 pb-7 md:flex-row md:items-end md:justify-between">
                            <div>
                                <h2 className="euk-display text-[38px] md:text-[52px] md:leading-[0.9]">
                                    One face.
                                    <br />
                                    Six examinations.
                                </h2>
                                <p className="pt-3 text-[16px] leading-relaxed text-[var(--ink-70)]">
                                    No preset fits all six. Each one is read from
                                    what that examination actually published.
                                </p>
                            </div>
                            <p className="text-[14px] leading-relaxed text-[var(--ink-55)] md:text-right">
                                418 requirements across {exams.length}{" "}
                                examinations
                            </p>
                        </Reveal>
                        <Reveal delay={120} className="flex items-end gap-3 overflow-x-auto pb-2 md:gap-5">
                            {SPECS.map((s) => (
                                <div
                                    key={s.label}
                                    className="flex shrink-0 flex-col items-center gap-2"
                                >
                                    <div
                                        className="flex items-end justify-center border-2 border-[var(--ink)] bg-white"
                                        style={{ width: s.w, height: s.h }}
                                    >
                                        <svg
                                            viewBox="0 0 40 48"
                                            className="h-[78%] w-auto"
                                            aria-hidden="true"
                                            fill="var(--ink-40)"
                                        >
                                            <ellipse cx="20" cy="15" rx="9" ry="11" />
                                            <path d="M20 28 C 9 28, 3 38, 2 48 L 38 48 C 37 38, 31 28, 20 28 Z" />
                                        </svg>
                                    </div>
                                    <span className="euk-figures text-[12px]">
                                        {s.label}
                                    </span>
                                </div>
                            ))}
                            <div className="flex shrink-0 flex-col items-center gap-2">
                                <div className="relative h-[92px] w-[78px] border-2 border-[var(--signal-deep)] bg-white">
                                    <div className="absolute inset-x-0 bottom-0 flex h-[24px] items-center justify-center border-t-2 border-dashed border-[var(--signal-deep)] bg-[var(--signal-soft)] text-[11px] font-semibold text-[var(--signal-deep)]">
                                        name + date
                                    </div>
                                </div>
                                <span className="text-[12px] text-[var(--signal-deep)]">
                                    TNPSC
                                </span>
                            </div>
                            <div className="flex shrink-0 flex-col items-center gap-2">
                                <div className="h-[78px] w-[78px] border-2 border-dashed border-[var(--notyet-line)] bg-[var(--notyet-fill)]" />
                                <span className="text-[12px] text-[var(--ink-55)]">
                                    Taken live
                                </span>
                            </div>
                        </Reveal>
                    </div>
                </section>

                {/* ---- why we built it ------------------------------------- */}
                <section className="euk-section" id="why">
                    <div className="euk-wrap euk-why">
                        <Reveal className="euk-scale" >
                            <span className="euk-scale-big euk-scale-big--small">
                                ₹3
                            </span>
                            <span className="euk-scale-small">against</span>
                            <span className="euk-scale-big">
                                the years you prepared
                            </span>
                        </Reveal>
                        <Reveal delay={120} className="euk-why-copy">
                            <h2 className="euk-display euk-h2">
                                The smallest part of your application
                                <br />
                                shouldn&rsquo;t cost you the biggest.
                            </h2>
                            <p>
                                An application is where months, often years, of
                                preparation meet a form. And the form is strict in ways that have nothing to do with how well you know the syllabus, like a file size in kilobytes or a name printed under the photograph.
                            </p>
                            <p>
                                Examinations do turn applications away over
                                this. SSC&rsquo;s 2022 notice for its Ladakh
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

                {/* ---- pricing --------------------------------------------- */}
                <section className="euk-section euk-section--alt" id="pricing">
                    <div className="euk-wrap">
                        <Reveal>
                            <h2 className="euk-display euk-h2">
                                The whole kit is ₹8.
                                <br />
                                However many files your exam asks for.
                            </h2>
                            <p className="euk-lede">
                                Most forms ask for more than two. Prepare them
                                together and every file costs less.
                            </p>
                        </Reveal>

                        <div className="euk-price-grid">
                            <Reveal className="euk-invert euk-price euk-price--kit">
                                <p className="euk-price-name">The whole kit</p>
                                <p className="euk-price-row">
                                    <span className="euk-price-figure">₹8</span>
                                    <span className="euk-price-was">₹10</span>
                                </p>
                                <p className="euk-price-body">
                                    Three files or more. The price stops at ₹8,
                                    whatever your examination asks for.
                                </p>
                                <Link href="/exams" className="primary-button">
                                    Find your examination
                                </Link>
                            </Reveal>
                            <Reveal delay={90} className="euk-price">
                                <p className="euk-price-name">Two files</p>
                                <p className="euk-price-row">
                                    <span className="euk-price-figure">₹5</span>
                                    <span className="euk-price-was">₹8</span>
                                </p>
                                <p className="euk-price-body">
                                    Two files, such as your photograph and your
                                    signature.
                                </p>
                            </Reveal>
                            <Reveal delay={180} className="euk-price">
                                <p className="euk-price-name">One file</p>
                                <p className="euk-price-row">
                                    <span className="euk-price-figure">₹3</span>
                                    <span className="euk-price-was">₹4</span>
                                </p>
                                <p className="euk-price-body">
                                    Any single file, such as your photograph.
                                </p>
                            </Reveal>
                        </div>

                        <div className="euk-value">
                            <Reveal className="euk-free">
                                <h3>Free with any prepared file</h3>
                                <ul className="euk-chips">
                                    {FREE_TOOLS.map((tool) => (
                                        <li key={tool} className="euk-chip">
                                            {tool}
                                        </li>
                                    ))}
                                </ul>
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
                                <p>
                                    Six tabs, and not one of them has read your
                                    examination&rsquo;s rules.
                                </p>
                            </Reveal>
                        </div>

                        <p className="euk-retention">
                            Files are deleted within 30 minutes, or within an
                            hour if you ask us to keep them. Payment doesn&rsquo;t
                            extend that, so download them when they&rsquo;re
                            ready.
                        </p>
                    </div>
                </section>

                {/* ---- our story ------------------------------------------- */}
                <section className="euk-section" id="story">
                    <div className="euk-wrap">
                        <Reveal>
                            <h2 className="euk-display euk-h2">
                                Why it&rsquo;s built
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
                                    <h3 className="euk-display">{p.title}</h3>
                                    <p>{p.body}</p>
                                </Reveal>
                            ))}
                        </div>
                    </div>
                </section>
            </main>
            <SiteFooter />
        </div>
    );
}
