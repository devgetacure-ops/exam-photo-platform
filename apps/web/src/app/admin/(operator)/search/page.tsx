import Link from "next/link";
import { Badge, Failure } from "../../../../components/operator/ui";
import { rupees, when, type Customer, type OrderView, type Ticket, type UploadRow } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

interface Results {
    orders: OrderView[];
    uploads: UploadRow[];
    customers: Customer[];
    tickets: Ticket[];
}

export default async function SearchPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
    await requireOperator();
    const q = ((await searchParams).q ?? "").trim();
    if (q.length < 2) return <p className="euk-op-quiet">Type at least two characters.</p>;
    const loaded = await engineJson<Results>(`/v1/operator/search?q=${encodeURIComponent(q)}`);
    if (!loaded.ok) return <Failure what="search" error={loaded.error} />;
    const { orders, uploads, customers, tickets } = loaded.value;
    const empty = !orders.length && !uploads.length && !customers.length && !tickets.length;

    return (
        <>
            <h1>“{q}”</h1>
            {empty && <p className="euk-op-quiet">Nothing matches.</p>}
            {customers.length > 0 && (
                <section className="euk-op-section">
                    <h2>Customers</h2>
                    <ul className="euk-op-plain">
                        {customers.map((c) => (
                            <li key={c.email}>
                                <Link href={`/admin/customers/${encodeURIComponent(c.email)}`}>{c.email}</Link>
                                {c.phone ? ` · ${c.phone}` : ""} · last seen {when(c.last_seen)}
                            </li>
                        ))}
                    </ul>
                </section>
            )}
            {orders.length > 0 && (
                <section className="euk-op-section">
                    <h2>Orders</h2>
                    <ul className="euk-op-plain">
                        {orders.map((o) => (
                            <li key={o.order_id}>
                                <Link href={`/admin/orders/${o.order_id}`}>{o.order_id}</Link> · {o.exam_names.join(", ") || "exam not recorded"} ·{" "}
                                {rupees(o.amount_paise)} · <Badge state={o.state} />
                            </li>
                        ))}
                    </ul>
                </section>
            )}
            {tickets.length > 0 && (
                <section className="euk-op-section">
                    <h2>Inbox</h2>
                    <ul className="euk-op-plain">
                        {tickets.map((t) => (
                            <li key={t.id}>
                                <Link href={`/admin/inbox/${t.id}`}>{t.reference ?? t.id}</Link> · {t.kind} · {t.email} · <Badge state={t.status} />
                            </li>
                        ))}
                    </ul>
                </section>
            )}
            {uploads.length > 0 && (
                <section className="euk-op-section">
                    <h2>Uploads</h2>
                    <ul className="euk-op-plain">
                        {uploads.map((u) => (
                            <li key={u.job_id}>
                                <Link href={`/admin/uploads/${u.job_id}`}>{u.requirement_name ?? u.job_id}</Link> · {u.exam_name} · {when(u.started_at)} ·{" "}
                                <Badge state={u.status} />
                            </li>
                        ))}
                    </ul>
                </section>
            )}
        </>
    );
}
