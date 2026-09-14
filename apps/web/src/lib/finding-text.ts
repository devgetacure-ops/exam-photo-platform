/**
 * Everything the engine reports about a file, said the way a person would say
 * it -- and never as a code (the owner's testing notes 15, 17 and 19).
 *
 * Three kinds of line arrive:
 *
 * - **Routine changes** the engine made to an ordinary upload: hidden camera
 *   data removed, a colour mode converted. Nothing is wrong, so they are never
 *   a finding and never earn a badge; they are listed quietly under "What we
 *   changed". Newer jobs report them in `changes`; older kits still carry them
 *   among `findings`, which is why they are recognised here too.
 * - **Issue codes** (uppercase with underscores), which get a sentence from
 *   the table below, or a plain generic one. A code is never shown.
 * - **Sentences** the engine already wrote for the candidate, passed through.
 */

export const ROUTINE_NOTES: Readonly<Record<string, string>> = {
    INPUT_METADATA_REMOVED: "Removed hidden camera data, such as location and phone model.",
    INPUT_COLOUR_MODE_CONVERTED: "Converted the colour mode for the exam's format.",
    INPUT_ICC_PROFILE_INVALID: "Replaced a broken colour profile.",
    INPUT_ORIENTATION_METADATA_INVALID: "Corrected the image's rotation.",
    INPUT_EXTENSION_MISMATCH: "Matched the file's extension to its real format.",
};

/** Codes that are about the file but already said, in words, by a finding. */
const SAID_ELSEWHERE = new Set(["PIPELINE_FINAL_BYTE_SIZE_BELOW_MINIMUM"]);

const FRAMING =
    "We couldn't frame a photo from this one. The head may be cut off, too small in the picture, or too close to an edge.";
const SEPARATING = "We couldn't separate you cleanly from the background in this photo.";
const UNREADABLE = "We couldn't open this file. Upload a JPEG, PNG or WebP photo.";

export const ISSUE_TEXT: Readonly<Record<string, string>> = {
    NO_FACE_DETECTED: "We could not find a face in this photo.",
    MULTIPLE_FACES: "There is more than one face in this photo.",
    IMAGE_TOO_BLURRY: "The photo is too blurry to use.",
    IMAGE_TOO_DARK: "The photo is too dark.",
    IMAGE_TOO_BRIGHT: "The photo is too bright.",
    EYES_CLOSED: "The eyes look closed.",
    SUITABILITY_NO_FACE: "We could not find a face in this photo.",
    SUITABILITY_MULTIPLE_FACES: "There is more than one face in this photo.",
    SUITABILITY_FACE_REGION_TOO_SMALL: "The face is too small in the frame. Use a photo taken closer.",
    SUITABILITY_RESOLUTION_TOO_LOW:
        "The photo is too small to prepare. Use the original from the camera, not a screenshot or a forwarded copy.",
    SUITABILITY_BLUR_SEVERE: "The photo is too blurry to use.",
    SUITABILITY_BLUR_WARNING: "The photo is slightly blurred.",
    SUITABILITY_UNDEREXPOSED_SEVERE: "The photo is too dark.",
    SUITABILITY_UNDEREXPOSED_WARNING: "The photo is a little dark.",
    SUITABILITY_OVEREXPOSED_SEVERE: "The photo is too bright.",
    SUITABILITY_OVEREXPOSED_WARNING: "The photo is a little bright.",
    SUITABILITY_POSE_EXTREME: "The face is turned too far from the camera.",
    SUITABILITY_POSE_WARNING: "The face is turned slightly from the camera.",
    SUITABILITY_HEAD_TOP_CLIPPED: "The top of the head is cut off.",
    SUITABILITY_HEAD_SIDE_CLIPPED: "The side of the head is cut off.",
    SUITABILITY_CHIN_CLIPPED: "The chin is cut off.",
    SUITABILITY_EYES_NOT_VISIBLE: "The eyes are not clearly visible.",
    SUITABILITY_FACE_OCCLUDED: "Something is covering part of the face.",
    PDF_PASSWORD_PROTECTED:
        "This PDF is password-protected, so we can’t open it. Upload a copy of the PDF without a password.",
    PIPELINE_CROP_FAILED: FRAMING,
    PIPELINE_CROP_MODE_UNSUPPORTED: FRAMING,
    PIPELINE_FACE_COUNT_INVALID: "We need exactly one face in the photo.",
    PIPELINE_HEAD_ESTIMATION_FAILED: FRAMING,
    PIPELINE_SEGMENTATION_FAILED: SEPARATING,
    PIPELINE_MASK_REFINEMENT_FAILED: SEPARATING,
    PIPELINE_BACKGROUND_FAILED: SEPARATING,
    PIPELINE_FINAL_BYTE_SIZE_INVALID:
        "Even at its smallest, this file is over the examination's size limit.",
    PIPELINE_FINAL_DIMENSIONS_INVALID: "We couldn't size this file exactly to the examination's dimensions.",
    PIPELINE_INPUT_INVALID: UNREADABLE,
    PIPELINE_RULE_INVALID: "This examination's record needs fixing on our side. Please tell us.",
    PIPELINE_ERROR: "Something went wrong while preparing this file. Please try again.",
    DELIVERABLE_PREPARATION_ERROR: UNREADABLE,
};

const GENERIC = "Something in this file stopped us preparing it. Please try another.";
const CODE = /^[A-Z][A-Z0-9_]+$/;

export function isRoutine(line: string): boolean {
    return line in ROUTINE_NOTES;
}

/** The sentence for an issue code; never the code itself. */
export function issueText(code: string): string {
    return ISSUE_TEXT[code] ?? GENERIC;
}

/**
 * What a candidate should read for one reported line, or null when it is a
 * routine change or already said by another line.
 */
export function plainFinding(line: string): string | null {
    if (isRoutine(line) || SAID_ELSEWHERE.has(line)) return null;
    if (CODE.test(line)) return issueText(line);
    return line;
}

/** The lines worth attention, in plain words, without repeats. */
export function plainFindings(lines: readonly string[]): string[] {
    const out: string[] = [];
    for (const line of lines) {
        const text = plainFinding(line);
        if (text && !out.includes(text)) out.push(text);
    }
    return out;
}

/** What to tell a candidate whose photograph could not be prepared. */
export const RETAKE_GUIDANCE =
    "Take a new photo facing the camera, with your whole head and shoulders in the picture and some space above your head, in daylight against a plain wall.";
