import Link from "next/link";
import { Failure } from "../../../../components/operator/ui";
import { when } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

interface Entry {
    at: string;
    actor: string;
    action: string;
    target?: string | null;
}

function href(target: string): string | null {
    const cut = target.indexOf(":");
    const kind = target.slice(0, cut);
    const id = target.slice(cut + 1);
    if (kind === "order") return `/admin/orders/${id}`;
    if (kind === "ticket") return `/admin/inbox/${id}`;
    if (kind === "upload") return `/admin/uploads/${id}`;
    if (kind === "customer") return `/admin/customers/${encodeURIComponent(id)}`;
    return null;
}

export default async function ActivityPage() {
    await requireOperator();
    const loaded = await engineJson<{ activity: Entry[] }>("/v1/operator/activity");
    if (!loaded.ok) return <Failure what="activity" error={loaded.error} />;
    return (
        <>
            <h1>Activity</h1>
            <p className="euk-op-quiet">Who opened an upload or a customer, and every change made on this page. Newest first.</p>
            {loaded.value.activity.length === 0 && <p className="euk-op-quiet">Nothing yet.</p>}
            <ul className="euk-op-plain">
                {loaded.value.activity.map((entry, index) => {
                    const link = entry.target ? href(entry.target) : null;
                    return (
                        <li key={index}>
                            <span className="euk-op-quiet">{when(entry.at)}</span> · {entry.actor} · {entry.action}
                            {entry.target ? " · " : ""}
                            {entry.target && (link ? <Link href={link}>{entry.target}</Link> : entry.target)}
                        </li>
                    );
                })}
            </ul>
        </>
    );
}
