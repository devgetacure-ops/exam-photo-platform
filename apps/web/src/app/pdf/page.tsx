import Link from "next/link";
import { JsonLd } from "../../components/json-ld";
import { absoluteUrl, pageMetadata } from "../../lib/site";
import { SiteHeader } from "../../components/site-header";
import { SiteFooter } from "../../components/site-footer";
import { Reveal } from "../../components/euk/reveal";
import { PdfToImage } from "../../components/exam/pdf-to-image";
import { Tick, Cross } from "../../components/exam/specimen-sheet";
import { PdfAction, PhonePdf } from "../../components/m/pdf-home";
// Shared with the phone's arrangement, so the two never describe different
// work; imported under the names this page has always used.
import { PDF_JOBS as JOBS, PDF_LIMITS as LIMITS } from "../../lib/pdf-work";

export const metadata = pageMetadata({
    title: "PDF work for exam forms: merge, compress and PDF to image",
    description:
        "Photographs into one PDF, certificates merged, pages reordered, turned or left out, compressed under the form's limit, and any PDF page saved as an image. Free with any file we prepare.",
    path: "/pdf",
});

/**
 * The PDF surface, gathered into one page.
 *
 * The work was built and then mentioned in a chip list inside pricing, which
 * is not where a candidate looking for "merge pdf for the ssc form" ever
 * lands. This page says the whole of it, and carries the one tool that needs
 * nothing from us — PDF to image runs in the candidate's own browser — so the
 * page is useful before anybody has paid for anything.
 */

export default function PdfPage() {
    return (
        <>
            <SiteHeader />
            <main className="euk euk-pdfpage" id="main-content">
                {/* Only the converter is a tool anybody can use on its own (DEC-083). */}
                <JsonLd
                    data={{
                        "@context": "https://schema.org",
                        "@type": "WebApplication",
                        name: "PDF page to image",
                        url: absoluteUrl("/pdf"),
                        applicationCategory: "UtilitiesApplication",
                        operatingSystem: "Any",
                        browserRequirements: "Requires JavaScript",
                        isAccessibleForFree: true,
                        description:
                            "Save any page of a PDF as a JPEG or PNG inside your own browser. Nothing is uploaded.",
                        offers: { "@type": "Offer", price: "0", priceCurrency: "INR" },
                    }}
                />
                {/* A phone's own arrangement: the converter as one row that
                    opens its own screen, the rest as rows that open a sheet. */}
                <PhonePdf />
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
                                examination asks for is ₹5. The PDF work is
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
            <PdfAction />
        </>
    );
}
