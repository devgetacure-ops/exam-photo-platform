import Link from "next/link";
import { notFound } from "next/navigation";
import { ActionForm, Badge, Fact, NotesBlock } from "../../../../../components/operator/ui";
import { rupees, when, type Note, type OrderDetail, type Ticket } from "../../../../../lib/operator/data";
import { engineJson } from "../../../../../lib/operator/engine";
import { requireOperator } from "../../../../../lib/operator/guard";
import { mailto, replies } from "../../../../../lib/operator/templates";

type TicketDetail = Ticket & { notes: Note[]; order: OrderDetail | null; same_exam?: number };

export default async function TicketPage({ params }: { params: Promise<{ ticketId: string }> }) {
    await requireOperator();
    const { ticketId } = await params;
    if (!/^t_[a-f0-9]{12}$/.test(ticketId)) notFound();
    const loaded = await engineJson<TicketDetail>(`/v1/operator/tickets/${ticketId}`);
    if (!loaded.ok) notFound();
    const ticket = loaded.value;
    const back = `/admin/inbox/${ticket.id}`;
    const action = `/admin/actions/ticket/${ticket.id}`;
    const templates = replies({
        exam: ticket.exam || ticket.order?.exam_names[0],
        paymentReference: ticket.order?.payment_reference ?? ticket.payment_reference,
        amountPaise: ticket.order?.amount_paise,
        reference: ticket.reference,
        refundReference: ticket.order?.refund?.reference,
    }).filter((reply) => (ticket.kind === "exam" ? ["exam-added", "acknowledge"].includes(reply.id) : reply.id !== "exam-added"));

    return (
        <>
            <p>
                <Link href={ticket.kind === "exam" ? "/admin/inbox?kind=exam" : "/admin/inbox"}>← Inbox</Link>
            </p>
            <h1 className="euk-op-row">
                <span>
                    {ticket.kind}
                    {ticket.exam ? `: ${ticket.exam}` : ""}
                </span>
                <Badge state={ticket.status} />
            </h1>
            <p className="euk-op-quiet">
                {ticket.reference ?? ticket.id} · {when(ticket.created_at)}
            </p>
            {ticket.message && <p className="euk-op-message euk-op-card">{ticket.message}</p>}

            <dl className="euk-op-facts">
                <Fact
                    label="From"
                    value={ticket.email ? <Link href={`/admin/customers/${encodeURIComponent(ticket.email)}`}>{ticket.email}</Link> : "—"}
                />
                <Fact label="Payment reference given" value={ticket.payment_reference} />
                <Fact label="Acknowledged" value={when(ticket.acknowledged_at)} alarm={ticket.ack_overdue} />
                <Fact label="Resolved" value={when(ticket.resolved_at)} alarm={ticket.resolve_overdue} />
                {ticket.kind === "exam" && <Fact label="People who asked for this" value={ticket.same_exam ?? 1} />}
                {ticket.kind === "exam" && <Fact label="Told it is added" value={when(ticket.added_at)} />}
            </dl>

            {ticket.order && (
                <section className="euk-op-section">
                    <h2>The order</h2>
                    <Link href={`/admin/orders/${ticket.order.order_id}`} className="euk-op-card euk-op-cardlink">
                        <p className="euk-op-row">
                            <strong>{ticket.order.exam_names.join(", ") || ticket.order.order_id}</strong>
                            <Badge state={ticket.order.state} />
                        </p>
                        <p>
                            {rupees(ticket.order.amount_paise)} · paid {when(ticket.order.paid_at)} ·{" "}
                            {ticket.order.delivered_at ? `delivered ${when(ticket.order.delivered_at)} by ${ticket.order.delivery_method}` : "nothing delivered"}
                        </p>
                    </Link>
                </section>
            )}

            <section className="euk-op-section">
                <h2>Status</h2>
                <ActionForm action={action} back={back} className="euk-op-filter">
                    {["open", "answered", "resolved"].map((state) => (
                        <button key={state} type="submit" name="status" value={state} className="euk-op-button" aria-pressed={ticket.status === state}>
                            Mark {state}
                        </button>
                    ))}
                </ActionForm>
                {ticket.kind === "exam" && (
                    <ActionForm action={action} back={back}>
                        <input type="hidden" name="added" value={ticket.added_at ? "false" : "true"} />
                        <button type="submit" className="euk-op-button">
                            {ticket.added_at ? "Undo: examination added" : "Examination is added"}
                        </button>
                    </ActionForm>
                )}
                {ticket.kind !== "exam" && (
                    <ActionForm action={action} back={back}>
                        <label>
                            <span className="euk-label">{ticket.order ? "Link to a different order" : "Link to an order"}</span>
                            <input name="order_id" pattern="order_[A-Za-z0-9_-]{1,64}" placeholder="order_…" required />
                        </label>
                        <button type="submit" className="euk-op-button">
                            Link
                        </button>
                    </ActionForm>
                )}
            </section>

            {ticket.email && (
                <section className="euk-op-section">
                    <h2>Reply</h2>
                    <p className="euk-op-quiet">Opens in your mail app. Mark it answered once sent.</p>
                    <p className="euk-op-filter">
                        {templates.map((reply) => (
                            <a key={reply.id} href={mailto(ticket.email as string, reply)}>
                                {reply.label}
                            </a>
                        ))}
                    </p>
                </section>
            )}

            <NotesBlock target={`ticket:${ticket.id}`} back={back} notes={ticket.notes} />
        </>
    );
}
