import Link from "next/link";
import { Bars, Failure, Fact } from "../../../../components/operator/ui";
import { percent, rupees, when } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

interface Row {
    visits: number;
    paid: number;
    [key: string]: string | number;
}

interface Growth {
    days: number;
    visits: number;
    funnel: { step: string; sessions: number }[];
    time_on_site_seconds: { median_all: number | null; median_paying: number | null; median_minutes_to_payment: number | null };
    sources: (Row & { source: string; prepared: number; revenue_paise: number })[];
    devices: Record<string, (Row & { value: string; uploaded: number; failed: number })[]>;
    landing_pages: { path: string; visits: number }[];
    empty_searches: { query: string; count: number; last_at: string }[];
    price_test: {
        running: boolean;
        ladder_b: string;
        share_b_percent: number;
        arms: { arm: string; orders: number; paid: number; revenue_paise: number; pay_rate: number | null }[];
    };
    repeat: { payers: number; returning: number; for_another_exam: number; median_days_to_return: number | null };
}

interface Reconcile {
    checked_at: string | null;
    status: string;
    captured?: number;
    error?: string;
    problems: { kind: string; payment_id: string; order_id: string | null; amount_paise: number; email: string | null }[];
}

const PERIODS = [7, 30, 90, 365];
const DEVICE_TITLES: Record<string, string> = { device: "Device", browser: "Browser", connection: "Network" };

function duration(seconds: number | null): string {
    if (seconds == null) return "—";
    return seconds < 90 ? `${Math.round(seconds)} s` : `${(seconds / 60).toFixed(1)} min`;
}

export default async function GrowthPage({ searchParams }: { searchParams: Promise<{ days?: string; recheck?: string }> }) {
    await requireOperator();
    const { days: rawDays, recheck } = await searchParams;
    const days = PERIODS.includes(Number(rawDays)) ? Number(rawDays) : 30;
    const [loaded, reconcile] = await Promise.all([
        engineJson<Growth>(`/v1/operator/growth?days=${days}`),
        engineJson<Reconcile>(`/v1/operator/reconcile${recheck ? "?force=true" : ""}`),
    ]);
    if (!loaded.ok) return <Failure what="growth" error={loaded.error} />;
    const data = loaded.value;
    const top = data.funnel[0]?.sessions || 1;

    return (
        <>
            <h1>Growth</h1>
            <p className="euk-op-quiet">From the site&rsquo;s own visit counter. Visits are counted from the day this was deployed.</p>
            <p className="euk-op-filter">
                {PERIODS.map((period) => (
                    <Link key={period} href={`/admin/growth?days=${period}`} aria-current={period === days}>
                        {period === 365 ? "1 year" : `${period} days`}
                    </Link>
                ))}
            </p>

            <section className="euk-op-section">
                <h2>Funnel</h2>
                <ol className="euk-op-funnel">
                    {data.funnel.map((step, index) => {
                        const before = index ? data.funnel[index - 1].sessions : step.sessions;
                        return (
                            <li key={step.step}>
                                <span className="euk-op-funnel-bar" style={{ width: `${Math.max(2, (step.sessions / top) * 100)}%` }} aria-hidden="true" />
                                <span className="euk-op-row">
                                    <strong>{step.step}</strong>
                                    <span>
                                        {step.sessions}
                                        {index > 0 && before > 0 ? ` · ${percent(step.sessions / before)} of the step before` : ""}
                                    </span>
                                </span>
                            </li>
                        );
                    })}
                </ol>
                <dl className="euk-op-facts">
                    <Fact label="Time on site, every visit (median)" value={duration(data.time_on_site_seconds.median_all)} />
                    <Fact label="Time on site, visits that paid (median)" value={duration(data.time_on_site_seconds.median_paying)} />
                    <Fact
                        label="Arrival to payment (median)"
                        value={data.time_on_site_seconds.median_minutes_to_payment == null ? "—" : `${data.time_on_site_seconds.median_minutes_to_payment} min`}
                    />
                </dl>
            </section>

            <section className="euk-op-section">
                <h2>Where visitors come from</h2>
                {data.sources.length === 0 && <p className="euk-op-quiet">No visits yet.</p>}
                <ul className="euk-op-list">
                    {data.sources.map((row) => (
                        <li key={row.source} className="euk-op-card">
                            <p className="euk-op-row">
                                <strong>{row.source}</strong>
                                <span>{rupees(row.revenue_paise)}</span>
                            </p>
                            <p className="euk-op-quiet">
                                {row.visits} visits · {row.prepared} prepared · {row.paid} paid ({percent(row.visits ? row.paid / row.visits : null)})
                            </p>
                        </li>
                    ))}
                </ul>
                <p className="euk-op-quiet">
                    Tag a link you share with <code>?utm_source=name</code> (or <code>?ref=name</code>) and it appears here under that name.
                </p>
                {data.landing_pages.length > 0 && (
                    <Bars
                        title="Where visits start"
                        bars={data.landing_pages.slice(0, 12).map((row) => ({ label: row.path.length > 14 ? `${row.path.slice(0, 13)}…` : row.path, value: row.visits, display: `${row.path} · ${row.visits} visits` }))}
                    />
                )}
            </section>

            <section className="euk-op-section">
                <h2>Devices and networks</h2>
                {Object.entries(data.devices).map(([key, rows]) => (
                    <details key={key} open={key === "device"}>
                        <summary>{DEVICE_TITLES[key] ?? key}</summary>
                        <table className="euk-op-table">
                            <thead>
                                <tr>
                                    <th scope="col">{DEVICE_TITLES[key] ?? key}</th>
                                    <th scope="col">Visits</th>
                                    <th scope="col">Uploaded</th>
                                    <th scope="col">Failed uploads</th>
                                    <th scope="col">Paid</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows.map((row) => (
                                    <tr key={row.value}>
                                        <th scope="row">{row.value}</th>
                                        <td>{row.visits}</td>
                                        <td>{row.uploaded}</td>
                                        <td>{row.failed}</td>
                                        <td>{row.paid}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </details>
                ))}
            </section>

            <section className="euk-op-section">
                <h2>Searches that found nothing</h2>
                <p className="euk-op-quiet">What candidates typed and we did not have: demand beside the request form.</p>
                {data.empty_searches.length === 0 && <p className="euk-op-quiet">None yet.</p>}
                <ul className="euk-op-plain">
                    {data.empty_searches.map((row) => (
                        <li key={row.query}>
                            <strong>{row.query}</strong> · {row.count} time{row.count === 1 ? "" : "s"} · last {when(row.last_at)}
                        </li>
                    ))}
                </ul>
            </section>

            <section className="euk-op-section">
                <h2>Price test</h2>
                {data.price_test.running ? (
                    <p>
                        Running: {data.price_test.share_b_percent}% of sessions see ladder B ({data.price_test.ladder_b} paise).
                    </p>
                ) : (
                    <p className="euk-op-quiet">
                        Off. To run one, set <code>EXAM_PHOTO_PRICE_TEST_LADDER</code> (for example <code>400,700</code>) and{" "}
                        <code>EXAM_PHOTO_PRICE_TEST_SHARE</code> (for example <code>50</code>) in <code>deploy/.env</code> and restart the engine.
                    </p>
                )}
                {data.price_test.arms.length > 0 && (
                    <table className="euk-op-table">
                        <thead>
                            <tr>
                                <th scope="col">Arm</th>
                                <th scope="col">Checkouts</th>
                                <th scope="col">Paid</th>
                                <th scope="col">Pay rate</th>
                                <th scope="col">Revenue</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.price_test.arms.map((arm) => (
                                <tr key={arm.arm}>
                                    <th scope="row">{arm.arm === "A" ? "A (standard)" : "B (test)"}</th>
                                    <td>{arm.orders}</td>
                                    <td>{arm.paid}</td>
                                    <td>{percent(arm.pay_rate)}</td>
                                    <td>{rupees(arm.revenue_paise)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </section>

            <section className="euk-op-section">
                <h2>Customers who come back</h2>
                <dl className="euk-op-facts">
                    <Fact label="Paying customers" value={data.repeat.payers} />
                    <Fact label="Paid again" value={`${data.repeat.returning}${data.repeat.payers ? ` (${percent(data.repeat.returning / data.repeat.payers)})` : ""}`} />
                    <Fact label="Came back for another examination" value={data.repeat.for_another_exam} />
                    <Fact
                        label="Days to come back (median)"
                        value={data.repeat.median_days_to_return == null ? "—" : `${data.repeat.median_days_to_return}`}
                    />
                </dl>
            </section>

            <section id="reconcile" className="euk-op-section">
                <h2>Razorpay reconciliation</h2>
                {!reconcile.ok && <Failure what="reconciliation" error={reconcile.error} />}
                {reconcile.ok && (
                    <>
                        <p className="euk-op-quiet">
                            {reconcile.value.status === "not_configured"
                                ? "Razorpay keys are not configured here."
                                : reconcile.value.status === "failed"
                                  ? `Razorpay could not be asked: ${reconcile.value.error}`
                                  : `Checked ${when(reconcile.value.checked_at)} against ${reconcile.value.captured ?? 0} captured payments in the last 48 hours.`}{" "}
                            <Link href={`/admin/growth?days=${days}&recheck=1#reconcile`}>Check now</Link>
                        </p>
                        {reconcile.value.problems.length === 0 && reconcile.value.status === "ok" && <p>Every captured payment released its files.</p>}
                        <ul className="euk-op-list">
                            {reconcile.value.problems.map((problem) => (
                                <li key={problem.payment_id} className="euk-op-card" data-state="refund-due">
                                    <strong>{problem.payment_id}</strong> · {rupees(problem.amount_paise ?? 0)} · {problem.email ?? "no email"}
                                    <br />
                                    {problem.kind === "unknown_order" ? "Razorpay took this payment for an order we never made." : "Razorpay took this payment and our order is not marked paid: nothing was released."}{" "}
                                    {problem.order_id && problem.kind !== "unknown_order" && <Link href={`/admin/orders/${problem.order_id}`}>Open the order</Link>}
                                </li>
                            ))}
                        </ul>
                    </>
                )}
            </section>
        </>
    );
}
