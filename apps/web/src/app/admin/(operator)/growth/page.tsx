import { RefreshCw } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { BarSeries, RankBars } from "../../../../components/console/charts";
import { when } from "../../../../lib/operator/format";
import { Badge, Card, CardHeader, Empty, PageHeader, Problem, Stat, buttonStyles, cn } from "../../../../components/console/ui";
import { rupees } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

export const metadata: Metadata = { title: "Growth" };

interface Row {
    visits: number;
    paid: number;
    uploaded: number;
    failed: number;
    value: string;
}

interface Growth {
    visits: number;
    funnel: { step: string; sessions: number }[];
    time_on_site_seconds: { median_all: number | null; median_paying: number | null; median_minutes_to_payment: number | null };
    sources: { source: string; visits: number; prepared: number; paid: number; revenue_paise: number }[];
    devices: Record<string, Row[]>;
    landing_pages: { path: string; visits: number }[];
    empty_searches: { query: string; count: number; last_at: string }[];
    price_test: { running: boolean; ladder_b: string; share_b_percent: number; arms: { arm: string; orders: number; paid: number; revenue_paise: number; pay_rate: number | null }[] };
    repeat: { payers: number; returning: number; for_another_exam: number; median_days_to_return: number | null };
}

interface Reconcile {
    checked_at: string | null;
    status: string;
    captured?: number;
    error?: string;
    problems: { kind: string; payment_id: string; order_id: string | null; amount_paise: number; email: string | null }[];
}

const PERIODS: [number, string][] = [
    [7, "7 days"],
    [30, "30 days"],
    [90, "90 days"],
    [365, "1 year"],
];
const STEP: Record<string, string> = {
    visited: "Visited",
    "opened an exam": "Opened an examination",
    uploaded: "Uploaded a file",
    prepared: "Got a prepared file",
    "opened checkout": "Opened checkout",
    paid: "Paid",
    received: "Received the files",
};

function duration(seconds: number | null) {
    if (seconds == null) return "—";
    return seconds < 90 ? `${Math.round(seconds)} s` : `${(seconds / 60).toFixed(1)} min`;
}

export default async function GrowthPage({ searchParams }: { searchParams: Promise<{ days?: string; recheck?: string }> }) {
    await requireOperator();
    const { days: raw, recheck } = await searchParams;
    const days = PERIODS.some(([d]) => d === Number(raw)) ? Number(raw) : 30;
    const [loaded, reconcile] = await Promise.all([
        engineJson<Growth>(`/v1/operator/growth?days=${days}`),
        engineJson<Reconcile>(`/v1/operator/reconcile${recheck ? "?force=true" : ""}`),
    ]);
    if (!loaded.ok) return <Problem what="growth" error={loaded.error} />;
    const data = loaded.value;
    const top = data.funnel[0]?.sessions || 0;

    return (
        <>
            <PageHeader
                title="Growth"
                description="From the site's own visit counter: where visitors come from, and where they stop."
                actions={
                    <div className="flex rounded-lg bg-[var(--op-muted-bg)] p-0.5">
                        {PERIODS.map(([value, label]) => (
                            <Link
                                key={value}
                                href={`/admin/growth?days=${value}`}
                                aria-current={value === days ? "page" : undefined}
                                className={cn("rounded-md px-3 py-1.5 text-[13px]", value === days ? "bg-[var(--op-card)] font-semibold shadow-[var(--op-shadow)]" : "text-[var(--op-muted)]")}
                            >
                                {label}
                            </Link>
                        ))}
                    </div>
                }
            />

            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-4">
                <Stat label="Visits" value={data.visits.toLocaleString("en-IN")} />
                <Stat label="Visitors who paid" value={top ? `${(((data.funnel.find((f) => f.step === "paid")?.sessions ?? 0) / top) * 100).toFixed(1)}%` : "—"} />
                <Stat label="Time on site, paying visits" value={duration(data.time_on_site_seconds.median_paying)} foot={`All visits ${duration(data.time_on_site_seconds.median_all)}`} />
                <Stat
                    label="Arrival to payment"
                    value={data.time_on_site_seconds.median_minutes_to_payment == null ? "—" : `${data.time_on_site_seconds.median_minutes_to_payment} min`}
                    foot="Median"
                />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
                <Card>
                    <CardHeader title="Funnel" description="How many visits reached each step, and the share kept from the step before." />
                    <div className="p-4">
                        {top === 0 ? (
                            <Empty title="No visits yet">Visits are counted from the day the counter went live.</Empty>
                        ) : (
                            <RankBars
                                rows={data.funnel.map((step, index) => {
                                    const before = index ? data.funnel[index - 1].sessions : step.sessions;
                                    return {
                                        label: STEP[step.step] ?? step.step,
                                        value: step.sessions,
                                        display: `${step.sessions.toLocaleString("en-IN")}${index && before ? ` · ${Math.round((step.sessions / before) * 100)}%` : ""}`,
                                    };
                                })}
                            />
                        )}
                    </div>
                </Card>
                <Card>
                    <CardHeader title="Where visitors come from" description={<>Tag a link with <code>?ref=name</code> and it shows here under that name.</>} />
                    {data.sources.length === 0 ? (
                        <Empty title="No visits yet" />
                    ) : (
                        <div className="op-scroll overflow-x-auto">
                            <table className="w-full border-collapse text-sm">
                                <thead>
                                    <tr className="border-b border-[var(--op-border)] bg-[var(--op-muted-bg)] text-left text-xs text-[var(--op-muted)]">
                                        <th scope="col" className="px-5 py-2.5 font-medium">Source</th>
                                        <th scope="col" className="px-3 py-2.5 text-right font-medium">Visits</th>
                                        <th scope="col" className="px-3 py-2.5 text-right font-medium">Paid</th>
                                        <th scope="col" className="px-5 py-2.5 text-right font-medium">Revenue</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.sources.slice(0, 10).map((row) => (
                                        <tr key={row.source} className="border-b border-[var(--op-border)] last:border-0">
                                            <td className="px-5 py-2.5 font-medium">{row.source}</td>
                                            <td className="op-num px-3 py-2.5 text-right">{row.visits}</td>
                                            <td className="op-num px-3 py-2.5 text-right">
                                                {row.paid} <span className="text-[var(--op-muted)]">({row.visits ? Math.round((row.paid / row.visits) * 100) : 0}%)</span>
                                            </td>
                                            <td className="op-num px-5 py-2.5 text-right">{rupees(row.revenue_paise)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </Card>
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
                {(["device", "browser", "connection"] as const).map((key) => (
                    <Card key={key}>
                        <CardHeader title={key === "device" ? "Devices" : key === "browser" ? "Browsers" : "Networks"} description="Visits · failed uploads · paid" />
                        <ul className="m-0 flex list-none flex-col p-0">
                            {(data.devices[key] ?? []).slice(0, 6).map((row) => (
                                <li key={row.value} className="flex items-center gap-3 border-b border-[var(--op-border)] px-5 py-2.5 text-sm last:border-0">
                                    <span className="flex-1 font-medium">{row.value}</span>
                                    <span className="op-num text-[var(--op-muted)]">
                                        {row.visits} · <span className={row.failed ? "text-[var(--op-bad)]" : ""}>{row.failed}</span> · {row.paid}
                                    </span>
                                </li>
                            ))}
                            {(data.devices[key] ?? []).length === 0 && <li className="px-5 py-6 text-center text-sm text-[var(--op-muted)]">No visits yet</li>}
                        </ul>
                    </Card>
                ))}
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
                <Card>
                    <CardHeader title="Searches that found nothing" description="What candidates typed and we did not have: demand for new examinations." />
                    {data.empty_searches.length === 0 ? (
                        <Empty title="None yet" />
                    ) : (
                        <ul className="m-0 flex list-none flex-col p-0">
                            {data.empty_searches.slice(0, 12).map((row) => (
                                <li key={row.query} className="flex items-center gap-3 border-b border-[var(--op-border)] px-5 py-2.5 text-sm last:border-0">
                                    <span className="flex-1 font-medium">{row.query}</span>
                                    <Badge tone="accent">{row.count}×</Badge>
                                    <span className="text-xs text-[var(--op-muted)]">{when(row.last_at)}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </Card>
                <Card>
                    <CardHeader title="Where visits start" />
                    <div className="px-3 pb-3 pt-4 sm:px-5">
                        {data.landing_pages.length === 0 ? (
                            <Empty title="No visits yet" />
                        ) : (
                            <BarSeries
                                ariaLabel="Visits by landing page"
                                highlightPeak={false}
                                tickEvery={0}
                                height={220}
                                points={data.landing_pages.slice(0, 8).map((row) => ({ label: row.path.length > 12 ? `${row.path.slice(0, 11)}…` : row.path, value: row.visits, display: `${row.path} · ${row.visits} visits` }))}
                            />
                        )}
                    </div>
                </Card>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
                <Card>
                    <CardHeader
                        title="Price test"
                        action={<Badge tone={data.price_test.running ? "good" : "neutral"}>{data.price_test.running ? "Running" : "Off"}</Badge>}
                        description={
                            data.price_test.running
                                ? `${data.price_test.share_b_percent}% of sessions see ladder B (${data.price_test.ladder_b} paise).`
                                : "Set EXAM_PHOTO_PRICE_TEST_LADDER and EXAM_PHOTO_PRICE_TEST_SHARE on the server to run one."
                        }
                    />
                    {data.price_test.arms.length > 0 && (
                        <table className="w-full border-collapse text-sm">
                            <thead>
                                <tr className="border-b border-[var(--op-border)] bg-[var(--op-muted-bg)] text-left text-xs text-[var(--op-muted)]">
                                    <th scope="col" className="px-5 py-2.5 font-medium">Arm</th>
                                    <th scope="col" className="px-3 py-2.5 text-right font-medium">Checkouts</th>
                                    <th scope="col" className="px-3 py-2.5 text-right font-medium">Pay rate</th>
                                    <th scope="col" className="px-5 py-2.5 text-right font-medium">Revenue</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.price_test.arms.map((arm) => (
                                    <tr key={arm.arm} className="border-b border-[var(--op-border)] last:border-0">
                                        <td className="px-5 py-2.5 font-medium">{arm.arm === "A" ? "A · standard" : "B · test"}</td>
                                        <td className="op-num px-3 py-2.5 text-right">{arm.orders}</td>
                                        <td className="op-num px-3 py-2.5 text-right">{arm.pay_rate == null ? "—" : `${Math.round(arm.pay_rate * 100)}%`}</td>
                                        <td className="op-num px-5 py-2.5 text-right">{rupees(arm.revenue_paise)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </Card>
                <Card>
                    <CardHeader title="Customers who come back" />
                    <div className="grid grid-cols-2 gap-4 p-5 text-sm">
                        <div>
                            <div className="op-num text-2xl font-semibold">{data.repeat.returning}</div>
                            <div className="text-[var(--op-muted)]">of {data.repeat.payers} paying customers paid again</div>
                        </div>
                        <div>
                            <div className="op-num text-2xl font-semibold">{data.repeat.for_another_exam}</div>
                            <div className="text-[var(--op-muted)]">came back for another examination</div>
                        </div>
                        <div>
                            <div className="op-num text-2xl font-semibold">{data.repeat.median_days_to_return ?? "—"}</div>
                            <div className="text-[var(--op-muted)]">days to come back (median)</div>
                        </div>
                    </div>
                </Card>
            </div>

            <Card id="reconcile">
                <CardHeader
                    title="Razorpay check"
                    description="Every payment Razorpay captured in the last 48 hours, compared with the files we released."
                    action={
                        <Link href={`/admin/growth?days=${days}&recheck=1#reconcile`} className={buttonStyles({ variant: "secondary", size: "sm" })}>
                            <RefreshCw size={14} aria-hidden="true" />
                            Check now
                        </Link>
                    }
                />
                <div className="p-5 text-sm">
                    {!reconcile.ok ? (
                        <p className="m-0 text-[var(--op-bad)]">Could not run: {reconcile.error}</p>
                    ) : reconcile.value.status === "not_configured" ? (
                        <p className="m-0 text-[var(--op-muted)]">Razorpay keys are not configured here.</p>
                    ) : reconcile.value.status === "failed" ? (
                        <p className="m-0 text-[var(--op-bad)]">Razorpay could not be asked: {reconcile.value.error}</p>
                    ) : reconcile.value.problems.length === 0 ? (
                        <p className="m-0">
                            <Badge tone="good">All matched</Badge>{" "}
                            <span className="text-[var(--op-muted)]">
                                {reconcile.value.captured ?? 0} captured payments checked {when(reconcile.value.checked_at)}.
                            </span>
                        </p>
                    ) : (
                        <ul className="m-0 flex list-none flex-col gap-2 p-0">
                            {reconcile.value.problems.map((problem) => (
                                <li key={problem.payment_id} className="rounded-lg border border-[var(--op-bad)] bg-[var(--op-bad-bg)] p-3">
                                    <strong>{problem.payment_id}</strong> · {rupees(problem.amount_paise ?? 0)} · {problem.email ?? "no email"}
                                    <br />
                                    {problem.kind === "unknown_order" ? "Taken for an order we never made." : "Taken, and our order is not marked paid: nothing was released."}{" "}
                                    {problem.order_id && problem.kind !== "unknown_order" && (
                                        <Link href={`/admin/orders?open=${problem.order_id}`} className="underline">
                                            Open the order
                                        </Link>
                                    )}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </Card>
        </>
    );
}
