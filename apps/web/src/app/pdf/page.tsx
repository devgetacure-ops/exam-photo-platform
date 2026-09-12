import Link from "next/link";
import { SiteHeader } from "../../components/site-header";
import { SiteFooter } from "../../components/site-footer";
import { Reveal } from "../../components/euk/reveal";
import { PdfToImage } from "../../components/exam/pdf-to-image";
import { Tick, Cross } from "../../components/exam/specimen-sheet";

export const metadata = {
    title: "PDF work for exam forms · examuploadkit",
    description:
        "Photographs into one PDF, certificates merged, pages reordered, turned or left out, compressed under the form's limit, and any PDF page saved as an image. Free with any file we prepare.",
    alternates: { canonical: "/pdf" },
};

/**
 * The PDF surface, gathered into one page.
 *
 * The work was built and then mentioned in a chip list inside pricing, which
 * is not where a candidate looking for "merge pdf for the ssc form" ever
 * lands. This page says the whole of it, and carries the one tool that needs
 * nothing from us — PDF to image runs in the candidate's own browser — so the
 * page is useful before anybody has paid for anything.
 */

const JOBS = [
    {
        title: "Photographs into one PDF",
        body: "The form wants a PDF and you have three photographs of a marksheet. They go in, in the order you set, as one file.",
    },
    {
        title: "Several files into one",
        body: "A portal that accepts one attachment, and a certificate that reached you as four separate scans.",
    },
    {
        title: "Pages in the order you want",
        body: "Front and back photographed the wrong way round, or a blank page this form never asked for. Move them, drop them, keep what's left.",
    },
    {
        title: "A sideways page turned upright",
        body: "You photographed it the long way round, so it uploads on its side. Turn it a quarter at a time.",
    },
    {
        title: "Under the size limit",
        body: "Forms cap the file at 200 KB, 500 KB, sometimes 1 MB. A scan is compressed down to whatever yours asks for.",
    },
    {
        title: "Named the way the portal expects",
        body: "Some portals refuse a file for its name alone. Yours comes back named to the rule your examination published.",
    },
];

const LIMITS = [
    "We don't read text out of a scan. There is no OCR here.",
    "We don't remove a PDF's password. A locked file is turned away, with a note to upload a copy that has none.",
    "We don't change what is written inside a PDF.",
    "We don't convert Word or Excel files.",
];

export default function PdfPage() {
    return (
        <>
            <SiteHeader />
            <main className="euk euk-pdfpage" id="main-content">
                <section className="euk-pdfpage-top">
                    <div className="euk-wrap euk-pdfpage-head">
                        <div>
                            <h1 className="euk-display euk-pdfpage-title">
                                Your form wants one PDF.
                                <br />
                                <span className="euk-mark">
                                    This is that whole job.
                                </span>
                            </h1>
                            <p className="euk-lede">
                                Portals rarely take what you already have. One
                                PDF of four certificates. An image of a page that
                                came to you as a PDF. Under 500 KB, named their
                                way.
                            </p>
                        </div>

                        {/* The two ways in, stated at the top instead of being
                            discovered two sections down — and it fills the
                            column the lede's reading measure leaves empty. */}
                        <aside className="euk-pdfpage-ways">
                            <div>
                                <p className="euk-label">
                                    Free for anybody, right now
                                </p>
                                <p>
                                    A PDF page saved as an image. It runs inside
                                    your own browser: nothing is uploaded,
                                    nothing is charged, and you need no kit.
                                </p>
                                <a href="#to-image" className="euk-link">
                                    Do it on this page ↓
                                </a>
                            </div>
                            <div>
                                <p className="euk-label">
                                    Free with any prepared file
                                </p>
                                <p>
                                    Pages merged, reordered, removed or rotated,
                                    compressed under the byte limit and named the
                                    way your form asks.
                                </p>
                                <Link href="/exams" className="euk-link">
                                    Find your examination ↗
                                </Link>
                            </div>
                        </aside>
                    </div>
                </section>

                <section className="euk-section" id="to-image">
                    <div className="euk-wrap">
                        <Reveal>
                            <h2 className="euk-display euk-h2">
                                A page as an image, right here
                            </h2>
                            <p className="euk-lede">
                                Nothing is uploaded and nothing is charged. Your
                                PDF opens inside this page, each page is drawn at
                                the resolution you pick, and you save it as JPEG
                                or PNG.
                            </p>
                        </Reveal>
                        <Reveal delay={90} className="euk-pdfpage-tool">
                            <p className="euk-pdfimg-caution">
                                An image of a digitally issued certificate
                                can&rsquo;t be verified the way the PDF can. Use
                                this only when the portal asks for an image.
                            </p>
                            <PdfToImage />
                        </Reveal>
                    </div>
                </section>

                <section className="euk-section euk-section--alt" id="jobs">
                    <div className="euk-wrap">
                        <Reveal>
                            <h2 className="euk-display euk-h2">
                                And everything else a form asks of a PDF
                            </h2>
                            <p className="euk-lede">
                                This work runs alongside the file we prepare, so
                                it follows your examination&rsquo;s own rules for
                                the page, the byte limit and the filename.
                            </p>
                        </Reveal>
                        <Reveal delay={90}>
                            <ul className="euk-pdfpage-jobs">
                                {JOBS.map((job) => (
                                    <li key={job.title} className="euk-pdfpage-job">
                                        <span
                                            className="euk-pdfpage-job-mark"
                                            aria-hidden="true"
                                        >
                                            <Tick />
                                        </span>
                                        <h3>{job.title}</h3>
                                        <p>{job.body}</p>
                                    </li>
                                ))}
                            </ul>
                        </Reveal>
                        <p className="euk-pdfpage-caveat">
                            Where a limit cannot be met without wrecking the page,
                            the result says so instead of pretending.
                        </p>
                    </div>
                </section>

                <section className="euk-section" id="limits">
                    <div className="euk-wrap">
                        <Reveal>
                            <h2 className="euk-display euk-h2">
                                What this doesn&rsquo;t do
                            </h2>
                            <p className="euk-lede">
                                Said plainly, so you don&rsquo;t spend the evening
                                uploading in hope.
                            </p>
                        </Reveal>
                        <Reveal delay={90}>
                            <ul className="euk-pdfpage-limits">
                                {LIMITS.map((limit) => (
                                    <li key={limit}>
                                        <span aria-hidden="true">
                                            <Cross />
                                        </span>
                                        {limit}
                                    </li>
                                ))}
                            </ul>
                        </Reveal>
                        <Reveal delay={150} className="euk-pdfpage-cta">
                            <h3>The PDF work is free with any file we prepare.</h3>
                            <p>
                                One prepared file is ₹3. Everything your
                                examination asks for is ₹8. The PDF work is
                                included in both, and it is the same work either
                                way.
                            </p>
                            <Link href="/exams" className="primary-button">
                                Find your examination
                            </Link>
                        </Reveal>
                        <p className="euk-retention">
                            Files you send us are deleted within 30 minutes, or
                            within an hour if you ask us to keep them. A PDF you
                            turn into an image above never reaches us at all.
                        </p>
                    </div>
                </section>
            </main>
            <SiteFooter />
        </>
    );
}
