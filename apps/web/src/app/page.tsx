import Image from "next/image";
import Link from "next/link";
import { ExamSearch } from "../components/exam-search";
import { SiteHeader } from "../components/site-header";
import { SiteFooter } from "../components/site-footer";
import { FileComparison } from "../components/file-comparison";
import { loadSearchIndex } from "../lib/catalogue.server";
import illustration from "./assets/upload-kit-illustration.png";

export default async function Home() {
    const { exams, unavailable } = await loadSearchIndex();
    const popular = [
        {
            label: "IBPS PO",
            exam: exams.find((e) => e.name.includes("IBPS CRP PO")),
        },
        { label: "NEET UG", exam: exams.find((e) => e.name.includes("NEET")) },
        { label: "GATE", exam: exams.find((e) => e.name.includes("GATE")) },
    ].filter((item) => item.exam);
    return (
        <main className="landing" id="main-content">
            <SiteHeader />
            <section className="landing-hero">
                <div className="arrival-copy">
                    <p className="arrival-note">
                        Your next chapter starts with an application.
                    </p>
                    <h1>
                        You prepare for the exam.
                        <br />
                        <span>We’ll prepare the files.</span>
                    </h1>
                    <p className="hero-description">
                        The photo. The signature. The right size, format and
                        filename. Bring your uploads together, with your exam’s
                        rules doing the guiding.
                    </p>
                    <div className="search-section" id="find-exam">
                        <p className="search-label">
                            Let’s start with your exam
                        </p>
                        <ExamSearch exams={exams} unavailable={unavailable} />
                        <div className="popular-exams">
                            <span>Popular choices</span>
                            {popular.map(({ label, exam }) => (
                                <Link key={exam!.id} href={`/exam/${exam!.id}`}>
                                    {label}
                                    <span aria-hidden="true"> ↗</span>
                                </Link>
                            ))}
                        </div>
                    </div>
                    <div className="landing-assurance">
                        <span>From ₹3</span>
                        <span>No account needed</span>
                        <span>{exams.length} exams in the catalogue</span>
                    </div>
                </div>
                <div className="hero-kit">
                    <div className="hero-kit-heading">
                        <span>Your application, coming together</span>
                        <span className="small-tag">Exam first</span>
                    </div>
                    <Image
                        src={illustration}
                        priority
                        sizes="(max-width: 760px) 90vw, 45vw"
                        alt="Fictional illustrated student portrait, signature and documents arranged as an application kit"
                    />
                    <div className="hero-kit-caption">
                        <span>Photograph · Signature · Documents</span>
                        <strong>One place. One less thing.</strong>
                    </div>
                    <p className="art-disclosure">
                        Fictional illustration · Your exam sets the
                        specifications
                    </p>
                </div>
            </section>
            <div className="editorial-strip">
                <span>Made for the details that matter.</span>
                <p>Exam-specific sizing</p>
                <p>Clear findings</p>
                <p>Your identity, preserved</p>
                <p>Review before paying</p>
            </div>
            <section className="story-section" aria-labelledby="story-title">
                <div>
                    <h2 id="story-title">
                        One application.
                        <br /> A surprising number
                        <br />
                        of open tabs.
                    </h2>
                    <p>
                        Resize here. Compress there. Convert it, rename it, then
                        wonder whether it still meets the rules. Your
                        application shouldn’t become a file-editing project.
                    </p>
                </div>
                <div className="file-story">
                    <ol>
                        <li>
                            <span aria-hidden="true">↔</span>
                            <strong>“Is this the right crop?”</strong>
                            <small>Head framing and background</small>
                        </li>
                        <li>
                            <span aria-hidden="true">↙</span>
                            <strong>“Now the file is too big.”</strong>
                            <small>Dimensions, format and compression</small>
                        </li>
                        <li>
                            <span aria-hidden="true">Aa</span>
                            <strong>“What am I supposed to call it?”</strong>
                            <small>The filename your portal expects</small>
                        </li>
                    </ol>
                    <div className="story-resolution">
                        <span>One connected workflow</span>
                        <strong>Choose the exam. We take it from there.</strong>
                    </div>
                </div>
            </section>
            <section className="demo-section">
                <div className="demo-copy">
                    <h2>
                        Better prepared.
                        <br />
                        <span>Still entirely you.</span>
                    </h2>
                    <p>
                        Natural framing. Exam-led formatting. A clear
                        explanation when something needs your attention. No
                        reshaping, whitening or cosmetic retouching.
                    </p>
                    <p className="fine-copy">
                        After you upload, compare your original with the actual
                        watermarked preview. This illustration demonstrates the
                        interaction; it isn’t a processed photograph.
                    </p>
                </div>
                <FileComparison
                    before={illustration.src}
                    after={illustration.src}
                    illustration
                />
            </section>
            <section className="how-section" id="how-it-works">
                <div>
                    <h2>
                        From “what size?”
                        <br />
                        to your next step.
                    </h2>
                    <p className="section-description">
                        You stay in control. We make the file work easier.
                    </p>
                </div>
                <ol>
                    {[
                        [
                            "Find your exam",
                            "See the upload checklist, published rules and sources. We clearly separate files we prepare from steps you complete yourself.",
                        ],
                        [
                            "Choose your files",
                            "Prepare only what you need. Photograph, signature, thumb impression or document—where your exam supports it.",
                        ],
                        [
                            "Review every detail",
                            "Inspect your protected preview and any findings. PDFs have no visual preview; we say so before you buy.",
                        ],
                        [
                            "Pay, download, get going",
                            "Check the final price and deletion deadline. Download the released files and save them somewhere safe.",
                        ],
                    ].map(([title, detail]) => (
                        <li key={title}>
                            <span aria-hidden="true">↗</span>
                            <div>
                                <h3>{title}</h3>
                                <p>{detail}</p>
                            </div>
                        </li>
                    ))}
                </ol>
            </section>
            <section className="pricing-section" id="pricing">
                <div className="section-heading">
                    <h2>
                        Pay for the preparation.
                        <br />
                        Keep your time for what’s next.
                    </h2>
                    <p>
                        One-time pricing for the files we can prepare. Supported
                        PDF document work is included with your purchase.
                    </p>
                </div>
                <div className="pricing-grid">
                    {[
                        {
                            title: "Just the one",
                            amount: "3",
                            was: "4",
                            detail: "One photograph, signature or other chargeable image.",
                            tag: "One file",
                        },
                        {
                            title: "The essential pair",
                            amount: "5",
                            was: "8",
                            detail: "Two chargeable images, such as your photograph and signature.",
                            tag: "Two files",
                        },
                        {
                            title: "Bring it together",
                            amount: "8",
                            was: "10",
                            detail: "Three or more chargeable images. The price stops here.",
                            tag: "Three or more",
                        },
                    ].map((tier, i) => (
                        <article
                            className={`price-option ${i === 1 ? "featured" : ""}`}
                            key={tier.title}
                        >
                            <p className="eyebrow">{tier.tag}</p>
                            <h3>{tier.title}</h3>
                            <p className="price-figure">
                                <span>₹{tier.amount}</span>
                                <del>₹{tier.was}</del>
                            </p>
                            <p>{tier.detail}</p>
                            <span className="price-inclusion">
                                Supported PDF work included
                            </span>
                            <Link
                                href="#find-exam"
                                className={
                                    i === 1
                                        ? "primary-button"
                                        : "secondary-button"
                                }
                            >
                                Choose your exam{" "}
                                <span aria-hidden="true">↗</span>
                            </Link>
                        </article>
                    ))}
                </div>
                <p className="pricing-footnote">
                    Your final quote comes from the preparation service. Live
                    capture, portal declarations and unsupported work are not
                    included. Preparing a file does not guarantee authority
                    acceptance.
                </p>
            </section>
            <section className="trust-section">
                <div>
                    <h2>
                        A file that looks right
                        <br />
                        still needs the right checks.
                    </h2>
                </div>
                <div>
                    <p>
                        For example, SSC’s 2022 Ladakh selection-post notice
                        lists unclear photographs and illegible signatures among
                        rejection conditions. Rules differ by exam and
                        cycle—which is why your selected exam drives the work.
                    </p>
                    <a
                        className="quiet-link"
                        href="https://ssc.nic.in/SSCFileServer/PortalManagement/UploadedFiles/notice_rhqladakh_23052022.pdf"
                        target="_blank"
                        rel="noreferrer"
                    >
                        Read the official notice · §20.1.3 ↗
                    </a>
                    <p className="fine-copy">
                        We check face count, coverage, blur, exposure and
                        geometry. Appearance requirements such as headwear
                        remain guidance. Any value chosen by the platform stays
                        marked as an estimate.
                    </p>
                </div>
            </section>
            <section className="our-story" id="our-story">
                <p>Why we’re building this</p>
                <h2>
                    The application is a beginning.
                    <br />
                    <span>It shouldn’t be an obstacle.</span>
                </h2>
                <div>
                    <p>
                        Preparing for an exam asks enough of you. Formatting the
                        files should be a small, manageable part of applying.
                    </p>
                    <p>
                        That’s the idea behind UploadReady: bring the
                        requirements, the preparation and the checks into one
                        considered experience. Give you the details you need,
                        and your time back for what matters next.
                    </p>
                    <Link className="quiet-link" href="/exams">
                        Find your starting point ↗
                    </Link>
                </div>
            </section>
            <section className="faq-section" id="questions">
                <div>
                    <h2>
                        A little clarity
                        <br />
                        goes a long way.
                    </h2>
                </div>
                <div>
                    {[
                        [
                            "Will this guarantee my application is accepted?",
                            "No. We prepare files to stored exam rules and show findings for you to review. Your exam authority makes the final acceptance decision. Always check the current official instructions.",
                        ],
                        [
                            "What happens to my uploads?",
                            "Files are deleted within 30 minutes of preparation, or within an hour if you ask us to keep them. Extend before the deadline, and download your paid files while they are available. Uploads are not used for model training.",
                        ],
                        [
                            "Can I come back to download?",
                            "Return using the same browser before the deletion deadline. Clearing browser data, switching device or using a private window can lose your kit references. Save your downloads as soon as they are released.",
                        ],
                        [
                            "Can you handle every requirement?",
                            "Your exam checklist shows exactly what we can prepare, what is only partly supported, and what you must do yourself. Live-capture photographs and portal declarations cannot be prepared here.",
                        ],
                        [
                            "Can I see a PDF before paying?",
                            "PDF previews are not available. You can review the filename, file details and findings before purchase, but you cannot inspect rendered PDF pages in this service.",
                        ],
                    ].map(([question, answer]) => (
                        <details key={question}>
                            <summary>{question}</summary>
                            <p>{answer}</p>
                        </details>
                    ))}
                </div>
            </section>
            <SiteFooter />
        </main>
    );
}
