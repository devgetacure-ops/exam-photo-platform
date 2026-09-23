import Link from "next/link";
import { Failure } from "../../../../components/operator/ui";
import { rupees, when, type Customer } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

const SOURCE_LABEL: Record<string, string> = {
    payment: "paid",
    delivery: "file emailed",
    checkout_failed: "payment failed",
    "form:exam": "asked for an exam",
    "form:question": "question",
    "form:complaint": "complaint",
    "form:grievance": "grievance",
    "form:support": "support",
};

export default async function CustomersPage({ searchParams }: { searchParams: Promise<{ q?: string; paid?: string }> }) {
    await requireOperator();
    const { q = "", paid = "" } = await searchParams;
    const loaded = await engineJson<{ customers: Customer[] }>(`/v1/operator/customers?q=${encodeURIComponent(q)}`);
    if (!loaded.ok) return <Failure what="customers" error={loaded.error} />;
    const all = loaded.value.customers;
    const shown = paid === "yes" ? all.filter((c) => (c.paid_orders ?? 0) > 0) : paid === "no" ? all.filter((c) => !c.paid_orders) : all;

    return (
        <>
            <h1>Customers</h1>
            <p className="euk-op-quiet">
                Every address a candidate gave: at payment, for delivery, or on a form. <Link href="/admin/export/customers" prefetch={false} download>Download as CSV</Link>.
            </p>
            <form method="get" className="euk-op-search">
                <input name="q" type="search" defaultValue={q} placeholder="Email or phone" aria-label="Filter customers" />
                <button type="submit" className="euk-op-button">
                    Filter
                </button>
            </form>
            <p className="euk-op-filter">
                <Link href={`/admin/customers${q ? `?q=${encodeURIComponent(q)}` : ""}`} aria-current={!paid}>
                    All ({all.length})
                </Link>
                <Link href={`/admin/customers?paid=yes${q ? `&q=${encodeURIComponent(q)}` : ""}`} aria-current={paid === "yes"}>
                    Paid
                </Link>
                <Link href={`/admin/customers?paid=no${q ? `&q=${encodeURIComponent(q)}` : ""}`} aria-current={paid === "no"}>
                    Never paid
                </Link>
            </p>
            {shown.length === 0 && <p className="euk-op-quiet">None yet. Addresses are collected from the day this release went live.</p>}
            <ul className="euk-op-list">
                {shown.map((customer) => (
                    <li key={customer.email} className="euk-op-card">
                        <Link href={`/admin/customers/${encodeURIComponent(customer.email)}`} className="euk-op-cardlink">
                            <p className="euk-op-row">
                                <strong>{customer.email}</strong>
                                <span>{rupees(customer.spent_paise ?? 0)}</span>
                            </p>
                            <p className="euk-op-quiet">
                                {customer.phone ? `${customer.phone} · ` : ""}
                                {customer.paid_orders ?? 0} paid order{customer.paid_orders === 1 ? "" : "s"} ·{" "}
                                {customer.sources.map((source) => SOURCE_LABEL[source] ?? source).join(", ")} · last seen {when(customer.last_seen)}
                            </p>
                        </Link>
                    </li>
                ))}
            </ul>
        </>
    );
}
