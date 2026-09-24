"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { Command } from "cmdk";
import {
    Activity,
    BarChart3,
    CalendarDays,
    Home,
    Image as ImageIcon,
    Inbox,
    Mail,
    Monitor,
    Moon,
    MoreHorizontal,
    Receipt,
    Search,
    Star,
    Sun,
    Ticket,
    Users,
    X,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import { Toaster, toast } from "sonner";
import { useConsoleRoot } from "./portal";
import { cn } from "./ui";

/**
 * The console's frame (DEC-113): a sidebar on a laptop, a bottom tab bar on a
 * phone, one search for everything (Ctrl K), a theme that follows the device,
 * and the confirmations every action returns with.
 */

export interface Badges {
    refund_due: number;
    inbox_open: number;
    inbox_overdue: number;
    exam_requests: number;
    reviews_pending: number;
}

interface NavItem {
    href: string;
    label: string;
    icon: typeof Home;
    count?: (b: Badges) => number;
    urgent?: (b: Badges) => boolean;
}

const MAIN: NavItem[] = [
    { href: "/admin", label: "Overview", icon: Home },
    { href: "/admin/orders", label: "Orders", icon: Receipt, count: (b) => b.refund_due, urgent: (b) => b.refund_due > 0 },
    { href: "/admin/uploads", label: "Uploads", icon: ImageIcon },
    { href: "/admin/customers", label: "Customers", icon: Users },
    { href: "/admin/inbox", label: "Inbox", icon: Inbox, count: (b) => b.inbox_open, urgent: (b) => b.inbox_overdue > 0 },
    { href: "/admin/reviews", label: "Reviews", icon: Star, count: (b) => b.reviews_pending },
];

const GROW: NavItem[] = [
    { href: "/admin/growth", label: "Growth", icon: BarChart3 },
    { href: "/admin/marketing", label: "Marketing", icon: Mail },
    { href: "/admin/coupons", label: "Coupons", icon: Ticket },
    { href: "/admin/calendar", label: "Calendar", icon: CalendarDays },
    { href: "/admin/activity", label: "Activity", icon: Activity },
];

const PHONE_TABS = ["/admin", "/admin/orders", "/admin/inbox", "/admin/reviews"];

function isActive(pathname: string, href: string) {
    return href === "/admin" ? pathname === "/admin" : pathname === href || pathname.startsWith(`${href}/`);
}

function Count({ item, badges, active }: { item: NavItem; badges: Badges | null; active?: boolean }) {
    const value = badges && item.count ? item.count(badges) : 0;
    if (!value) return null;
    const urgent = badges && item.urgent ? item.urgent(badges) : false;
    return (
        <span
            className={cn(
                "op-num ml-auto rounded-full px-1.5 text-[11px] font-semibold leading-5",
                urgent ? "bg-[var(--op-accent)] text-white" : active ? "bg-[var(--op-card)]" : "bg-[var(--op-muted-bg)]",
            )}
        >
            {value}
        </span>
    );
}

function NavLink({ item, badges, pathname, onNavigate }: { item: NavItem; badges: Badges | null; pathname: string; onNavigate?: () => void }) {
    const active = isActive(pathname, item.href);
    const Icon = item.icon;
    return (
        <Link
            href={item.href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={cn(
                "flex h-9 items-center gap-2.5 rounded-lg px-2.5 text-sm",
                active ? "bg-[var(--op-hover)] font-semibold" : "text-[var(--op-muted)] hover:bg-[var(--op-hover)] hover:text-[var(--op-text)]",
            )}
        >
            <Icon size={16} strokeWidth={2} aria-hidden="true" />
            {item.label}
            <Count item={item} badges={badges} active={active} />
        </Link>
    );
}

type Theme = "system" | "light" | "dark";
const THEME_KEY = "euk-op-theme";

const THEME_EVENT = "euk-op-theme-change";

function readTheme(): Theme {
    try {
        const saved = localStorage.getItem(THEME_KEY);
        return saved === "light" || saved === "dark" ? saved : "system";
    } catch {
        return "system";
    }
}

function subscribeTheme(onChange: () => void) {
    window.addEventListener("storage", onChange);
    window.addEventListener(THEME_EVENT, onChange);
    return () => {
        window.removeEventListener("storage", onChange);
        window.removeEventListener(THEME_EVENT, onChange);
    };
}

/** The owner's choice, else the device's. Kept in this browser only. */
function useTheme(): [Theme, (next: Theme) => void] {
    const theme = useSyncExternalStore(subscribeTheme, readTheme, () => "system" as Theme);
    useEffect(() => {
        const root = document.querySelector<HTMLElement>(".op-root");
        if (!root) return;
        if (theme === "system") root.removeAttribute("data-theme");
        else root.setAttribute("data-theme", theme);
    }, [theme]);
    const set = (next: Theme) => {
        try {
            if (next === "system") localStorage.removeItem(THEME_KEY);
            else localStorage.setItem(THEME_KEY, next);
        } catch {
            /* Kept for this visit only. */
        }
        window.dispatchEvent(new Event(THEME_EVENT));
    };
    return [theme, set];
}

function ThemeSwitch() {
    const [theme, setTheme] = useTheme();
    const options: [Theme, typeof Sun, string][] = [
        ["system", Monitor, "Follow device"],
        ["light", Sun, "Light"],
        ["dark", Moon, "Dark"],
    ];
    return (
        <div role="radiogroup" aria-label="Theme" className="flex rounded-lg bg-[var(--op-muted-bg)] p-0.5">
            {options.map(([value, Icon, label]) => (
                <button
                    key={value}
                    type="button"
                    role="radio"
                    aria-checked={theme === value}
                    aria-label={label}
                    title={label}
                    onClick={() => setTheme(value)}
                    className={cn(
                        "flex h-7 w-8 cursor-pointer items-center justify-center rounded-md",
                        theme === value ? "bg-[var(--op-card)] shadow-[var(--op-shadow)]" : "text-[var(--op-muted)]",
                    )}
                >
                    <Icon size={14} aria-hidden="true" />
                </button>
            ))}
        </div>
    );
}

interface SearchResults {
    orders: { order_id: string; exam_names: string[]; state: string; amount_paise: number; emails: string[] }[];
    customers: { email: string; phone?: string | null }[];
    tickets: { id: string; kind: string; email?: string | null; reference?: string | null }[];
    uploads: { job_id: string; exam_name?: string | null; requirement_name?: string | null }[];
}

function CommandMenu({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
    const router = useRouter();
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<SearchResults | null>(null);
    const [loading, setLoading] = useState(false);

    const text = query.trim();
    const shown = text.length >= 2 ? results : null;
    useEffect(() => {
        if (!open || text.length < 2) return;
        const controller = new AbortController();
        const timer = setTimeout(() => {
            setLoading(true);
            fetch(`/admin/api/search?q=${encodeURIComponent(text)}`, { signal: controller.signal, cache: "no-store" })
                .then((r) => (r.ok ? (r.json() as Promise<SearchResults>) : null))
                .then((value) => setResults(value))
                .catch(() => undefined)
                .finally(() => setLoading(false));
        }, 180);
        return () => {
            clearTimeout(timer);
            controller.abort();
        };
    }, [text, open]);

    const container = useConsoleRoot();
    const go = (href: string) => {
        onOpenChange(false);
        setQuery("");
        router.push(href);
    };
    const item = "flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm data-[selected=true]:bg-[var(--op-hover)]";

    return (
        <Dialog.Root open={open} onOpenChange={onOpenChange}>
            <Dialog.Portal container={container}>
                <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40" />
                <Dialog.Content
                    className="fixed left-1/2 top-[12vh] z-50 w-[min(640px,calc(100vw-24px))] -translate-x-1/2 overflow-hidden rounded-xl border border-[var(--op-border)] bg-[var(--op-card)] text-[var(--op-text)] shadow-[var(--op-shadow-lg)]"
                    aria-describedby={undefined}
                >
                    <Dialog.Title className="sr-only">Search</Dialog.Title>
                    <Command shouldFilter={false} label="Search everything">
                        <div className="flex items-center gap-2 border-b border-[var(--op-border)] px-4">
                            <Search size={16} className="text-[var(--op-muted)]" aria-hidden="true" />
                            <Command.Input
                                value={query}
                                onValueChange={setQuery}
                                placeholder="Email, phone, order, payment, code, upload…"
                                className="h-12 flex-1 bg-transparent text-[15px] outline-none placeholder:text-[var(--op-faint)]"
                            />
                        </div>
                        <Command.List className="op-scroll max-h-[60vh] overflow-y-auto p-2">
                            {text.length < 2 && (
                                <div className="px-3 py-6 text-center text-[13px] text-[var(--op-muted)]">Type at least two characters.</div>
                            )}
                            {loading && !shown && <Command.Loading>Searching…</Command.Loading>}
                            {shown && (
                                <Command.Empty className="px-3 py-6 text-center text-[13px] text-[var(--op-muted)]">Nothing matches.</Command.Empty>
                            )}
                            {shown && shown.customers.length > 0 && (
                                <Command.Group heading="Customers" className="text-xs text-[var(--op-muted)] [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-1.5">
                                    {shown.customers.slice(0, 5).map((c) => (
                                        <Command.Item key={c.email} value={`c-${c.email}`} onSelect={() => go(`/admin/customers?open=${encodeURIComponent(c.email)}`)} className={item}>
                                            <Users size={15} aria-hidden="true" />
                                            <span className="flex-1 text-[var(--op-text)]">{c.email}</span>
                                            <span className="text-xs">{c.phone}</span>
                                        </Command.Item>
                                    ))}
                                </Command.Group>
                            )}
                            {shown && shown.orders.length > 0 && (
                                <Command.Group heading="Orders" className="text-xs text-[var(--op-muted)] [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-1.5">
                                    {shown.orders.slice(0, 6).map((o) => (
                                        <Command.Item key={o.order_id} value={`o-${o.order_id}`} onSelect={() => go(`/admin/orders?open=${o.order_id}`)} className={item}>
                                            <Receipt size={15} aria-hidden="true" />
                                            <span className="flex-1 text-[var(--op-text)]">{o.exam_names.join(", ") || o.order_id}</span>
                                            <span className="text-xs">{o.emails[0] ?? o.order_id}</span>
                                        </Command.Item>
                                    ))}
                                </Command.Group>
                            )}
                            {shown && shown.tickets.length > 0 && (
                                <Command.Group heading="Inbox" className="text-xs text-[var(--op-muted)] [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-1.5">
                                    {shown.tickets.slice(0, 5).map((t) => (
                                        <Command.Item key={t.id} value={`t-${t.id}`} onSelect={() => go(`/admin/inbox?open=${t.id}`)} className={item}>
                                            <Inbox size={15} aria-hidden="true" />
                                            <span className="flex-1 text-[var(--op-text)]">
                                                {t.kind} · {t.email}
                                            </span>
                                            <span className="text-xs">{t.reference}</span>
                                        </Command.Item>
                                    ))}
                                </Command.Group>
                            )}
                            {shown && shown.uploads.length > 0 && (
                                <Command.Group heading="Uploads" className="text-xs text-[var(--op-muted)] [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-1.5">
                                    {shown.uploads.slice(0, 5).map((u) => (
                                        <Command.Item key={u.job_id} value={`u-${u.job_id}`} onSelect={() => go(`/admin/uploads?open=${u.job_id}`)} className={item}>
                                            <ImageIcon size={15} aria-hidden="true" />
                                            <span className="flex-1 text-[var(--op-text)]">{u.requirement_name ?? u.job_id}</span>
                                            <span className="text-xs">{u.exam_name}</span>
                                        </Command.Item>
                                    ))}
                                </Command.Group>
                            )}
                        </Command.List>
                    </Command>
                </Dialog.Content>
            </Dialog.Portal>
        </Dialog.Root>
    );
}

/** Shows the message an action returned with, once, then tidies the address. */
function ActionToasts() {
    const params = useSearchParams();
    const router = useRouter();
    const pathname = usePathname();
    const shown = useRef("");
    useEffect(() => {
        const done = params.get("done");
        const failed = params.get("failed");
        if (!done && !failed) return;
        const key = `${done}|${failed}`;
        if (shown.current === key) return;
        shown.current = key;
        if (done) toast.success(done);
        if (failed) toast.error(failed);
        const next = new URLSearchParams(params.toString());
        next.delete("done");
        next.delete("failed");
        const query = next.toString();
        router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    }, [params, pathname, router]);
    return null;
}

export function ConsoleShell({ badges, operator, children }: { badges: Badges | null; operator: string; children: ReactNode }) {
    const pathname = usePathname() ?? "/admin";
    const [searchOpen, setSearchOpen] = useState(false);
    const [moreOpen, setMoreOpen] = useState(false);
    const container = useConsoleRoot();

    useEffect(() => {
        const key = (event: KeyboardEvent) => {
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
                event.preventDefault();
                setSearchOpen((open) => !open);
            }
        };
        window.addEventListener("keydown", key);
        return () => window.removeEventListener("keydown", key);
    }, []);

    const phoneTabs = MAIN.filter((item) => PHONE_TABS.includes(item.href));
    const phoneMore = [...MAIN.filter((item) => !PHONE_TABS.includes(item.href)), ...GROW];
    const moreActive = phoneMore.some((item) => isActive(pathname, item.href));

    return (
        <>
            <aside className="hidden w-60 shrink-0 flex-col gap-0.5 border-r border-[var(--op-border)] bg-[var(--op-card)] px-3 py-4 lg:flex">
                <Link href="/admin" className="mb-4 flex items-center gap-2.5 px-2">
                    <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--op-accent)] text-[13px] font-bold text-white">E</span>
                    <span className="flex flex-col leading-tight">
                        <span className="font-semibold">ExamUploadKit</span>
                        <span className="text-xs text-[var(--op-muted)]">Operator</span>
                    </span>
                </Link>
                {MAIN.map((item) => (
                    <NavLink key={item.href} item={item} badges={badges} pathname={pathname} />
                ))}
                <div className="mx-1 my-3 h-px bg-[var(--op-border)]" />
                {GROW.map((item) => (
                    <NavLink key={item.href} item={item} badges={badges} pathname={pathname} />
                ))}
                <div className="flex-1" />
                <div className="flex items-center justify-between gap-2 px-1">
                    <span className="truncate text-xs text-[var(--op-muted)]" title={operator}>
                        {operator}
                    </span>
                    <ThemeSwitch />
                </div>
            </aside>

            <div className="flex min-w-0 flex-1 flex-col">
                <header className="flex h-14 shrink-0 items-center gap-3 border-b border-[var(--op-border)] bg-[var(--op-card)] px-4 lg:h-15 lg:px-7">
                    <Link href="/admin" className="flex items-center lg:hidden" aria-label="Overview">
                        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--op-accent)] text-[13px] font-bold text-white">E</span>
                    </Link>
                    <button
                        type="button"
                        onClick={() => setSearchOpen(true)}
                        className="flex h-9 min-w-0 flex-1 cursor-pointer items-center gap-2.5 rounded-lg border border-[var(--op-border)] bg-[var(--op-bg)] px-3 text-left text-[var(--op-muted)] lg:max-w-xl"
                    >
                        <Search size={16} aria-hidden="true" />
                        <span className="flex-1 truncate">Search email, phone, order, code…</span>
                        <kbd className="hidden rounded border border-[var(--op-border)] px-1.5 text-[11px] font-sans sm:inline">Ctrl K</kbd>
                    </button>
                    <div className="lg:hidden">
                        <ThemeSwitch />
                    </div>
                </header>
                <main className="op-scroll min-h-0 flex-1 overflow-y-auto pb-24 lg:pb-10">
                    <div className="mx-auto flex w-full max-w-[1400px] flex-col gap-5 px-4 py-5 lg:px-7 lg:py-7">{children}</div>
                </main>
            </div>

            <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-40 flex border-t border-[var(--op-border)] bg-[var(--op-card)] px-1 pb-[max(8px,env(safe-area-inset-bottom))] pt-1 lg:hidden">
                {phoneTabs.map((item) => {
                    const Icon = item.icon;
                    const active = isActive(pathname, item.href);
                    const value = badges && item.count ? item.count(badges) : 0;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            aria-current={active ? "page" : undefined}
                            className={cn("relative flex flex-1 flex-col items-center gap-0.5 py-1.5 text-[11px]", active ? "font-semibold text-[var(--op-accent)]" : "text-[var(--op-muted)]")}
                        >
                            <Icon size={22} aria-hidden="true" />
                            {item.label === "Overview" ? "Home" : item.label}
                            {value > 0 && (
                                <span className="op-num absolute right-[calc(50%-20px)] top-0.5 rounded-full bg-[var(--op-accent)] px-1.5 text-[10px] font-bold leading-4 text-white">{value}</span>
                            )}
                        </Link>
                    );
                })}
                <button
                    type="button"
                    onClick={() => setMoreOpen(true)}
                    className={cn("flex flex-1 cursor-pointer flex-col items-center gap-0.5 py-1.5 text-[11px]", moreActive ? "font-semibold text-[var(--op-accent)]" : "text-[var(--op-muted)]")}
                >
                    <MoreHorizontal size={22} aria-hidden="true" />
                    More
                </button>
            </nav>

            <Dialog.Root open={moreOpen} onOpenChange={setMoreOpen}>
                <Dialog.Portal container={container}>
                    <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40 lg:hidden" />
                    <Dialog.Content className="fixed inset-x-0 bottom-0 z-50 rounded-t-2xl border-t border-[var(--op-border)] bg-[var(--op-card)] p-3 pb-[max(16px,env(safe-area-inset-bottom))] text-[var(--op-text)] lg:hidden" aria-describedby={undefined}>
                        <div className="mb-2 flex items-center justify-between px-2">
                            <Dialog.Title className="m-0 text-[15px] font-semibold">More</Dialog.Title>
                            <Dialog.Close className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-lg" aria-label="Close">
                                <X size={18} />
                            </Dialog.Close>
                        </div>
                        <div className="grid grid-cols-2 gap-1">
                            {phoneMore.map((item) => (
                                <NavLink key={item.href} item={item} badges={badges} pathname={pathname} onNavigate={() => setMoreOpen(false)} />
                            ))}
                        </div>
                    </Dialog.Content>
                </Dialog.Portal>
            </Dialog.Root>

            <CommandMenu open={searchOpen} onOpenChange={setSearchOpen} />
            <ActionToasts />
            <Toaster position="top-center" richColors closeButton toastOptions={{ style: { fontFamily: "var(--font-geist), system-ui, sans-serif" } }} />
        </>
    );
}
