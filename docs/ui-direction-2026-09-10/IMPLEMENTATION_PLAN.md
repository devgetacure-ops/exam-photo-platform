# Implementation plan — the brief, sentence by sentence

**Written 11 September 2026**, after the owner resent the second half of the brief
because it was being treated as themes rather than a specification. Each line
below is a requirement from `ORIGINAL_VERBATIM.txt`, the surface it lands on, and
its state. Nothing is marked done until it is built, looked at at real
resolution, and run through the detector.

States: **todo** · **building** · **done** · **blocked** (with the reason).

**Last updated 11 September 2026** — landing page and footer rebuilt and verified;
missing-examination page and request form rebuilt and verified; support and the three
policies rebuilt and verified; the exam page, purchase flow, error states, directory
and rules page rebuilt and verified; PDF to image and page rotation added to the
document tools.

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
| Animations, micro-animations, interactivity | `Reveal`, stroke draw-on, the before-and-after band | done — reveal, stroke draw-on, hover ticks, and a band that drags itself: a photograph and a signature side by side, each sweeping on its own and cycling the owner's examples, with dots to choose one, one Pause control, and a first drag that hands the handle over. Still under prefers-reduced-motion and while off screen. Examples are representational and say so |
| The story of the problem crores of students face | problem section | done — with the brief's point 5 as a ledger of what a free tool calls "ready" and leaves out: sizing, the file limit and the name; face coverage; flagging a bad photograph; the prompt it expects you to write |
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
| Every piece of exam information, well structured | `exam/[examId]` | done — hero (who sets it, what it asks for, the files we prepare, live capture), the kit and its price, one panel per file; source citations on `/rules`, rebuilt in the same language (file cards with all five support states kept distinct, appearance verdicts, sources stated as strongly as the record allows) |
| Every component justifies its use, position and existence | exam page | building — the checkout panel under the kit is still the previous design, rebuilt with the purchase flow |
| Rules shown with visual references — what to do and what not to | requirement panel | done — a drawn specimen sheet per file; every "don't" is either ruled out by this examination's record or something the engine checks every upload for |
| Research how exams present visual examples and adapt that style | requirement panel | done — SSC's captioned sheet of photographs not acceptable, and the banking notices' capitals rule set beside the signature, adapted as drawings rather than photographs of strangers |
| Photo, signature, documents: each curated for itself, one shared language | per-type panels | done — one frame (name, what we do, measurements, upload, specimens), with each file's own intro, specimens and drop zone |
| Full kit price vs single-file price, shown | kit list | done — the price moves on the server's ladder as files are ticked, with the struck price and what the whole kit costs |
| Push the kit at each step; advertise its benefits | kit list, panel, review | done — "Add the other N for ₹X more" on the price card, a price bar on phones, "Add it to the kit" on an unticked file, an Add button on every row that ticks the file and carries the candidate down to it, and a step at the foot of each file offering the next file that is in the kit and still waiting — or, when none are, review and pay |
| One photo plus PDFs is Rs 3 (from Rs 4) | quote | done — server-computed |
| Show the value: without us, they collect these across several sites | exam page | done — the separate tools this application's files would need, read from its own record |
| PDF to image, image to PDF, rearrange, remove, merge — shown as free | document tools | done — image to PDF, merge, reorder, rotate (newly given its button; the engine already supported it) and remove, plus PDF to image in the candidate's own browser with pdf.js: 100/150/200 dpi, JPEG or PNG, nothing uploaded, and the cost to a certificate's verifiability stated beside it. Each failure has the retry that fits it: a password-protected PDF is turned away with a direction to upload a copy without a password (the same check runs before any PDF is uploaded, and no password is ever asked for), a page that can't be drawn keeps the pages before it and retries from that page, a converter that didn't load tries again, and a damaged file is not offered a retry that can't work. DEC-052 amended. The work has its own page at `/pdf` — the browser-side converter usable before anyone pays, every job a form asks of a PDF, and what we don't do (no OCR, no password removal, no editing inside a PDF, no Word or Excel) — linked from the header, the footer and the pricing block |
| Attention to minute detail | everywhere | building |
| Visual interaction while a process runs | preparation | done — the candidate's own photograph sharpens and regains its colour with the engine's real progress, the frame's edge fills, and the steps tick as the engine reports them (DEC-075); honest when progress can't be read |
| Kit pre-selected; the candidate unchecks; price follows | kit list | done |
| Exam tips and facts: special, attention-getting, not the main subject, the centre of interest | exam page | done — pinned beside the title in the hero, each fact in the source's wording with the source a tap away. Facts that only restate a measurement the page already prints in full (file size, format, dimensions) are dropped where the facts are read. It moves on by itself at the owner's instruction, and stops on hover, on focus, under a reduced-motion preference and on its own pause control, which WCAG 2.2.2 makes compulsory rather than optional |

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


## The owner's eighteen desktop notes — 12 September 2026

Given one at a time against screenshots, with instructions to ingest them all
before acting. Everything below is on the desktop view; the phone build is
parked at the owner's word until this is settled.

| # | The note | What was done |
|---|---|---|
| 1 | The PDF tiles are uneven | Seven jobs became six ("pages in the right order" and "a page left out" are one job), and the grid is capped at three columns so no row is short |
| 2 | Negative space between two blocks on /pdf | The seam has one owner: the lede closes tight and the section below opens it |
| 3 | The arrows between the five steps are unaligned | Arrows gone. A single ruled track with a node per step, the one step that is ours picked out in the signal colour |
| 4 | Put examination buttons in the empty space | Eight hand-picked shortcuts under the hero, each a real catalogue id; any id that leaves the catalogue drops out at build rather than shipping as a dead link. It is not called a popularity ranking, because there is no traffic to rank |
| 5 | Photograph and signature side by side, in one screen | One band, two comparison frames, equal in everything but the aspect each file has |
| 6 | Impersonate real browser tabs | A drawn window: tab strip, address bar on a page still loading, and the paragraph inside it as that page. Background tabs drop their close button before their name, as a real strip does. The address is invented — naming a real tool here would be a swipe at somebody's product |
| 7 | This section is barren land | The six frames are a measured sheet now: a datum line, a dimension line on each frame, and a title block. Equal area rather than equal scale, and the block says so |
| 8 | Make the ₹5 tile playful on hover | The tile lifts and presses, its file glyphs rise in sequence, and the old price strikes itself through |
| 9 | The principles section is ordinary | Each of the four refusals performs itself: a wand passes over a face that does not change, a blank fills with est. rather than a number, an upload closes instead of pretending, a sheet is swept clean. Every one reads at rest as well as in motion |
| 10 | The arrow pointers everywhere are ruining it | Every drawn arrow is gone. Notes are margin marks against a signal rule; where direction is genuinely needed there is one small chevron |
| 11, 15 | Remove the rectangle inside the search bar | The frame carries focus itself; the global focus ring no longer draws a second box inside the first |
| 12 | Logo hard left, options hard right, fixed, and the search moves up into it | The bar runs the full width and stays. On the landing page and the directory the search appears only once the page's own has scrolled away, and is out of the tab order before that. Opening it drops a full-width panel with the predictive list; slash opens it from anywhere that is not a text field |
| 13 | Worth knowing should not restate rules, and should scroll itself | Both done. The owner's own facts file replaces the generated one when it arrives; nothing in the reader assumes the generated wording |
| 14 | An Add button on every item in the kit | Every row has one. It ticks the file if it was unticked and takes the candidate to its panel — the reason it exists is that clicking a row changed something off screen |
| 16 | Next should appear only when there is one, and end in review and pay | A pure function decides: only from a file that is in the kit, only to a file that is in the kit and still waiting, and review and pay when none are. Tested on its own |
| 17 | The three options are stuck to the section | Air on both sides of the rule above them |
| 18 | The exam page's bar search should size to the name, and lose "Change exam" | The control is sized to what it holds, so a long examination name sets its width. "Change exam" is gone from the bar and from the foot of the kit: the bar is how you change exam |

Verified: lint, types and 165 frontend tests pass; the production build generates
415 pages; the landing, examination, directory and PDF pages were screenshotted at
1024, 1280 and 1440 and read; the design detector reports no new finding on the
examination, directory or PDF pages.

One detector complaint on the landing page is a false positive worth writing down
rather than chasing: the six frames sit on the drafting grid, which is a repeating
gradient over a background colour, and the detector's analytic path cannot
composite the two — it reports 1.6:1 for text measured at 10.2:1 from the rendered
pixels. The eight low-contrast findings on that section are all this, and three of
them predate this work.

## The owner's second round of desktop notes — 12 September 2026

Same drill: screenshots one at a time, ingest all of them before acting.

| The note | What was done |
|---|---|
| The rectangle inside the search bar is still there | It always was. The Tailwind utility meant to suppress the focus ring could never win: utilities are layered CSS and unlayered CSS beats a layer whatever the specificity says, so the site's own `:focus-visible` rule kept drawing. The exemption is written where that rule lives, named, and the frame carries focus alone |
| The bar's search acts like a button that opens another search | It is a field now. Type in the bar, the predictive list drops out of the bar. The picker's behaviour moved into one hook and one results component so the page's search and the bar's cannot drift apart |
| Enlarge the bar's search, with good spacing | It takes the middle of the bar with clear air either side — 125px → 434px at 1024. The lockup wears smaller cells in the bar, and the three text links stand down below 1280px where the search is worth more than a jump to a section of the same page |
| The scroll choreography crops "Six tabs" | The bar and that headline were both made sticky in the same session with two unreconciled numbers, so the headline pinned behind the bar. One measured token, `--bar`, is now the only number: the anchor scroll-padding and all five sticky blocks read it. Four of the five had the same fault and nobody had reported them yet |
| Move the shortcuts down, and add more exams | Eighteen, every id checked against the catalogue, wrapping to two even rows of nine, starting 133px clear of the search |
| Large negative space beside the before/after band | The representational-examples note sits beside the frames instead of below them, which fills the empty column and takes a screen's worth of height out of the section |
| Large negative space on the PDF page | The head is two columns: headline and lede left, the two ways in — free in your browser, free with a prepared file — right, stated at the top instead of discovered two sections down. The earlier attempt at this seam wrote `.euk-section:first-of-type`, which asks for an element that is both `.euk-section` and the first `<section>` sibling; the first one is the head, which carries no such class, so the rule had matched nothing at all. The converter now opens above the fold |

**And the thing that came out of it.** Searching "CGL" returned nothing, in
every search on the site, because 117 of the 135 research records carried no
aliases. 337 short forms were added to the research sidecar and encoded into
the catalogue by the usual run; every one is tested to bring back its own
examination. DEC-080.
