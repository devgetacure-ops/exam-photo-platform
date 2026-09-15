import type { Metadata, Viewport } from "next";
import Script from "next/script";
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
import "./hub.css";
import "./compress.css";
import "./resize.css";
import "./mobile.css";
import { InstallCard } from "../components/m/install-card";
import { INSTALL_LISTENER_SCRIPT } from "../lib/install";
import { JsonLd } from "../components/json-ld";
import { CONTACT_EMAILS, ORGANIZATION_ID, SITE_NAME, SITE_URL } from "../lib/site";

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
    // Every relative canonical and preview address on the site resolves
    // against this. Without it they have no domain at all (DEC-087).
    metadataBase: new URL(SITE_URL),
    applicationName: SITE_NAME,
    title: {
        default: "ExamUploadKit: exam upload files, prepared to the rules",
        template: `%s | ${SITE_NAME}`,
    },
    description:
        "Choose your examination and we prepare every upload it asks for — photograph, signature, thumb impression, declaration and certificates — to that examination's published specification.",
    openGraph: { siteName: SITE_NAME, locale: "en_IN", type: "website" },
    twitter: { card: "summary_large_image" },
    // Search Console and Bing Webmaster Tools prove ownership with these,
    // set on the host. Bing's index also feeds several AI answer engines.
    verification: {
        ...(process.env.GOOGLE_SITE_VERIFICATION ? { google: process.env.GOOGLE_SITE_VERIFICATION } : {}),
        ...(process.env.BING_SITE_VERIFICATION
            ? { other: { "msvalidate.01": process.env.BING_SITE_VERIFICATION } }
            : {}),
    },
    // Added to the home screen on an iPhone, this opens without Safari's
    // chrome; the manifest covers Android.
    appleWebApp: {
        capable: true,
        title: "ExamUploadKit",
        statusBarStyle: "default",
    },
};

/**
 * Who publishes the site, for search and answer engines: the service and its
 * support address, never a person (DEC-086, DEC-087).
 */
const SITE_GRAPH = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "Organization",
            "@id": ORGANIZATION_ID,
            name: SITE_NAME,
            url: SITE_URL,
            logo: { "@type": "ImageObject", url: `${SITE_URL}/icon-512.png`, width: 512, height: 512 },
            email: CONTACT_EMAILS.support,
            contactPoint: [
                {
                    "@type": "ContactPoint",
                    contactType: "customer support",
                    email: CONTACT_EMAILS.support,
                    areaServed: "IN",
                    availableLanguage: ["en"],
                },
            ],
        },
        {
            "@type": "WebSite",
            "@id": `${SITE_URL}/#website`,
            url: SITE_URL,
            name: SITE_NAME,
            inLanguage: "en-IN",
            publisher: { "@id": ORGANIZATION_ID },
        },
    ],
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
            lang="en-IN"
            data-theme="light"
            className={`${shoulders.variable} ${anek.variable} ${petrona.variable} h-full antialiased`}
        >
            <head>
                <script
                    dangerouslySetInnerHTML={{
                        __html: "try{var t=localStorage.getItem('uploadready:theme');document.documentElement.dataset.theme=t==='dark'?'dark':'light'}catch(e){}",
                    }}
                />
                {/* Before any bundle, because the browser's install event can
                    arrive before React does (lib/install.ts). */}
                <script dangerouslySetInnerHTML={{ __html: INSTALL_LISTENER_SCRIPT }} />
            </head>
            <body className="min-h-full flex flex-col bg-paper text-ink">
                <a className="skip-link" href="#main-content">
                    Skip to content
                </a>
                <JsonLd data={SITE_GRAPH} />
                {children}
                <InstallCard />
                {/* Cloudflare Web Analytics (DEC-097): visit counts with no
                    cookie and no profile. Nothing loads unless the token is set. */}
                {process.env.NEXT_PUBLIC_CF_BEACON_TOKEN && (
                    <Script
                        strategy="afterInteractive"
                        src="https://static.cloudflareinsights.com/beacon.min.js"
                        data-cf-beacon={JSON.stringify({
                            token: process.env.NEXT_PUBLIC_CF_BEACON_TOKEN,
                        })}
                    />
                )}
            </body>
        </html>
    );
}
