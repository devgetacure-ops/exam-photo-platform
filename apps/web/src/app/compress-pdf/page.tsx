import Link from "next/link";

import { CompressPdf } from "../../components/tools/compress-pdf";
import { SiteHeader } from "../../components/site-header";
import { SiteFooter } from "../../components/site-footer";
import { JsonLd } from "../../components/json-ld";
import { Chevron } from "../../components/euk/doodles";
import { absoluteUrl, breadcrumbs, pageMetadata } from "../../lib/site";

export const metadata = pageMetadata({
    title: "Compress a PDF to 100 KB, 200 KB or any size, free",
    description:
        "Reduce a scanned certificate or document PDF to the KB limit your exam form allows, in your own browser. Free, no sign-up, and the file never leaves your device.",
    path: "/compress-pdf",
});

/**
 * Compress a PDF to a size (DEC-098): free and in the browser, like the photo
 * tool. It says plainly what it does to a PDF with real text, because a
 * digitally issued certificate is the one file where that matters.
 */

export default function CompressPdfPage() {
    return (
        <>
            <SiteHeader />
            <main className="euk euk-cmp" id="main-content">
                <JsonLd
                    data={{
                        "@context": "https://schema.org",
                        "@type": "WebApplication",
                        name: "Compress a PDF to a size",
                        url: absoluteUrl("/compress-pdf"),
                        applicationCategory: "UtilitiesApplication",
                        operatingSystem: "Any",
                        browserRequirements: "Requires JavaScript",
                        isAccessibleForFree: true,
                        description:
                            "Compress a PDF to a KB limit inside your own browser. Nothing is uploaded.",
                        offers: { "@type": "Offer", price: "0", priceCurrency: "INR" },
                    }}
                />
                <JsonLd
                    data={breadcrumbs([
                        { name: "Home", path: "/" },
                        { name: "PDF tools", path: "/pdf" },
                        { name: "Compress a PDF", path: "/compress-pdf" },
                    ])}
                />

                <section className="euk-cmp-top">
                    <div className="euk-wrap euk-cmp-head">
                        <div>
                            <h1 className="euk-display euk-cmp-title">
                                Compress a PDF
                                <br />
                                <span className="euk-mark">to the size your form allows.</span>
                            </h1>
                            <p className="euk-lede">
                                Pick the limit, choose the PDF, and download one just
                                under it. Each page is saved as an image, which suits a
                                scanned certificate; text in the result can&rsquo;t be
                                selected, and a digitally signed certificate loses the
                                signature a portal could verify.
                            </p>
                        </div>
                        <div className="euk-cmp-tool">
                            <CompressPdf />
                        </div>
                    </div>
                </section>

                <section className="euk-cmp-more">
                    <div className="euk-wrap">
                        <h2 className="euk-display">More than one file into one PDF?</h2>
                        <p>
                            Merging certificates, turning photographs into a PDF and
                            putting pages in order are on the PDF tools page, and each
                            examination&rsquo;s page prepares its documents to its rules.
                        </p>
                        <Link className="primary-button" href="/pdf">
                            PDF tools
                            <Chevron />
                        </Link>
                    </div>
                </section>
            </main>
            <SiteFooter />
        </>
    );
}
