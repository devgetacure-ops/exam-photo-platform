"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/** The three policies, one strip apart, with the one being read marked. */
const POLICIES = [
    { href: "/privacy", label: "Privacy" },
    { href: "/terms", label: "Terms" },
    { href: "/refund-policy", label: "Refunds" },
];

export function PolicyTabs() {
    const pathname = usePathname();
    return (
        <nav className="euk-policy-tabs" aria-label="Policies">
            {POLICIES.map((policy) => (
                <Link
                    key={policy.href}
                    href={policy.href}
                    aria-current={pathname === policy.href ? "page" : undefined}
                >
                    {policy.label}
                </Link>
            ))}
        </nav>
    );
}
