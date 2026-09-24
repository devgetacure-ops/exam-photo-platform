import type { Metadata } from "next";
import Link from "next/link";
import { ActionForm, Badge, Button, Card, Check, Input, PageHeader, Problem, cn } from "../../../../components/console/ui";
import { rupees } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

export const metadata: Metadata = { title: "Calendar" };

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

function left(row: CalendarRow) {
    if (row.days_left == null) return <Badge>No date</Badge>;
    if (row.days_left < 0) return <Badge>Closed</Badge>;
    if (row.days_left === 0) return <Badge tone="bad">Closes today</Badge>;
    return <Badge tone={row.days_left <= 7 ? "bad" : row.days_left <= 21 ? "warn" : "neutral"}>{row.days_left} days left</Badge>;
}

export default async function CalendarPage({ searchParams }: { searchParams: Promise<{ q?: string; edit?: string }> }) {
    await requireOperator();
    const { q = "", edit } = await searchParams;
    const loaded = await engineJson<{ exams: CalendarRow[] }>("/v1/operator/calendar");
    if (!loaded.ok) return <Problem what="the calendar" error={loaded.error} />;
    const needle = q.trim().toLowerCase();
    const rows = loaded.value.exams.filter((row) => !needle || row.exam_name.toLowerCase().includes(needle));
    const upcoming = rows.filter((row) => row.days_left != null && row.days_left >= 0);
    const rest = rows.filter((row) => !(row.days_left != null && row.days_left >= 0));

    const table = (list: CalendarRow[]) => (
        <div className="op-scroll overflow-x-auto">
            <table className="w-full min-w-[720px] border-collapse text-sm">
                <thead>
                    <tr className="border-b border-[var(--op-border)] bg-[var(--op-muted-bg)] text-left text-xs text-[var(--op-muted)]">
                        <th scope="col" className="px-5 py-2.5 font-medium">Examination</th>
                        <th scope="col" className="px-3 py-2.5 font-medium">Closes</th>
                        <th scope="col" className="px-3 py-2.5 text-right font-medium">Uploads, 30 d</th>
                        <th scope="col" className="px-3 py-2.5 text-right font-medium">Revenue, 30 d</th>
                        <th scope="col" className="px-3 py-2.5 text-right font-medium">Past customers</th>
                        <th scope="col" className="px-5 py-2.5 text-right font-medium">
                            <span className="sr-only">Edit</span>
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {list.map((row) => (
                        <tr key={row.exam_id} className="border-b border-[var(--op-border)] align-top last:border-0">
                            <td className="px-5 py-3">
                                <div className="font-medium">{row.exam_name}</div>
                                {row.note && <div className="text-xs text-[var(--op-muted)]">{row.note}</div>}
                                {edit === row.exam_id && (
                                    <ActionForm action={`/admin/actions/deadline/${row.exam_id}`} back={`/admin/calendar${q ? `?q=${encodeURIComponent(q)}` : ""}`} className="mt-3 flex flex-col gap-2">
                                        <div className="flex flex-wrap gap-2">
                                            <Input type="date" name="closes_on" defaultValue={row.closes_on ?? ""} aria-label="Closing date" className="w-44" />
                                            <Input name="note" maxLength={300} defaultValue={row.note ?? ""} placeholder="Where the date came from" aria-label="Note" className="min-w-0 flex-1" />
                                        </div>
                                        <Check name="auto_remind" value="yes" defaultChecked={row.auto_remind}>
                                            Email everyone who paid for it, 3 days before it closes
                                        </Check>
                                        <div className="flex gap-2">
                                            <Button type="submit" variant="primary" size="sm">
                                                Save
                                            </Button>
                                            <Link href={`/admin/calendar${q ? `?q=${encodeURIComponent(q)}` : ""}`} className="flex h-8 items-center px-3 text-[13px] text-[var(--op-muted)]">
                                                Cancel
                                            </Link>
                                        </div>
                                    </ActionForm>
                                )}
                            </td>
                            <td className="px-3 py-3">
                                <div className="flex flex-col items-start gap-1">
                                    {left(row)}
                                    {row.closes_on && <span className="text-xs text-[var(--op-muted)]">{row.closes_on}{row.auto_remind ? " · reminder on" : ""}</span>}
                                </div>
                            </td>
                            <td className="op-num px-3 py-3 text-right">{row.uploads_30d}</td>
                            <td className="op-num px-3 py-3 text-right">{rupees(row.revenue_30d_paise)}</td>
                            <td className="op-num px-3 py-3 text-right">{row.past_customers}</td>
                            <td className="px-5 py-3 text-right">
                                {edit !== row.exam_id && (
                                    <Link href={`/admin/calendar?${new URLSearchParams({ ...(q ? { q } : {}), edit: row.exam_id })}`} className="text-[13px] font-medium underline">
                                        {row.closes_on ? "Edit" : "Set date"}
                                    </Link>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );

    return (
        <>
            <PageHeader title="Calendar" description="Closing dates you enter, beside what each examination brings in. With the reminder on, past customers are emailed 3 days before, once, at 9:00 IST." />
            <form method="get" className="flex max-w-sm gap-2">
                <Input name="q" defaultValue={q} placeholder="Find an examination" aria-label="Find an examination" />
                <Button type="submit">Find</Button>
            </form>
            {upcoming.length > 0 && (
                <Card className={cn(upcoming.some((r) => (r.days_left ?? 99) <= 7) && "border-[var(--op-warn)]")}>
                    <div className="border-b border-[var(--op-border)] px-5 py-3.5 text-[15px] font-semibold">Coming up</div>
                    {table(upcoming)}
                </Card>
            )}
            <Card>
                <div className="border-b border-[var(--op-border)] px-5 py-3.5 text-[15px] font-semibold">All examinations</div>
                {table(rest)}
            </Card>
        </>
    );
}
