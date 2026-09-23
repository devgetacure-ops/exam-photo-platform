import type { Metadata } from "next";
import Link from "next/link";
import "../operator.css";
import {
    bytes,
    orderState,
    revenue,
    rupees,
    when,
    type Health,
    type OperatorJob,
    type Order,
    type UsageSummary,
} from "../../lib/operator/data";
import { engineJson } from "../../lib/operator/engine";
import { requireOperator } from "../../lib/operator/guard";
import { readRequests, requestsDirectory } from "../../lib/operator/requests";

export const metadata: Metadata = {
    title: "Operator",
    robots: { index: false, follow: false },
};

const STATE_LABEL = {
    "refund-due": "Refund due",
    delivered: "Delivered",
    paid: "Paid",
    unpaid: "Not paid",
} as const;

// Settings /ready reports, in the order they matter when something breaks.
const HEALTH_KEYS = [
    "status",
    "warmup",
    "matting_backend",
    "purchase_gate",
    "operator_surface",
    "payments",
    "email",
];

export default async function OperatorPage({
    searchParams,
}: {
    searchParams: Promise<{ orders?: string }>;
}) {
    const operator = await requireOperator();
    const { orders: orderFilter } = await searchParams;
    const [orders, jobs, usage, health, requests] = await Promise.all([
        engineJson<{ orders: Order[] }>("/v1/orders"),
        engineJson<{ jobs: OperatorJob[] }>("/v1/operator/jobs"),
        engineJson<UsageSummary>("/v1/metrics/usage"),
        engineJson<Health>("/v1/operator/health"),
        readRequests(requestsDirectory()),
    ]);
    const allOrders = orders.ok ? orders.value.orders : [];
    const money = revenue(allOrders);
    const shownOrders =
        orderFilter === "refund"
            ? allOrders.filter((order) => orderState(order) === "refund-due")
            : allOrders;
    const liveJobs = jobs.ok ? jobs.value.jobs : [];

    return (
        <div className="euk euk-op">
            <header className="euk-op-head">
                <h1>Operator</h1>
                <p className="euk-op-quiet">
                    {operator} · {when(new Date().toISOString())} IST
                </p>
                <nav className="euk-op-nav" aria-label="Sections">
                    <a href="#orders">Orders</a>
                    <a href="#uploads">Uploads ({liveJobs.length})</a>
                    <a href="#requests">Requests ({requests.length})</a>
                    <a href="#business">Business</a>
                    <a href="#health">Health</a>
                </nav>
            </header>

            <section className="euk-op-tiles" aria-label="At a glance">
                <Tile label="Today" value={rupees(money.todayPaise)} />
                <Tile label="7 days" value={rupees(money.weekPaise)} />
                <Tile label="30 days" value={rupees(money.monthPaise)} />
                <Tile label="All time" value={rupees(money.allPaise)} />
                <Tile
                    label="Refund due"
                    value={`${money.refundDue} · ${rupees(money.refundDuePaise)}`}
                    alarm={money.refundDue > 0}
                />
                <Tile
                    label="Engine"
                    value={health.ok ? health.value.status : "unreachable"}
                    alarm={!health.ok || health.value.status !== "ready"}
                />
            </section>

            <section id="orders" className="euk-op-section">
                <h2>Orders</h2>
                <p className="euk-op-filter">
                    <Link href="/admin#orders" aria-current={orderFilter !== "refund"}>
                        All ({allOrders.length})
                    </Link>
                    <Link href="/admin?orders=refund#orders" aria-current={orderFilter === "refund"}>
                        Paid, not delivered ({money.refundDue})
                    </Link>
                </p>
                {!orders.ok && <Failure what="orders" error={orders.error} />}
                {orders.ok && shownOrders.length === 0 && <p className="euk-op-quiet">None.</p>}
                <ul className="euk-op-list">
                    {shownOrders.map((order) => (
                        <OrderCard key={order.order_id} order={order} live={liveJobs} />
                    ))}
                </ul>
            </section>

            <section id="uploads" className="euk-op-section">
                <h2>Uploads still held</h2>
                <p className="euk-op-quiet">
                    Every file still inside its retention window. They disappear from here when the
                    sweeper erases them.
                </p>
                {!jobs.ok && <Failure what="uploads" error={jobs.error} />}
                {jobs.ok && liveJobs.length === 0 && <p className="euk-op-quiet">None right now.</p>}
                <ul className="euk-op-uploads">
                    {liveJobs.map((job) => (
                        <li key={job.job_id}>
                            <Link href={`/admin/uploads/${job.job_id}`} className="euk-op-upload">
                                {job.files?.some((f) => f.name === "input.jpg") && (
                                    // eslint-disable-next-line @next/next/no-img-element
                                    <img
                                        src={`/admin/files/${job.job_id}/input.jpg`}
                                        alt=""
                                        loading="lazy"
                                    />
                                )}
                                <span>
                                    <strong>{job.exam_name ?? job.exam_id ?? "No examination"}</strong>
                                    <br />
                                    {job.requirement_name ?? job.requirement_type ?? "—"}
                                    <br />
                                    <span className="euk-op-quiet">
                                        {when(job.created_at)} · {job.outcome ?? job.status} ·{" "}
                                        {job.released ? "paid" : "unpaid"} · erased{" "}
                                        {when(job.expires_at)}
                                    </span>
                                </span>
                            </Link>
                        </li>
                    ))}
                </ul>
            </section>

            <section id="requests" className="euk-op-section">
                <h2>Requests</h2>
                <p className="euk-op-quiet">
                    From the request form. Each is deleted 30 days after it arrives; the full address
                    is in the email support@ received.
                </p>
                {requests.length === 0 && <p className="euk-op-quiet">None.</p>}
                <ul className="euk-op-list">
                    {requests.map((request) => (
                        <li key={request.reference} className="euk-op-card">
                            <p className="euk-op-row">
                                <strong>
                                    {request.kind === "exam" ? request.exam : "Support"}
                                </strong>
                                <span className="euk-op-badge">{request.kind}</span>
                            </p>
                            {request.message && <p className="euk-op-message">{request.message}</p>}
                            <p className="euk-op-quiet">
                                {request.reference} · {request.maskedEmail} · {when(request.createdAt)}{" "}
                                · deleted {when(request.expiresAt)}
                            </p>
                        </li>
                    ))}
                </ul>
            </section>

            <section id="business" className="euk-op-section">
                <h2>Business</h2>
                {!usage.ok && <Failure what="usage" error={usage.error} />}
                {usage.ok && (
                    <>
                        <dl className="euk-op-facts">
                            <Fact label="Kits (sessions)" value={usage.value.kits} />
                            <Fact label="Files prepared" value={usage.value.preparations} />
                            <Fact label="Kits that paid" value={usage.value.kits_that_purchased} />
                            <Fact
                                label="Conversion"
                                value={
                                    usage.value.conversion_rate == null
                                        ? "—"
                                        : `${(usage.value.conversion_rate * 100).toFixed(1)}%`
                                }
                            />
                            <Fact label="Paid orders" value={money.paidOrders} />
                            <Fact label="Orders not paid" value={money.unpaidOrders} />
                            <Fact
                                label="Average paid order"
                                value={
                                    money.paidOrders
                                        ? rupees(Math.round(money.allPaise / money.paidOrders))
                                        : "—"
                                }
                            />
                            <Fact
                                label="Files per kit"
                                value={`median ${usage.value.preparations_per_kit.median ?? "—"} · p90 ${
                                    usage.value.preparations_per_kit.p90 ?? "—"
                                } · max ${usage.value.preparations_per_kit.max ?? "—"}`}
                            />
                        </dl>
                        {usage.value.heaviest_kits.length > 0 && (
                            <>
                                <h3>Busiest kits</h3>
                                <ul className="euk-op-plain">
                                    {usage.value.heaviest_kits.map((kit) => (
                                        <li key={kit.kit_id}>
                                            <code>{kit.kit_id}</code> · {kit.preparations} prepared ·{" "}
                                            {kit.purchases} purchase{kit.purchases === 1 ? "" : "s"}
                                        </li>
                                    ))}
                                </ul>
                            </>
                        )}
                    </>
                )}
            </section>

            <section id="health" className="euk-op-section">
                <h2>Health</h2>
                {!health.ok && <Failure what="the engine" error={health.error} />}
                {health.ok && (
                    <dl className="euk-op-facts">
                        {HEALTH_KEYS.filter((key) => key in health.value).map((key) => (
                            <Fact key={key} label={key.replace(/_/g, " ")} value={describe(health.value[key])} />
                        ))}
                        {health.value.disk && (
                            <Fact
                                label="Disk free"
                                value={`${bytes(health.value.disk.free_bytes)} of ${bytes(
                                    health.value.disk.total_bytes,
                                )}`}
                                alarm={health.value.disk.free_bytes < 10e9}
                            />
                        )}
                    </dl>
                )}
            </section>
        </div>
    );
}

function describe(value: unknown): string {
    if (value == null) return "—";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
}

function Tile({ label, value, alarm }: { label: string; value: string; alarm?: boolean }) {
    return (
        <div className="euk-op-tile" data-alarm={alarm ? "true" : undefined}>
            <span className="euk-label">{label}</span>
            <strong>{value}</strong>
        </div>
    );
}

function Fact({ label, value, alarm }: { label: string; value: string | number; alarm?: boolean }) {
    return (
        <div data-alarm={alarm ? "true" : undefined}>
            <dt>{label}</dt>
            <dd>{value}</dd>
        </div>
    );
}

function Failure({ what, error }: { what: string; error: string }) {
    return (
        <p className="euk-op-failure" role="alert">
            Could not load {what}: {error}
        </p>
    );
}

function OrderCard({ order, live }: { order: Order; live: OperatorJob[] }) {
    const state = orderState(order);
    const items = order.items ?? [];
    const exams = [...new Set(items.map((item) => item.exam_name).filter(Boolean))];
    const liveIds = new Set(live.map((job) => job.job_id));
    return (
        <li className="euk-op-card" data-state={state}>
            <p className="euk-op-row">
                <strong>{exams.join(", ") || "Examination not recorded"}</strong>
                <span className="euk-op-badge" data-state={state}>
                    {STATE_LABEL[state]}
                </span>
            </p>
            <p>
                {rupees(order.amount_paise)} · {items.length || order.job_ids.length} file
                {(items.length || order.job_ids.length) === 1 ? "" : "s"} · ordered{" "}
                {when(order.created_at)}
            </p>
            <p className="euk-op-quiet">
                {order.paid_at
                    ? `Paid ${when(order.paid_at)} · ${order.payment_reference ?? "no reference"}`
                    : "No payment arrived"}
                {" · "}
                {order.delivered_at
                    ? `First delivered ${when(order.delivered_at)} by ${order.delivery_method}`
                    : "Nothing delivered"}
            </p>
            <details>
                <summary>Everything about this order</summary>
                <dl className="euk-op-facts">
                    <Fact label="Order" value={order.order_id} />
                    <Fact label="Kit" value={order.kit_id} />
                    <Fact label="Currency" value={order.currency} />
                </dl>
                <h3>Files</h3>
                {items.length === 0 && (
                    <p className="euk-op-quiet">Not recorded (order made before DEC-108).</p>
                )}
                <ul className="euk-op-plain">
                    {(items.length ? items : order.job_ids.map((job_id) => ({ job_id }))).map(
                        (item) => (
                            <li key={item.job_id}>
                                {"requirement_name" in item && item.requirement_name
                                    ? `${item.requirement_name} · `
                                    : ""}
                                {liveIds.has(item.job_id) ? (
                                    <Link href={`/admin/uploads/${item.job_id}`}>{item.job_id}</Link>
                                ) : (
                                    <code>{item.job_id}</code>
                                )}
                                {liveIds.has(item.job_id) ? "" : " (erased)"}
                            </li>
                        ),
                    )}
                </ul>
                <h3>Deliveries</h3>
                {(order.deliveries ?? []).length === 0 && (
                    <p className="euk-op-quiet">
                        {order.delivered_at
                            ? "Only the first delivery was recorded (order made before DEC-108)."
                            : "None."}
                    </p>
                )}
                <ul className="euk-op-plain">
                    {(order.deliveries ?? []).map((delivery, index) => (
                        <li key={`${delivery.at}-${index}`}>
                            {when(delivery.at)} · {delivery.method}
                            {delivery.masked_address ? ` to ${delivery.masked_address}` : ""} ·{" "}
                            {delivery.succeeded ? "sent" : `failed: ${delivery.error ?? "unknown"}`}
                        </li>
                    ))}
                </ul>
            </details>
        </li>
    );
}
