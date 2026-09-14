import type { Metadata } from "next";

/**
 * The site's public address, and the metadata every page shares (DEC-087).
 *
 * Search engines, AI answer engines and messaging apps each read a page
 * differently: a crawler wants one canonical address, an answer engine wants
 * structured facts it can quote, and WhatsApp wants a title, a description
 * and an image. One helper sets all of them, so a page cannot ship with a
 * canonical and no preview, or a preview whose title disagrees with the tab.
 */

export const SITE_NAME = "ExamUploadKit";

/** Set at build time on the host; the production domain otherwise. */
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || "https://examuploadkit.com").replace(/\/+$/, "");

export const CONTACT_EMAILS = {
    support: "support@examuploadkit.com",
    privacy: "privacy@examuploadkit.com",
    grievance: "grievance@examuploadkit.com",
    legal: "legal@examuploadkit.com",
} as const;

export function absoluteUrl(path: string): string {
    return `${SITE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export function pageMetadata({
    title,
    description,
    path,
    index = true,
    image = "/opengraph-image",
}: {
    title: string;
    description: string;
    path: string;
    /** False for a page that duplicates another one; links are still followed. */
    index?: boolean;
    /**
     * The preview image's route. A page that sets Open Graph fields loses the
     * image it would have inherited from a parent segment, so it is named here
     * rather than assumed. A generated image in the page's own segment still
     * takes precedence over this.
     */
    image?: string;
}): Metadata {
    const images = [{ url: image, width: 1200, height: 630, alt: title }];
    return {
        title,
        description,
        alternates: { canonical: path },
        openGraph: {
            title,
            description,
            url: path,
            siteName: SITE_NAME,
            locale: "en_IN",
            type: "website",
            images,
        },
        twitter: { card: "summary_large_image", title, description, images },
        ...(index ? {} : { robots: { index: false, follow: true } }),
    };
}

/**
 * JSON for a `<script type="application/ld+json">`, escaped as the Next.js
 * guide asks: no value, however it was written, can close the script tag.
 */
export function serializeJsonLd(data: unknown): string {
    return JSON.stringify(data).replace(/</g, "\\u003c");
}

export function breadcrumbs(items: { name: string; path: string }[]) {
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        itemListElement: items.map((item, index) => ({
            "@type": "ListItem",
            position: index + 1,
            name: item.name,
            item: absoluteUrl(item.path),
        })),
    };
}

export const ORGANIZATION_ID = `${SITE_URL}/#organization`;
