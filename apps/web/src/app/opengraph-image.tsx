import { ImageResponse } from "next/og";

import { OG_SIZE, OgCard, og } from "../components/og-card";

export const alt = "examuploadkit: exam upload files, prepared to the rules";
export const size = OG_SIZE;
export const contentType = "image/png";

export default function Image() {
    return new ImageResponse(
        (
            <OgCard footer="Photograph, signature, thumb impression and documents · ₹3 a file · examuploadkit.com">
                <div style={{ display: "flex", fontSize: 88, lineHeight: 1.02, color: og.INK }}>
                    You prepare for the exam.
                </div>
                <div style={{ display: "flex", fontSize: 88, lineHeight: 1.02, marginTop: 8 }}>
                    <span>We’ll prepare&nbsp;</span>
                    <span style={{ background: og.SIGNAL, padding: "0 14px" }}>the files.</span>
                </div>
            </OgCard>
        ),
        size,
    );
}
