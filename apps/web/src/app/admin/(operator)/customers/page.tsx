import { Download } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { NotesSection } from "../../../../components/console/notes";
import { ReplyMenu } from "../../../../components/console/reply-menu";
import { Sheet, SheetSection } from "../../../../components/console/sheet";
import { CustomersTable } from "../../../../components/console/tables";
import { when } from "../../../../lib/operator/format";
import { Facts, PageHeader, Problem, StateBadge, buttonStyles } from "../../../../components/console/ui";
import { rupees, type Customer, type CustomerDetail } from "../../../../lib/operator/data";
import { engineJson, enginePost } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

export const metadata: Metadata = { title: "Customers" };

export default async function CustomersPage({ searchParams }: { searchParams: Promise<{ paid?: string; open?: string }> }) {
    const operator = await requireOperator();
    const { paid = "", open } = await searchParams;
    const loaded = await engineJson<{ customers: Customer[] }>("/v1/operator/customers");
    if (!loaded.ok) return <Problem what="customers" error={loaded.error} />;
    const all = loaded.value.customers;
    const payers = all.filter((c) => (c.paid_orders ?? 0) > 0);
    const shown = paid === "yes" ? payers : paid === "no" ? all.filter((c) => !c.paid_orders) : paid === "repeat" ? all.filter((c) => (c.paid_orders ?? 0) > 1) : all;
    const chips = [
        { value: "", label: "Everyone", count: all.length },
        { value: "yes", label: "Paid", count: payers.length },
        { value: "repeat", label: "Paid more than once", count: all.filter((c) => (c.paid_orders ?? 0) > 1).length },
        { value: "no", label: "Never paid", count: all.length - payers.length },
    ];
    const email = open && open.includes("@") && open.length <= 254 ? open : null;
    const detail = email ? await engineJson<CustomerDetail>(`/v1/operator/customers/${encodeURIComponent(email)}`) : null;
    if (detail?.ok) await enginePost("/v1/operator/activity", { actor: operator, action: "viewed customer", target: `customer:${detail.value.email}` }).catch(() => null);

    return (
        <>
            <PageHeader
                title="Customers"
                description="Every address a candidate gave us: at payment, for delivery, or on a form."
                actions={
                    <a href="/admin/export/customers" download className={buttonStyles({ variant: "secondary" })}>
                        <Download size={15} aria-hidden="true" />
                        Export CSV
                    </a>
                }
            />
            <CustomersTable customers={shown} chips={chips} selected={open} />
            {detail?.ok && <CustomerSheet customer={detail.value} back={`/admin/customers?${new URLSearchParams({ ...(paid ? { paid } : {}), open: detail.value.email })}`} />}
        </>
    );
}

function CustomerSheet({ customer, back }: { customer: CustomerDetail; back: string }) {
    const latest = customer.orders[0];
    return (
        <Sheet
            title={customer.email}
            subtitle={`Customer since ${when(customer.contact?.first_seen)}`}
            actions={<ReplyMenu email={customer.email} context={{ exam: latest?.exam_names[0], paymentReference: latest?.payment_reference, amountPaise: latest?.amount_paise }} />}
        >
            <Facts
                rows={[
                    ["Spent", rupees(customer.spent_paise)],
                    ["Orders", customer.orders.length],
                    ["Phone", customer.contact?.phone ? <a href={`tel:${customer.contact.phone}`} className="underline">{customer.contact.phone}</a> : null],
                    ["Last seen", when(customer.contact?.last_seen)],
                    ["Messages", customer.tickets.length],
                ]}
            />
            <SheetSection title={`Orders (${customer.orders.length})`}>
                {customer.orders.length === 0 && <p className="m-0 text-sm text-[var(--op-muted)]">None.</p>}
                {customer.orders.map((order) => (
                    <Link key={order.order_id} href={`/admin/orders?open=${order.order_id}`} className="flex items-center gap-3 rounded-lg border border-[var(--op-border)] p-3 text-sm hover:bg-[var(--op-hover)]">
                        <span className="min-w-0 flex-1">
                            <strong className="font-medium">{order.exam_names.join(", ") || order.order_id}</strong>
                            <span className="block text-xs text-[var(--op-muted)]">
                                {rupees(order.amount_paise)} · {when(order.created_at)}
                            </span>
                        </span>
                        <StateBadge state={order.state} />
                    </Link>
                ))}
            </SheetSection>
            {customer.tickets.length > 0 && (
                <SheetSection title="Messages">
                    {customer.tickets.map((ticket) => (
                        <Link key={ticket.id} href={`/admin/inbox?open=${ticket.id}`} className="flex items-center gap-3 rounded-lg border border-[var(--op-border)] p-3 text-sm hover:bg-[var(--op-hover)]">
                            <span className="min-w-0 flex-1">
                                <strong className="font-medium first-letter:uppercase">
                                    {ticket.kind}
                                    {ticket.exam ? ` · ${ticket.exam}` : ""}
                                </strong>
                                <span className="block truncate text-xs text-[var(--op-muted)]">{ticket.message}</span>
                            </span>
                            <StateBadge state={ticket.status} />
                        </Link>
                    ))}
                </SheetSection>
            )}
            {customer.uploads.length > 0 && (
                <SheetSection title="Uploads">
                    {customer.uploads.slice(0, 20).map((row) => (
                        <Link key={row.job_id} href={`/admin/uploads?days=365&open=${row.job_id}`} className="flex items-center gap-3 rounded-lg px-1 py-1.5 text-sm hover:bg-[var(--op-hover)]">
                            <span className="min-w-0 flex-1 truncate">
                                {row.requirement_name ?? row.job_id} · {row.exam_name}
                            </span>
                            <span className="op-num text-xs text-[var(--op-muted)]">{when(row.started_at)}</span>
                        </Link>
                    ))}
                </SheetSection>
            )}
            <NotesSection target={`customer:${customer.email}`} back={back} notes={customer.notes} />
        </Sheet>
    );
}
