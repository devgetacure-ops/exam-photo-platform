import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { loadExams } from "../../../lib/catalogue.server";
import { EXAM_FAMILIES, familyBySlug, familyOf } from "../../../lib/exam-families";
import {
    photographSpecRows,
    requirementSpecRows,
    type SpecRow,
} from "../../../lib/spec-format";
import type { ExamDetail } from "../../../lib/types";
import { SiteHeader } from "../../../components/site-header";
import { SiteFooter } from "../../../components/site-footer";
import { JsonLd } from "../../../components/json-ld";
import { Chevron } from "../../../components/euk/doodles";
import { absoluteUrl, breadcrumbs, pageMetadata } from "../../../lib/site";

/**
 * A family hub (DEC-096): every examination in one family, with its
 * photograph and signature sizes in one list.
 *
 * For the candidate who searches "bank exam photo size" rather than one
 * examination's name, and for the crawler, which reaches every examination
 * page beneath it. Each figure is the one its examination page shows, est.
 * included, because both are read from the same record by the same helpers.
 * On a phone each examination is a block of its own, never a table to scroll
 * sideways.
 */

export const dynamicParams = false;

export function generateStaticParams() {
    return EXAM_FAMILIES.map((family) => ({ family: family.slug }));
}

async function membersOf(slug: string): Promise<ExamDetail[]> {
    const exams = await loadExams();
    return exams
        .filter((exam) => familyOf(exam.category)?.slug === slug)
        .sort((a, b) => a.exam_name.localeCompare(b.exam_name));
}

function sizes(rows: SpecRow[]): { text: string; estimated: boolean } | null {
    const shown = rows.filter((row) => row.term === "Dimensions" || row.term === "File size");
    if (shown.length === 0) return null;
    return {
        text: shown.map((row) => `${row.value}${row.estimated ? " (est.)" : ""}`).join(" · "),
        estimated: shown.some((row) => row.estimated),
    };
}

function photograph(exam: ExamDetail) {
    const requirements = exam.requirements ?? [];
    const uploaded = requirements.find(
        (r) => r.requirement_type === "photograph" && r.submission_method !== "official_live_capture",
    );
    const live = requirements.some(
        (r) => r.requirement_type === "photograph" && r.submission_method === "official_live_capture",
    );
    if (uploaded && exam.image_requirements) {
        const found = sizes(photographSpecRows(exam));
        if (found) return found;
    }
    if (live && !uploaded) return { text: "Taken live on the portal", estimated: false };
    if (uploaded) return { text: "Asked for; see the examination page", estimated: false };
    return { text: "Not listed separately", estimated: false };
}

function signature(exam: ExamDetail) {
    const requirements = exam.requirements ?? [];
    const index = requirements.findIndex((r) => r.requirement_type === "signature");
    if (index < 0) return { text: "Not listed separately", estimated: false };
    return (
        sizes(requirementSpecRows(requirements[index], index, exam.provenance)) ?? {
            text: "Asked for; see the examination page",
            estimated: false,
        }
    );
}

function prepared(exam: ExamDetail): number {
    return (exam.requirements ?? []).filter(
        (r) => r.platform_support === "supported" || r.platform_support === "partially_supported",
    ).length;
}

export async function generateMetadata({
    params,
}: {
    params: Promise<{ family: string }>;
}): Promise<Metadata> {
    const { family: slug } = await params;
    const family = familyBySlug(slug);
    if (!family) return { title: "Exam family not found" };
    const exams = await membersOf(slug);
    const named = exams.slice(0, 3).map((exam) => exam.exam_name).join(", ");
    return pageMetadata({
        title: `${family.name} exam photo and signature size: all ${exams.length}`,
        description: `Photograph and signature sizes for ${exams.length} ${family.phrase} examinations, including ${named}. Each figure is the one the examination's own notice sets.`,
        path: `/exams/${family.slug}`,
    });
}

export default async function FamilyPage({
    params,
}: {
    params: Promise<{ family: string }>;
}) {
    const { family: slug } = await params;
    const family = familyBySlug(slug);
    if (!family) notFound();
    const exams = await membersOf(family.slug);
    const rows = exams.map((exam) => ({
        exam,
        photo: photograph(exam),
        sign: signature(exam),
        files: prepared(exam),
    }));
    const anyEstimate = rows.some((row) => row.photo.estimated || row.sign.estimated);
    const others = EXAM_FAMILIES.filter((other) => other.slug !== family.slug);

    return (
        <>
            <SiteHeader />
            <main className="euk euk-hub" id="main-content">
                <JsonLd
                    data={{
                        "@context": "https://schema.org",
                        "@type": "ItemList",
                        name: `${family.name} examinations`,
                        numberOfItems: exams.length,
                        itemListElement: exams.map((exam, index) => ({
                            "@type": "ListItem",
                            position: index + 1,
                            name: exam.exam_name,
                            url: absoluteUrl(`/exam/${exam.exam_id}`),
                        })),
                    }}
                />
                <JsonLd
                    data={breadcrumbs([
                        { name: "Home", path: "/" },
                        { name: "All examinations", path: "/exams" },
                        { name: family.name, path: `/exams/${family.slug}` },
                    ])}
                />

                <section className="euk-hub-top">
                    <div className="euk-wrap">
                        <p className="euk-label euk-hub-crumb">
                            <Link href="/exams">All examinations</Link>
                        </p>
                        <h1 className="euk-display euk-hub-title">
                            {family.name} exams:
                            <br />
                            <span className="euk-mark">photo and signature sizes.</span>
                        </h1>
                        <p className="euk-lede">
                            {family.blurb} {exams.length} examinations, each with the
                            sizes its own notice sets.
                        </p>
                    </div>
                </section>

                <section className="euk-hub-main" aria-label={`${family.name} examinations`}>
                    <div className="euk-wrap">
                        <ol className="euk-hub-list">
                            {rows.map(({ exam, photo, sign, files }) => (
                                <li key={exam.exam_id} className="euk-hub-item">
                                    <div className="min-w-0">
                                        <h2 className="euk-hub-name">
                                            <Link href={`/exam/${exam.exam_id}`}>{exam.exam_name}</Link>
                                        </h2>
                                        <p className="euk-hub-by">{exam.conducting_body}</p>
                                    </div>
                                    <dl className="euk-hub-specs">
                                        <div>
                                            <dt>Photograph</dt>
                                            <dd>{photo.text}</dd>
                                        </div>
                                        <div>
                                            <dt>Signature</dt>
                                            <dd>{sign.text}</dd>
                                        </div>
                                    </dl>
                                    <Link className="euk-hub-go" href={`/exam/${exam.exam_id}`}>
                                        {files > 0
                                            ? `Prepare ${files} file${files === 1 ? "" : "s"}`
                                            : "See what it asks for"}
                                        <Chevron />
                                    </Link>
                                </li>
                            ))}
                        </ol>
                        {anyEstimate && (
                            <p className="euk-hub-note">
                                A value marked est. is our estimate, because the notice
                                gives no figure for it.
                            </p>
                        )}

                        <nav className="euk-hub-families" aria-labelledby="other-families">
                            <h2 id="other-families" className="euk-display">
                                Other exam families
                            </h2>
                            <ul>
                                {others.map((other) => (
                                    <li key={other.slug}>
                                        <Link href={`/exams/${other.slug}`}>{other.name}</Link>
                                    </li>
                                ))}
                                <li>
                                    <Link href="/exams">All, A to Z</Link>
                                </li>
                            </ul>
                        </nav>
                    </div>
                </section>
            </main>
            <SiteFooter />
        </>
    );
}
