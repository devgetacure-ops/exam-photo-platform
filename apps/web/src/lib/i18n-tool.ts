import type { Locale } from "./i18n";

/**
 * Hindi for the fixed sentences the preparation tool builds from records
 * (DEC-129): specimen captions, appearance guidance and spec labels. Keyed
 * by the exact English, so a sentence nobody has translated falls back to
 * English rather than to nothing. Wording quoted from a notice is never
 * translated: it stays as the authority wrote it.
 */

const HI: Record<string, string> = {
    // Specimen captions
    "Straight on, eyes open, the whole face visible": "सीधे कैमरे की ओर, आँखें खुली, पूरा चेहरा दिखे",
    "A cap or hat": "टोपी या हैट",
    "Dark glasses": "काला चश्मा",
    Spectacles: "चश्मा",
    "Glare hiding the eyes": "चमक से आँखें छिपी हों",
    "A face mask": "फ़ेस मास्क",
    "Shadow across the face": "चेहरे पर छाया",
    "Turned from the camera": "कैमरे से मुँह मोड़ा हुआ",
    "Eyes closed": "आँखें बंद",
    "Taken too far away": "बहुत दूर से खींची गई",
    "Top of the head cut off": "सिर का ऊपरी हिस्सा कटा हुआ",
    Blurred: "धुंधली",
    "Too dark": "बहुत अँधेरी",
    "Your full signature, black ink, white paper": "आपका पूरा हस्ताक्षर, काली स्याही, सफ़ेद काग़ज़",
    "Your full signature, dark ink, plain paper": "आपका पूरा हस्ताक्षर, गहरी स्याही, सादा काग़ज़",
    "In capital letters": "कैपिटल (बड़े) अक्षरों में",
    "Strokes cut off at the edge": "किनारे पर कटी लकीरें",
    "Pencil, or ink too faint": "पेंसिल, या बहुत हल्की स्याही",
    "The whole impression, ridges clear": "पूरा निशान, रेखाएँ साफ़",
    "Smudged or blotted": "फैला हुआ या धब्बेदार",
    "The whole page, written clearly": "पूरा पन्ना, साफ़ लिखा हुआ",
    "Page cut off at the edges": "किनारों से कटा पन्ना",
    "Every page whole and readable": "हर पन्ना पूरा और पढ़ने लायक",
    "Corners cut off, or shot at an angle": "कोने कटे हुए, या तिरछे से खींचा गया",

    // Appearance guidance titles
    "Caps and head coverings": "टोपी और सिर ढकना",
    "Face masks": "फ़ेस मास्क",
    Expression: "चेहरे का भाव",
    "How recent": "कितनी नई",
    "Printed on the photograph": "फ़ोटो पर छपा हुआ",
    "Text on the photograph": "फ़ोटो पर लिखावट",
    "Signature on the photograph": "फ़ोटो पर हस्ताक्षर",
    Colour: "रंग",
    Eyes: "आँखें",
    Pose: "मुद्रा",

    // Appearance guidance details we write (not the notice's own words)
    "Glasses are allowed, but reflections must not hide your eyes.": "चश्मा चल सकता है, पर उसकी चमक से आँखें नहीं छिपनी चाहिए।",
    "Your face must be fully visible.": "आपका पूरा चेहरा दिखना चाहिए।",
    "Your face must be uncovered.": "आपका चेहरा ढका नहीं होना चाहिए।",
    "Your face must be visible.": "आपका चेहरा दिखना चाहिए।",
    "Smiling is fine.": "मुस्कुराना ठीक है।",
    "Keep a natural expression.": "चेहरे का भाव सामान्य रखें।",
    "No name, date or watermark printed on the image.": "फ़ोटो पर नाम, तारीख़ या वॉटरमार्क छपा नहीं होना चाहिए।",
    "This exam wants your full signature on the bottom part of the photograph. We cannot add that — you will need to before you upload.":
        "यह परीक्षा फ़ोटो के निचले हिस्से पर आपका पूरा हस्ताक्षर माँगती है। यह हम नहीं जोड़ सकते, अपलोड से पहले आपको जोड़ना होगा।",
    "A colour photograph — black and white will not be accepted.": "रंगीन फ़ोटो, ब्लैक एंड व्हाइट स्वीकार नहीं होगी।",
    "Both eyes open and clearly visible.": "दोनों आँखें खुली और साफ़ दिखें।",
    "Face the camera straight on — no side or three-quarter angle.": "कैमरे की ओर सीधे देखें, बगल या तिरछे कोण से नहीं।",

    // What the engine reports (lib/finding-text.ts)
    "Removed hidden camera data, such as location and phone model.": "कैमरे का छिपा डेटा हटाया, जैसे जगह और फ़ोन का मॉडल।",
    "Converted the colour mode for the exam's format.": "परीक्षा के फ़ॉर्मेट के लिए रंग का मोड बदला।",
    "Replaced a broken colour profile.": "ख़राब कलर प्रोफ़ाइल बदली।",
    "Corrected the image's rotation.": "फ़ोटो का घुमाव ठीक किया।",
    "Matched the file's extension to its real format.": "फ़ाइल का एक्सटेंशन उसके असली फ़ॉर्मेट से मिलाया।",
    "We couldn't frame a photo from this one. The head may be cut off, too small in the picture, or too close to an edge.":
        "इस फ़ोटो से सही फ़्रेम नहीं बन सका। हो सकता है सिर कटा हो, फ़ोटो में बहुत छोटा हो, या किनारे के बहुत पास हो।",
    "We couldn't separate you cleanly from the background in this photo.": "इस फ़ोटो में आपको बैकग्राउंड से साफ़ अलग नहीं कर सके।",
    "We couldn't open this file. Upload a JPEG, PNG or WebP photo.": "यह फ़ाइल खुल नहीं सकी। JPEG, PNG या WebP फ़ोटो अपलोड करें।",
    "We could not find a face in this photo.": "इस फ़ोटो में चेहरा नहीं मिला।",
    "There is more than one face in this photo.": "इस फ़ोटो में एक से ज़्यादा चेहरे हैं।",
    "The photo is too blurry to use.": "फ़ोटो इतनी धुंधली है कि काम नहीं आएगी।",
    "The photo is too dark.": "फ़ोटो बहुत अँधेरी है।",
    "The photo is too bright.": "फ़ोटो बहुत ज़्यादा चमकीली है।",
    "The eyes look closed.": "आँखें बंद लग रही हैं।",
    "The face is too small in the frame. Use a photo taken closer.": "फ़्रेम में चेहरा बहुत छोटा है। पास से खींची फ़ोटो लें।",
    "The photo is too small to prepare. Use the original from the camera, not a screenshot or a forwarded copy.":
        "फ़ोटो तैयार करने के लिए बहुत छोटी है। कैमरे की असली फ़ोटो लें, स्क्रीनशॉट या फ़ॉरवर्ड की हुई कॉपी नहीं।",
    "The photo is slightly blurred.": "फ़ोटो थोड़ी धुंधली है।",
    "The photo is a little dark.": "फ़ोटो थोड़ी अँधेरी है।",
    "The photo is a little bright.": "फ़ोटो थोड़ी ज़्यादा चमकीली है।",
    "The face is turned too far from the camera.": "चेहरा कैमरे से बहुत ज़्यादा मुड़ा हुआ है।",
    "The face is turned slightly from the camera.": "चेहरा कैमरे से थोड़ा मुड़ा हुआ है।",
    "The top of the head is cut off.": "सिर का ऊपरी हिस्सा कटा हुआ है।",
    "The side of the head is cut off.": "सिर का बगल वाला हिस्सा कटा हुआ है।",
    "The chin is cut off.": "ठोड़ी कटी हुई है।",
    "The eyes are not clearly visible.": "आँखें साफ़ नहीं दिख रहीं।",
    "Something is covering part of the face.": "चेहरे का कुछ हिस्सा किसी चीज़ से ढका है।",
    "This PDF is password-protected, so we can’t open it. Upload a copy of the PDF without a password.":
        "यह PDF पासवर्ड से बंद है, इसलिए खुल नहीं सकती। बिना पासवर्ड वाली PDF अपलोड करें।",
    "This looks like a photograph, not a signature. Sign on plain white paper and take a photo of just the signature.":
        "यह हस्ताक्षर नहीं, फ़ोटो लग रही है। सादे सफ़ेद काग़ज़ पर हस्ताक्षर करें और सिर्फ़ हस्ताक्षर की फ़ोटो लें।",
    "This looks like a photograph, not a thumb impression. Press your thumb on plain white paper and take a photo of just the impression.":
        "यह अंगूठे का निशान नहीं, फ़ोटो लग रही है। सादे सफ़ेद काग़ज़ पर अंगूठा लगाएँ और सिर्फ़ निशान की फ़ोटो लें।",
    "We need exactly one face in the photo.": "फ़ोटो में ठीक एक चेहरा होना चाहिए।",
    "Even at its smallest, this file is over the examination's size limit.": "सबसे छोटा करने पर भी यह फ़ाइल परीक्षा की साइज़ सीमा से बड़ी है।",
    "We couldn't size this file exactly to the examination's dimensions.": "यह फ़ाइल परीक्षा के बताए आकार में ठीक नहीं बैठ सकी।",
    "This examination's record needs fixing on our side. Please tell us.": "इस परीक्षा की जानकारी हमारी तरफ़ से ठीक करनी है। कृपया हमें बताएँ।",
    "Something went wrong while preparing this file. Please try again.": "फ़ाइल तैयार करते समय कुछ गड़बड़ हुई। फिर से कोशिश करें।",
    "Something in this file stopped us preparing it. Please try another.": "इस फ़ाइल में कुछ ऐसा है जिससे यह तैयार नहीं हो सकी। दूसरी फ़ाइल आज़माएँ।",
    "Take a new photo facing the camera, with your whole head and shoulders in the picture and some space above your head, in daylight against a plain wall.":
        "कैमरे की ओर देखते हुए नई फ़ोटो लें, पूरा सिर और कंधे फ़ोटो में हों, सिर के ऊपर थोड़ी जगह हो, दिन की रोशनी में सादी दीवार के सामने।",

    // Spec labels
    Dimensions: "आकार (पिक्सेल)",
    "File size": "फ़ाइल साइज़",
    Format: "फ़ॉर्मेट",
    Background: "बैकग्राउंड",
};

/** A fixed tool sentence in the reader's language; English if no translation exists. */
export function toolText(locale: Locale, english: string): string {
    if (locale === "en") return english;
    const exact = HI[english];
    if (exact) return exact;
    const recency = /^Taken within the last (\d+) days — about (\d+) months?\.$/.exec(english);
    if (recency) return `पिछले ${recency[1]} दिनों के अंदर खींची गई, लगभग ${recency[2]} महीने।`;
    return english;
}
