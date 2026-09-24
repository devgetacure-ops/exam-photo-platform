import { Download } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { NotesSection } from "../../../../components/console/notes";
import { ReplyMenu } from "../../../../components/console/reply-menu";
import { Sheet, SheetSection, Timeline } from "../../../../components/console/sheet";
import { OrdersTable } from "../../../../components/console/tables";
import { when } from "../../../../lib/operator/format";
import { ActionForm, Button, Facts, Input, PageHeader, Problem, StateBadge, buttonStyles } from "../../../../components/console/ui";
import { rupees, type OrderDetail, type OrderView } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

export const metadata: Metadata = { title: "Orders" };

const CHIPS: [string, string, "bad" | "warn" | undefined][] = [
    ["", "All", undefined],
    ["refund-due", "Refund due", "bad"],
    ["delivered", "Delivered", undefined],
    ["payment-failed", "Payment failed", "warn"],
    ["unpaid", "Not paid", undefined],
    ["free", "Free · code", undefined],
    ["refunded", "Refunded", undefined],
];

function stateOf(order: OrderView) {
    return order.amount_paise === 0 && order.paid_at && order.coupon_code ? "free" : order.state;
}

export default async function OrdersPage({ searchParams }: { searchParams: Promise<{ state?: string; open?: string }> }) {
    await requireOperator();
    const { state = "", open } = await searchParams;
    const loaded = await engineJson<{ orders: OrderView[] }>("/v1/operator/orders");
    if (!loaded.ok) return <Problem what="orders" error={loaded.error} />;
    const all = loaded.value.orders;
    const shown = state ? all.filter((order) => stateOf(order) === state) : all;
    const chips = CHIPS.map(([value, label, tone]) => ({ value, label, tone, count: value ? all.filter((o) => stateOf(o) === value).length : all.length }));
    const detail = open && /^order_[A-Za-z0-9_-]{1,64}$/.test(open) ? await engineJson<OrderDetail>(`/v1/operator/orders/${open}`) : null;

    return (
        <>
            <PageHeader
                title="Orders"
                description="Every checkout, paid or not. Select one to see everything about it."
                actions={
                    <a href="/admin/export/orders" download className={buttonStyles({ variant: "secondary" })}>
                        <Download size={15} aria-hidden="true" />
                        Export CSV
                    </a>
                }
            />
            <OrdersTable orders={shown} chips={chips} selected={open} />
            {detail?.ok && <OrderSheet order={detail.value} back={`/admin/orders?${new URLSearchParams({ ...(state ? { state } : {}), open: detail.value.order_id })}`} />}
            {detail && !detail.ok && <Problem what="that order" error={detail.error} />}
        </>
    );
}

function OrderSheet({ order, back }: { order: OrderDetail; back: string }) {
    const email = order.emails[0];
    const state = stateOf(order);
    const refundForm = (
        <ActionForm action={`/admin/actions/refund/${order.order_id}`} back={back} className="flex basis-full gap-2 sm:basis-auto sm:flex-1">
            {order.refund ? (
                <>
                    <input type="hidden" name="undo" value="true" />
                    <Button type="submit" size="lg" className="flex-1">
                        Undo refund mark
                    </Button>
                </>
            ) : (
                <>
                    <Input name="reference" maxLength={80} placeholder="Razorpay refund id (rfnd_…)" aria-label="Razorpay refund reference" className="h-11 min-w-0 flex-1" />
                    <Button type="submit" variant="primary" size="lg" disabled={!order.paid_at || order.amount_paise === 0}>
                        Mark refunded
                    </Button>
                </>
            )}
        </ActionForm>
    );
    const events = order.timeline.map((event) => ({
        at: when(event.at),
        what: event.what,
        tone: /FAILED|failed/.test(event.what) ? ("bad" as const) : /^Paid|^Email|^Download/.test(event.what) ? ("good" as const) : undefined,
    }));

    return (
        <Sheet
            title={`${order.exam_names.join(", ") || "Order"} · ${rupees(order.amount_paise)}`}
            subtitle={order.order_id}
            badge={<StateBadge state={state} />}
            actions={
                <>
                    {email && <ReplyMenu email={email} context={{ exam: order.exam_names[0], paymentReference: order.payment_reference, amountPaise: order.amount_paise, refundReference: order.refund?.reference }} />}
                    {order.paid_at && order.amount_paise > 0 && refundForm}
                </>
            }
        >
            {state === "refund-due" && (
                <p className="m-0 rounded-lg bg-[var(--op-bad-bg)] px-3 py-2.5 text-sm text-[var(--op-bad)]">
                    Paid and nothing has reached the customer. Refund it in Razorpay, then record the refund id below.
                </p>
            )}
            <Facts
                rows={[
                    ["Customer", email ? <Link href={`/admin/customers?open=${encodeURIComponent(email)}`} className="underline">{email}</Link> : "Not known"],
                    ["Other emails", order.emails.slice(1).join(", ") || null],
                    ["Phone", order.payer_contact ? <a href={`tel:${order.payer_contact}`} className="underline">{order.payer_contact}</a> : null],
                    ["Ordered", when(order.created_at)],
                    ["Paid", order.paid_at ? `${when(order.paid_at)} · ${order.payment_method ?? "—"}` : "No"],
                    ["Payment id", order.payment_reference],
                    ["Code used", order.coupon_code ? `${order.coupon_code} (−${rupees(order.discount_paise ?? 0)})` : null],
                    ["First delivered", order.delivered_at ? `${when(order.delivered_at)} by ${order.delivery_method}` : "Nothing yet"],
                    ["Refund", order.refund ? `${when(order.refund.at)} · ${order.refund.reference ?? "no id"} · by ${order.refund.actor}` : null],
                    ["Session", <code key="kit" className="text-xs">{order.kit_id}</code>],
                ]}
            />
            <SheetSection title={`Files (${order.uploads.length})`}>
                {order.uploads.map((upload) => (
                    <Link
                        key={upload.job_id}
                        href={`/admin/uploads?open=${upload.job_id}`}
                        className="flex items-center gap-3 rounded-lg border border-[var(--op-border)] p-2.5 hover:bg-[var(--op-hover)]"
                    >
                        {upload.live ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={`/admin/files/${upload.job_id}/input.jpg`} alt="" className="h-14 w-11 shrink-0 rounded object-cover" />
                        ) : (
                            <span className="flex h-14 w-11 shrink-0 items-center justify-center rounded border border-dashed border-[var(--op-border-strong)] text-[10px] text-[var(--op-faint)]">erased</span>
                        )}
                        <span className="flex min-w-0 flex-1 flex-col text-sm">
                            <strong className="font-medium">{upload.requirement_name ?? upload.job_id}</strong>
                            <span className="text-xs text-[var(--op-muted)]">
                                {upload.processing_seconds != null ? `Prepared in ${upload.processing_seconds.toFixed(1)} s` : "Not in the history"}
                                {upload.output_width ? ` · ${upload.output_width}×${upload.output_height}` : ""}
                            </span>
                        </span>
                        <span className="text-xs text-[var(--op-muted)]">{upload.live ? "photo held" : ""}</span>
                    </Link>
                ))}
            </SheetSection>
            {order.tickets.length > 0 && (
                <SheetSection title="Messages from this customer">
                    {order.tickets.map((ticket) => (
                        <Link key={ticket.id} href={`/admin/inbox?open=${ticket.id}`} className="flex items-center gap-3 rounded-lg border border-[var(--op-border)] p-3 text-sm hover:bg-[var(--op-hover)]">
                            <span className="min-w-0 flex-1">
                                <strong className="font-medium first-letter:uppercase">{ticket.kind}</strong>
                                <span className="block truncate text-xs text-[var(--op-muted)]">{ticket.message}</span>
                            </span>
                            <StateBadge state={ticket.status} />
                        </Link>
                    ))}
                </SheetSection>
            )}
            <SheetSection title="Timeline">
                <Timeline events={events} />
            </SheetSection>
            <NotesSection target={`order:${order.order_id}`} back={back} notes={order.notes} />
        </Sheet>
    );
}
