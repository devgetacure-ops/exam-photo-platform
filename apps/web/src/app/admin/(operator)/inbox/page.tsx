import type { Metadata } from "next";
import Link from "next/link";
import { NotesSection } from "../../../../components/console/notes";
import { ReplyMenu } from "../../../../components/console/reply-menu";
import { Sheet, SheetSection } from "../../../../components/console/sheet";
import { TicketsTable } from "../../../../components/console/tables";
import { when } from "../../../../lib/operator/format";
import { ActionForm, Button, Card, Check, Facts, Field, Input, PageHeader, Problem, StateBadge, Textarea } from "../../../../components/console/ui";
import { rupees, type Note, type OrderDetail, type Ticket } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

export const metadata: Metadata = { title: "Inbox" };

type TicketDetail = Ticket & { notes: Note[]; order: OrderDetail | null; same_exam?: number };

const VIEWS: [string, string][] = [
    ["", "Open"],
    ["complaints", "Complaints & grievances"],
    ["resolved", "Resolved"],
    ["exams", "Exam requests"],
];

export default async function InboxPage({ searchParams }: { searchParams: Promise<{ view?: string; open?: string }> }) {
    await requireOperator();
    const { view = "", open } = await searchParams;
    const loaded = await engineJson<{ tickets: Ticket[] }>("/v1/operator/tickets");
    if (!loaded.ok) return <Problem what="the inbox" error={loaded.error} />;
    const all = loaded.value.tickets;
    const messages = all.filter((t) => t.kind !== "exam");
    const exams = all.filter((t) => t.kind === "exam");
    const pick: Record<string, Ticket[]> = {
        "": messages.filter((t) => t.status !== "resolved"),
        complaints: messages.filter((t) => t.kind === "complaint" || t.kind === "grievance"),
        resolved: messages.filter((t) => t.status === "resolved"),
        exams,
    };
    const shown = pick[view] ?? pick[""];
    const chips = VIEWS.map(([value, label]) => ({
        value,
        label,
        count: pick[value].length,
        tone: value === "" && pick[""].some((t) => t.ack_overdue) ? ("bad" as const) : undefined,
    }));
    const detail = open && /^t_[a-f0-9]{12}$/.test(open) ? await engineJson<TicketDetail>(`/v1/operator/tickets/${open}`) : null;
    const template =
        detail?.ok && detail.value.kind === "exam" && detail.value.exam
            ? await engineJson<{ subject: string; body: string }>(`/v1/operator/exam-requests/template?exam=${encodeURIComponent(detail.value.exam)}`)
            : null;

    return (
        <>
            <PageHeader title="Inbox" description="Questions, complaints and grievances from the support form, matched to their order; and requests for new examinations." />
            {view === "exams" && <DemandSummary tickets={exams} />}
            <TicketsTable tickets={shown} chips={chips} selected={open} />
            {detail?.ok && (
                <TicketSheet
                    ticket={detail.value}
                    template={template?.ok ? template.value : null}
                    back={`/admin/inbox?${new URLSearchParams({ ...(view ? { view } : {}), open: detail.value.id })}`}
                />
            )}
        </>
    );
}

function DemandSummary({ tickets }: { tickets: Ticket[] }) {
    const groups = new Map<string, { name: string; count: number; waiting: number; first: string }>();
    for (const ticket of tickets) {
        const key = (ticket.exam ?? "").trim().toLowerCase() || "(no name)";
        const entry = groups.get(key) ?? { name: ticket.exam || "(no name)", count: 0, waiting: 0, first: ticket.id };
        entry.count += 1;
        if (!ticket.added_at) entry.waiting += 1;
        groups.set(key, entry);
    }
    const ranked = [...groups.values()].sort((a, b) => b.waiting - a.waiting || b.count - a.count).slice(0, 8);
    if (ranked.length === 0) return null;
    return (
        <Card className="p-4">
            <p className="m-0 mb-3 text-[13px] font-semibold uppercase tracking-wide text-[var(--op-muted)]">Most wanted</p>
            <div className="flex flex-wrap gap-2">
                {ranked.map((group) => (
                    <Link
                        key={group.name}
                        href={`/admin/inbox?view=exams&open=${group.first}`}
                        className="flex items-center gap-2 rounded-full border border-[var(--op-border)] px-3 py-1.5 text-sm hover:bg-[var(--op-hover)]"
                    >
                        {group.name}
                        <span className="op-num rounded-full bg-[var(--op-accent-soft)] px-1.5 text-xs font-semibold text-[var(--op-accent-text)]">{group.waiting}</span>
                    </Link>
                ))}
            </div>
        </Card>
    );
}

function TicketSheet({ ticket, template, back }: { ticket: TicketDetail; template: { subject: string; body: string } | null; back: string }) {
    const action = `/admin/actions/ticket/${ticket.id}`;
    const isExam = ticket.kind === "exam";
    return (
        <Sheet
            title={isExam ? `Exam request · ${ticket.exam}` : `${ticket.kind[0].toUpperCase()}${ticket.kind.slice(1)}${ticket.exam ? ` · ${ticket.exam}` : ""}`}
            subtitle={`${ticket.reference ?? ticket.id} · ${when(ticket.created_at)}`}
            badge={<StateBadge state={ticket.status} />}
            actions={
                <>
                    {ticket.email && (
                        <ReplyMenu
                            email={ticket.email}
                            only={isExam ? ["exam-added", "acknowledge"] : ["acknowledge", "file-missing", "refund-done", "wrong-size", "charged-twice"]}
                            context={{
                                exam: ticket.exam || ticket.order?.exam_names[0],
                                paymentReference: ticket.order?.payment_reference ?? ticket.payment_reference,
                                amountPaise: ticket.order?.amount_paise,
                                reference: ticket.reference,
                                refundReference: ticket.order?.refund?.reference,
                            }}
                        />
                    )}
                    {ticket.status !== "resolved" ? (
                        <ActionForm action={action} back={back} className="flex flex-1 gap-2">
                            {ticket.status === "open" && (
                                <Button type="submit" name="status" value="answered" size="lg" className="flex-1">
                                    Mark answered
                                </Button>
                            )}
                            <Button type="submit" name="status" value="resolved" variant="primary" size="lg" className="flex-1">
                                Resolve
                            </Button>
                        </ActionForm>
                    ) : (
                        <ActionForm action={action} back={back} className="flex flex-1">
                            <Button type="submit" name="status" value="open" size="lg" className="flex-1">
                                Reopen
                            </Button>
                        </ActionForm>
                    )}
                </>
            }
        >
            {(ticket.ack_overdue || ticket.resolve_overdue) && (
                <p className="m-0 rounded-lg bg-[var(--op-bad-bg)] px-3 py-2.5 text-sm text-[var(--op-bad)]">
                    {ticket.ack_overdue ? "Waiting more than 48 hours for a reply." : "Open for more than a month."} The grievance page promises better.
                </p>
            )}
            {ticket.message && <p className="m-0 whitespace-pre-wrap rounded-lg bg-[var(--op-muted-bg)] px-4 py-3 text-[15px] leading-relaxed">{ticket.message}</p>}
            <Facts
                rows={[
                    ["From", ticket.email ? <Link key="e" href={`/admin/customers?open=${encodeURIComponent(ticket.email)}`} className="underline">{ticket.email}</Link> : null],
                    ["Payment id given", ticket.payment_reference],
                    ["Acknowledged", when(ticket.acknowledged_at)],
                    ["Resolved", when(ticket.resolved_at)],
                    ...(isExam ? ([["Asked by", `${ticket.same_exam ?? 1} people`], ["Told it is added", when(ticket.added_at)]] as [string, string][]) : []),
                ]}
            />
            {ticket.order && (
                <SheetSection title="The order">
                    <Link href={`/admin/orders?open=${ticket.order.order_id}`} className="flex items-center gap-3 rounded-lg border border-[var(--op-border)] p-3 text-sm hover:bg-[var(--op-hover)]">
                        <span className="min-w-0 flex-1">
                            <strong className="font-medium">{ticket.order.exam_names.join(", ") || ticket.order.order_id}</strong>
                            <span className="block text-xs text-[var(--op-muted)]">
                                {rupees(ticket.order.amount_paise)} · paid {when(ticket.order.paid_at)} ·{" "}
                                {ticket.order.delivered_at ? `delivered by ${ticket.order.delivery_method}` : "nothing delivered"}
                            </span>
                        </span>
                        <StateBadge state={ticket.order.state} />
                    </Link>
                </SheetSection>
            )}
            {!isExam && (
                <SheetSection title={ticket.order ? "Link to a different order" : "Link to an order"}>
                    <ActionForm action={action} back={back} className="flex gap-2">
                        <Input name="order_id" pattern="order_[A-Za-z0-9_-]{1,64}" placeholder="order_…" required aria-label="Order id" />
                        <Button type="submit">Link</Button>
                    </ActionForm>
                </SheetSection>
            )}
            {isExam && ticket.exam && template && !ticket.added_at && (
                <SheetSection title={`Tell everyone who asked (${ticket.same_exam ?? 1})`}>
                    <ActionForm action="/admin/actions/exam-added" back={back} className="flex flex-col gap-3">
                        <input type="hidden" name="target" value={ticket.exam} />
                        <Field label="Subject">
                            <Input name="subject" maxLength={200} required defaultValue={template.subject} />
                        </Field>
                        <Field label="Message">
                            <Textarea name="body" rows={5} maxLength={20000} required defaultValue={template.body} />
                        </Field>
                        <Check name="confirm" value="yes" required>
                            It is added: email them all and close their requests
                        </Check>
                        <Button type="submit" variant="primary" className="self-start">
                            Send
                        </Button>
                    </ActionForm>
                </SheetSection>
            )}
            <NotesSection target={`ticket:${ticket.id}`} back={back} notes={ticket.notes} />
        </Sheet>
    );
}
