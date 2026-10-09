import Link from "next/link";
import { Reveal } from "../../components/euk/reveal";
import {
    CertificateDrawing,
    PhotoDrawing,
    SignatureDrawing,
    ThumbDrawing,
} from "../../components/euk/doodles";
import { UntouchedMark } from "../../components/euk/principle-marks";
import { JsonLd } from "../../components/json-ld";
import { SiteFooter } from "../../components/site-footer";
import { SiteHeader } from "../../components/site-header";
import { rupees, tier } from "../../lib/kit-pricing";
import { breadcrumbs, pageMetadata } from "../../lib/site";

export const metadata = pageMetadata({
    title: "WE vs AI: exam photo preparation, compared",
    description:
        "Can ChatGPT prepare your exam photo? Compare AI editing with ExamUploadKit: identity, framing, pixels, KB, DPI, filenames, preview and pricing.",
    path: "/we-vs-ai",
});

/**
 * The comparison page: what an AI leaves to the candidate, set against what
 * the examination's record already answers here.
 *
 * It is fair on purpose. A free AI can do most of this for a candidate who
 * knows the numbers and checks the result, and the page says so; the argument
 * is the work left over, not that the tools are bad. Nothing here is a
 * benchmark, and no figure is quoted that we did not measure.
 */

const SSC_NOTICE =
    "https://ssc.gov.in/api/attachment/uploads/masterData/NoticeBoards/Notice_of_RHQ_2026_phase_xiv.pdf";
const NIST_REPORT = "https://doi.org/10.6028/NIST.AI.100-4";
const OPENAI_FREE = "https://help.openai.com/en/articles/9275245-chatgpt-free-tier-faq";

/** What our side of the hero already holds, before the candidate types more. */
const ON_FILE = ["Frame and pixels", "KB limit", "Format", "Background", "The other files too"];

const ROWS = [
    {
        what: "The rules",
        ai: "You find the notice and read it out.",
        us: "Already on file for your examination.",
    },
    {
        what: "Pixels",
        ai: "Right, if you give it the right numbers.",
        us: "Set from the examination's record.",
    },
    {
        what: "KB and format",
        ai: "Export, check the size, compress again.",
        us: "Compressed to sit under the limit.",
    },
    {
        what: "DPI",
        ai: "Easy to confuse with pixels.",
        us: "Applied where the examination asks for it.",
    },
    {
        what: "Head framing",
        ai: "A clean background isn't a correct crop.",
        us: "Cropped to the frame. Never stretched.",
    },
    {
        what: "Your face",
        ai: "It may redraw it. You have to look.",
        us: "Never redrawn, reshaped or whitened.",
    },
    {
        what: "The other files",
        ai: "One at a time, named by hand.",
        us: "Signature, thumb, declaration and PDFs together.",
    },
    {
        what: "The last check",
        ai: "Yours to do.",
        us: "A watermarked preview before you pay.",
    },
];

const POINTS = [
    {
        title: "Editing isn't generating.",
        body: "We find your face and lift it off the background. Then it's cropping, resizing and compression. No new face, no new outfit.",
    },
    {
        title: "Live capture means live.",
        body: "Some portals photograph you themselves, and no uploaded file replaces that. SSC's Phase-XIV/2026 notice is one.",
        link: { href: SSC_NOTICE, label: "Read the notice" },
    },
    {
        title: "Detection isn't the test.",
        body: "Detectors exist and they are uneven. The question is whether the photograph follows the instructions, not whether an edit would be caught.",
        link: { href: NIST_REPORT, label: "NIST's overview" },
    },
];

const YOURSELF = [
    "You know the exact pixels and KB",
    "You'll check the exported file",
    "It's a single file",
];

const WITH_US = [
    "You don't know the numbers",
    "The form wants several files",
    "The deadline is close",
];

const QUESTIONS = [
    {
        question: "Can ChatGPT do the same thing?",
        answer: "Much of it. It can explain instructions, edit images and, with the right tools, resize, compress and rename files. A careful person can assemble a working routine. We bring your examination's stored requirements and the preparation together, so you don't assemble it each time.",
    },
    {
        question: "Do I need ChatGPT Plus to prepare a photo?",
        answer: "Not necessarily. ChatGPT's free tier includes image creation, uploads and data analysis, with usage limits. A paid plan doesn't make a file compliant and a free one doesn't make it wrong. What matters is the file you export.",
    },
    {
        question: "Will every exam portal detect an AI-generated photo?",
        answer: "We don't know that every portal runs a detector, and nobody should tell you they do. Detection tools exist and their accuracy varies. Some examinations require a recent photograph or live capture; follow that whether or not an edit would be noticed.",
    },
    {
        question: "Does removing a watermark make an AI photo acceptable?",
        answer: "No. A missing watermark says nothing about whether the photograph is recent, real or allowed by the examination.",
    },
    {
        question: "Can I generate formal clothes or improve my face first?",
        answer: "Use a real, recent photograph and follow the examination's instructions on clothing and appearance. A generated outfit or a reshaped face changes what the photograph is of. We don't do either.",
    },
    {
        question: "Is 75–80% face coverage compulsory for every exam?",
        answer: "No. Requirements differ and so do the ways they are measured. A file with the right pixels and KB can still be badly framed, and one coverage figure can't settle acceptance.",
    },
    {
        question: "Does ExamUploadKit use AI?",
        answer: "Yes. Computer-vision models find the face and separate you from the background. That is not the same as generating a person. Resizing and compression are ordinary image processing.",
    },
    {
        question: "Can you verify that a photo is recent, or mine?",
        answer: "No. Pixels can't prove a photograph is recent or belongs to you, and we don't detect every appearance rule. Read your examination's instructions and look at the preview.",
    },
    {
        question: "What if my exam or file isn't fully supported?",
        answer: "The examination's page says so for each file: supported, partly supported, guidance only, or not yet supported. A file we can't prepare has no upload button.",
    },
    {
        question: "Is portal acceptance guaranteed?",
        answer: "No. We prepare files to the stored requirements and the examination authority decides. Check the current official notice, especially if it has changed.",
    },
];

/** A gap in the prompt: the number the candidate has to know. */
function Blank({ wide = false }: { wide?: boolean }) {
    return (
        <span className={`euk-vs-blank ${wide ? "euk-vs-blank--wide" : ""}`}>
            <span className="sr-only">blank</span>
        </span>
    );
}

export default function WeVsAi() {
    return (
        <div className="euk euk-vs">
            <SiteHeader />
            <JsonLd
                data={breadcrumbs([
                    { name: "Home", path: "/" },
                    { name: "WE vs AI", path: "/we-vs-ai" },
                ])}
            />
            <JsonLd
                data={{
                    "@context": "https://schema.org",
                    "@type": "FAQPage",
                    mainEntity: QUESTIONS.map(({ question, answer }) => ({
                        "@type": "Question",
                        name: question,
                        acceptedAnswer: { "@type": "Answer", text: answer },
                    })),
                }}
            />
            <main id="main-content">
                {/* ---- hero ------------------------------------------------ */}
                <section className="euk-vs-top">
                    <div className="euk-wrap euk-vs-top-grid">
                        <div className="euk-vs-top-say">
                            <h1 className="euk-display euk-vs-title">
                                We <span className="euk-mark">vs</span> AI
                            </h1>
                            <p className="euk-display euk-vs-claim">
                                An AI edits a photo. Your exam wants a file.
                            </p>
                            <p className="euk-lede">
                                A file has pixels, a KB limit, a format and a name, and it still
                                has to be you. An AI does what you tell it. We already know what
                                your examination asked for.
                            </p>
                            <div className="euk-vs-top-act">
                                <Link href="/exams" className="primary-button">
                                    Find your examination
                                </Link>
                                <span>From {rupees(tier(1))}. You see it before you pay.</span>
                            </div>
                        </div>

                        <div className="euk-vs-duel">
                            <figure className="euk-vs-pane euk-vs-pane--ai">
                                <figcaption>What you type into an AI</figcaption>
                                <p className="euk-vs-prompt">
                                    Crop this to <Blank /> × <Blank /> pixels. White background.
                                    Keep it under <Blank /> KB, as a JPG. Don&rsquo;t change my
                                    face. Name it <Blank wide />.
                                </p>
                                <p className="euk-vs-pane-foot">
                                    Then check every one of those yourself.
                                </p>
                            </figure>
                            <figure className="euk-vs-pane euk-vs-pane--us">
                                <figcaption>What you type here</figcaption>
                                <p className="euk-vs-field">
                                    <svg
                                        viewBox="0 0 20 20"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth={2.2}
                                        aria-hidden="true"
                                    >
                                        <circle cx="8.5" cy="8.5" r="5.5" />
                                        <path d="M13 13l5 5" strokeLinecap="round" />
                                    </svg>
                                    <span>IBPS PO</span>
                                    <span className="euk-vs-caret" aria-hidden="true" />
                                </p>
                                <ul className="euk-vs-onfile">
                                    {ON_FILE.map((item) => (
                                        <li key={item}>{item}</li>
                                    ))}
                                </ul>
                                <p className="euk-vs-pane-foot">Already on file.</p>
                            </figure>
                        </div>
                    </div>
                </section>

                {/* ---- the comparison --------------------------------------- */}
                <section className="euk-section euk-section--alt" id="comparison">
                    <div className="euk-wrap">
                        <Reveal>
                            <h2 className="euk-display euk-h2">Eight things. Who does each.</h2>
                            <p className="euk-lede">
                                A routine you run yourself with an AI, next to the same job here.
                            </p>
                        </Reveal>
                        <Reveal delay={120}>
                            <table className="euk-vs-table">
                                <thead>
                                    <tr>
                                        <th scope="col">
                                            <span className="sr-only">The requirement</span>
                                        </th>
                                        <th scope="col">You and an AI</th>
                                        <th scope="col">Here</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {ROWS.map((row) => (
                                        <tr key={row.what}>
                                            <th scope="row">{row.what}</th>
                                            <td data-tag="AI">{row.ai}</td>
                                            <td data-tag="Us">{row.us}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </Reveal>
                    </div>
                </section>

                {/* ---- identity --------------------------------------------- */}
                <section className="euk-invert euk-section" id="identity">
                    <div className="euk-wrap euk-vs-identity">
                        <Reveal className="euk-vs-identity-head">
                            <h2 className="euk-display euk-h2">
                                Prepare the file.{" "}
                                <span className="euk-mark">Keep the person.</span>
                            </h2>
                            <UntouchedMark className="euk-vs-identity-mark" />
                            <p className="euk-lede">
                                The photograph on your admit card has to be the person who walks
                                into the hall. A more polished face is not a more suitable one.
                            </p>
                        </Reveal>
                        <ul className="euk-vs-points">
                            {POINTS.map((point, i) => (
                                <li key={point.title}>
                                    <Reveal delay={i * 110}>
                                        <h3 className="euk-display">{point.title}</h3>
                                        <p>
                                            {point.body}
                                            {point.link && (
                                                <>
                                                    {" "}
                                                    <a
                                                        href={point.link.href}
                                                        className="euk-link"
                                                        target="_blank"
                                                        rel="noreferrer"
                                                    >
                                                        {point.link.label}
                                                    </a>
                                                </>
                                            )}
                                        </p>
                                    </Reveal>
                                </li>
                            ))}
                        </ul>
                    </div>
                </section>

                {/* ---- why pay, and what ------------------------------------ */}
                <section className="euk-section" id="cost">
                    <div className="euk-wrap">
                        <Reveal>
                            <h2 className="euk-display euk-h2">
                                A free AI can do this. So why pay {rupees(tier(1))}?
                            </h2>
                            <p className="euk-lede">
                                For the part it leaves to you: knowing the numbers, and checking
                                the result.{" "}
                                <a
                                    href={OPENAI_FREE}
                                    className="euk-link"
                                    target="_blank"
                                    rel="noreferrer"
                                >
                                    What ChatGPT&rsquo;s free tier includes
                                </a>
                            </p>
                        </Reveal>

                        <div className="euk-value euk-vs-value">
                            <Reveal className="euk-elsewhere">
                                <h3>Do it yourself if</h3>
                                <ul className="euk-chips">
                                    {YOURSELF.map((item) => (
                                        <li key={item} className="euk-chip">
                                            {item}
                                        </li>
                                    ))}
                                </ul>
                                <p>
                                    Then it may be all you need.{" "}
                                    <Link href="/compress-image" className="euk-link">
                                        Our compressor is free
                                    </Link>
                                </p>
                            </Reveal>
                            <Reveal delay={120} className="euk-free">
                                <h3>Use us if</h3>
                                <ul className="euk-chips">
                                    {WITH_US.map((item) => (
                                        <li key={item} className="euk-chip">
                                            {item}
                                        </li>
                                    ))}
                                </ul>
                                <p>That is what this was built for.</p>
                            </Reveal>
                        </div>

                        <div className="euk-price-grid euk-vs-prices">
                            <Reveal className="euk-invert euk-price euk-price--kit">
                                <p className="euk-price-name">The whole kit</p>
                                <p className="euk-price-row">
                                    <span className="euk-price-figure">{rupees(tier(2))}</span>
                                </p>
                                <p className="euk-price-files euk-vs-files" aria-hidden="true">
                                    <PhotoDrawing />
                                    <SignatureDrawing />
                                    <ThumbDrawing />
                                    <CertificateDrawing />
                                </p>
                                <p className="euk-price-body">
                                    Two files or more. PDF work is free with them.
                                </p>
                                <Link href="/exams" className="primary-button">
                                    Find your examination
                                </Link>
                            </Reveal>
                            <Reveal delay={90} className="euk-price">
                                <p className="euk-price-name">One file</p>
                                <p className="euk-price-row">
                                    <span className="euk-price-figure">{rupees(tier(1))}</span>
                                </p>
                                <p className="euk-price-files euk-vs-files" aria-hidden="true">
                                    <PhotoDrawing />
                                </p>
                                <p className="euk-price-body">
                                    Any single file, such as your photograph.
                                </p>
                                <Link href="/exams" className="euk-price-hit">
                                    <span className="sr-only">Find your examination</span>
                                </Link>
                            </Reveal>
                        </div>
                    </div>
                </section>

                {/* ---- questions -------------------------------------------- */}
                <section className="euk-section euk-section--alt" id="questions">
                    <div className="euk-wrap euk-vs-faq">
                        <h2 className="euk-display euk-h2">Fair questions. Straight answers.</h2>
                        <div className="euk-vs-faq-list">
                            {QUESTIONS.map(({ question, answer }) => (
                                <details key={question}>
                                    <summary>{question}</summary>
                                    <p>{answer}</p>
                                </details>
                            ))}
                        </div>
                    </div>
                </section>

                {/* ---- sources ---------------------------------------------- */}
                <section className="euk-vs-sources" aria-labelledby="sources-title">
                    <div className="euk-wrap">
                        <h2 id="sources-title">Where this comes from</h2>
                        <ul>
                            <li>
                                <a href={OPENAI_FREE} target="_blank" rel="noreferrer">
                                    OpenAI: ChatGPT free tier FAQ
                                </a>
                            </li>
                            <li>
                                <a href={SSC_NOTICE} target="_blank" rel="noreferrer">
                                    SSC: Phase-XIV/2026 Selection Posts notice
                                </a>
                            </li>
                            <li>
                                <a href={NIST_REPORT} target="_blank" rel="noreferrer">
                                    NIST AI 100-4: Reducing Risks Posed by Synthetic Content
                                </a>
                            </li>
                        </ul>
                        <p>
                            Read on 2 October 2026. We compared routines, not benchmark scores,
                            and we are not affiliated with OpenAI or any examination authority.{" "}
                            <Link href="/support">Tell us if something here is out of date</Link>
                        </p>
                    </div>
                </section>
            </main>
            <SiteFooter />
        </div>
    );
}
