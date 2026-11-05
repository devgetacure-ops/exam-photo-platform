# ExamUploadKit launch campaign

This folder contains the working launch campaign and deterministic exports.

## Cover direction

The three pinned Instagram covers use exact excerpts from the authorised
ExamUploadKit logo:

1. `EXAM`
2. `UPLOAD`
3. `KIT`

No letter, grid rule, colour or proportion is redrawn. Each original logo row
is cropped from `apps/web/public/brand/examuploadkit-stacked-light.png`, scaled
uniformly, and centred inside a 1080 x 1350 canvas. The artwork also remains
inside the centred 1080 x 1080 safe square so profile cropping does not remove
any part of the word.

Run the deterministic renderer from the repository root:

```powershell
node campaigns/launch-2026/scripts/render-logo-covers.mjs
```

The publishable PNG files and their provenance manifest are in `exports/`.
