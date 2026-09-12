import type { MetadataRoute } from "next";

/**
 * Installed to the home screen, this opens without browser chrome, which is
 * most of what makes the mobile build feel like an application rather than a
 * page. Portrait only: every flow is a column, and nothing here is improved by
 * turning a phone sideways.
 */
export default function manifest(): MetadataRoute.Manifest {
    return {
        name: "examuploadkit — exam upload files, prepared to the rules",
        short_name: "examuploadkit",
        description:
            "Your photograph, signature, thumb impression, declaration and certificates, prepared to the rules your examination published.",
        start_url: "/",
        scope: "/",
        display: "standalone",
        orientation: "portrait",
        background_color: "#faf9f6",
        theme_color: "#faf9f6",
        categories: ["education", "utilities"],
        icons: [
            { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
            { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
            {
                src: "/icon-maskable-512.png",
                sizes: "512x512",
                type: "image/png",
                purpose: "maskable",
            },
        ],
    };
}
