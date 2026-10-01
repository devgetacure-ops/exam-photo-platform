import type { Metadata } from "next";
import Link from "next/link";
import { when } from "../../../../lib/operator/format";
import { ActionForm, Badge, Button, Card, CardHeader, Empty, Field, Input, PageHeader, Problem, Select, cn } from "../../../../components/console/ui";
import { rupees } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";
import { couponTimeline, refusalWords, statusOf, STATUS_WORDS, type CouponRecord } from "../../../../lib/operator/coupon-timeline";

export const metadata: Metadata = { title: "Coupons" };

type Coupon = CouponRecord;

function describe(coupon: Coupon) {
    if (coupon.kind === "free") return "Files free";
    if (coupon.kind === "percent") return `${coupon.value}% off`;
    return `${rupees(coupon.value)} off`;
}

export default async function CouponsPage({ searchParams }: { searchParams: Promise<{ show?: string }> }) {
    await requireOperator();
    // Every code is on the page when it opens (DEC-120). The page used to open
    // on "Your codes", so a review reward sat behind a tab and the section
    // read as empty.
    const asked = (await searchParams).show;
    const show = asked === "rewards" || asked === "yours" ? asked : "all";
    const [coupons, reviews] = await Promise.all([
        engineJson<{ coupons: Coupon[]; unknown_attempts?: { code: string; kit_id: string; reason: string; at: string }[] }>("/v1/operator/coupons"),
        engineJson<{ offer_on: boolean }>("/v1/operator/reviews?status=pending"),
    ]);
    if (!coupons.ok) return <Problem what="coupons" error={coupons.error} />;
    const offerOn = reviews.ok && reviews.value.offer_on;
    const today = new Date().toISOString().slice(0, 10);
    const everything = [...coupons.value.coupons].sort((a, b) => b.created_at.localeCompare(a.created_at));
    const mine = everything.filter((c) => c.source !== "reward");
    const rewards = everything.filter((c) => c.source === "reward");
    const list = show === "rewards" ? rewards : show === "yours" ? mine : everything;
    const back = show === "all" ? "/admin/coupons" : `/admin/coupons?show=${show}`;
    const strays = coupons.value.unknown_attempts ?? [];

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
                                ["all", `All ${everything.length}`, "/admin/coupons"],
                                ["yours", `Your codes ${mine.length}`, "/admin/coupons?show=yours"],
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

                    {list.length === 0 ? (
                        <Card>
                            <Empty title={show === "rewards" ? "No review rewards yet" : show === "yours" ? "No codes of your own yet" : "No codes yet"}>
                                {show === "rewards" ? "They are created when a customer reviews while the offer runs." : "Make one with the form."}
                            </Empty>
                        </Card>
                    ) : (
                        list.map((coupon) => {
                            const status = STATUS_WORDS[statusOf(coupon, today)];
                            const events = couponTimeline(coupon, today);
                            return (
                                <Card key={coupon.code} className={cn(!coupon.active && "opacity-80")}>
                                    <div className="flex flex-wrap items-start gap-x-4 gap-y-3 p-5">
                                        <div className="min-w-0 flex-1">
                                            <div className="flex flex-wrap items-center gap-2">
                                                <span className="font-mono text-[15px] font-semibold">{coupon.code}</span>
                                                <Badge tone={status.tone}>{status.label}</Badge>
                                                <Badge tone="neutral">{coupon.source === "reward" ? "Review reward" : "Your code"}</Badge>
                                            </div>
                                            <p className="m-0 mt-1 text-[13px] text-[var(--op-muted)]">
                                                {describe(coupon)} · used {coupon.uses}
                                                {coupon.max_uses != null ? ` of ${coupon.max_uses}` : " times, no limit"}
                                                {coupon.expires_on ? ` · last day ${coupon.expires_on}` : " · no last day"}
                                                {coupon.orders > 0 ? ` · ${rupees(coupon.discount_paise)} given away, ${rupees(coupon.revenue_paise)} taken` : ""}
                                            </p>
                                        </div>
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
                                    </div>
                                    <ol className="m-0 list-none border-t border-[var(--op-border)] px-5 py-3 text-[13px]" aria-label={`${coupon.code} history`}>
                                        {events.map((event, index) => (
                                            <li key={`${event.at}-${index}`} className="flex gap-3 py-1.5">
                                                <span
                                                    aria-hidden="true"
                                                    className={cn(
                                                        "mt-1.5 h-2 w-2 flex-none rounded-full",
                                                        event.kind === "used" ? "bg-[var(--op-good)]" : event.kind === "refused" || event.kind === "ended" ? "bg-[var(--op-bad)]" : "bg-[var(--op-border-strong)]",
                                                    )}
                                                />
                                                <span className="min-w-0 flex-1">
                                                    {event.text}
                                                    {event.orderId ? (
                                                        <>
                                                            {" · "}
                                                            <Link href={`/admin/orders?open=${event.orderId}`} className="underline">
                                                                {event.orderId}
                                                            </Link>
                                                        </>
                                                    ) : null}
                                                </span>
                                                <span className="op-num flex-none text-[var(--op-muted)]">{event.kind === "ended" && event.at.endsWith("23:59:59") ? "" : when(event.at)}</span>
                                            </li>
                                        ))}
                                    </ol>
                                </Card>
                            );
                        })
                    )}

                    {strays.length > 0 && (
                        <Card>
                            <CardHeader title="Codes tried that do not exist" description="What candidates typed under “Have a code?” that matched nothing. A code here many times may be one you announced and never made." />
                            <ol className="m-0 list-none px-5 py-3 text-[13px]">
                                {strays.map((attempt, index) => (
                                    <li key={`${attempt.code}-${attempt.at}-${index}`} className="flex gap-3 py-1.5">
                                        <span className="min-w-0 flex-1">
                                            <span className="font-mono font-semibold">{attempt.code}</span> · {refusalWords(attempt.reason)}
                                        </span>
                                        <span className="op-num flex-none text-[var(--op-muted)]">{when(attempt.at)}</span>
                                    </li>
                                ))}
                            </ol>
                        </Card>
                    )}
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
