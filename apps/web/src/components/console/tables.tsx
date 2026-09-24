"use client";

import { useMemo } from "react";
import type { Customer, OrderView, Ticket, UploadRow } from "../../lib/operator/data";
import { DataTable, type Chip, type Column } from "./data-table";
import { when } from "../../lib/operator/format";
import { StateBadge } from "./ui";

/**
 * Each list's columns (DEC-113). Client-side, because a column's cell is a
 * function and functions do not cross from the server.
 */

function rupees(paise: number) {
    return `₹${(paise / 100).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
}

function orderState(order: OrderView) {
    return order.amount_paise === 0 && order.paid_at && order.coupon_code ? "free" : order.state;
}

export function OrdersTable({ orders, chips, selected }: { orders: OrderView[]; chips: Chip[]; selected?: string | null }) {
    const columns = useMemo<Column<OrderView>[]>(
        () => [
            { id: "created", header: "When", value: (o) => o.created_at, cell: (o) => <span className="op-num whitespace-nowrap text-[var(--op-muted)]">{when(o.created_at)}</span> },
            {
                id: "who",
                header: "Customer · examination",
                value: (o) => `${o.emails.join(" ")} ${o.payer_contact ?? ""} ${o.exam_names.join(" ")} ${o.order_id} ${o.payment_reference ?? ""}`,
                cell: (o) => (
                    <span className="flex flex-col">
                        <strong className="font-semibold">{o.emails[0] ?? o.payer_contact ?? "No email yet"}</strong>
                        <span className="text-xs text-[var(--op-muted)]">
                            {o.exam_names.join(", ") || "Examination not recorded"} · {o.job_ids.length} file{o.job_ids.length === 1 ? "" : "s"}
                        </span>
                    </span>
                ),
            },
            { id: "amount", header: "Amount", align: "right", value: (o) => o.amount_paise, cell: (o) => <span className="op-num">{rupees(o.amount_paise)}</span> },
            { id: "state", header: "Status", value: (o) => orderState(o), cell: (o) => <StateBadge state={orderState(o)} /> },
            {
                id: "method",
                header: "Paid by",
                value: (o) => o.payment_method ?? "",
                cell: (o) => <span className="text-[var(--op-muted)]">{o.coupon_code && !o.amount_paise ? o.coupon_code : (o.payment_method ?? "—")}</span>,
            },
        ],
        [],
    );
    return (
        <DataTable
            rows={orders}
            columns={columns}
            rowId={(o) => o.order_id}
            selected={selected}
            chips={chips}
            initialSort={{ id: "created", desc: true }}
            searchPlaceholder="Filter by email, phone, exam, payment…"
            empty={<p className="m-0 px-6 py-12 text-center text-[var(--op-muted)]">No orders match.</p>}
            mobile={(o) => (
                <span className="flex items-start gap-3">
                    <span className="flex min-w-0 flex-1 flex-col">
                        <strong className="truncate font-semibold">{o.emails[0] ?? o.payer_contact ?? "No email yet"}</strong>
                        <span className="truncate text-xs text-[var(--op-muted)]">
                            {o.exam_names.join(", ") || "Examination not recorded"} · {when(o.created_at)}
                        </span>
                    </span>
                    <span className="flex flex-col items-end gap-1">
                        <span className="op-num font-semibold">{rupees(o.amount_paise)}</span>
                        <StateBadge state={orderState(o)} />
                    </span>
                </span>
            )}
        />
    );
}

export function UploadsTable({ uploads, chips, selected }: { uploads: UploadRow[]; chips: Chip[]; selected?: string | null }) {
    const columns = useMemo<Column<UploadRow>[]>(
        () => [
            { id: "started", header: "When", value: (u) => u.started_at, cell: (u) => <span className="op-num whitespace-nowrap text-[var(--op-muted)]">{when(u.started_at)}</span> },
            {
                id: "what",
                header: "Examination · file",
                value: (u) => `${u.exam_name ?? u.exam_id ?? ""} ${u.requirement_name ?? ""} ${u.job_id} ${u.kit_id ?? ""}`,
                cell: (u) => (
                    <span className="flex items-center gap-3">
                        {u.live ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={`/admin/files/${u.job_id}/input.jpg`} alt="" loading="lazy" className="h-10 w-8 shrink-0 rounded object-cover" />
                        ) : (
                            <span className="h-10 w-8 shrink-0 rounded border border-dashed border-[var(--op-border-strong)]" aria-hidden="true" />
                        )}
                        <span className="flex flex-col">
                            <strong className="font-semibold">{u.exam_name ?? u.exam_id ?? "No examination"}</strong>
                            <span className="text-xs text-[var(--op-muted)]">{u.requirement_name ?? u.requirement_type ?? "—"}</span>
                        </span>
                    </span>
                ),
            },
            { id: "time", header: "Took", align: "right", value: (u) => u.processing_seconds ?? -1, cell: (u) => <span className="op-num">{u.processing_seconds != null ? `${u.processing_seconds.toFixed(1)} s` : "—"}</span> },
            { id: "status", header: "Result", value: (u) => u.status, cell: (u) => <StateBadge state={u.status} /> },
            { id: "problem", header: "Findings", value: (u) => (u.error ?? (u.findings ?? []).join(", ")) || "", cell: (u) => <span className="text-[var(--op-muted)]">{u.error ?? ((u.findings ?? []).join(", ").replace(/_/g, " ") || "—")}</span> },
        ],
        [],
    );
    return (
        <DataTable
            rows={uploads}
            columns={columns}
            rowId={(u) => u.job_id}
            selected={selected}
            chips={chips}
            chipParam="status"
            initialSort={{ id: "started", desc: true }}
            searchPlaceholder="Filter by exam, file, session…"
            mobile={(u) => (
                <span className="flex items-center gap-3">
                    {u.live ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={`/admin/files/${u.job_id}/input.jpg`} alt="" loading="lazy" className="h-12 w-10 shrink-0 rounded object-cover" />
                    ) : (
                        <span className="h-12 w-10 shrink-0 rounded border border-dashed border-[var(--op-border-strong)]" aria-hidden="true" />
                    )}
                    <span className="flex min-w-0 flex-1 flex-col">
                        <strong className="truncate font-semibold">{u.exam_name ?? u.exam_id ?? "No examination"}</strong>
                        <span className="truncate text-xs text-[var(--op-muted)]">
                            {u.requirement_name ?? "—"} · {when(u.started_at)}
                        </span>
                    </span>
                    <StateBadge state={u.status} />
                </span>
            )}
        />
    );
}

const SOURCE: Record<string, string> = {
    payment: "Paid",
    delivery: "File emailed",
    checkout_failed: "Payment failed",
    "form:exam": "Asked for an exam",
    "form:question": "Question",
    "form:complaint": "Complaint",
    "form:grievance": "Grievance",
    "form:support": "Support",
};

export function CustomersTable({ customers, chips, selected }: { customers: Customer[]; chips: Chip[]; selected?: string | null }) {
    const columns = useMemo<Column<Customer>[]>(
        () => [
            {
                id: "email",
                header: "Customer",
                value: (c) => `${c.email} ${c.phone ?? ""}`,
                cell: (c) => (
                    <span className="flex flex-col">
                        <strong className="font-semibold">{c.email}</strong>
                        <span className="text-xs text-[var(--op-muted)]">{c.phone ?? "No phone"}</span>
                    </span>
                ),
            },
            { id: "spent", header: "Spent", align: "right", value: (c) => c.spent_paise ?? 0, cell: (c) => <span className="op-num">{rupees(c.spent_paise ?? 0)}</span> },
            { id: "orders", header: "Paid orders", align: "right", value: (c) => c.paid_orders ?? 0, cell: (c) => <span className="op-num">{c.paid_orders ?? 0}</span> },
            { id: "sources", header: "How we know them", value: (c) => c.sources.join(" "), cell: (c) => <span className="text-[var(--op-muted)]">{c.sources.map((s) => SOURCE[s] ?? s).join(", ")}</span> },
            { id: "seen", header: "Last seen", value: (c) => c.last_seen, cell: (c) => <span className="op-num whitespace-nowrap text-[var(--op-muted)]">{when(c.last_seen)}</span> },
        ],
        [],
    );
    return (
        <DataTable
            rows={customers}
            columns={columns}
            rowId={(c) => c.email}
            selected={selected}
            chips={chips}
            chipParam="paid"
            initialSort={{ id: "seen", desc: true }}
            searchPlaceholder="Filter by email or phone…"
            mobile={(c) => (
                <span className="flex items-center gap-3">
                    <span className="flex min-w-0 flex-1 flex-col">
                        <strong className="truncate font-semibold">{c.email}</strong>
                        <span className="truncate text-xs text-[var(--op-muted)]">
                            {c.paid_orders ?? 0} paid · last seen {when(c.last_seen)}
                        </span>
                    </span>
                    <span className="op-num font-semibold">{rupees(c.spent_paise ?? 0)}</span>
                </span>
            )}
        />
    );
}

export function TicketsTable({ tickets, chips, selected, chipParam = "view" }: { tickets: Ticket[]; chips: Chip[]; selected?: string | null; chipParam?: string }) {
    const columns = useMemo<Column<Ticket>[]>(
        () => [
            { id: "created", header: "When", value: (t) => t.created_at, cell: (t) => <span className="op-num whitespace-nowrap text-[var(--op-muted)]">{when(t.created_at)}</span> },
            {
                id: "what",
                header: "Message",
                value: (t) => `${t.kind} ${t.email ?? ""} ${t.exam ?? ""} ${t.message ?? ""} ${t.reference ?? ""}`,
                cell: (t) => (
                    <span className="flex flex-col">
                        <strong className="font-semibold first-letter:uppercase">
                            {t.kind}
                            {t.exam ? ` · ${t.exam}` : ""}
                        </strong>
                        <span className="line-clamp-1 text-xs text-[var(--op-muted)]">{t.message || t.email}</span>
                    </span>
                ),
            },
            { id: "from", header: "From", value: (t) => t.email ?? "", cell: (t) => <span className="text-[var(--op-muted)]">{t.email}</span> },
            {
                id: "status",
                header: "Status",
                value: (t) => t.status,
                cell: (t) => (
                    <span className="flex items-center gap-1.5">
                        <StateBadge state={t.status} />
                        {(t.ack_overdue || t.resolve_overdue) && <span className="text-xs font-semibold text-[var(--op-bad)]">late</span>}
                    </span>
                ),
            },
        ],
        [],
    );
    return (
        <DataTable
            rows={tickets}
            columns={columns}
            rowId={(t) => t.id}
            selected={selected}
            chips={chips}
            chipParam={chipParam}
            initialSort={{ id: "created", desc: true }}
            searchPlaceholder="Filter by email, exam, words…"
            mobile={(t) => (
                <span className="flex items-start gap-3">
                    <span className="flex min-w-0 flex-1 flex-col">
                        <strong className="truncate font-semibold first-letter:uppercase">
                            {t.kind}
                            {t.exam ? ` · ${t.exam}` : ""}
                        </strong>
                        <span className="line-clamp-2 text-xs text-[var(--op-muted)]">{t.message || t.email}</span>
                        <span className="text-xs text-[var(--op-faint)]">{when(t.created_at)}</span>
                    </span>
                    <StateBadge state={t.status} />
                </span>
            )}
        />
    );
}
