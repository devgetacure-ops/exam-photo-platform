import type { Metadata } from "next";

import { PdfToolScreen } from "../../../components/m/pdf-tool";

export const metadata: Metadata = {
    title: "PDF page to image",
    description:
        "Save any page of a PDF as a JPEG or PNG, inside your own browser. Nothing is uploaded and nothing is charged.",
    // The converter is also on /pdf, which is the page to rank.
    robots: { index: false, follow: true },
    alternates: { canonical: "/pdf" },
};

/**
 * The converter as its own screen: the one row on the phone's PDF page that
 * is a tool anybody can use right now. A route rather than a sheet, so the
 * back button returns to the list and a refresh stays on the tool.
 */
export default function PdfToImagePage() {
    return (
        <main id="main-content">
            <PdfToolScreen />
        </main>
    );
}
