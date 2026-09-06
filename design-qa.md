# Design QA — option 3 exam upload workspace

## Reference and test state

- Source: `C:\Users\dmbar\.codex\generated_images\01a071ed-e323-7cf3-a15f-8da0ee53b1a6\exec-1f0ee6a7-46d4-44d5-8845-e8e5598934d2.png`
- Source dimensions: 1536 × 1024 composite board containing desktop 1440 × 1024 and mobile 390 × 844 targets.
- Prototype route: `http://localhost:3000/exam/ibps-crp-po-mt-xvi`
- Captures: `design-qa-desktop.png` at 1440 × 1024 and `design-qa-mobile.png` at 390 × 844, device scale 1.
- State: light theme, empty six-requirement kit, first photograph requirement selected, no active upload.

## Fidelity surfaces checked

- Global shell: white restrained header, pale blue task surface and persistent desktop price bar.
- Hierarchy: exam context and promise at the start, kit progress on the left, visual guidance in the centre, authoritative rules and upload action on the right.
- Mobile re-composition: compact header, tappable requirement progress, image-first guidance, rejection examples, then upload and price controls.
- Typography, colour, border, radius and spacing remain token-based in `globals.css`; motion respects reduced-motion preferences.
- The source mock's illustrative four-item kit was reconciled with the real six-item catalogue. Its invented specifications were replaced by current catalogue rules instead of being copied as product facts.

## Comparison history

### Pass 1

The source and initial implementation were viewed together. The visible differences worth correcting were:

- Mobile exposed too much requirement copy before the visual guidance.
- The two rejected photograph examples did not depict the same fictional person as the accepted example.
- Desktop pricing could fall below the first viewport.
- The desktop promise lacked the reference's strong left-hand anchor.
- The requirement panel showed technical specifications without enough concise appearance guidance.

Corrections applied: mobile became image-first; a consistent fictional portrait set was generated; desktop pricing was fixed to the viewport; the promise was moved to the left composition; and four real catalogue appearance rules were surfaced before specifications.

### Pass 2

The reference, desktop capture and mobile capture were viewed together again at the target sizes. The page now preserves the selected reference's quiet three-column desktop composition and intentionally different mobile task order. No P0, P1 or P2 visual defect remains.

Accepted P3 differences:

- The production page shows the real examination name and six real requirements rather than the mock's shortened labels.
- The supplied project has no authorised brand logo or complete icon set, so the UI uses a restrained text wordmark and existing interface symbols without inventing a logo asset.
- The live-capture notice is retained through progressive disclosure because it is required product guidance.

## Interaction and implementation QA

- Predictive search accepts `IBPS PO` and routes to the correct examination.
- Mobile requirement progress switches to signature guidance and back to photograph guidance.
- Report issue opens as a labelled native dialog and closes from keyboard-accessible controls.
- Visual example controls are semantic buttons with pressed state; upload controls retain labels and 44px-class touch targets.
- Browser console check found no application errors. Earlier LCP warnings were addressed by prioritising the initial portrait image.
- Protected previews render only when the API supplies both a preview URL and `preview_watermarked: true`; clean output is never used as a visual fallback.

final result: passed
