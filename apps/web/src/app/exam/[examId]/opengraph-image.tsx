import { ImageResponse } from "next/og";

import { OG_SIZE, OgCard, og } from "../../../components/og-card";
import { loadExam, loadExams } from "../../../lib/catalogue.server";
import { examSpecs } from "../../../lib/exam-answers";

/**
 * The preview for an examination's link: its name and the figures a candidate
 * is looking for, so a shared link answers the question before it is opened.
 * Also the preview for its rules page, which sits under this segment.
 */

export const alt = "The upload file sizes this examination asks for";
export const size = OG_SIZE;
export const contentType = "image/png";

export async function generateStaticParams() {
    const exams = await loadExams();
    return exams.map((exam) => ({ examId: exam.exam_id }));
}

export default async function Image({ params }: { params: Promise<{ examId: string }> }) {
    const { examId } = await params;
    const exam = await loadExam(examId);
    const name = exam?.exam_name ?? "Your examination";
    const specs = exam ? examSpecs(exam).slice(0, 3) : [];

    return new ImageResponse(
        (
            <OgCard footer={exam ? `Set by ${exam.conducting_body} · examuploadkit.com` : "examuploadkit.com"}>
                <div style={{ display: "flex", fontSize: name.length > 40 ? 58 : 74, lineHeight: 1.05, color: og.INK }}>
                    {name}
                </div>
                <div style={{ display: "flex", flexDirection: "column", marginTop: 26 }}>
                    {specs.length > 0 ? (
                        specs.map(({ label, rows }) => (
                            <div key={label} style={{ display: "flex", fontSize: 30, marginTop: 10 }}>
                                <span style={{ background: og.SIGNAL, padding: "0 10px", marginRight: 16 }}>
                                    {label.charAt(0).toUpperCase() + label.slice(1)}
                                </span>
                                <span>
                                    {rows
                                        .filter((row) => row.term !== "Background")
                                        .map((row) => `${row.value}${row.estimated ? " (est.)" : ""}`)
                                        .join(" · ")}
                                </span>
                            </div>
                        ))
                    ) : (
                        <div style={{ display: "flex", fontSize: 32 }}>
                            Photo, signature and document upload rules
                        </div>
                    )}
                </div>
            </OgCard>
        ),
        size,
    );
}
