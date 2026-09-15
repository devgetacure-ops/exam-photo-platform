import Link from "next/link";

import { CompressImage } from "../../components/tools/compress-image";
import { SiteHeader } from "../../components/site-header";
import { SiteFooter } from "../../components/site-footer";
import { JsonLd } from "../../components/json-ld";
import { Chevron } from "../../components/euk/doodles";
import { EXAM_FAMILIES } from "../../lib/exam-families";
import { absoluteUrl, breadcrumbs, pageMetadata } from "../../lib/site";

export const metadata = pageMetadata({
    title: "Compress a photo to 20 KB, 50 KB or any size, free",
    description:
        "Reduce a photo or signature to the KB limit your exam form allows, in your own browser. Free, no sign-up, and the photo never leaves your device.",
    path: "/compress-image",
});

/**
 * Compress to a size (DEC-096): the most searched tool phrase around
 * application forms, and one that names no examination. Free and in the
 * browser, the owner's choice, so it costs nothing to run and nothing leaves
 * the candidate's phone. The page then says, once, that a form's size limit
 * is usually one rule among several, and points to the examinations.
 */

export default function CompressImagePage() {
    return (
        <>
            <SiteHeader />
            <main className="euk euk-cmp" id="main-content">
                <JsonLd
                    data={{
                        "@context": "https://schema.org",
                        "@type": "WebApplication",
                        name: "Compress a photo to a size",
                        url: absoluteUrl("/compress-image"),
                        applicationCategory: "UtilitiesApplication",
                        operatingSystem: "Any",
                        browserRequirements: "Requires JavaScript",
                        isAccessibleForFree: true,
                        description:
                            "Compress a photo or signature to a KB limit inside your own browser. Nothing is uploaded.",
                        offers: { "@type": "Offer", price: "0", priceCurrency: "INR" },
                    }}
                />
                <JsonLd
                    data={breadcrumbs([
                        { name: "Home", path: "/" },
                        { name: "Compress a photo", path: "/compress-image" },
                    ])}
                />

                <section className="euk-cmp-top">
                    <div className="euk-wrap euk-cmp-head">
                        <div>
                            <h1 className="euk-display euk-cmp-title">
                                Compress a photo
                                <br />
                                <span className="euk-mark">to the size your form allows.</span>
                            </h1>
                            <p className="euk-lede">
                                Pick the limit, choose the photo, and download a JPEG
                                just under it. It works for a signature too.
                            </p>
                        </div>
                        <div className="euk-cmp-tool">
                            <CompressImage />
                        </div>
                    </div>
                </section>

                <section className="euk-cmp-more">
                    <div className="euk-wrap">
                        <h2 className="euk-display">Size is often one rule of several.</h2>
                        <p>
                            Many forms also set the photograph&rsquo;s pixel dimensions,
                            its background and how tightly the face is framed. Pick your
                            examination and each file comes back prepared to all of its
                            rules.
                        </p>
                        <Link className="primary-button" href="/exams">
                            Find your examination
                            <Chevron />
                        </Link>
                        <div className="euk-cmp-families">
                            <nav className="euk-hub-families" aria-label="Exam families">
                                <ul>
                                    {EXAM_FAMILIES.map((family) => (
                                        <li key={family.slug}>
                                            <Link href={`/exams/${family.slug}`}>{family.name}</Link>
                                        </li>
                                    ))}
                                </ul>
                            </nav>
                        </div>
                    </div>
                </section>
            </main>
            <SiteFooter />
        </>
    );
}
