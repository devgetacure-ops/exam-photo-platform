import { deadlineStatus, stampText, type Deadline } from "../../lib/deadlines";

/** The ink stamp on a deadline: "Closes in 2 days", "Extended", … (DEC-135). */
export function DeadlineStamp({
    entry,
    today,
    locale = "en",
    small = false,
}: {
    entry: Deadline;
    today: string;
    locale?: "en" | "hi";
    /** The smaller stamp beside a name in a list. */
    small?: boolean;
}) {
    const status = deadlineStatus(entry, today);
    const text = stampText(status, today, locale);
    if (!text) return null;
    return (
        <span className={small ? "euk-dstamp euk-dstamp--small" : "euk-dstamp"} data-state={status.state}>
            {text}
        </span>
    );
}
