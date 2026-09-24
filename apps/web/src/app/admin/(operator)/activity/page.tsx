import type { Metadata } from "next";
import Link from "next/link";
import { when } from "../../../../lib/operator/format";
import { Card, Empty, PageHeader, Problem } from "../../../../components/console/ui";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

export const metadata: Metadata = { title: "Activity" };

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
    const map: Record<string, string> = { order: "orders", ticket: "inbox", upload: "uploads", customer: "customers" };
    return map[kind] ? `/admin/${map[kind]}?open=${encodeURIComponent(id)}` : null;
}

export default async function ActivityPage() {
    await requireOperator();
    const loaded = await engineJson<{ activity: Entry[] }>("/v1/operator/activity");
    if (!loaded.ok) return <Problem what="activity" error={loaded.error} />;
    const entries = loaded.value.activity;
    return (
        <>
            <PageHeader title="Activity" description="Every change made here, and every time an upload or a customer was opened. Newest first." />
            <Card>
                {entries.length === 0 ? (
                    <Empty title="Nothing yet" />
                ) : (
                    <ul className="m-0 list-none divide-y divide-[var(--op-border)] p-0">
                        {entries.map((entry, index) => {
                            const link = entry.target ? href(entry.target) : null;
                            return (
                                <li key={index} className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5 px-5 py-3 text-sm">
                                    <span className="op-num w-32 shrink-0 text-xs text-[var(--op-muted)]">{when(entry.at)}</span>
                                    <span className="font-medium first-letter:uppercase">{entry.action}</span>
                                    {entry.target &&
                                        (link ? (
                                            <Link href={link} className="truncate text-[var(--op-muted)] underline">
                                                {entry.target}
                                            </Link>
                                        ) : (
                                            <span className="truncate text-[var(--op-muted)]">{entry.target}</span>
                                        ))}
                                    <span className="ml-auto text-xs text-[var(--op-faint)]">{entry.actor}</span>
                                </li>
                            );
                        })}
                    </ul>
                )}
            </Card>
        </>
    );
}
