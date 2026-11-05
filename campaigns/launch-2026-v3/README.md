# ExamUploadKit launch campaign v3

This is the production-ready launch system that replaces the earlier single-hero direction.

## Creative idea

The three pinned Instagram carousels read as **EXAM / UPLOAD / KIT** on the profile grid. The exact authorised logo artwork supplies those three cover excerpts. Inside each carousel, every slide has a separate job and a distinct composition:

The approved cover direction is **Dark / Controlled Light**: restrained frosted depth, one concealed colour source, cool ambient light and a quiet utility footer. Every cover includes `EXAMUPLOADKIT.COM`, an eight-slide progress cue and `SWIPE →` without competing with the logo.

- **EXAM** explains the problem: examination rules differ, generic resizing misses the specification, and the complete application kit matters.
- **UPLOAD** explains the journey: find the exam, see what it asks for, keep the files needed, preview the work, and download it.
- **KIT** explains the deliverables: photograph, signature, thumb impression, declaration, certificates, PDF work, pricing, and privacy.

The platform-overview decks use current product screens captured from the live website on 2 October 2026. They present the interface as evidence rather than decoration.

## Deliverables

- `exports/instagram/pinned/` — three 8-slide carousels, 1080 x 1350
- `exports/instagram/product-overview/` — eleven slides, 1080 x 1350
- `exports/linkedin/product-overview/` — eleven slides, 1200 x 1500
- `exports/reddit/product-overview/` — eight slides, 1080 x 1080
- `exports/x/product-overview/` — four images, 1600 x 900
- `exports/reviews/` — contact sheets and the three-cover profile preview
- `copy.md` — platform-specific post copy
- `slide-purpose.md` — internal claim and evidence map
- `source-ui/` — dated live-product captures used in the overview decks

The LinkedIn document carousel is exported separately at `output/pdf/examuploadkit-linkedin-product-overview.pdf`.

## Publishing order

Instagram displays newly pinned posts from newest to oldest. Publish **KIT**, then **UPLOAD**, then **EXAM**, and pin all three so the final visible row reads **EXAM / UPLOAD / KIT** from left to right. Confirm the order on the profile before promoting the launch.

## Accuracy boundary

The interface captures are from the live public product and contain no candidate data. The before-and-after photograph and signature examples come from the website's disclosed representational assets. They show the intended service treatment and are not presented as proof of a live candidate result. ExamUploadKit prepares supported files; the candidate reviews them and submits the official application, and the examination portal remains the final authority.

## Rebuild and verification

From the repository root:

```powershell
node campaigns/launch-2026-v3/scripts/final-cover-directions.mjs
node campaigns/launch-2026-v3/scripts/render-v3.mjs
node campaigns/launch-2026-v3/scripts/verify-v3.mjs
python campaigns/launch-2026-v3/scripts/build-linkedin-pdf.py
```

The current build contains 58 final PNG exports. Desktop product walkthroughs use a consistent viewport; mobile views appear only on the installable-application slide. The before-payment prepared preview carries a watermark; the KIT photograph example uses the clean disclosed prepared image. Dimension, source, file-size, viewport-policy, watermark-policy, and duplicate checks pass. The eleven-page LinkedIn PDF has also been rendered and visually inspected.
