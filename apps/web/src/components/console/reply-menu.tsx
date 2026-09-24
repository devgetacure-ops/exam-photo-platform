"use client";

import * as Menu from "@radix-ui/react-dropdown-menu";
import { ChevronDown, Mail } from "lucide-react";
import { mailto, replies, type ReplyContext } from "../../lib/operator/templates";
import { useConsoleRoot } from "./portal";
import { buttonStyles, cn } from "./ui";

/**
 * Saved replies (DEC-109), as a menu. Each opens the owner's own mail app,
 * addressed and filled in; nothing is sent from here.
 */
export function ReplyMenu({ email, context, only }: { email: string; context: ReplyContext; only?: string[] }) {
    const container = useConsoleRoot();
    const list = replies(context).filter((reply) => !only || only.includes(reply.id));
    return (
        <Menu.Root>
            <Menu.Trigger className={cn(buttonStyles({ variant: "secondary", size: "lg" }), "flex-1 sm:flex-none")}>
                <Mail size={16} aria-hidden="true" />
                Reply
                <ChevronDown size={14} aria-hidden="true" />
            </Menu.Trigger>
            <Menu.Portal container={container}>
                <Menu.Content
                    align="start"
                    sideOffset={6}
                    className="z-50 min-w-60 rounded-xl border border-[var(--op-border)] bg-[var(--op-card)] p-1 text-[var(--op-text)] shadow-[var(--op-shadow-lg)]"
                >
                    <Menu.Label className="px-3 py-1.5 text-xs text-[var(--op-muted)]">Opens in your mail app, to {email}</Menu.Label>
                    <Menu.Item asChild className="cursor-pointer rounded-lg px-3 py-2 text-sm outline-none data-[highlighted]:bg-[var(--op-hover)]">
                        <a href={`mailto:${encodeURIComponent(email)}`}>Blank email</a>
                    </Menu.Item>
                    {list.map((reply) => (
                        <Menu.Item key={reply.id} asChild className="cursor-pointer rounded-lg px-3 py-2 text-sm outline-none data-[highlighted]:bg-[var(--op-hover)]">
                            <a href={mailto(email, reply)}>{reply.label}</a>
                        </Menu.Item>
                    ))}
                </Menu.Content>
            </Menu.Portal>
        </Menu.Root>
    );
}
