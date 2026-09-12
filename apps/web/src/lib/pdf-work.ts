/**
 * What the PDF work is and is not, said once for both layouts.
 *
 * The desktop page sets these as a grid and a list; the phone sets them as
 * rows that open a sheet. One source so the two can never describe different
 * work.
 */

export interface PdfJob {
    title: string;
    body: string;
}

export const PDF_JOBS: PdfJob[] = [
    {
        title: "Photographs into one PDF",
        body: "The form wants a PDF and you have three photographs of a marksheet. They go in, in the order you set, as one file.",
    },
    {
        title: "Several files into one",
        body: "A portal that accepts one attachment, and a certificate that reached you as four separate scans.",
    },
    {
        title: "Pages in the order you want",
        body: "Front and back photographed the wrong way round, or a blank page this form never asked for. Move them, drop them, keep what's left.",
    },
    {
        title: "A sideways page turned upright",
        body: "You photographed it the long way round, so it uploads on its side. Turn it a quarter at a time.",
    },
    {
        title: "Under the size limit",
        body: "Forms cap the file at 200 KB, 500 KB, sometimes 1 MB. A scan is compressed down to whatever yours asks for.",
    },
    {
        title: "Named the way the portal expects",
        body: "Some portals refuse a file for its name alone. Yours comes back named to the rule your examination published.",
    },
];

export const PDF_LIMITS: string[] = [
    "We don't read text out of a scan. There is no OCR here.",
    "We don't remove a PDF's password. A locked file is turned away, with a note to upload a copy that has none.",
    "We don't change what is written inside a PDF.",
    "We don't convert Word or Excel files.",
];
