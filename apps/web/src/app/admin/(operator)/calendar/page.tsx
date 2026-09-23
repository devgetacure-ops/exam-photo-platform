import Link from "next/link";
import { ActionForm, Failure } from "../../../../components/operator/ui";
import { rupees } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

interface CalendarRow {
    exam_id: string;
    exam_name: string;
    closes_on: string | null;
    days_left: number | null;
    note: string | null;
    auto_remind: boolean;
    uploads_30d: number;
    revenue_30d_paise: number;
    past_customers: number;
}

export default async function CalendarPage({ searchParams }: { searchParams: Promise<{ all?: string }> }) {
    await requireOperator();
    const showAll = (await searchParams).all === "1";
    const loaded = await engineJson<{ exams: CalendarRow[] }>("/v1/operator/calendar");
    if (!loaded.ok) return <Failure what="the calendar" error={loaded.error} />;
    const rows = loaded.value.exams;
    const dated = rows.filter((row) => row.days_left != null && row.days_left >= 0);
    const rest = rows.filter((row) => !(row.days_left != null && row.days_left >= 0));

    return (
        <>
            <h1>Deadline calendar</h1>
            <p className="euk-op-quiet">
                Enter an examination&rsquo;s closing date to see what is coming. With the reminder ticked, everyone who paid for it is
                emailed three days before it closes, once, at 9:00 IST.
            </p>
            <section className="euk-op-section">
                <h2>Closing soon</h2>
                {dated.length === 0 && <p className="euk-op-quiet">No dates entered yet.</p>}
                <ul className="euk-op-list">
                    {dated.map((row) => (
                        <Row key={row.exam_id} row={row} />
                    ))}
                </ul>
            </section>
            <section className="euk-op-section">
                <h2>Every examination</h2>
                <ul className="euk-op-list">
                    {(showAll ? rest : rest.slice(0, 15)).map((row) => (
                        <Row key={row.exam_id} row={row} />
                    ))}
                </ul>
                {!showAll && rest.length > 15 && (
                    <p>
                        <Link href="/admin/calendar?all=1">Show all {rest.length}</Link>
                    </p>
                )}
            </section>
        </>
    );
}

function Row({ row }: { row: CalendarRow }) {
    const soon = row.days_left != null && row.days_left >= 0 && row.days_left <= 7;
    return (
        <li className="euk-op-card" data-state={soon ? "refund-due" : undefined}>
            <p className="euk-op-row">
                <strong>{row.exam_name}</strong>
                <span>
                    {row.days_left == null ? "no date" : row.days_left < 0 ? "closed" : row.days_left === 0 ? "closes today" : `${row.days_left} days left`}
                </span>
            </p>
            <p className="euk-op-quiet">
                {row.uploads_30d} uploads and {rupees(row.revenue_30d_paise)} in 30 days · {row.past_customers} past customer
                {row.past_customers === 1 ? "" : "s"}
            </p>
            <details>
                <summary>{row.closes_on ? `Closes ${row.closes_on}${row.auto_remind ? " · reminder on" : ""}` : "Set a closing date"}</summary>
                <ActionForm action={`/admin/actions/deadline/${row.exam_id}`} back="/admin/calendar">
                    <label>
                        <span className="euk-label">Closing date</span>
                        <input type="date" name="closes_on" defaultValue={row.closes_on ?? ""} />
                    </label>
                    <label>
                        <span className="euk-label">Note</span>
                        <input name="note" maxLength={300} defaultValue={row.note ?? ""} placeholder="Where the date came from" />
                    </label>
                    <label className="euk-op-check">
                        <input type="checkbox" name="auto_remind" value="yes" defaultChecked={row.auto_remind} />
                        Email past customers three days before
                    </label>
                    <button type="submit" className="euk-op-button">
                        Save
                    </button>
                </ActionForm>
            </details>
        </li>
    );
}
