"use client";
import { useEffect, useState } from "react";
export function ThemeToggle() {
    const [dark, setDark] = useState(false);
    useEffect(() => {
        let value = false;
        try {
            value = localStorage.getItem("uploadready:theme") === "dark";
        } catch {
            /* Optional preference. */
        }
        document.documentElement.dataset.theme = value ? "dark" : "light";
        const frame = requestAnimationFrame(() => setDark(value));
        return () => cancelAnimationFrame(frame);
    }, []);
    return (
        <button
            className="theme-toggle"
            type="button"
            aria-label="Dark mode"
            aria-pressed={dark}
            onClick={() => {
                const next = !dark;
                setDark(next);
                document.documentElement.dataset.theme = next
                    ? "dark"
                    : "light";
                try {
                    localStorage.setItem(
                        "uploadready:theme",
                        next ? "dark" : "light",
                    );
                } catch {
                    /* Still works for this page. */
                }
            }}
        >
            {dark ? "Light" : "Dark"}
            <span aria-hidden="true">◐</span>
        </button>
    );
}
