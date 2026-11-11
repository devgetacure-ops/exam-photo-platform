import Link from "next/link";
import { loadExams } from "../../lib/catalogue.server";
import { examSpecs } from "../../lib/exam-answers";
import { familyOf } from "../../lib/exam-families";
import type { ExamDetail } from "../../lib/types";

const SHOWN = 6;

/** Words that say nothing about which examination this is. */
const NOISE = new Set(["and", "of", "the", "for", "exam", "examination", "test", "recruitment", "online", "application"]);

function words(text: string | null | undefined): Set<string> {
    return new Set(
        (text ?? "")
            .toLowerCase()
            .split(/[^a-z]+/)
            .filter((word) => word.length > 2 && !NOISE.has(word)),
    );
}

function overlap(a: Set<string>, b: Set<string>): number {
    let count = 0;
    for (const word of a) if (b.has(word)) count += 1;
    return count;
}

/**
 * Other examinations a candidate applying to this one is likely to apply to
 * as well (DEC-128): the same conducting body first, then the rest of its
 * family, each with its photograph size so the list answers on its own. A
 * candidate applies to several in one season; this is where the next one is.
 */
export async function ExamRelated({ exam }: { exam: ExamDetail }) {
    const family = familyOf(exam.category);
    if (!family) return null;
    const members = (await loadExams()).filter(
        (other) => other.exam_id !== exam.exam_id && familyOf(other.category)?.slug === family.slug,
    );
    if (members.length === 0) return null;
    const score = (other: ExamDetail) =>
        4 * Number(other.conducting_body === exam.conducting_body) +
        2 * overlap(words(other.category), words(exam.category)) +
        overlap(words(other.exam_name), words(exam.exam_name));
    const ranked = [...members].sort(
        (a, b) => score(b) - score(a) || a.exam_name.localeCompare(b.exam_name),
    );
    const shown = ranked.slice(0, SHOWN).map((other) => {
        const photo = examSpecs(other).find((spec) => spec.type === "photograph");
        const size = photo?.rows
            .filter((row) => row.term === "Dimensions" || row.term === "File size")
            .map((row) => `${row.value}${row.estimated ? " (est.)" : ""}`)
            .join(" · ");
        return { id: other.exam_id, name: other.exam_name, size };
    });

    return (
        <section className="euk-related" aria-labelledby="exam-related-title">
            <div className="euk-wrap">
                <h2 id="exam-related-title" className="euk-display euk-related-title">
                    Applying to more?
                </h2>
                <ul className="euk-related-list">
                    {shown.map((item) => (
                        <li key={item.id}>
                            <Link href={`/exam/${item.id}`}>
                                <strong>{item.name}</strong>
                                {item.size && <span>Photo {item.size}</span>}
                            </Link>
                        </li>
                    ))}
                </ul>
                <Link className="euk-link euk-related-all" href={`/exams/${family.slug}`}>
                    All {members.length + 1} {family.phrase} examinations
                </Link>
            </div>
        </section>
    );
}
