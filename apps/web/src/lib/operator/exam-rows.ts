import type { Deadline } from "../deadlines";

/** One examination on the console's Exams page (DEC-136). */
export interface ExamRow {
    exam_id: string;
    exam_name: string;
    short_name: string | null;
    conducting_body: string | null;
    files: number;
    edited: boolean;
    edited_at: string | null;
    uploads_30d: number;
    dates: {
        opens_on: string | null;
        closes_on: string | null;
        extended_to: string | null;
        exam_date: string | null;
        exam_date_note: string | null;
        source_url: string | null;
        last_verified: string | null;
        note: string | null;
        auto_remind: boolean;
    };
}

export function asDeadline(row: ExamRow): Deadline {
    return {
        examId: row.exam_id,
        examName: row.exam_name,
        shortName: row.short_name,
        conductingBody: row.conducting_body,
        opens: row.dates.opens_on,
        closes: row.dates.closes_on,
        extendedTo: row.dates.extended_to,
        examDate: row.dates.exam_date,
        examDateNote: row.dates.exam_date_note,
        sourceUrl: row.dates.source_url,
        lastVerified: row.dates.last_verified,
    };
}

export function hasDates(row: ExamRow): boolean {
    return Boolean(row.dates.closes_on || row.dates.exam_date || row.dates.opens_on);
}
