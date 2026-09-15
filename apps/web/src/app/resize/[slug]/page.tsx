import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { loadSpecTargets } from "../../../lib/catalogue.server";
import type { SpecTarget } from "../../../lib/seo-keywords";
import { CompressImage } from "../../../components/tools/compress-image";
import { CropResize } from "../../../components/tools/crop-resize";
import { SiteHeader } from "../../../components/site-header";
import { SiteFooter } from "../../../components/site-footer";
import { JsonLd } from "../../../components/json-ld";
import { absoluteUrl, breadcrumbs, pageMetadata } from "../../../lib/site";

/**
 * One page per published size (DEC-098): "compress signature to 20kb",
 * "photo 200x230". Only sizes a record published get a page, the same list
 * the keyword map targets, and each names the examinations that publish it.
 *
 * A KB limit opens the compress tool on that limit. An exact pixel size opens
 * the crop frame at that shape, so nothing is stretched. Both run in the
 * browser; the examination pages remain where a file is prepared to every
 * rule at once.
 */

export const dynamicParams = false;

export async function generateStaticParams() {
    const { targets } = await loadSpecTargets();
    return targets.map((target) => ({ slug: target.slug }));
}

const DOCUMENTS = new Set(["certificate", "id proof", "declaration"]);

function label(word: string): string {
    return word === "id proof" ? "ID proof" : word;
}

function article(word: string): string {
    return /^(id|[aeiou])/i.test(word) ? "an" : "a";
}

function kilobytes(target: SpecTarget): number {
    return target.unit === "mb" ? (target.max ?? 0) * 1000 : (target.max ?? 0);
}

function heading(target: SpecTarget): string {
    const thing = `${article(target.word)} ${label(target.word)}`;
    return target.kind === "size"
        ? `Compress ${thing} to ${target.max} ${target.unit?.toUpperCase()}`
        : `Resize ${thing} to ${target.width} × ${target.height} pixels`;
}

async function find(slug: string) {
    const { exams, targets } = await loadSpecTargets();
    const target = targets.find((entry) => entry.slug === slug);
    if (!target) return null;
    const members = exams
        .filter((exam) => target.examIds.includes(exam.exam_id))
        .sort((a, b) => a.exam_name.localeCompare(b.exam_name));
    return { target, members };
}

export async function generateMetadata({
    params,
}: {
    params: Promise<{ slug: string }>;
}): Promise<Metadata> {
    const { slug } = await params;
    const found = await find(slug);
    if (!found) return { title: "Size not found" };
    const { target, members } = found;
    const named = members.slice(0, 3).map((exam) => exam.exam_name).join(", ");
    const what =
        target.kind === "size"
            ? `${article(target.word)} ${label(target.word)} of at most ${target.max} ${target.unit?.toUpperCase()}`
            : `${article(target.word)} ${label(target.word)} of ${target.width} × ${target.height} px`;
    return pageMetadata({
        title: `${heading(target)}, free`,
        description: `${heading(target)} in your own browser. ${members.length} examination${members.length === 1 ? "" : "s"} we cover ask${members.length === 1 ? "s" : ""} for ${what}, including ${named}.`,
        path: `/resize/${target.slug}`,
    });
}

export default async function ResizePage({ params }: { params: Promise<{ slug: string }> }) {
    const { slug } = await params;
    const found = await find(slug);
    if (!found) notFound();
    const { target, members } = found;
    const noun = label(target.word);
    const kb = kilobytes(target);

    return (
        <>
            <SiteHeader />
            <main className="euk euk-cmp" id="main-content">
                <JsonLd
                    data={{
                        "@context": "https://schema.org",
                        "@type": "WebApplication",
                        name: heading(target),
                        url: absoluteUrl(`/resize/${target.slug}`),
                        applicationCategory: "UtilitiesApplication",
                        operatingSystem: "Any",
                        browserRequirements: "Requires JavaScript",
                        isAccessibleForFree: true,
                        offers: { "@type": "Offer", price: "0", priceCurrency: "INR" },
                    }}
                />
                <JsonLd
                    data={breadcrumbs([
                        { name: "Home", path: "/" },
                        { name: "Compress a photo", path: "/compress-image" },
                        { name: heading(target), path: `/resize/${target.slug}` },
                    ])}
                />

                <section className="euk-cmp-top">
                    <div className="euk-wrap euk-cmp-head">
                        <div>
                            <h1 className="euk-display euk-cmp-title">{heading(target)}</h1>
                            <p className="euk-lede">
                                {target.kind === "size"
                                    ? `Choose the ${noun} and download a JPEG just under ${target.max} ${target.unit?.toUpperCase()}.`
                                    : `Place the ${noun} in the frame and download a JPEG of exactly ${target.width} × ${target.height} pixels, never stretched.`}
                            </p>
                            {target.kind === "size" && DOCUMENTS.has(target.word) && (
                                <p className="euk-resize-pdf">
                                    <Link href={`/compress-pdf?kb=${kb}`}>
                                        Is it a PDF? Compress a PDF to {kb} KB
                                    </Link>
                                </p>
                            )}
                        </div>
                        <div className="euk-cmp-tool">
                            {target.kind === "size" ? (
                                <CompressImage initialKb={kb} noun={noun} />
                            ) : (
                                <CropResize width={target.width!} height={target.height!} noun={noun} />
                            )}
                        </div>
                    </div>
                </section>

                <section className="euk-cmp-more">
                    <div className="euk-wrap">
                        <h2 className="euk-display">
                            {members.length === 1
                                ? "The examination that asks for this"
                                : `The ${members.length} examinations that ask for this`}
                        </h2>
                        <ul className="euk-resize-exams">
                            {members.map((exam) => (
                                <li key={exam.exam_id}>
                                    <Link href={`/exam/${exam.exam_id}`}>{exam.exam_name}</Link>
                                </li>
                            ))}
                        </ul>
                        <p>
                            {target.word === "photo"
                                ? "An examination photograph usually has rules beyond its size: a plain background, and a frame tight around the face. Each examination's page prepares the photograph to all of them."
                                : "Each examination's page lists every file it asks for and prepares them to its rules."}
                        </p>
                    </div>
                </section>
            </main>
            <SiteFooter />
        </>
    );
}
