import { AlertTriangle, CheckCircle2, Clock, CircleDollarSign, MessageSquareWarning, Star } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { BarSeries } from "../../../components/console/charts";
import { Card, CardHeader, Empty, PageHeader, Problem, Stat, cn } from "../../../components/console/ui";
import { bytes, rupees, when, type Health, type Overview } from "../../../lib/operator/data";
import { engineJson } from "../../../lib/operator/engine";
import { requireOperator } from "../../../lib/operator/guard";

export const metadata: Metadata = { title: "Overview" };

const PERIODS: [number, string][] = [
    [1, "Today"],
    [7, "7 days"],
    [30, "30 days"],
    [90, "90 days"],
];

interface Growth {
    visits: number;
    funnel: { step: string; sessions: number }[];
}

function change(now: number, before: number): { text: string | null; good: boolean } {
    if (!before) return { text: now ? "new" : null, good: true };
    const pct = Math.round(((now - before) / before) * 100);
    return { text: `${pct >= 0 ? "▲" : "▼"} ${Math.abs(pct)}%`, good: pct >= 0 };
}

function greeting(): string {
    const hour = Number(new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata", hour: "numeric", hour12: false }));
    return hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
}

export default async function OverviewPage({ searchParams }: { searchParams: Promise<{ days?: string }> }) {
    await requireOperator();
    const requested = Number((await searchParams).days);
    const days = PERIODS.some(([d]) => d === requested) ? requested : 30;
    const [loaded, growth, health] = await Promise.all([
        engineJson<Overview>(`/v1/operator/overview?days=${days * 2}`),
        engineJson<Growth>(`/v1/operator/growth?days=${days}`),
        engineJson<Health>("/v1/operator/health"),
    ]);
    if (!loaded.ok) return <Problem what="the overview" error={loaded.error} />;
    const data = loaded.value;
    const current = data.series.slice(-days);
    const previous = data.series.slice(0, data.series.length - days);
    const sum = (rows: typeof current, key: "revenue_paise" | "orders" | "uploads") => rows.reduce((t, r) => t + r[key], 0);
    const revenueNow = sum(current, "revenue_paise");
    const ordersNow = sum(current, "orders");
    const revenueChange = change(revenueNow, sum(previous, "revenue_paise"));
    const ordersChange = change(ordersNow, sum(previous, "orders"));
    const visits = growth.ok ? growth.value.visits : 0;
    const paidVisits = growth.ok ? (growth.value.funnel.find((f) => f.step === "paid")?.sessions ?? 0) : 0;
    const short = (day: string) => `${Number(day.slice(8, 10))} ${new Date(`${day}T00:00:00Z`).toLocaleString("en-IN", { month: "short", timeZone: "UTC" })}`;

    const todo = [
        ...data.refund_due.map((order) => ({
            key: `r-${order.order_id}`,
            href: `/admin/orders?open=${order.order_id}`,
            icon: CircleDollarSign,
            tone: "bad" as const,
            title: `Refund due · ${rupees(order.amount_paise)}`,
            detail: `${order.exam_names.join(", ") || "Examination not recorded"} · paid, nothing delivered`,
        })),
        ...data.tickets.overdue.map((ticket) => ({
            key: `t-${ticket.id}`,
            href: `/admin/inbox?open=${ticket.id}`,
            icon: MessageSquareWarning,
            tone: "warn" as const,
            title: ticket.ack_overdue ? `${ticket.kind} unanswered for 48 hours` : `${ticket.kind} unresolved after a month`,
            detail: ticket.email ?? "",
        })),
        ...data.refund_review.map((order) => ({
            key: `c-${order.order_id}`,
            href: `/admin/orders?open=${order.order_id}`,
            icon: MessageSquareWarning,
            tone: "warn" as const,
            title: "Complaint on a delivered order",
            detail: order.exam_names.join(", ") || order.order_id,
        })),
        ...(data.reviews.pending
            ? [
                  {
                      key: "reviews",
                      href: "/admin/reviews",
                      icon: Star,
                      tone: data.low_reviews.length ? ("warn" as const) : ("neutral" as const),
                      title: `${data.reviews.pending} review${data.reviews.pending === 1 ? "" : "s"} to approve`,
                      detail: data.low_reviews.length ? `${data.low_reviews.length} rated 2★ or less` : "Approve or reject",
                  },
              ]
            : []),
        ...(data.stuck.length
            ? [
                  {
                      key: "stuck",
                      href: "/admin/uploads?status=error",
                      icon: AlertTriangle,
                      tone: "neutral" as const,
                      title: `${data.stuck.length} failed or refused preparation${data.stuck.length === 1 ? "" : "s"}`,
                      detail: "In the last day",
                  },
              ]
            : []),
    ];
    const dot = { bad: "bg-[var(--op-bad)]", warn: "bg-[var(--op-warn)]", neutral: "bg-[var(--op-faint)]" };

    return (
        <>
            <PageHeader
                title={greeting()}
                description="Here is how the business is doing."
                actions={
                    <div className="flex rounded-lg bg-[var(--op-muted-bg)] p-0.5">
                        {PERIODS.map(([value, label]) => (
                            <Link
                                key={value}
                                href={`/admin?days=${value}`}
                                aria-current={value === days ? "page" : undefined}
                                className={cn(
                                    "rounded-md px-3 py-1.5 text-[13px]",
                                    value === days ? "bg-[var(--op-card)] font-semibold shadow-[var(--op-shadow)]" : "text-[var(--op-muted)] hover:text-[var(--op-text)]",
                                )}
                            >
                                {label}
                            </Link>
                        ))}
                    </div>
                }
            />

            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-4">
                <Stat
                    label="Revenue"
                    value={rupees(revenueNow)}
                    delta={revenueChange.text}
                    good={revenueChange.good}
                    spark={current.map((d) => d.revenue_paise)}
                    foot={`${rupees(data.money.all_time_paise)} all time`}
                />
                <Stat
                    label="Paid orders"
                    value={ordersNow.toLocaleString("en-IN")}
                    delta={ordersChange.text}
                    good={ordersChange.good}
                    spark={current.map((d) => d.orders)}
                    foot={ordersNow ? `Average ${rupees(Math.round(revenueNow / ordersNow))}` : "No orders yet in this period"}
                    href="/admin/orders"
                />
                <Stat
                    label="Visitors who paid"
                    value={visits ? `${((paidVisits / visits) * 100).toFixed(1)}%` : "—"}
                    foot={`${visits.toLocaleString("en-IN")} visits · ${paidVisits} paid`}
                    href="/admin/growth"
                />
                <Stat
                    label="Rating"
                    value={data.reviews.average == null ? "—" : `${data.reviews.average}★`}
                    foot={`${data.reviews.count} review${data.reviews.count === 1 ? "" : "s"} · ${data.reviews.pending} waiting`}
                    href="/admin/reviews"
                />
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
                <Card className="lg:col-span-2">
                    <CardHeader title="Revenue per day" description="Hover or tap a day for its figure." />
                    <div className="px-3 pb-3 pt-4 sm:px-5">
                        <BarSeries
                            ariaLabel={`Revenue per day, last ${days} days`}
                            points={current.map((d) => ({ label: short(d.day), value: d.revenue_paise / 100, display: `${rupees(d.revenue_paise)} · ${d.orders} orders` }))}
                            tickPrefix="₹"
                        />
                    </div>
                </Card>
                <Card className="flex flex-col">
                    <CardHeader title="To do" action={todo.length ? <span className="op-num rounded-full bg-[var(--op-bad-bg)] px-2 text-xs font-semibold leading-5 text-[var(--op-bad)]">{todo.length}</span> : undefined} />
                    {todo.length === 0 ? (
                        <Empty title="All clear" icon={<CheckCircle2 size={28} />}>
                            Refunds, unanswered messages, reviews to approve and failed preparations appear here.
                        </Empty>
                    ) : (
                        <ul className="m-0 flex list-none flex-col gap-2 p-3">
                            {todo.slice(0, 8).map((item) => (
                                <li key={item.key}>
                                    <Link href={item.href} className="flex items-start gap-3 rounded-lg border border-[var(--op-border)] p-3 hover:bg-[var(--op-hover)]">
                                        <span className={cn("mt-1.5 h-2 w-2 shrink-0 rounded-full", dot[item.tone])} />
                                        <span className="flex min-w-0 flex-col">
                                            <strong className="font-semibold first-letter:uppercase">{item.title}</strong>
                                            <span className="truncate text-[13px] text-[var(--op-muted)]">{item.detail}</span>
                                        </span>
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    )}
                </Card>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
                <Card>
                    <CardHeader title="Uploads per day" description={`${data.uploads.prepared} prepared · ${data.uploads.failed} errors · ${data.uploads.busy} refused while busy`} />
                    <div className="px-3 pb-3 pt-4 sm:px-5">
                        <BarSeries
                            ariaLabel={`Uploads per day, last ${days} days`}
                            highlightPeak={false}
                            points={current.map((d) => ({ label: short(d.day), value: d.uploads, display: `${d.uploads} uploads` }))}
                            height={200}
                        />
                    </div>
                </Card>
                <Card>
                    <CardHeader
                        title="When candidates upload"
                        description={`Preparing takes ${data.preparation_seconds.median ?? "—"} s at the median, ${data.preparation_seconds.p95 ?? "—"} s for the slowest 5%`}
                        action={<Clock size={16} className="text-[var(--op-muted)]" aria-hidden="true" />}
                    />
                    <div className="px-3 pb-3 pt-4 sm:px-5">
                        <BarSeries
                            ariaLabel="Uploads by hour of day, India time"
                            highlightPeak={false}
                            tickEvery={2}
                            points={data.uploads_by_hour_ist.map((count, hour) => ({ label: `${hour}`, value: count, display: `${hour}:00–${hour}:59 IST · ${count} uploads` }))}
                            height={200}
                        />
                        <p className="m-0 mt-1 text-center text-xs text-[var(--op-muted)]">Hour of day, India time</p>
                    </div>
                </Card>
            </div>

            <Card>
                <CardHeader title="Examinations" action={<Link href="/admin/growth" className="text-[13px] text-[var(--op-muted)] hover:text-[var(--op-text)]">Growth →</Link>} />
                {data.exams.length === 0 ? (
                    <Empty title="No uploads in this period" />
                ) : (
                    <div className="op-scroll overflow-x-auto">
                        <table className="w-full min-w-[640px] border-collapse text-sm">
                            <thead>
                                <tr className="border-b border-[var(--op-border)] bg-[var(--op-muted-bg)] text-left text-xs text-[var(--op-muted)]">
                                    <th scope="col" className="px-5 py-2.5 font-medium">Examination</th>
                                    <th scope="col" className="px-3 py-2.5 text-right font-medium">Revenue</th>
                                    <th scope="col" className="px-3 py-2.5 text-right font-medium">Uploads</th>
                                    <th scope="col" className="px-3 py-2.5 text-right font-medium">Sessions paid</th>
                                    <th scope="col" className="px-5 py-2.5 font-medium">Commonest problem</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.exams.slice(0, 10).map((exam) => (
                                    <tr key={exam.exam} className="border-b border-[var(--op-border)] last:border-0">
                                        <td className="px-5 py-3 font-medium">
                                            <Link href={`/admin/uploads?q=${encodeURIComponent(exam.exam)}`} className="hover:underline">
                                                {exam.exam}
                                            </Link>
                                        </td>
                                        <td className="op-num px-3 py-3 text-right">{rupees(exam.revenue_paise)}</td>
                                        <td className="op-num px-3 py-3 text-right">{exam.uploads}</td>
                                        <td className="op-num px-3 py-3 text-right">
                                            {exam.kits_paid}/{exam.kits}
                                            {exam.conversion != null ? ` · ${Math.round(exam.conversion * 100)}%` : ""}
                                        </td>
                                        <td className="px-5 py-3 text-[var(--op-muted)]">{exam.top_reasons[0]?.[0]?.replace(/_/g, " ") ?? "—"}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </Card>
            <Card>
                <CardHeader title="System" description="The same checks the watch emails you about, every five minutes." />
                <div className="grid grid-cols-2 gap-4 p-5 text-sm sm:grid-cols-3 lg:grid-cols-6">
                    {(
                        [
                            ["Engine", health.ok ? String(health.value.status) : "unreachable", health.ok && health.value.status === "ready"],
                            ["Payments", health.ok ? String(health.value.payments ?? "—") : "—", health.ok && health.value.payments === "configured"],
                            ["Email", health.ok ? String(health.value.email ?? "—") : "—", health.ok && health.value.email === "configured"],
                            ["Purchase gate", health.ok ? String(health.value.purchase_gate ?? "—") : "—", health.ok && health.value.purchase_gate === "enabled"],
                            [
                                "Disk free",
                                health.ok && health.value.disk ? bytes(health.value.disk.free_bytes) : "—",
                                Boolean(health.ok && health.value.disk && health.value.disk.free_bytes > 10e9),
                            ],
                            [
                                "Last 7 days",
                                data.health.length ? `${data.health.filter((h) => h.status !== "ready").length} of ${data.health.length} checks down` : "No history yet",
                                data.health.every((h) => h.status === "ready"),
                            ],
                        ] as [string, string, boolean][]
                    ).map(([label, value, fine]) => (
                        <div key={label} className="flex flex-col gap-1">
                            <span className="text-xs text-[var(--op-muted)]">{label}</span>
                            <span className="flex items-center gap-2 font-medium">
                                <span className={cn("h-2 w-2 shrink-0 rounded-full", fine ? "bg-[var(--op-good)]" : "bg-[var(--op-bad)]")} />
                                {value}
                            </span>
                        </div>
                    ))}
                </div>
                {data.health.length > 0 && <p className="m-0 px-5 pb-4 text-xs text-[var(--op-muted)]">Last checked {when(data.health[data.health.length - 1].at)}.</p>}
            </Card>
        </>
    );
}