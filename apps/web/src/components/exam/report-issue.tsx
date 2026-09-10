import Link from "next/link";

export function ReportIssue({
    examName,
    requirementName = "General",
    ruleId = "",
}: {
    examName: string;
    requirementName?: string;
    ruleId?: string;
}) {
    const context = [examName, requirementName, ruleId]
        .filter(Boolean)
        .join(" · ");
    return (
        <Link
            className="quiet-link"
            href={`/support?exam=${encodeURIComponent(context)}`}
        >
            Report an issue
        </Link>
    );
}
