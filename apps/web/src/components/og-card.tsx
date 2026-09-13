import type { ReactNode } from "react";

/**
 * The card a link shows when it is shared (DEC-087). WhatsApp and Telegram
 * groups are where candidates pass links to each other, and a link with no
 * preview is a link nobody taps.
 *
 * Drawn for `next/og`, which lays out with flexbox only: every element with
 * more than one child sets `display: flex`. The colours are the design
 * system's light tokens, written out, because the renderer has no stylesheet.
 */

export const OG_SIZE = { width: 1200, height: 630 };

const PAPER = "#faf9f6";
const INK = "#111110";
const SIGNAL = "#f04e23";

function Wordmark() {
    return (
        <div style={{ display: "flex" }}>
            {"EXAMUPLOADKIT".split("").map((letter, i) => (
                <div
                    key={i}
                    style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        width: 38,
                        height: 50,
                        marginLeft: i === 0 ? 0 : -3,
                        border: `3px solid ${INK}`,
                        fontSize: 28,
                        color: INK,
                    }}
                >
                    {letter}
                </div>
            ))}
        </div>
    );
}

export function OgCard({ children, footer }: { children: ReactNode; footer: string }) {
    return (
        <div
            style={{
                width: "100%",
                height: "100%",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                background: PAPER,
                color: INK,
                padding: "56px 64px",
                borderBottom: `18px solid ${SIGNAL}`,
            }}
        >
            <Wordmark />
            <div style={{ display: "flex", flexDirection: "column" }}>{children}</div>
            <div style={{ display: "flex", fontSize: 26, color: "#55534e" }}>{footer}</div>
        </div>
    );
}

export const og = { INK, SIGNAL, PAPER };
