import type { Metadata } from "next";
import Link from "next/link";
import { when } from "../../../../lib/operator/format";
import { ActionForm, Badge, Button, Card, CardHeader, Empty, Field, Input, PageHeader, Problem, Select, cn } from "../../../../components/console/ui";
import { rupees } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

export const metadata: Metadata = { title: "Coupons" };

interface Coupon {
    code: string;
    kind: string;
    value: number;
    partner: string | null;
    active: number;
    max_uses: number | null;
    uses: number;
    expires_on: string | null;
    created_at: string;
    source: string;
    issued_for_order: string | null;
    orders: number;
    revenue_paise: number;
    discount_paise: number;
}

function describe(coupon: Coupon) {
    if (coupon.kind === "free") return "Files free";
    if (coupon.kind === "percent") return `${coupon.value}% off`;
    return `${rupees(coupon.value)} off`;
}

export default async function CouponsPage({ searchParams }: { searchParams: Promise<{ show?: string }> }) {
    await requireOperator();
    const show = (await searchParams).show === "rewards" ? "rewards" : "yours";
    const [coupons, reviews] = await Promise.all([engineJson<{ coupons: Coupon[] }>("/v1/operator/coupons"), engineJson<{ offer_on: boolean }>("/v1/operator/reviews?status=pending")]);
    if (!coupons.ok) return <Problem what="coupons" error={coupons.error} />;
    const offerOn = reviews.ok && reviews.value.offer_on;
    const mine = coupons.value.coupons.filter((c) => c.source !== "reward");
    const rewards = coupons.value.coupons.filter((c) => c.source === "reward");
    const list = show === "rewards" ? rewards : mine;
    const back = show === "rewards" ? "/admin/coupons?show=rewards" : "/admin/coupons";

    return (
        <>
            <PageHeader title="Coupons" description="Your own codes for partners and friends, and the free-files reward for reviews." />

            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_380px]">
                <div className="flex flex-col gap-4">
                    <Card className={cn("flex flex-wrap items-center gap-4 p-5", offerOn && "border-[var(--op-good)]")}>
                        <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                                <h2 className="m-0 text-[15px] font-semibold">Review reward offer</h2>
                                <Badge tone={offerOn ? "good" : "neutral"}>{offerOn ? "Running" : "Off"}</Badge>
                            </div>
                            <p className="m-0 mt-1 text-[13px] text-[var(--op-muted)]">
                                Each paying customer who reviews gets one code that makes their next examination free. One per person, used once.{" "}
                                {rewards.length} given, {rewards.filter((c) => c.uses > 0).length} used.
                            </p>
                        </div>
                        <ActionForm action="/admin/actions/offer" back={back}>
                            <input type="hidden" name="on" value={offerOn ? "false" : "true"} />
                            <Button type="submit" variant={offerOn ? "secondary" : "primary"} size="lg">
                                {offerOn ? "Stop the offer" : "Start the offer"}
                            </Button>
                        </ActionForm>
                    </Card>

                    <div className="flex self-start rounded-lg bg-[var(--op-muted-bg)] p-0.5">
                        {(
                            [
                                ["yours", `Your codes ${mine.length}`, "/admin/coupons"],
                                ["rewards", `Review rewards ${rewards.length}`, "/admin/coupons?show=rewards"],
                            ] as const
                        ).map(([value, label, href]) => (
                            <Link
                                key={value}
                                href={href}
                                aria-current={show === value ? "page" : undefined}
                                className={cn("rounded-md px-3 py-1.5 text-[13px]", show === value ? "bg-[var(--op-card)] font-semibold shadow-[var(--op-shadow)]" : "text-[var(--op-muted)]")}
                            >
                                {label}
                            </Link>
                        ))}
                    </div>

                    <Card>
                        {list.length === 0 ? (
                            <Empty title={show === "rewards" ? "No review rewards yet" : "No codes yet"}>{show === "rewards" ? "They are created when a customer reviews while the offer runs." : "Make one with the form."}</Empty>
                        ) : (
                            <div className="op-scroll overflow-x-auto">
                                <table className="w-full min-w-[640px] border-collapse text-sm">
                                    <thead>
                                        <tr className="border-b border-[var(--op-border)] bg-[var(--op-muted-bg)] text-left text-xs text-[var(--op-muted)]">
                                            <th scope="col" className="px-5 py-2.5 font-medium">Code</th>
                                            <th scope="col" className="px-3 py-2.5 font-medium">Gives</th>
                                            <th scope="col" className="px-3 py-2.5 text-right font-medium">Used</th>
                                            <th scope="col" className="px-3 py-2.5 text-right font-medium">Revenue</th>
                                            <th scope="col" className="px-5 py-2.5 text-right font-medium">On</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {list.map((coupon) => (
                                            <tr key={coupon.code} className={cn("border-b border-[var(--op-border)] last:border-0", !coupon.active && "opacity-60")}>
                                                <td className="px-5 py-3">
                                                    <div className="font-mono font-semibold">{coupon.code}</div>
                                                    <div className="text-xs text-[var(--op-muted)]">
                                                        {coupon.issued_for_order ? (
                                                            <Link href={`/admin/orders?open=${coupon.issued_for_order}`} className="underline">
                                                                for a review
                                                            </Link>
                                                        ) : (
                                                            coupon.partner || "—"
                                                        )}
                                                        {coupon.expires_on ? ` · until ${coupon.expires_on}` : ""} · {when(coupon.created_at)}
                                                    </div>
                                                </td>
                                                <td className="px-3 py-3">{describe(coupon)}</td>
                                                <td className="op-num px-3 py-3 text-right">
                                                    {coupon.uses}
                                                    {coupon.max_uses != null ? ` / ${coupon.max_uses}` : ""}
                                                </td>
                                                <td className="op-num px-3 py-3 text-right">{rupees(coupon.revenue_paise)}</td>
                                                <td className="px-5 py-3 text-right">
                                                    <ActionForm action={`/admin/actions/coupon-active/${coupon.code}`} back={back}>
                                                        <input type="hidden" name="active" value={coupon.active ? "false" : "true"} />
                                                        <button
                                                            type="submit"
                                                            role="switch"
                                                            aria-checked={Boolean(coupon.active)}
                                                            aria-label={`${coupon.code} ${coupon.active ? "on" : "off"}`}
                                                            className={cn("relative h-6 w-11 cursor-pointer rounded-full transition-colors", coupon.active ? "bg-[var(--op-good)]" : "bg-[var(--op-border-strong)]")}
                                                        >
                                                            <span className={cn("absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all", coupon.active ? "left-[22px]" : "left-0.5")} />
                                                        </button>
                                                    </ActionForm>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </Card>
                </div>

                <Card className="h-fit">
                    <CardHeader title="New code" description="Candidates type it under “Have a code?” before paying." />
                    <ActionForm action="/admin/actions/coupon" back="/admin/coupons" className="flex flex-col gap-4 p-5">
                        <Field label="Code" hint="Letters, digits, - or _. Shown in capitals.">
                            <Input name="code" required pattern="[A-Za-z0-9_-]{2,32}" placeholder="COACHING10" className="font-mono uppercase" />
                        </Field>
                        <div className="grid grid-cols-2 gap-3">
                            <Field label="Gives">
                                <Select name="kind" defaultValue="percent">
                                    <option value="percent">% off</option>
                                    <option value="flat">₹ off</option>
                                    <option value="free">Files free</option>
                                </Select>
                            </Field>
                            <Field label="Amount" hint="Ignored for free">
                                <Input name="value" type="number" min={0} max={1000} defaultValue={10} />
                            </Field>
                        </div>
                        <Field label="Who it is for">
                            <Input name="partner" maxLength={120} placeholder="A coaching centre, a friend…" />
                        </Field>
                        <div className="grid grid-cols-2 gap-3">
                            <Field label="Most uses" hint="Blank = unlimited">
                                <Input name="max_uses" type="number" min={1} />
                            </Field>
                            <Field label="Last day" hint="Optional">
                                <Input name="expires_on" type="date" />
                            </Field>
                        </div>
                        <p className="m-0 text-xs text-[var(--op-muted)]">% and ₹ codes never take a total below ₹1, Razorpay&rsquo;s smallest charge. A free code skips payment.</p>
                        <Button type="submit" variant="primary" size="lg">
                            Save code
                        </Button>
                    </ActionForm>
                </Card>
            </div>
        </>
    );
}
