import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";
import "../../operator.css";

export const metadata: Metadata = {
    title: "Operator",
    robots: { index: false, follow: false },
};

// Every page below runs `requireOperator()` itself: a layout is not re-run on
// every navigation, so it cannot be the gate.
export default function OperatorLayout({ children }: { children: ReactNode }) {
    return (
        <div className="euk euk-op">
            <header className="euk-op-head">
                <nav className="euk-op-nav" aria-label="Operator">
                    <Link href="/admin">Overview</Link>
                    <Link href="/admin/orders">Orders</Link>
                    <Link href="/admin/uploads">Uploads</Link>
                    <Link href="/admin/customers">Customers</Link>
                    <Link href="/admin/inbox">Inbox</Link>
                    <Link href="/admin/growth">Growth</Link>
                    <Link href="/admin/calendar">Calendar</Link>
                    <Link href="/admin/marketing">Marketing</Link>
                    <Link href="/admin/activity">Activity</Link>
                </nav>
                <form action="/admin/search" method="get" className="euk-op-search" role="search">
                    <label htmlFor="operator-search" className="euk-label">
                        Search
                    </label>
                    <input
                        id="operator-search"
                        name="q"
                        type="search"
                        placeholder="Email, phone, order, payment, upload, reference"
                        minLength={2}
                    />
                    <button type="submit" className="euk-op-button">
                        Find
                    </button>
                </form>
            </header>
            {children}
        </div>
    );
}
