import type { Metadata, Viewport } from "next";
import {
    Big_Shoulders,
    Courier_Prime,
    Anek_Latin,
    Petrona,
} from "next/font/google";
import "./globals.css";
import "./journey.css";
import "./editorial.css";
import "./system.css";

/**
 * Four families, which is one more than this would normally allow, so it is a
 * decision rather than an accident. Each carries a different register and none
 * of them is a default: the previous setting ran Instrument Sans and IBM Plex,
 * both of which read as the face a generator reaches for.
 *
 * Big Shoulders Display — condensed and industrial, for display and the
 * wordmark. Its narrowness is what lets a four-line headline hold a 452px
 * column at 88px.
 *
 * Courier Prime — the form's own register. Labels, measurements, part numbers.
 * It is doing the job a typewriter did on the document this interface is built
 * from.
 *
 * Anek Latin — body and interface. Chosen for what comes later: its siblings
 * cover Devanagari, Bangla, Odia, Gurmukhi, Gujarati, Tamil, Telugu, Kannada
 * and Malayalam, so adding those languages is a face swap and not a redesign.
 *
 * Petrona italic — asides only, three or four on a page. The one warm voice.
 */
const shoulders = Big_Shoulders({
    variable: "--font-shoulders",
    subsets: ["latin"],
    display: "swap",
});

const courier = Courier_Prime({
    variable: "--font-courier",
    subsets: ["latin"],
    display: "swap",
    weight: ["400", "700"],
    style: ["normal", "italic"],
});

const anek = Anek_Latin({
    variable: "--font-anek",
    subsets: ["latin"],
    display: "swap",
});

const petrona = Petrona({
    variable: "--font-petrona",
    subsets: ["latin"],
    display: "swap",
    style: ["italic"],
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
        { media: "(prefers-color-scheme: light)", color: "#faf9f6" },
        { media: "(prefers-color-scheme: dark)", color: "#12100e" },
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
            className={`${shoulders.variable} ${courier.variable} ${anek.variable} ${petrona.variable} h-full antialiased`}
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
