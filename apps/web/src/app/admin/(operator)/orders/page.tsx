import Link from "next/link";
import { Badge, Failure } from "../../../../components/operator/ui";
import { rupees, when, type OrderView } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

const STATES = ["refund-due", "delivered", "payment-failed", "unpaid", "refunded"];

export default async function OrdersPage({
    searchParams,
}: {
    searchParams: Promise<{ q?: string; state?: string }>;
}) {
    await requireOperator();
    const { q = "", state = "" } = await searchParams;
    const loaded = await engineJson<{ orders: OrderView[] }>(`/v1/operator/orders?q=${encodeURIComponent(q)}`);
    if (!loaded.ok) return <Failure what="orders" error={loaded.error} />;
    const all = loaded.value.orders;
    const shown = state ? all.filter((order) => order.state === state) : all;
    const count = (name: string) => all.filter((order) => order.state === name).length;
    const link = (next: string) => `/admin/orders?${new URLSearchParams({ ...(q ? { q } : {}), ...(next ? { state: next } : {}) })}`;

    return (
        <>
            <h1>Orders</h1>
            <form method="get" className="euk-op-search">
                <input name="q" type="search" defaultValue={q} placeholder="Email, phone, order, payment, exam" aria-label="Filter orders" />
                {state && <input type="hidden" name="state" value={state} />}
                <button type="submit" className="euk-op-button">
                    Filter
                </button>
            </form>
            <p className="euk-op-filter">
                <Link href={link("")} aria-current={!state}>
                    All ({all.length})
                </Link>
                {STATES.map((name) => (
                    <Link key={name} href={link(name)} aria-current={state === name}>
                        <Badge state={name} /> {count(name)}
                    </Link>
                ))}
            </p>
            {shown.length === 0 && <p className="euk-op-quiet">None.</p>}
            <ul className="euk-op-list">
                {shown.map((order) => (
                    <li key={order.order_id} className="euk-op-card" data-state={order.state}>
                        <Link href={`/admin/orders/${order.order_id}`} className="euk-op-cardlink">
                            <p className="euk-op-row">
                                <strong>{order.exam_names.join(", ") || "Examination not recorded"}</strong>
                                <Badge state={order.state} />
                            </p>
                            <p>
                                {rupees(order.amount_paise)} · {order.job_ids.length} file{order.job_ids.length === 1 ? "" : "s"} · {when(order.created_at)}
                            </p>
                            <p className="euk-op-quiet">
                                {order.emails.join(", ") || "no email yet"}
                                {order.payer_contact ? ` · ${order.payer_contact}` : ""}
                                {order.payment_reference ? ` · ${order.payment_reference}` : ""}
                            </p>
                        </Link>
                    </li>
                ))}
            </ul>
        </>
    );
}
