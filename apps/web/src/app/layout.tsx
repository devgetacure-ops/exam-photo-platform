import type { Metadata, Viewport } from "next";
import {
    Big_Shoulders,
    Anek_Latin,
    Petrona,
} from "next/font/google";
import "./system.css";
import "./app.css";
import "./story.css";
import "./request.css";
import "./policy.css";
import "./exam.css";
import "./checkout.css";
import "./states.css";
import "./directory.css";
import "./rules.css";
import "./pdf.css";
import "./mobile.css";

/**
 * Three families. Each carries a different register and none of them is a
 * default: the previous setting ran Instrument Sans and IBM Plex,
 * both of which read as the face a generator reaches for.
 *
 * Big Shoulders Display — condensed and industrial, for display and the
 * wordmark. Its narrowness is what lets a four-line headline hold a 452px
 * column at 88px.
 *
 * The form's technical register — labels, measurements, part numbers — is set
 * in Anek uppercase and tracked rather than a monospace. A light typewriter
 * face is the least legible thing on a page at the 10px these labels run at,
 * which is the whole reason the register existed.
 *
 * Anek Latin — body and interface. Chosen for what comes later: its siblings
 * cover Devanagari, Bangla, Odia, Gurmukhi, Gujarati, Tamil, Telugu, Kannada
 * and Malayalam, so adding those languages is a face swap and not a redesign.
 *
 * Petrona italic — asides only, three or four on a page. The one warm voice.
 */
// No metric overrides exist for Big Shoulders, so Next cannot generate a
// size-adjusted fallback and warns at build. A condensed system face is the
// closest shape a phone already has while the webfont loads.
const shoulders = Big_Shoulders({
    variable: "--font-shoulders",
    subsets: ["latin"],
    display: "swap",
    adjustFontFallback: false,
    fallback: ["Arial Narrow", "Roboto Condensed", "sans-serif-condensed", "sans-serif"],
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
    // Added to the home screen on an iPhone, this opens without Safari's
    // chrome; the manifest covers Android.
    appleWebApp: {
        capable: true,
        title: "examuploadkit",
        statusBarStyle: "default",
    },
};

export const viewport: Viewport = {
    // Without this iOS reports every safe-area inset as zero, and the action
    // bar sits under the home indicator.
    viewportFit: "cover",
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
            className={`${shoulders.variable} ${anek.variable} ${petrona.variable} h-full antialiased`}
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
