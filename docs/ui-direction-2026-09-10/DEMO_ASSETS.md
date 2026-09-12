# The demonstration images

**Recorded 12 September 2026.** What is in `apps/web/public/examples/band/`,
where it came from, and what may be claimed about it.

## What these are

Fourteen files: four photograph pairs (`photo-a1..a4`) and three signature
pairs (`sign-s1..s3`), each an `-uploaded` and a `-prepared` side. They drive
the before-and-after band on the landing page.

**They are generated, and they are representational.** The people do not exist
and the signatures are of invented names. The owner produced them on
12 September 2026 from the prompts in this conversation's record, supplied as
PNGs outside the repository, and confirmed they are to be used as they are.

**They are not engine output.** The `-prepared` side was generated to show what
a good file looks like; it did not come from this platform's pipeline. The band
says so under the frames, in those words, because a demonstration that implies
"our engine produced this" when it did not is the kind of claim this product
does not make. No exam's specification is quoted against them either: they are
not sized, named or compressed to any published rule.

**No candidate's photograph or signature appears anywhere on this site.** The
placeholder images that used to sit in `public/examples/` — `portrait-*.jpg`,
`photo-*.jpg`, `signature-*.jpg`, `hero-*.jpg`, and the two guide PNGs — were
deleted with this change. Their provenance was never confirmed (HANDOFF.md open
risk 8) and nothing referenced them any more. They remain in git history; a
history rewrite is the owner's call and is not needed for anything shipped.

## What was done to them

Nothing but scaling. Each file is the supplied image resized to 720×960
(photographs) or 960×720 (signatures) and saved as JPEG at quality 86. No
cropping, no straightening, no colour work, on either side.

An earlier version of this change cropped the uploaded photographs so the two
faces lined up across the wipe. The owner reversed that on 12 September 2026:
both sides are shown as supplied. The uploaded side is therefore a wide room
shot against a tight head-and-shoulders prepared file, and the partition
crosses between them at different scales — which is what the upload actually
looks like.

## How they are shown

On one sheet, set the way the head of an application form is set: the
photograph box, and beneath it a signature strip of the same width. Side by
side, a tall portrait against a short landscape left the row ragged along the
bottom and the two comparisons arguing with each other.

The sweep runs one way only: it starts on the upload, travels across to the
prepared file, rests there long enough to be read, then dissolves into the next
example and starts again. Running it out and back said "the prepared file
becomes your phone photograph" for half of every cycle, which is the story
backwards. The checks tick from the prepared side for the same reason — they
count what has been fixed, not what is still wrong.

Both frames run it together. Each is otherwise its own: dragging one holds only
that one, and it picks itself up three seconds after the last touch. Each moves
to its next example after every run, so all seven pairs are seen without
anybody clicking. One control pauses and plays both.

The motion cannot be verified from a headless screenshot: virtual time does not
drive `requestAnimationFrame` there, so every capture shows the frame at rest.
`src/tests/wipe-demo.test.tsx` steps the clock by hand instead, and that is
what holds these rules.

## If they are replaced

Keep the same file names, or update `PHOTO_PAIRS` and `SIGNATURE_PAIRS` in
`apps/web/src/app/page.tsx`. Next.js caches optimised images by URL, so a new
file under an old name will not appear until `.next/cache/images` is cleared,
and a running dev server can hold one in memory past that — changing the name,
or the folder, is the reliable move. That is why these live in `band/` and not
the `demo/` they started in. The band takes any number of pairs per kind and
builds its own selector dots.
