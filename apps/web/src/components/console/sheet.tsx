"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { ReactNode } from "react";
import { useConsoleRoot } from "./portal";

/**
 * The side panel a row opens (DEC-113). Its open state lives in the address
 * (`?open=…`), so a panel can be linked, reloaded and closed with Back. On a
 * laptop it slides over the right of the list; on a phone it fills the screen.
 */
export function Sheet({
    title,
    subtitle,
    badge,
    actions,
    children,
}: {
    title: ReactNode;
    subtitle?: ReactNode;
    badge?: ReactNode;
    actions?: ReactNode;
    children: ReactNode;
}) {
    const router = useRouter();
    const pathname = usePathname();
    const params = useSearchParams();
    const container = useConsoleRoot();
    const close = () => {
        const next = new URLSearchParams(params.toString());
        next.delete("open");
        const query = next.toString();
        router.push(query ? `${pathname}?${query}` : pathname, { scroll: false });
    };
    return (
        <Dialog.Root open onOpenChange={(open) => !open && close()}>
            <Dialog.Portal container={container}>
                <Dialog.Overlay className="fixed inset-0 z-40 bg-black/25" />
                <Dialog.Content
                    aria-describedby={undefined}
                    className="fixed inset-0 z-40 flex flex-col bg-[var(--op-card)] text-[var(--op-text)] shadow-[var(--op-shadow-lg)] sm:inset-y-0 sm:left-auto sm:right-0 sm:w-[min(560px,100vw)] sm:border-l sm:border-[var(--op-border)]"
                >
                    <div className="flex items-start gap-3 border-b border-[var(--op-border)] px-5 py-4">
                        <div className="min-w-0 flex-1">
                            {subtitle && <div className="truncate text-xs text-[var(--op-muted)]">{subtitle}</div>}
                            <Dialog.Title className="m-0 truncate text-[17px] font-semibold">{title}</Dialog.Title>
                        </div>
                        {badge}
                        <Dialog.Close
                            aria-label="Close"
                            className="flex h-9 w-9 shrink-0 cursor-pointer items-center justify-center rounded-lg border border-[var(--op-border)] hover:bg-[var(--op-hover)]"
                        >
                            <X size={16} />
                        </Dialog.Close>
                    </div>
                    <div className="op-scroll flex-1 overflow-y-auto px-5 py-5">
                        <div className="flex flex-col gap-6">{children}</div>
                    </div>
                    {actions && (
                        <div className="flex flex-wrap gap-2 border-t border-[var(--op-border)] px-5 py-3 pb-[max(12px,env(safe-area-inset-bottom))]">
                            {actions}
                        </div>
                    )}
                </Dialog.Content>
            </Dialog.Portal>
        </Dialog.Root>
    );
}

export function SheetSection({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
    return (
        <section className="flex flex-col gap-2.5">
            <div className="flex items-center">
                <h3 className="m-0 flex-1 text-[13px] font-semibold uppercase tracking-wide text-[var(--op-muted)]">{title}</h3>
                {action}
            </div>
            {children}
        </section>
    );
}

export function Timeline({ events }: { events: { at: string; what: string; tone?: "good" | "bad" }[] }) {
    return (
        <ol className="m-0 flex list-none flex-col gap-3 p-0">
            {events.map((event, index) => (
                <li key={index} className="flex gap-3 text-sm">
                    <span
                        className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full"
                        style={{ background: event.tone === "good" ? "var(--op-good)" : event.tone === "bad" ? "var(--op-bad)" : "var(--op-border-strong)" }}
                    />
                    <span className="flex-1">{event.what}</span>
                    <span className="op-num shrink-0 text-xs text-[var(--op-muted)]">{event.at}</span>
                </li>
            ))}
        </ol>
    );
}
