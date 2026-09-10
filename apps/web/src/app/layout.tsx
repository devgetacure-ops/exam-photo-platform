import type { Metadata, Viewport } from "next";
import { Instrument_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import "./journey.css";
import "./editorial.css";

/**
 * Two families, used with real hierarchy, rather than three used loosely —
 * this is served to candidates on cheap Android handsets over slow
 * connections, and every extra face is weight they pay for.
 *
 * Instrument Sans carries the interface: high x-height, slightly narrow, so it
 * stays legible at small sizes on a phone without reading as the default
 * system stack.
 *
 * IBM Plex Mono carries specifications and identifiers. That is a decision
 * about meaning, not texture: the product's substance is exact figures, and
 * tabular digits let a candidate compare two file-size limits by eye.
 */
const instrument = Instrument_Sans({
    variable: "--font-instrument",
    subsets: ["latin"],
    display: "swap",
    weight: ["400", "500", "600", "700"],
});

const plexMono = IBM_Plex_Mono({
    variable: "--font-plex-mono",
    subsets: ["latin"],
    display: "swap",
    weight: ["400", "500"],
});

export const metadata: Metadata = {
    title: {
        default: "Exam upload files, prepared to the rules",
        template: "%s",
    },
    description:
        "Choose your examination and we prepare every upload it asks for — photograph, signature, thumb impression, declaration and certificates — to that examination's published specification.",
};

export const viewport: Viewport = {
    themeColor: [
        { media: "(prefers-color-scheme: light)", color: "#fbfcfd" },
        { media: "(prefers-color-scheme: dark)", color: "#0b1418" },
    ],
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html
            suppressHydrationWarning
            lang="en"
            data-theme="light"
            className={`${instrument.variable} ${plexMono.variable} h-full antialiased`}
        >
            <head>
                <script
                    dangerouslySetInnerHTML={{
                        __html: "try{var t=localStorage.getItem('uploadready:theme');document.documentElement.dataset.theme=t==='dark'?'dark':'light'}catch(e){}",
                    }}
                />
            </head>
            <body className="min-h-full flex flex-col bg-paper text-ink">
                <a className="skip-link" href="#main-content">
                    Skip to content
                </a>
                {children}
            </body>
        </html>
    );
}
