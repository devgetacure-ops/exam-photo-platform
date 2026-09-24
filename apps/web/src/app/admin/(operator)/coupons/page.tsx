import Link from "next/link";
import { ActionForm, Failure } from "../../../../components/operator/ui";
import { rupees, when } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

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

function describe(coupon: Coupon): string {
    if (coupon.kind === "free") return "Free files";
    if (coupon.kind === "percent") return `${coupon.value}% off`;
    return `${rupees(coupon.value)} off`;
}

export default async function CouponsPage({ searchParams }: { searchParams: Promise<{ show?: string }> }) {
    await requireOperator();
    const show = (await searchParams).show === "rewards" ? "rewards" : "yours";
    const [coupons, reviews] = await Promise.all([
        engineJson<{ coupons: Coupon[] }>("/v1/operator/coupons"),
        engineJson<{ offer_on: boolean }>("/v1/operator/reviews?status=pending"),
    ]);
    if (!coupons.ok) return <Failure what="coupons" error={coupons.error} />;
    const offerOn = reviews.ok && reviews.value.offer_on;
    const mine = coupons.value.coupons.filter((c) => c.source !== "reward");
    const rewards = coupons.value.coupons.filter((c) => c.source === "reward");
    const rewardsUsed = rewards.filter((c) => c.uses > 0).length;

    return (
        <>
            <h1>Coupons</h1>

            <section className="euk-op-section">
                <h2>Review reward offer</h2>
                <p>
                    <strong>{offerOn ? "Running." : "Off."}</strong> While it runs, every paying customer who reviews their order gets
                    a code that makes their next examination&rsquo;s files free. One code per person, used once; free orders do not earn
                    one.
                </p>
                <p className="euk-op-quiet">
                    {rewards.length} codes given, {rewardsUsed} used.
                </p>
                <ActionForm action="/admin/actions/offer" back="/admin/coupons">
                    <input type="hidden" name="on" value={offerOn ? "false" : "true"} />
                    <button type="submit" className="euk-op-button">
                        {offerOn ? "Stop the offer" : "Start the offer"}
                    </button>
                </ActionForm>
                <p className="euk-op-quiet">Stopping it gives no new codes; codes already given still work once.</p>
            </section>

            <section className="euk-op-section">
                <h2>New code</h2>
                <ActionForm action="/admin/actions/coupon" back="/admin/coupons">
                    <label>
                        <span className="euk-label">Code</span>
                        <input name="code" required pattern="[A-Za-z0-9_-]{2,32}" placeholder="COACHING10" />
                    </label>
                    <label>
                        <span className="euk-label">What it does</span>
                        <select name="kind" defaultValue="percent">
                            <option value="percent">Percent off (1–90)</option>
                            <option value="flat">Rupees off</option>
                            <option value="free">Makes the files free</option>
                        </select>
                    </label>
                    <label>
                        <span className="euk-label">Amount (ignored for free)</span>
                        <input name="value" type="number" min={0} max={1000} defaultValue={10} />
                    </label>
                    <label>
                        <span className="euk-label">Who it is for</span>
                        <input name="partner" maxLength={120} placeholder="A coaching centre, a friend, a campaign" />
                    </label>
                    <label>
                        <span className="euk-label">Most uses (optional; 1 for a one-off)</span>
                        <input name="max_uses" type="number" min={1} />
                    </label>
                    <label>
                        <span className="euk-label">Last day (optional)</span>
                        <input name="expires_on" type="date" />
                    </label>
                    <p className="euk-op-quiet">
                        Percent and rupee codes never take a total below ₹1, Razorpay&rsquo;s smallest charge. A free code skips payment
                        altogether.
                    </p>
                    <button type="submit" className="euk-op-button">
                        Save code
                    </button>
                </ActionForm>
            </section>

            <section className="euk-op-section">
                <p className="euk-op-filter">
                    <Link href="/admin/coupons" aria-current={show === "yours"}>
                        Your codes ({mine.length})
                    </Link>
                    <Link href="/admin/coupons?show=rewards" aria-current={show === "rewards"}>
                        Review rewards ({rewards.length})
                    </Link>
                </p>
                {(show === "rewards" ? rewards : mine).length === 0 && <p className="euk-op-quiet">None yet.</p>}
                <ul className="euk-op-list">
                    {(show === "rewards" ? rewards : mine).map((coupon) => (
                        <li key={coupon.code} className="euk-op-card" data-state={coupon.active ? undefined : "unpaid"}>
                            <p className="euk-op-row">
                                <strong>{coupon.code}</strong>
                                <span>{describe(coupon)}</span>
                            </p>
                            <p className="euk-op-quiet">
                                {coupon.partner || "—"} · used {coupon.uses}
                                {coupon.max_uses != null ? ` of ${coupon.max_uses}` : ""} · {coupon.orders} paid orders ·{" "}
                                {rupees(coupon.revenue_paise)} revenue · {rupees(coupon.discount_paise)} given away
                                {coupon.expires_on ? ` · until ${coupon.expires_on}` : ""} · made {when(coupon.created_at)}
                                {coupon.issued_for_order ? " · for " : ""}
                                {coupon.issued_for_order && <Link href={`/admin/orders/${coupon.issued_for_order}`}>{coupon.issued_for_order}</Link>}
                            </p>
                            <ActionForm action={`/admin/actions/coupon-active/${coupon.code}`} back={show === "rewards" ? "/admin/coupons?show=rewards" : "/admin/coupons"}>
                                <input type="hidden" name="active" value={coupon.active ? "false" : "true"} />
                                <button type="submit" className="euk-op-button">
                                    {coupon.active ? "Switch off" : "Switch on"}
                                </button>
                            </ActionForm>
                        </li>
                    ))}
                </ul>
            </section>
        </>
    );
}
