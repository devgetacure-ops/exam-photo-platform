"use client";

import Link from "next/link";
import { useState } from "react";

import { Wordmark } from "../euk/wordmark";
import { ThemeToggle } from "../theme-toggle";
import { InstallMenuItem } from "./install-card";
import { PhoneSearch, openPhoneSearch } from "./search-screen";
import { Sheet } from "./sheet";

/**
 * The phone's top bar, on every page that carries the site header.
 *
 * Subtle on purpose (the owner's call): the wordmark, a way to search, and a
 * way to everything else. The desktop bar's links, its inline search and the
 * theme control do not fit a 360px screen and were clipping off its right
 * edge; here they live in the menu, which opens as a sheet from the bottom of
 * the screen, where the thumb already is.
 *
 * Nothing that finishes a task lives up here. Those actions are the bottom
 * bar's.
 */

const MENU: { group: string; links: { href: string; label: string }[] }[] = [
    {
        group: "Your application",
        links: [
            { href: "/exams", label: "Every examination, A to Z" },
            { href: "/about#how", label: "How it works" },
            { href: "/about#pricing", label: "What it costs" },
            { href: "/compress-image", label: "Compress a photo to a size" },
            { href: "/pdf", label: "PDF tools" },
            { href: "/exam-request", label: "Ask for an examination" },
        ],
    },
    {
        group: "If something goes wrong",
        links: [
            { href: "/support", label: "Support and grievances" },
            { href: "/refund-policy", label: "Refunds" },
        ],
    },
    {
        group: "The fine print",
        links: [
            { href: "/privacy", label: "Privacy" },
            { href: "/terms", label: "Terms" },
        ],
    },
];

export function PhoneBar() {
    const [menu, setMenu] = useState(false);

    return (
        <div className="euk-mtop">
            <Link href="/" aria-label="ExamUploadKit home" className="euk-mtop-mark">
                <Wordmark />
            </Link>

            <button
                type="button"
                className="euk-mtop-btn"
                aria-label="Search for your examination"
                onClick={openPhoneSearch}
            >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
                    <circle cx="11" cy="11" r="7" />
                    <path d="m20.5 20.5-4.2-4.2" />
                </svg>
            </button>

            <button
                type="button"
                className="euk-mtop-btn"
                aria-label="Menu"
                aria-haspopup="dialog"
                aria-expanded={menu}
                onClick={() => setMenu(true)}
            >
                <svg width="20" height="16" viewBox="0 0 20 16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="square" aria-hidden="true">
                    <path d="M1 2 H19 M1 8 H19 M1 14 H12" />
                </svg>
            </button>

            <Sheet open={menu} title="Menu" onClose={() => setMenu(false)}>
                <nav className="euk-mmenu" aria-label="Site">
                    {MENU.map((group) => (
                        <div key={group.group} className="euk-mmenu-group">
                            <p className="euk-mmenu-title">{group.group}</p>
                            <ul>
                                {group.links.map((link) => (
                                    <li key={link.href}>
                                        <Link href={link.href} onClick={() => setMenu(false)}>
                                            {link.label}
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </nav>
                <InstallMenuItem />
                <div className="euk-mmenu-foot">
                    <span>Appearance</span>
                    <ThemeToggle />
                </div>
            </Sheet>

            <PhoneSearch />
        </div>
    );
}
