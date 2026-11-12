"use client";

import { deadlineStatus, stampText, todayKey } from "../../lib/deadlines";
import { asDeadline, hasDates, type ExamRow } from "../../lib/operator/exam-rows";
import { DataTable, type Chip, type Column } from "./data-table";
import { Badge } from "./ui";

function DatesBadge({ row }: { row: ExamRow }) {
    if (!hasDates(row)) return <span className="text-xs text-[var(--op-muted)]">No dates</span>;
    const today = todayKey();
    const status = deadlineStatus(asDeadline(row), today);
    if (status.state === "past") return <Badge>Past</Badge>;
    const text = stampText(status, today);
    const tone = status.state === "closing" || status.state === "extended" ? "bad" : status.state === "open" ? "good" : "neutral";
    return <Badge tone={tone}>{text}</Badge>;
}

export function ExamsTable({ exams, chips, selected }: { exams: ExamRow[]; chips: Chip[]; selected?: string | null }) {
    const columns: Column<ExamRow>[] = [
        {
            id: "name",
            header: "Examination",
            value: (row) => `${row.exam_name} ${row.short_name ?? ""} ${row.conducting_body ?? ""}`,
            cell: (row) => (
                <div className="min-w-0">
                    <div className="font-medium">{row.exam_name}</div>
                    <div className="truncate text-xs text-[var(--op-muted)]">{row.conducting_body}</div>
                </div>
            ),
        },
        {
            id: "dates",
            header: "Dates",
            value: (row) => row.dates.extended_to ?? row.dates.closes_on ?? row.dates.exam_date ?? "9999",
            cell: (row) => <DatesBadge row={row} />,
        },
        { id: "files", header: "Files", value: (row) => row.files, align: "right" },
        {
            id: "edited",
            header: "Record",
            value: (row) => (row.edited ? 1 : 0),
            cell: (row) => (row.edited ? <Badge tone="warn">Edited</Badge> : <span className="text-xs text-[var(--op-muted)]">Original</span>),
        },
        { id: "uploads", header: "Uploads, 30 d", value: (row) => row.uploads_30d, align: "right" },
    ];
    return (
        <DataTable
            rows={exams}
            columns={columns}
            rowId={(row) => row.exam_id}
            chips={chips}
            chipParam="show"
            selected={selected}
            searchPlaceholder="Find an examination, body or short name…"
            initialSort={{ id: "dates", desc: false }}
            pageSize={50}
            mobile={(row) => (
                <div className="flex flex-col gap-1">
                    <div className="font-medium">{row.exam_name}</div>
                    <div className="flex flex-wrap items-center gap-2">
                        <DatesBadge row={row} />
                        {row.edited && <Badge tone="warn">Edited</Badge>}
                    </div>
                </div>
            )}
        />
    );
}
