import type { Metadata } from "next";
import Link from "next/link";

import { ExamEditor } from "../../../../../components/console/exam-editor";
import { PageHeader, Problem } from "../../../../../components/console/ui";
import { engineJson } from "../../../../../lib/operator/engine";
import { requireOperator } from "../../../../../lib/operator/guard";

export const metadata: Metadata = { title: "Edit examination" };

interface ExamDetail {
    exam_id: string;
    record: Record<string, unknown> & { exam?: { exam_name?: string; conducting_body?: string } };
    original: Record<string, unknown> | null;
    edited: boolean;
    edited_at: string | null;
}

/** One examination's whole record, editable (DEC-136). */
export default async function EditExamPage({ params }: { params: Promise<{ examId: string }> }) {
    await requireOperator();
    const { examId } = await params;
    if (!/^[a-z0-9][a-z0-9-]{1,160}$/.test(examId)) return <Problem what="this examination" error="invalid id" />;
    const loaded = await engineJson<ExamDetail>(`/v1/operator/exams/${examId}`);
    if (!loaded.ok) return <Problem what="this examination" error={loaded.error} />;
    const detail = loaded.value;
    return (
        <>
            <PageHeader
                title={detail.record.exam?.exam_name ?? examId}
                description={
                    <>
                        {detail.record.exam?.conducting_body}.{" "}
                        <Link className="underline" href={`/admin/exams?open=${examId}`}>
                            Dates
                        </Link>{" "}
                        ·{" "}
                        <a className="underline" href={`/exam/${examId}`} target="_blank" rel="noreferrer">
                            Public page ↗
                        </a>
                    </>
                }
            />
            <ExamEditor examId={examId} initial={detail.record} original={detail.original} edited={detail.edited} editedAt={detail.edited_at} />
        </>
    );
}
