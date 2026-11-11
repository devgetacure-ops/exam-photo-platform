/**
 * Hindi alongside English (DEC-129).
 *
 * English keeps its addresses; Hindi lives under `/hi`. Every page that has
 * a Hindi twin names both in its metadata, so a search engine serves the one
 * that matches the searcher. Only words are translated: examination names,
 * figures and units stay exactly as the authority published them.
 */

export type Locale = "en" | "hi";

export function localePath(locale: Locale, path: string): string {
    return locale === "hi" ? `/hi${path === "/" ? "" : path}` : path;
}

/** `alternates.languages` for a page that exists in both languages. */
export function languageAlternates(path: string): Record<string, string> {
    return { "en-IN": path, "hi-IN": localePath("hi", path), "x-default": path };
}

const HI_VALUE_WORDS: [RegExp, string][] = [
    [/\bpreferred\b/gi, "(सुझाया गया)"],
    [/\bwhite\b/gi, "सफ़ेद"],
    [/\bor\b/gi, "या"],
    [/\bmaximum\b/gi, "अधिकतम"],
    [/\bminimum\b/gi, "न्यूनतम"],
];

/** A published figure in the reader's language: units untouched, the few English words around them translated. */
export function localValue(locale: Locale, value: string): string {
    const plain = value.replace(/#fff(fff)?\b/gi, "white");
    if (locale === "en") return plain;
    return HI_VALUE_WORDS.reduce((text, [pattern, word]) => text.replace(pattern, word), plain);
}

export const COPY = {
    en: {
        fileNames: {
            photograph: ["Photograph", "photographs"],
            signature: ["Signature", "signatures"],
            thumb_impression: ["Thumb impression", "thumb impressions"],
            handwritten_declaration: ["Declaration", "declarations"],
            portal_declaration: ["Declaration", "declarations"],
            certificate_scan: ["Certificate", "certificates"],
            identity_document: ["ID document", "ID documents"],
            other: ["Other file", "other files"],
        } as Record<string, [string, string]>,
        searchLabel: {
            photograph: "photo",
            signature: "signature",
            thumb_impression: "thumb impression",
            handwritten_declaration: "handwritten declaration",
        } as Record<string, string>,
        setBy: (body: string) => `Set by ${body}`,
        answer: "The answer",
        estimated: "est.",
        estimatedTitle: "our estimate",
        from: "From",
        everyRule: "Every rule, in full",
        relatedTitle: "Applying to more?",
        relatedPhoto: "Photo",
        relatedAll: (count: number, phrase: string) => `All ${count} ${phrase} examinations`,
    },
    hi: {
        fileNames: {
            photograph: ["फ़ोटो", "फ़ोटो"],
            signature: ["हस्ताक्षर", "हस्ताक्षर"],
            thumb_impression: ["अंगूठे का निशान", "अंगूठे के निशान"],
            handwritten_declaration: ["घोषणा", "घोषणाएँ"],
            portal_declaration: ["घोषणा", "घोषणाएँ"],
            certificate_scan: ["प्रमाणपत्र", "प्रमाणपत्र"],
            identity_document: ["पहचान पत्र", "पहचान पत्र"],
            other: ["अन्य फ़ाइल", "अन्य फ़ाइलें"],
        } as Record<string, [string, string]>,
        searchLabel: {
            photograph: "फ़ोटो",
            signature: "हस्ताक्षर",
            thumb_impression: "अंगूठे का निशान",
            handwritten_declaration: "हाथ से लिखी घोषणा",
        } as Record<string, string>,
        setBy: (body: string) => `${body} द्वारा तय`,
        answer: "जवाब",
        estimated: "अनुमानित",
        estimatedTitle: "हमारा अनुमान",
        from: "स्रोत:",
        everyRule: "सारे नियम विस्तार से (अंग्रेज़ी में)",
        relatedTitle: "और परीक्षाओं के लिए भी आवेदन कर रहे हैं?",
        relatedPhoto: "फ़ोटो",
        relatedAll: (count: number) => `इस वर्ग की सभी ${count} परीक्षाएँ`,
    },
} as const;
