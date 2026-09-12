"use client";

import { PdfToImage } from "../exam/pdf-to-image";
import { AppBar } from "./app-bar";

/**
 * PDF page to image, as a screen of its own.
 *
 * On the desktop page the converter sits in a block among the rest of the
 * PDF story. On a phone it is the one thing a candidate came to do, so it
 * gets the whole screen: what it is in two lines, the caution that matters,
 * and the file picker first, with the format and resolution folded under
 * it at the settings most portals want.
 */
export function PdfToolScreen() {
    return (
        <div className="euk euk-m euk-mpdftool">
            <AppBar title="PDF page to image" backHref="/pdf" pinned />
            <div className="euk-m-screen">
                <h2 className="euk-display euk-m-title">A PDF page as an image</h2>
                <p className="euk-m-lede">
                    Your PDF opens inside this page and never leaves this device.
                    Choose it, and each page comes back as an image to download.
                </p>
                <p className="euk-pdfimg-caution">
                    An image of a digitally issued certificate can&rsquo;t be
                    verified the way the PDF can. Use this only when the portal asks
                    for an image.
                </p>
                <PdfToImage pickerFirst />
            </div>
        </div>
    );
}
