import Link from "next/link";
import { Badge, Failure } from "../../../../components/operator/ui";
import { when, type Ticket } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

const VIEWS: [string, string][] = [
    ["", "Complaints and questions"],
    ["complaint,grievance", "Complaints and grievances"],
    ["exam", "Exam requests"],
];

export default async function InboxPage({ searchParams }: { searchParams: Promise<{ kind?: string; status?: string }> }) {
    await requireOperator();
    const { kind = "", status = "" } = await searchParams;
    const kinds = kind || "question,complaint,grievance,support";
    const loaded = await engineJson<{ tickets: Ticket[] }>(
        `/v1/operator/tickets?kind=${encodeURIComponent(kinds)}&status=${encodeURIComponent(status)}`,
    );
    if (!loaded.ok) return <Failure what="the inbox" error={loaded.error} />;
    const tickets = loaded.value.tickets;
    const link = (next: Record<string, string>) => `/admin/inbox?${new URLSearchParams({ ...(kind ? { kind } : {}), ...(status ? { status } : {}), ...next })}`;

    return (
        <>
            <h1>Inbox</h1>
            <p className="euk-op-filter">
                {VIEWS.map(([value, label]) => (
                    <Link key={value} href={link({ kind: value })} aria-current={kind === value}>
                        {label}
                    </Link>
                ))}
            </p>
            <p className="euk-op-filter">
                {["", "open", "answered", "resolved"].map((value) => (
                    <Link key={value} href={link({ status: value })} aria-current={status === value}>
                        {value ? <Badge state={value} /> : "Any status"}
                    </Link>
                ))}
            </p>
            {kind === "exam" ? <Demand tickets={tickets} /> : <List tickets={tickets} />}
        </>
    );
}

function List({ tickets }: { tickets: Ticket[] }) {
    if (tickets.length === 0) return <p className="euk-op-quiet">Nothing here.</p>;
    return (
        <ul className="euk-op-list">
            {tickets.map((ticket) => (
                <li key={ticket.id} className="euk-op-card" data-state={ticket.ack_overdue || ticket.resolve_overdue ? "refund-due" : undefined}>
                    <Link href={`/admin/inbox/${ticket.id}`} className="euk-op-cardlink">
                        <p className="euk-op-row">
                            <strong>
                                {ticket.kind}
                                {ticket.exam ? ` · ${ticket.exam}` : ""}
                            </strong>
                            <Badge state={ticket.status} />
                        </p>
                        <p className="euk-op-message">{(ticket.message ?? "").slice(0, 200)}</p>
                        <p className="euk-op-quiet">
                            {ticket.email} · {when(ticket.created_at)}
                            {ticket.order_id ? ` · linked to ${ticket.order_id}` : ""}
                            {ticket.ack_overdue ? " · unanswered after 48 hours" : ticket.resolve_overdue ? " · unresolved after a month" : ""}
                        </p>
                    </Link>
                </li>
            ))}
        </ul>
    );
}

/** Exam requests grouped by what was asked for, most wanted first. */
function Demand({ tickets }: { tickets: Ticket[] }) {
    const groups = new Map<string, Ticket[]>();
    for (const ticket of tickets) {
        const key = (ticket.exam ?? "").trim().toLowerCase() || "(no name)";
        groups.set(key, [...(groups.get(key) ?? []), ticket]);
    }
    const ranked = [...groups.values()].sort((a, b) => b.length - a.length);
    if (ranked.length === 0) return <p className="euk-op-quiet">No exam requests yet.</p>;
    return (
        <ul className="euk-op-list">
            {ranked.map((group) => {
                const waiting = group.filter((ticket) => !ticket.added_at).length;
                return (
                    <li key={group[0].id} className="euk-op-card">
                        <p className="euk-op-row">
                            <strong>{group[0].exam || "(no name)"}</strong>
                            <span>
                                {group.length} asked{waiting < group.length ? ` · ${group.length - waiting} told it is added` : ""}
                            </span>
                        </p>
                        <ul className="euk-op-plain">
                            {group.map((ticket) => (
                                <li key={ticket.id}>
                                    <Link href={`/admin/inbox/${ticket.id}`}>{ticket.email}</Link> · {when(ticket.created_at)}
                                    {ticket.added_at ? " · added" : ""}
                                </li>
                            ))}
                        </ul>
                    </li>
                );
            })}
        </ul>
    );
}
