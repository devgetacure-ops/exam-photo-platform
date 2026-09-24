import type { Metadata, Viewport } from "next";
import { Geist } from "next/font/google";
import { headers } from "next/headers";
import type { ReactNode } from "react";
import { ConsoleShell, type Badges } from "../../../components/console/shell";
import { operatorFromHeaders } from "../../../lib/operator/access";
import { engineJson } from "../../../lib/operator/engine";
import "./console.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist", display: "swap" });

export const metadata: Metadata = {
    title: { default: "Operator", template: "%s · Operator" },
    robots: { index: false, follow: false },
};

export const viewport: Viewport = {
    themeColor: [
        { media: "(prefers-color-scheme: light)", color: "#ffffff" },
        { media: "(prefers-color-scheme: dark)", color: "#161412" },
    ],
};

/**
 * The console's frame (DEC-113). Every page below still runs
 * `requireOperator()` itself: a layout is not re-run on every navigation, so
 * it cannot be the gate. Without a verified visitor it draws nothing but the
 * page's own 404.
 */
export default async function OperatorLayout({ children }: { children: ReactNode }) {
    const operator = await operatorFromHeaders(await headers());
    if (!operator) return <>{children}</>;
    const badges = await engineJson<Badges>("/v1/operator/badges");
    return (
        <div className={`op-root ${geist.variable}`}>
            <ConsoleShell badges={badges.ok ? badges.value : null} operator={operator}>
                {children}
            </ConsoleShell>
        </div>
    );
}
