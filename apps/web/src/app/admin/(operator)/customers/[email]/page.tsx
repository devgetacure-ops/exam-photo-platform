import Link from "next/link";
import { notFound } from "next/navigation";
import { Badge, Fact, NotesBlock } from "../../../../../components/operator/ui";
import { rupees, seconds, when, type CustomerDetail } from "../../../../../lib/operator/data";
import { engineJson, enginePost } from "../../../../../lib/operator/engine";
import { requireOperator } from "../../../../../lib/operator/guard";
import { mailto, replies } from "../../../../../lib/operator/templates";

export default async function CustomerPage({ params }: { params: Promise<{ email: string }> }) {
    const operator = await requireOperator();
    const email = decodeURIComponent((await params).email);
    if (!email.includes("@") || email.length > 254) notFound();
    const loaded = await engineJson<CustomerDetail>(`/v1/operator/customers/${encodeURIComponent(email)}`);
    if (!loaded.ok) notFound();
    const customer = loaded.value;
    await enginePost("/v1/operator/activity", { actor: operator, action: "viewed customer", target: `customer:${customer.email}` }).catch(() => null);
    const back = `/admin/customers/${encodeURIComponent(customer.email)}`;
    const latest = customer.orders[0];

    return (
        <>
            <p>
                <Link href="/admin/customers">← Customers</Link>
            </p>
            <h1>{customer.email}</h1>
            <dl className="euk-op-facts">
                <Fact label="Spent" value={rupees(customer.spent_paise)} />
                <Fact label="Orders" value={customer.orders.length} />
                <Fact label="Phone" value={customer.contact?.phone} />
                <Fact label="First seen" value={when(customer.contact?.first_seen)} />
                <Fact label="Last seen" value={when(customer.contact?.last_seen)} />
                <Fact label="Messages" value={customer.tickets.length} />
            </dl>

            <section className="euk-op-section">
                <h2>Write to them</h2>
                <p className="euk-op-filter">
                    <a href={`mailto:${encodeURIComponent(customer.email)}`}>Blank email</a>
                    {replies({
                        exam: latest?.exam_names[0],
                        paymentReference: latest?.payment_reference,
                        amountPaise: latest?.amount_paise,
                    }).map((reply) => (
                        <a key={reply.id} href={mailto(customer.email, reply)}>
                            {reply.label}
                        </a>
                    ))}
                </p>
            </section>

            <section className="euk-op-section">
                <h2>Orders</h2>
                {customer.orders.length === 0 && <p className="euk-op-quiet">None.</p>}
                <ul className="euk-op-list">
                    {customer.orders.map((order) => (
                        <li key={order.order_id} className="euk-op-card">
                            <Link href={`/admin/orders/${order.order_id}`} className="euk-op-row">
                                <span>
                                    {order.exam_names.join(", ") || order.order_id} · {rupees(order.amount_paise)} · {when(order.created_at)}
                                </span>
                                <Badge state={order.state} />
                            </Link>
                        </li>
                    ))}
                </ul>
            </section>

            <section className="euk-op-section">
                <h2>Messages</h2>
                {customer.tickets.length === 0 && <p className="euk-op-quiet">None.</p>}
                <ul className="euk-op-list">
                    {customer.tickets.map((ticket) => (
                        <li key={ticket.id} className="euk-op-card">
                            <Link href={`/admin/inbox/${ticket.id}`} className="euk-op-row">
                                <span>
                                    {ticket.kind}
                                    {ticket.exam ? ` · ${ticket.exam}` : ""} · {when(ticket.created_at)}
                                </span>
                                <Badge state={ticket.status} />
                            </Link>
                        </li>
                    ))}
                </ul>
            </section>

            <section className="euk-op-section">
                <h2>Uploads in their sessions</h2>
                {customer.uploads.length === 0 && <p className="euk-op-quiet">None recorded.</p>}
                <ul className="euk-op-plain">
                    {customer.uploads.map((row) => (
                        <li key={row.job_id}>
                            <Link href={`/admin/uploads/${row.job_id}`}>{row.requirement_name ?? row.job_id}</Link> · {row.exam_name} ·{" "}
                            {row.outcome ?? row.status} · {seconds(row.processing_seconds)} · {when(row.started_at)}
                        </li>
                    ))}
                </ul>
            </section>

            <NotesBlock target={`customer:${customer.email}`} back={back} notes={customer.notes} />
        </>
    );
}
