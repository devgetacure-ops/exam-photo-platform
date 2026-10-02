import Link from "next/link";
import { ArrowRight, Check, FileCheck2, ScanFace } from "lucide-react";
import { SiteHeader } from "../../components/site-header";
import { SiteFooter } from "../../components/site-footer";
import { JsonLd } from "../../components/json-ld";
import { breadcrumbs, pageMetadata } from "../../lib/site";
import { rupees, tier } from "../../lib/kit-pricing";
import styles from "./page.module.css";

export const metadata = pageMetadata({
    title: "WE vs AI: exam photo preparation, compared",
    description: "Can ChatGPT prepare your exam photo? Compare AI editing with ExamUploadKit: identity, framing, pixels, KB, DPI, filenames, preview and pricing.",
    path: "/we-vs-ai",
});

const comparisons = [
    ["Finding the requirements", "You supply the right notice, cycle and instructions, then check the interpretation.", "Your selected exam loads its stored requirements. Published values and platform estimates are distinguished."],
    ["Dimensions & aspect ratio", "AI-assisted code or a resize tool can set exact pixels if you provide the correct values.", "The stored configuration sets the output frame and dimensions for supported files; the subject is not stretched."],
    ["File size & format", "You request an export, inspect the actual file and adjust compression if needed.", "Preparation targets the configured size limits and format, with final output checks and findings."],
    ["DPI & resolution", "You must distinguish pixel dimensions from DPI metadata and specify what the notice actually asks for.", "DPI is applied when configured. An unpublished value is not presented as an official requirement."],
    ["Face framing & coverage", "A clean background or correct pixel size does not establish correct head framing.", "Natural cropping aims to preserve the whole head. Coverage is a diagnostic, not a universal rejection threshold."],
    ["Background & identity", "Editing and generative recreation are different operations. Ask for an edit and inspect whether your face or clothing changed.", "Background processing and restrained capture corrections preserve identity. No generated face, outfit or cosmetic makeover."],
    ["Filename & other files", "You coordinate names and separate preparation steps for signatures, declarations and documents.", "Supported files share one exam-first workflow, with configured output naming and file-specific processing."],
    ["Final review", "You are responsible for checking the exported file against the current notice.", "You review a watermarked preview and any findings before payment. Final acceptance remains the authority’s decision."],
];

const questions = [
    { question: "Can ChatGPT do the same thing?", answer: "It can help explain instructions, edit images and, with suitable tools or code, resize, compress and rename files. A careful user can assemble a working workflow. ExamUploadKit’s value is bringing stored exam requirements and supported preparation steps together, without asking you to assemble that workflow each time." },
    { question: "Do I need ChatGPT Plus to prepare a photo?", answer: "Not necessarily. ChatGPT’s free tier includes image creation, uploads and data analysis with usage limits. Free does not mean incapable, and paid does not mean automatically compliant. What matters is the actual exported file and the applicable exam instructions." },
    { question: "Will every exam portal detect an AI-generated photo?", answer: "We have not established that every portal uses an AI-image detector. Detection tools exist, but their performance varies; a detector result is not proof of acceptance or rejection. Some exams require live capture or a recent photograph. Follow those instructions regardless of whether an edited image might be detected." },
    { question: "Does removing a watermark make an AI photo acceptable?", answer: "No. A missing visible watermark says nothing about whether the photograph is recent, authentic or permitted by the exam. Do not treat a detector score or watermark removal as a substitute for the authority’s instructions." },
    { question: "Can I generate formal clothes or improve my face first?", answer: "Use a real recent photograph and follow the exam’s clothing and appearance instructions. Generating an outfit, reshaping facial features or cosmetically recreating the image can change what the photograph represents. ExamUploadKit does not perform those transformations." },
    { question: "Is 75–80% face coverage compulsory for every exam?", answer: "No. Requirements and measurement methods vary. Our natural-framing objective is not a universal official threshold. A file with the correct pixels and KB can still have poor framing; conversely, one calculated coverage percentage alone cannot establish portal acceptance." },
    { question: "Does ExamUploadKit use AI?", answer: "Yes. Computer-vision models help locate the face and separate the subject from the background. That is different from generating a new identity. We also use conventional image processing for tasks such as resizing and compression. We do not claim the service is AI-free." },
    { question: "Can you verify recency, identity or every appearance rule?", answer: "No. We cannot establish from pixels alone that a photograph is recent or belongs to you, and we do not automatically detect every appearance issue. Read the exam’s instructions and review the result. If the portal requires live capture, complete it there." },
    { question: "What if my exam or file is not fully supported?", answer: "The exam page distinguishes supported, partially supported, guidance-only and not-yet-supported requirements. Read that status before uploading. Partial support is not a claim that every requirement has been completed." },
    { question: "Is portal acceptance guaranteed?", answer: "No. We prepare supported files against stored requirements; the exam authority makes the final decision. Check the current official notice, especially if its instructions have changed since the source used in our record." },
];

export default function WeVsAi() {
    return (
        <div className={`euk ${styles.page}`}>
            <SiteHeader />
            <JsonLd data={breadcrumbs([{ name: "Home", path: "/" }, { name: "WE vs AI", path: "/we-vs-ai" }])} />
            <JsonLd data={{ "@context": "https://schema.org", "@type": "FAQPage", mainEntity: questions.map(({ question, answer }) => ({ "@type": "Question", name: question, acceptedAnswer: { "@type": "Answer", text: answer } })) }} />
            <main id="main-content">
                <section className={styles.hero} aria-labelledby="comparison-title">
                    <div className={`euk-wrap ${styles.heroGrid}`}>
                        <div>
                            <h1 id="comparison-title" className={`euk-display ${styles.title}`}>WE <span>vs</span> AI</h1>
                            <h2 className={styles.headline}>An edited photo is one step.<br />An exam upload is the whole job.</h2>
                            <p className={styles.intro}>AI can help you make and edit images. ExamUploadKit connects your exam’s stored requirements to the files you need to submit.</p>
                            <Link href="/exams" className="primary-button">Find your examination <ArrowRight size={18} aria-hidden="true" /></Link>
                            <p className={styles.priceNote}>From {rupees(tier(1))}. Review the preview before you pay.</p>
                        </div>
                        <div className={styles.requirementSheet}>
                            <FileCheck2 size={36} strokeWidth={1.5} aria-hidden="true" />
                            <h2>A file has more than<br />one requirement.</h2>
                            <ul>{["Your real identity", "Natural head framing", "Required dimensions", "Allowed KB & format", "DPI & naming, when specified"].map((item) => <li key={item}><Check size={18} aria-hidden="true" /><span>{item}</span></li>)}</ul>
                            <p>They need to work together.</p>
                            <small>Requirements vary by exam. This is a checklist of considerations, not an acceptance certificate.</small>
                        </div>
                    </div>
                </section>

                <nav className={styles.contents} aria-label="On this page"><div className="euk-wrap">{[["journey", "The workflow"], ["comparison", "Compare the details"], ["identity", "Your identity"], ["cost", "What it costs"], ["questions", "Your questions"]].map(([id, label]) => <a href={`#${id}`} key={id}>{label}</a>)}</div></nav>

                <section id="journey" className={styles.section}>
                    <div className="euk-wrap">
                        <h2 className={`euk-display ${styles.sectionTitle}`}>Less coordinating.<br />More getting it done.</h2>
                        <p className={styles.lead}>A shop can help. A collection of online tools can help. The difference is how much of the preparation you still have to manage.</p>
                        <div className={styles.journeys}>
                            <article><h3>At a studio or cybercafé</h3><p>Bring the instructions. Explain the size. Get the photograph and files prepared with someone’s help.</p><p className={styles.takeaway}>You coordinate the visit and the requirements.</p></article>
                            <article><h3>Across AI and editing tools</h3><ol><li>Edit the background</li><li>Resize to the required pixels</li><li>Compress to the KB limit</li><li>Rename the file</li><li>Check the complete result</li></ol><p className={styles.takeaway}>You connect the tools and verify the output.</p></article>
                            <article className={styles.ourJourney}><h3>With ExamUploadKit</h3><ol><li>Choose your examination</li><li>Upload your originals</li><li>Review the preview and findings</li><li>Pay and download supported files</li></ol><p className={styles.takeaway}>The exam configures the preparation.</p></article>
                        </div>
                        <div className={styles.reality}><strong>Correct KB. Wrong framing. Still a problem.</strong><p>Changing a background, adding a generated outfit, resizing, compressing and renaming can leave the most important question unanswered: does the result meet this exam’s instructions? File size alone cannot answer it.</p></div>
                    </div>
                </section>

                <section id="comparison" className={`${styles.section} ${styles.soft}`}>
                    <div className="euk-wrap">
                        <h2 className={`euk-display ${styles.sectionTitle}`}>The details make<br />the difference.</h2>
                        <p className={styles.lead}>A practical comparison with a do-it-yourself AI workflow—not a claim that every AI platform has the same capabilities.</p>
                        <div className={styles.comparison}>
                            <div className={styles.columnHeads} aria-hidden="true"><span>The requirement</span><span>You + general AI tools</span><span>With ExamUploadKit</span></div>
                            {comparisons.map(([topic, diy, euk]) => <article className={styles.comparisonRow} key={topic}><h3>{topic}</h3><div><span className={styles.mobileLabel}>You + general AI tools</span><p>{diy}</p></div><div className={styles.ourCell}><span className={styles.mobileLabel}>With ExamUploadKit</span><p>{euk}</p></div></article>)}
                        </div>
                        <p className={styles.note}>This compares workflows, not benchmark scores. We have not run a controlled performance comparison against every AI tool.</p>
                    </div>
                </section>

                <section id="identity" className={styles.section}>
                    <div className={`euk-wrap ${styles.identityGrid}`}>
                        <div className={styles.identityStatement}><ScanFace size={52} strokeWidth={1.3} aria-hidden="true" /><h2 className={`euk-display ${styles.sectionTitle}`}>Prepare the file.<br /><span>Keep the person.</span></h2><p>Your exam photo represents you. A more polished image is not necessarily a more suitable identity photograph.</p></div>
                        <div className={styles.identityCopy}>
                            <article><h3>Background editing is not identity generation.</h3><p>ExamUploadKit uses computer vision for face location and background separation. Resizing, compression and restrained capture corrections prepare the file; they do not generate a new face or outfit, reshape features or whiten skin.</p></article>
                            <article><h3>Recent photos and live capture mean what they say.</h3><p>A generated portrait cannot prove recency. An uploaded file cannot replace live capture when the portal requires it. SSC’s Phase-XIV/2026 notice, for example, specifies live photograph capture. <a href="#source-ssc">Read the official notice.</a></p></article>
                            <article><h3>AI detection is not an acceptance test.</h3><p>Detection methods exist, including methods that do not depend on a visible watermark. Their accuracy and limitations vary. We have no basis to say every exam portal uses them or can reliably identify the generator. <a href="#source-nist">See NIST’s research overview.</a></p><p>The useful question is whether your photograph follows the instructions—not whether an alteration might go undetected.</p></article>
                        </div>
                    </div>
                </section>

                <section className={`${styles.section} ${styles.soft}`}>
                    <div className={`euk-wrap ${styles.honesty}`}>
                        <h2 className={`euk-display ${styles.sectionTitle}`}>Free AI can help.<br />So why pay us?</h2>
                        <div><p className={styles.lead}>For the connected workflow, not because free tools are incapable.</p><p>ChatGPT’s free tier includes image creation, file uploads and data analysis, subject to limits. A subscription is not a certificate of exam compliance, and a free plan is not proof of a bad result. <a href="#source-openai">Check the current feature information.</a></p><p>If you know the specifications and are comfortable checking your exported files, doing it yourself may be enough. If you want supported preparation organised around your examination, that is what ExamUploadKit is built for.</p><Link href="/compress-image" className={styles.textLink}>Only need compression? Use our free tool <ArrowRight size={17} aria-hidden="true" /></Link></div>
                    </div>
                </section>

                <section id="cost" className={styles.section}>
                    <div className={`euk-wrap ${styles.pricing}`}>
                        <div><h2 className={`euk-display ${styles.sectionTitle}`}>See the result.<br />Then decide.</h2><p className={styles.lead}>Review the watermarked preview and any findings before paying for your prepared files.</p><p>Photographs, signatures, thumb impressions and handwritten declarations are chargeable. Supported document and PDF work is free.</p></div>
                        <div className={styles.pricePanel}><div><span>One chargeable file</span><strong>{rupees(tier(1))}</strong></div><div><span>Two or more chargeable files</span><strong>{rupees(tier(2))}<small> total</small></strong></div><Link href="/exams" className="primary-button">Choose your exam <ArrowRight size={18} aria-hidden="true" /></Link><p>Check the support status for each file. Final acceptance is the examination authority’s decision.</p></div>
                    </div>
                </section>

                <section id="questions" className={`${styles.section} ${styles.soft}`}>
                    <div className={`euk-wrap ${styles.faqLayout}`}><h2 className={`euk-display ${styles.sectionTitle}`}>Fair questions.<br />Straight answers.</h2><div>{questions.map(({ question, answer }) => <details className={styles.faq} key={question}><summary>{question}</summary><p>{answer}</p></details>)}</div></div>
                </section>

                <section className={`${styles.section} ${styles.sources}`} aria-labelledby="sources-title"><div className="euk-wrap"><h2 id="sources-title">Sources and scope</h2><p>Reviewed 2 October 2026. Product descriptions cover supported preparation against stored requirements. Capabilities, plans and exam instructions can change; the current official notice takes precedence.</p><ol><li id="source-openai"><a href="https://help.openai.com/en/articles/9275245-chatgpt-free-tier-faq">OpenAI: ChatGPT Free Tier FAQ</a> — free features and usage limits.</li><li id="source-ssc"><a href="https://ssc.gov.in/api/attachment/uploads/masterData/NoticeBoards/Notice_of_RHQ_2026_phase_xiv.pdf">SSC: Phase-XIV/2026 Selection Posts notice</a> — exam-specific live photograph instructions, not a rule for every exam.</li><li id="source-nist"><a href="https://doi.org/10.6028/NIST.AI.100-4">NIST AI 100-4: Reducing Risks Posed by Synthetic Content</a> — provenance, watermarking and detection approaches and limitations.</li></ol><p>ExamUploadKit is an independent service, not affiliated with OpenAI or any examination authority. <Link href="/support">Report an outdated comparison or rule.</Link></p></div></section>
            </main>
            <SiteFooter />
        </div>
    );
}
