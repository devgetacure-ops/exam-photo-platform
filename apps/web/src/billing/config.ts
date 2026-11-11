/**
 * The one switch for every paid mechanism on the site (DEC-127).
 *
 * Off by default: ExamUploadKit is free and paid for by advertising. Set
 * `NEXT_PUBLIC_BILLING=on` at build time, together with the engine's
 * `EXAM_PHOTO_BILLING=on`, to bring back pricing, the watermark, checkout,
 * coupons and paid reviews. See `README.md` in this folder.
 */
export const BILLING_ENABLED = process.env.NEXT_PUBLIC_BILLING === "on";
