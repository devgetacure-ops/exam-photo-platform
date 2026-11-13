# Same Night, Twice — the ExamUploadKit launch film

A 1:45 film for LinkedIn, built in code with Remotion so every frame uses the product's own
type, colours and real screens. 4:5 (1080×1350) master; 9:16 and 16:9 cuts come from the same scenes.

```
npm ci
npm run studio      # scrub and preview in the browser
npm run render      # out/launch-film-4x5.mp4
node scripts/stills.mjs 40 900 1400   # review frames into out/stills
node scripts/capture.cjs              # re-capture the live site's screens
node scripts/capture-clean.cjs        # full pages with the sticky bars split off
```

## Structure (30 fps)

| Act | Frames | Time | What happens |
|---|---|---|---|
| 1 · Night one | 0–900 | 0:00–0:30 | Rejection in macro → 11:14 PM → generic tools → 80% face → signature → filename → 2:40 AM → the unopened book |
| 2 · Rewind + wall | 900–1320 | 0:30–0:44 | Clock unwinds, cold turns warm → "Same night. Again." → phone search → wall of exams → push into JEE (Main) |
| 3 · Night two | 1320–2520 | 0:44–1:24 | Real JEE page on a phone → every file at once → one-take across the table (face, white background, KB dial, filename, signature, PDFs) → before/after → sealed kit → laptop → stamps → 11:19 PM |
| 4 · Payoff | 2520–3120 | 1:24–1:44 | The book opens, night to dawn → wordmark, English then Hindi, the other scripts, URL |

## What is real

- Every product screen is a capture of examuploadkit.com (`public/ui/`), not a mock.
- Exam names and the files each one asks for are counted from `examples/rules/`.
- JEE (Main) figures (413 × 531 px, 10–200 KB, 80% face coverage, 6 files) come from its rule record.
- The filename follows the engine's own pattern (`jee-main_photo.jpg`).

## Inputs still to arrive

### 1. The candidate's photograph (one generated image)

Put it at `public/photo/source.jpg`. It is run through the real engine to make
`public/photo/prepared.jpg`, so the before/after in the film is the product's actual output.
Until it exists, a drawn stand-in plays in every scene.

### 2. Voice-over → `public/audio/vo/`

### 3. Music → `public/audio/music.mp3`

See the brief given in chat; the audio is laid in once the files land.
