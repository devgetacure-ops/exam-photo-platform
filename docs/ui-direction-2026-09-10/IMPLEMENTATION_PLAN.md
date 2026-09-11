# Implementation plan — the brief, sentence by sentence

**Written 11 September 2026**, after the owner resent the second half of the brief
because it was being treated as themes rather than a specification. Each line
below is a requirement from `ORIGINAL_VERBATIM.txt`, the surface it lands on, and
its state. Nothing is marked done until it is built, looked at at real
resolution, and run through the detector.

States: **todo** · **building** · **done** · **blocked** (with the reason).

**Last updated 11 September 2026** — landing page and footer rebuilt and verified;
missing-examination page and request form rebuilt and verified; support and the three
policies rebuilt and verified.

## Standards that apply everywhere

| Requirement | How it is held | State |
|---|---|---|
| Premium, no AI-slop | impeccable `detect` clean on every surface before it is called done | building |
| No lag at high volume | motion on transform/opacity/stroke only; one shared IntersectionObserver; no animation library; inline SVG, no image requests for doodles | done — reveals arm only off-screen blocks after script runs; nothing hidden without JS |
| No section labels, decorative labels or numbering | detector's `kicker-above-heading` rule is a hard gate | done on the landing page; other surfaces pending |
| Typography is the most unique thing | Big Shoulders (display), Anek Latin (text), Petrona italic (pointing only) — as approved from direction E | done |
| Copywriting connects instantly, never confuses | every block of copy run through `slopmonster` before commit | building — landing copy lints 5/5; rival-model cleanse blocked, local Codex CLI is missing its win32 binary |
| Every click has a welcoming effect | press compresses the element into its shadow; hover lifts it out; reduced motion removes both | building |
| Everything has a purpose; nothing dummy or decorative-only | a visual that carries no information does not ship | building |

## Landing page

| Requirement | Surface | State |
|---|---|---|
| Centre-aligned hero | `app/page.tsx` | done |
| Big search bar in the hero | `ExamSearch` | done |
| Bold heading that tells the whole story | hero | done |
| Search any exam; if absent, a dedicated page saying we are working on it | `/exam-request` | done — an empty search hands over to it (link, and Enter); the page answers three ways: already here under that name, already on the list with the catalogue's own reason, or not here yet. What happens after you ask is told with no promised date |
| That page takes the exam name and an email to notify | `request-form` | done — exam name carried from the search, email, optional notice link; designed sending, error (fields kept, focus moved to the message) and receipt (reference, copy, stamp) states. Submissions had been refused 403 whenever the server's own host differed from the address bar; the origin check now compares the host the browser addressed |
| Scroll reveals, in order: what we do | landing | done |
| — how we do it | landing | done |
| — what problem we solve | landing | done |
| — why we built it | landing | done |
| — pricing | landing | done |
| — our story | landing | done — told as the product's principles; a founder account needs the owner's words |
| Editorial, not AI-slop; copy that connects | landing | done — slopmonster 5/5 |
| Doodles, graphics, illustrations, drawings | inline SVG, drawn in the system's ink | done — each drawing is a file the product prepares |
| Animations, micro-animations, interactivity | `Reveal`, stroke draw-on, the comparison | done — reveal, stroke draw-on, the comparison, hover ticks |
| The story of the problem crores of students face | problem section | done |
| Rs 3 against years of preparation | why / pricing | done |
| Footer that is not industry-standard | the back of the form: declaration, signature, date, enclosures | done — the back of the form |

## Legal and support

| Requirement | Surface | State |
|---|---|---|
| Privacy policy | `/privacy` | done — redesigned: the three policies a strip apart, sections listed and kept in view on desktop, 17px text at a 66ch measure, ends on a way to ask. Needs business facts |
| Terms and conditions | `/terms` | done — as privacy. Needs business facts |
| Refund policy | `/refund-policy` | done — as privacy; asks for the payment reference a candidate can actually find, since no screen shows our order id. Needs business facts |
| Support, redressal and request forum for queries, issues, grievances | `/support` | done — every known problem answered in public (payment confirming, failed payment, double charge, deleted files, rejected file, rules that don't match a notice, missing email, missing examination, deletion), a private request with a reference for a case of one's own, and a grievance route. See OWNER_DECISIONS C10. Needs a named grievance officer from the owner |

## Exam page

| Requirement | Surface | State |
|---|---|---|
| Every piece of exam information, well structured | `exam/[examId]` | done — hero (who sets it, what it asks for, the files we prepare, live capture), the kit and its price, one panel per file; source citations stay on `/rules` |
| Every component justifies its use, position and existence | exam page | building — the checkout panel under the kit is still the previous design, rebuilt with the purchase flow |
| Rules shown with visual references — what to do and what not to | requirement panel | done — a drawn specimen sheet per file; every "don't" is either ruled out by this examination's record or something the engine checks every upload for |
| Research how exams present visual examples and adapt that style | requirement panel | done — SSC's captioned sheet of photographs not acceptable, and the banking notices' capitals rule set beside the signature, adapted as drawings rather than photographs of strangers |
| Photo, signature, documents: each curated for itself, one shared language | per-type panels | done — one frame (name, what we do, measurements, upload, specimens), with each file's own intro, specimens and drop zone |
| Full kit price vs single-file price, shown | kit list | done — the price moves on the server's ladder as files are ticked, with the struck price and what the whole kit costs |
| Push the kit at each step; advertise its benefits | kit list, panel, review | building — "Add the other N for ₹X more" on the price card, a price bar on phones, "Add it to the kit" on an unticked file; the review step comes with the purchase flow |
| One photo plus PDFs is Rs 3 (from Rs 4) | quote | done — server-computed |
| Show the value: without us, they collect these across several sites | exam page | done — the separate tools this application's files would need, read from its own record |
| PDF to image, image to PDF, rearrange, remove, merge — shown as free | document tools | building — image to PDF, merge, reorder and remove are shown free with the kit; PDF to image still needs the browser-side rasteriser, see note |
| Attention to minute detail | everywhere | building |
| Visual interaction while a process runs | preparation | done — the candidate's own photograph sharpens and regains its colour with the engine's real progress, the frame's edge fills, and the steps tick as the engine reports them (DEC-075); honest when progress can't be read |
| Kit pre-selected; the candidate unchecks; price follows | kit list | done |
| Exam tips and facts: special, attention-getting, not the main subject, the centre of interest | exam page | done — pinned beside the title in the hero, each fact in the source's wording with the source a tap away; plays only when asked |

## Purchase flow

| Requirement | Surface | State |
|---|---|---|
| Review before ordering: all details, email, WhatsApp, deletion warning | review | done — every file with its state and findings, a live deletion clock that turns urgent under five minutes, email delivery that can be set up before paying and sends on release, the server's quote with the struck price and free documents, and the acknowledgement. WhatsApp is stated honestly: it carries a reminder link, not files |
| Payment sequence: creative, playful, animated, with exam tips during it | checkout | done — while Razorpay's window is open and while payment confirms, a rubber stamp presses PAID onto the form, with this examination's facts rotating beside it and a Pause for both. Nothing is released until the server confirms |
| Success: creative, animated, warm, good wishes, downloads, expiry warning, the details | success | done — an admit card settles, ALL THE BEST is stamped on it and a tick writes itself; "We've prepared the files. Now it's your exam." Then the clock, downloads and the ZIP, email, a WhatsApp reminder, and the receipt (examination, files, amount, order reference) |
| Designed error states with visuals and copy that make them feel handled | errors, failed payment, other issues | done — failed payment, quote unavailable, expired files, email failure and a quote that no longer matches the review each have their own state. The 404 leads with the exam search; a failed page says the kit is untouched and gives a support reference; a failed root layout brings its own document and styles. Each has its own drawing, drawn once |

## Notes that change what gets built

**PDF to image.** The engine deliberately does not rasterise PDFs (DEC-052), and the
one rasteriser it could have used is AGPL. The brief asks for it again, and the
owner has standing authority over prior decisions. It is buildable without the
engine: `pdf.js` (Apache 2.0) renders pages to images in the candidate's own
browser. DEC-052 is scoped to what the engine returns as a prepared file for a PDF
requirement; a tool the candidate invokes on their own document is a different
thing, and DEC-052 will be amended to say so. `pdf.js` loads only on the tool, so it
costs nothing on any other page.

**WhatsApp.** A `wa.me` link carries text, not files. The review and success pages
offer email delivery of the files and WhatsApp as a way to send the link back to
yourself. They will not say the files go over WhatsApp.

**Our story.** No founder story has been supplied, and one will not be invented. The
section tells the true story of why the product is built the way it is, and marks
the place a real founder account would go.
