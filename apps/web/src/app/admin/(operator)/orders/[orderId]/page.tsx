import Link from "next/link";
import { notFound } from "next/navigation";
import { ActionForm, Badge, Failure, Fact, NotesBlock } from "../../../../../components/operator/ui";
import { rupees, seconds, when, type OrderDetail } from "../../../../../lib/operator/data";
import { engineJson } from "../../../../../lib/operator/engine";
import { requireOperator } from "../../../../../lib/operator/guard";
import { mailto, replies } from "../../../../../lib/operator/templates";

export default async function OrderPage({ params }: { params: Promise<{ orderId: string }> }) {
    await requireOperator();
    const { orderId } = await params;
    if (!/^order_[A-Za-z0-9_-]{1,64}$/.test(orderId)) notFound();
    const loaded = await engineJson<OrderDetail>(`/v1/operator/orders/${orderId}`);
    if (!loaded.ok) return <Failure what={orderId} error={loaded.error} />;
    const order = loaded.value;
    const back = `/admin/orders/${order.order_id}`;
    const email = order.emails[0];
    const templates = replies({
        exam: order.exam_names[0],
        paymentReference: order.payment_reference,
        amountPaise: order.amount_paise,
        refundReference: order.refund?.reference,
    });

    return (
        <>
            <p>
                <Link href="/admin/orders">← Orders</Link>
            </p>
            <h1 className="euk-op-row">
                <span>{order.exam_names.join(", ") || "Order"}</span>
                <Badge state={order.state} />
            </h1>
            <p className="euk-op-quiet">{order.order_id}</p>

            <dl className="euk-op-facts">
                <Fact label="Amount" value={rupees(order.amount_paise)} />
                <Fact label="Ordered" value={when(order.created_at)} />
                <Fact label="Paid" value={order.paid_at ? when(order.paid_at) : "No"} alarm={order.state === "refund-due"} />
                <Fact label="Payment reference" value={order.payment_reference} />
                <Fact label="Method" value={order.payment_method} />
                <Fact
                    label="Email"
                    value={order.emails.length ? order.emails.map((address) => (
                        <Link key={address} href={`/admin/customers/${encodeURIComponent(address)}`}>
                            {address}{" "}
                        </Link>
                    )) : "Not known"}
                />
                <Fact label="Phone" value={order.payer_contact} />
                <Fact label="First delivered" value={order.delivered_at ? `${when(order.delivered_at)} by ${order.delivery_method}` : "Nothing delivered"} />
                <Fact label="Session" value={<code>{order.kit_id}</code>} />
                {order.refund && <Fact label="Refunded" value={`${when(order.refund.at)} · ${order.refund.reference ?? "no reference"} · ${order.refund.actor}`} />}
            </dl>

            <section className="euk-op-section">
                <h2>Files</h2>
                <ul className="euk-op-list">
                    {order.uploads.map((upload) => (
                        <li key={upload.job_id} className="euk-op-card">
                            <Link href={`/admin/uploads/${upload.job_id}`} className="euk-op-upload">
                                {upload.live && (
                                    // eslint-disable-next-line @next/next/no-img-element
                                    <img src={`/admin/files/${upload.job_id}/input.jpg`} alt="" loading="lazy" />
                                )}
                                <span>
                                    <strong>{upload.requirement_name ?? upload.job_id}</strong>
                                    <br />
                                    {upload.outcome ?? upload.status} · {seconds(upload.processing_seconds)}
                                    {upload.output_width ? ` · ${upload.output_width} × ${upload.output_height} px` : ""}
                                    <br />
                                    <span className="euk-op-quiet">
                                        {upload.started_at ? when(upload.started_at) : "not in the history"} · {upload.live ? "photo still held" : "erased"}
                                    </span>
                                </span>
                            </Link>
                        </li>
                    ))}
                </ul>
            </section>

            <section className="euk-op-section">
                <h2>Deliveries</h2>
                {(order.deliveries ?? []).length === 0 && <p className="euk-op-quiet">None recorded.</p>}
                <ul className="euk-op-plain">
                    {(order.deliveries ?? []).map((delivery, index) => (
                        <li key={index}>
                            {when(delivery.at)} · {delivery.method}
                            {delivery.address ? ` to ${delivery.address}` : delivery.masked_address ? ` to ${delivery.masked_address}` : ""} ·{" "}
                            {delivery.succeeded ? "sent" : `failed: ${delivery.error ?? "unknown"}`}
                        </li>
                    ))}
                </ul>
                {(order.failed_payments ?? []).length > 0 && (
                    <>
                        <h3>Failed payment attempts</h3>
                        <ul className="euk-op-plain">
                            {(order.failed_payments ?? []).map((attempt, index) => (
                                <li key={index}>
                                    {when(attempt.at)} · {attempt.method ?? "?"} · {attempt.error ?? "no reason given"}
                                </li>
                            ))}
                        </ul>
                    </>
                )}
            </section>

            <section className="euk-op-section">
                <h2>Complaints and messages</h2>
                {order.tickets.length === 0 && <p className="euk-op-quiet">None.</p>}
                <ul className="euk-op-list">
                    {order.tickets.map((ticket) => (
                        <li key={ticket.id} className="euk-op-card">
                            <Link href={`/admin/inbox/${ticket.id}`} className="euk-op-row">
                                <span>
                                    {ticket.kind} · {when(ticket.created_at)} · {ticket.message?.slice(0, 80)}
                                </span>
                                <Badge state={ticket.status} />
                            </Link>
                        </li>
                    ))}
                </ul>
            </section>

            <section className="euk-op-section">
                <h2>Timeline</h2>
                <ol className="euk-op-timeline">
                    {order.timeline.map((event, index) => (
                        <li key={index}>
                            <span className="euk-op-quiet">{when(event.at)}</span> {event.what}
                        </li>
                    ))}
                </ol>
            </section>

            <section className="euk-op-section">
                <h2>Refund</h2>
                {order.refund ? (
                    <ActionForm action={`/admin/actions/refund/${order.order_id}`} back={back}>
                        <input type="hidden" name="undo" value="true" />
                        <p>
                            Marked refunded {when(order.refund.at)} by {order.refund.actor}
                            {order.refund.reference ? `, reference ${order.refund.reference}` : ""}.
                        </p>
                        <button type="submit" className="euk-op-button">
                            Undo the mark
                        </button>
                    </ActionForm>
                ) : (
                    <ActionForm action={`/admin/actions/refund/${order.order_id}`} back={back}>
                        <p className="euk-op-quiet">
                            Issue the refund in the Razorpay dashboard first, then record it here. This page never moves money.
                        </p>
                        <label>
                            <span className="euk-label">Razorpay refund reference</span>
                            <input name="reference" maxLength={80} placeholder="rfnd_…" />
                        </label>
                        <button type="submit" className="euk-op-button" disabled={!order.paid_at}>
                            Mark refunded
                        </button>
                    </ActionForm>
                )}
            </section>

            {email && (
                <section className="euk-op-section">
                    <h2>Reply</h2>
                    <p className="euk-op-quiet">Opens in your mail app, addressed to {email} and filled in.</p>
                    <p className="euk-op-filter">
                        {templates.map((reply) => (
                            <a key={reply.id} href={mailto(email, reply)}>
                                {reply.label}
                            </a>
                        ))}
                    </p>
                </section>
            )}

            <NotesBlock target={`order:${order.order_id}`} back={back} notes={order.notes} />
        </>
    );
}
