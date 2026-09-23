import Link from "next/link";
import { Badge, Bars, Failure, Fact, Tile } from "../../../components/operator/ui";
import {
    bytes,
    percent,
    rupees,
    seconds,
    when,
    type Health,
    type Overview,
} from "../../../lib/operator/data";
import { engineJson } from "../../../lib/operator/engine";
import { requireOperator } from "../../../lib/operator/guard";

const PERIODS = [7, 30, 90, 365];

// Settings /ready reports, in the order they matter when something breaks.
const HEALTH_KEYS = ["status", "warmup", "matting_backend", "purchase_gate", "operator_surface", "payments", "email"];

export default async function OverviewPage({ searchParams }: { searchParams: Promise<{ days?: string }> }) {
    const operator = await requireOperator();
    const requested = Number((await searchParams).days);
    const days = PERIODS.includes(requested) ? requested : 30;
    const [loaded, health] = await Promise.all([
        engineJson<Overview>(`/v1/operator/overview?days=${days}`),
        engineJson<Health>("/v1/operator/health"),
    ]);
    if (!loaded.ok) return <Failure what="the overview" error={loaded.error} />;
    const data = loaded.value;
    const labelEvery = Math.ceil(data.series.length / 8);
    const short = (day: string) => day.slice(8, 10) + "/" + day.slice(5, 7);
    const lastHealth = data.health.at(-1);

    return (
        <>
            <h1>Overview</h1>
            <p className="euk-op-quiet">
                {operator} · {when(new Date().toISOString())} IST
            </p>
            <p className="euk-op-filter">
                {PERIODS.map((period) => (
                    <Link key={period} href={`/admin?days=${period}`} aria-current={period === days}>
                        {period === 365 ? "1 year" : `${period} days`}
                    </Link>
                ))}
            </p>

            <section className="euk-op-tiles" aria-label="At a glance">
                <Tile label="Today" value={rupees(data.money.today_paise)} />
                <Tile label={`${days} days`} value={rupees(data.money.period_paise)} />
                <Tile label="All time" value={rupees(data.money.all_time_paise)} />
                <Tile
                    label="Refund due"
                    value={data.refund_due.length}
                    alarm={data.refund_due.length > 0}
                    href="/admin/orders?state=refund-due"
                />
                <Tile
                    label="Inbox open"
                    value={`${data.tickets.open}${data.tickets.overdue.length ? ` · ${data.tickets.overdue.length} late` : ""}`}
                    alarm={data.tickets.overdue.length > 0}
                    href="/admin/inbox"
                />
                <Tile
                    label="Engine"
                    value={health.ok ? health.value.status : "unreachable"}
                    alarm={!health.ok || health.value.status !== "ready"}
                    href="#health"
                />
            </section>

            <Attention data={data} />

            <section className="euk-op-section">
                <h2>Money</h2>
                <Bars
                    title={`Revenue per day, last ${days} days`}
                    tone="signal"
                    everyNthLabel={labelEvery}
                    bars={data.series.map((d) => ({ label: short(d.day), value: d.revenue_paise, display: `${rupees(d.revenue_paise)} · ${d.orders} orders` }))}
                />
                <dl className="euk-op-facts">
                    <Fact label="Paid orders, all time" value={data.money.paid_orders} />
                    <Fact label="Average paid order" value={rupees(data.money.average_order_paise)} />
                    <Fact label="Refunded" value={`${data.money.refunded_orders} · ${rupees(data.money.refunded_paise)}`} />
                    <Fact label="Paying customers" value={data.customers.payers} />
                    <Fact
                        label="Came back and paid again"
                        value={`${data.customers.repeat_payers}${data.customers.payers ? ` (${percent(data.customers.repeat_payers / data.customers.payers)})` : ""}`}
                    />
                    <Fact label="Email addresses held" value={data.customers.contacts} />
                </dl>
                <p className="euk-op-quiet">
                    Exports: <Link href="/admin/export/orders" prefetch={false} download>orders.csv</Link> · <Link href="/admin/export/customers" prefetch={false} download>customers.csv</Link> ·{" "}
                    <Link href="/admin/export/uploads" prefetch={false} download>uploads.csv</Link>
                </p>
            </section>

            <section className="euk-op-section">
                <h2>Uploads</h2>
                <Bars
                    title={`Uploads per day, last ${days} days`}
                    everyNthLabel={labelEvery}
                    bars={data.series.map((d) => ({ label: short(d.day), value: d.uploads, display: `${d.uploads} uploads` }))}
                />
                <Bars
                    title="Uploads by hour of day (IST)"
                    everyNthLabel={3}
                    bars={data.uploads_by_hour_ist.map((count, hour) => ({ label: `${hour}`, value: count, display: `${hour}:00–${hour}:59 · ${count} uploads` }))}
                />
                <dl className="euk-op-facts">
                    <Fact label="Uploads" value={data.uploads.total} />
                    <Fact label="Prepared" value={data.uploads.prepared} />
                    <Fact label="Errors" value={data.uploads.failed} alarm={data.uploads.failed > 0} />
                    <Fact label="Refused, server busy" value={data.uploads.busy} alarm={data.uploads.busy > 0} />
                    <Fact label="Sessions that prepared and did not pay" value={data.unpaid_kits} />
                    <Fact
                        label="Time to prepare"
                        value={`median ${seconds(data.preparation_seconds.median)} · p95 ${seconds(data.preparation_seconds.p95)} · slowest ${seconds(data.preparation_seconds.max)}`}
                    />
                </dl>
                {Object.keys(data.preparation_seconds.stages_median_ms).length > 0 && (
                    <details>
                        <summary>Median time per pipeline stage</summary>
                        <table className="euk-op-table">
                            <tbody>
                                {Object.entries(data.preparation_seconds.stages_median_ms).map(([stage, ms]) => (
                                    <tr key={stage}>
                                        <th scope="row">{stage}</th>
                                        <td>{(ms / 1000).toFixed(2)} s</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </details>
                )}
            </section>

            <section className="euk-op-section">
                <h2>By examination</h2>
                {data.exams.length === 0 && <p className="euk-op-quiet">No uploads in this period.</p>}
                <ul className="euk-op-list">
                    {data.exams.map((exam) => (
                        <li key={exam.exam} className="euk-op-card">
                            <p className="euk-op-row">
                                <Link href={`/admin/uploads?q=${encodeURIComponent(exam.exam)}&days=${days}`}>
                                    <strong>{exam.exam}</strong>
                                </Link>
                                <span>{rupees(exam.revenue_paise)}</span>
                            </p>
                            <p className="euk-op-quiet">
                                {exam.uploads} uploads · {exam.prepared} prepared · {exam.failed} errors · {exam.kits_paid} of {exam.kits}{" "}
                                sessions paid ({percent(exam.conversion)})
                            </p>
                            {exam.top_reasons.length > 0 && (
                                <p className="euk-op-quiet">
                                    Most common findings: {exam.top_reasons.map(([reason, count]) => `${reason} (${count})`).join(", ")}
                                </p>
                            )}
                        </li>
                    ))}
                </ul>
            </section>

            <section id="health" className="euk-op-section">
                <h2>Health</h2>
                {!health.ok && <Failure what="the engine" error={health.error} />}
                {health.ok && (
                    <dl className="euk-op-facts">
                        {HEALTH_KEYS.filter((key) => key in health.value).map((key) => (
                            <Fact key={key} label={key.replace(/_/g, " ")} value={String(health.value[key] ?? "—")} />
                        ))}
                        {health.value.disk && (
                            <Fact
                                label="Disk free"
                                value={`${bytes(health.value.disk.free_bytes)} of ${bytes(health.value.disk.total_bytes)}`}
                                alarm={health.value.disk.free_bytes < 10e9}
                            />
                        )}
                    </dl>
                )}
                <HealthHistory samples={data.health} />
                {lastHealth && <p className="euk-op-quiet">Last sample {when(lastHealth.at)}.</p>}
            </section>
        </>
    );
}

function Attention({ data }: { data: Overview }) {
    const items = [
        ...data.refund_due.map((order) => ({
            key: `r-${order.order_id}`,
            href: `/admin/orders/${order.order_id}`,
            state: "refund-due",
            text: `${rupees(order.amount_paise)} paid ${when(order.paid_at)}, nothing delivered · ${order.exam_names.join(", ") || order.order_id}`,
        })),
        ...data.refund_review.map((order) => ({
            key: `c-${order.order_id}`,
            href: `/admin/orders/${order.order_id}`,
            state: "open",
            text: `Complaint on a delivered order · ${order.exam_names.join(", ") || order.order_id}`,
        })),
        ...data.tickets.overdue.map((ticket) => ({
            key: `t-${ticket.id}`,
            href: `/admin/inbox/${ticket.id}`,
            state: "open",
            text: `${ticket.kind} from ${ticket.email ?? "unknown"} is ${ticket.ack_overdue ? "unanswered after 48 hours" : "unresolved after a month"}`,
        })),
        ...data.stuck.slice(0, 10).map((row) => ({
            key: `s-${row.job_id}`,
            href: `/admin/uploads/${row.job_id}`,
            state: row.status,
            text: `${row.exam_name ?? row.exam_id ?? "Upload"} · ${row.error ?? row.status} · ${when(row.started_at)}`,
        })),
    ];
    return (
        <section className="euk-op-section">
            <h2>Needs attention</h2>
            {items.length === 0 && <p className="euk-op-quiet">Nothing. Refunds, late replies and failed preparations appear here.</p>}
            <ul className="euk-op-list">
                {items.map((item) => (
                    <li key={item.key} className="euk-op-card">
                        <Link href={item.href} className="euk-op-row">
                            <span>{item.text}</span>
                            <Badge state={item.state} />
                        </Link>
                    </li>
                ))}
            </ul>
            {data.followups.length > 0 && (
                <>
                    <h3>Checkouts that did not pay ({data.followups.length})</h3>
                    <p className="euk-op-quiet">Razorpay collected an address or phone, then the payment failed or was abandoned.</p>
                    <ul className="euk-op-plain">
                        {data.followups.slice(0, 20).map((order) => (
                            <li key={order.order_id}>
                                <Link href={`/admin/orders/${order.order_id}`}>{order.emails[0] ?? order.payer_contact ?? order.order_id}</Link>{" "}
                                · {rupees(order.amount_paise)} · {order.exam_names.join(", ") || "exam not recorded"} · {when(order.created_at)}
                            </li>
                        ))}
                    </ul>
                </>
            )}
        </section>
    );
}

function HealthHistory({ samples }: { samples: Overview["health"] }) {
    if (samples.length === 0) return <p className="euk-op-quiet">No history yet: the engine samples every five minutes.</p>;
    const down = samples.filter((sample) => sample.status !== "ready");
    const busy = samples.reduce((sum, sample) => sum + (sample.busy_refusals || 0), 0);
    const byDay = new Map<string, { total: number; down: number }>();
    for (const sample of samples) {
        const day = new Date(sample.at).toLocaleDateString("en-IN", { timeZone: "Asia/Kolkata", day: "2-digit", month: "2-digit" });
        const entry = byDay.get(day) ?? { total: 0, down: 0 };
        entry.total += 1;
        if (sample.status !== "ready") entry.down += 1;
        byDay.set(day, entry);
    }
    return (
        <>
            <p>
                Last 7 days: {down.length === 0 ? "ready at every check" : `${down.length} of ${samples.length} checks not ready`} ·{" "}
                {busy} preparation{busy === 1 ? "" : "s"} refused as busy.
            </p>
            <Bars
                title="Checks not ready, per day"
                bars={[...byDay.entries()].map(([day, entry]) => ({
                    label: day,
                    value: entry.down,
                    display: `${entry.down} of ${entry.total} checks not ready`,
                }))}
                tone="signal"
            />
        </>
    );
}
