"use client";

import Link from "next/link";
import { useTr } from "../locale-context";

export function ReportIssue({
    examName,
    requirementName = "General",
    ruleId = "",
}: {
    examName: string;
    requirementName?: string;
    ruleId?: string;
}) {
    const tr = useTr();
    const context = [examName, requirementName, ruleId]
        .filter(Boolean)
        .join(" · ");
    return (
        <Link
            className="quiet-link"
            href={`/support?exam=${encodeURIComponent(context)}`}
        >
            {tr("Report an issue", "समस्या बताएँ")}
        </Link>
    );
}
