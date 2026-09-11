# Implementation plan — the brief, sentence by sentence

**Written 11 September 2026**, after the owner resent the second half of the brief
because it was being treated as themes rather than a specification. Each line
below is a requirement from `ORIGINAL_VERBATIM.txt`, the surface it lands on, and
its state. Nothing is marked done until it is built, looked at at real
resolution, and run through the detector.

States: **todo** · **building** · **done** · **blocked** (with the reason).

**Last updated 11 September 2026** — landing page and footer rebuilt and verified.

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
| Search any exam; if absent, a dedicated page saying we are working on it | `/exam-request` | todo |
| That page takes the exam name and an email to notify | `request-form` | todo |
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
| Privacy policy | `/privacy` | done — needs business facts |
| Terms and conditions | `/terms` | done — needs business facts |
| Refund policy | `/refund-policy` | done — needs business facts |
| Support, redressal and request forum for queries, issues, grievances | `/support` | todo — built as a private ticket flow; a public forum needs moderation and exposes candidates' own faces and signatures in posts |

## Exam page

| Requirement | Surface | State |
|---|---|---|
| Every piece of exam information, well structured | `exam/[examId]` | building |
| Every component justifies its use, position and existence | exam page | building |
| Rules shown with visual references — what to do and what not to | requirement panel | todo |
| Research how exams present visual examples and adapt that style | requirement panel | todo |
| Photo, signature, documents: each curated for itself, one shared language | per-type panels | todo |
| Full kit price vs single-file price, shown | kit list | todo |
| Push the kit at each step; advertise its benefits | kit list, panel, review | todo |
| One photo plus PDFs is Rs 3 (from Rs 4) | quote | done — server-computed |
| Show the value: without us, they collect these across several sites | exam page | todo |
| PDF to image, image to PDF, rearrange, remove, merge — shown as free | document tools | todo — PDF to image needs a browser-side rasteriser, see note |
| Attention to minute detail | everywhere | building |
| Visual interaction while a process runs | preparation | todo |
| Kit pre-selected; the candidate unchecks; price follows | kit list | done |
| Exam tips and facts: special, attention-getting, not the main subject, the centre of interest | exam page | todo |

## Purchase flow

| Requirement | Surface | State |
|---|---|---|
| Review before ordering: all details, email, WhatsApp, deletion warning | review | todo |
| Payment sequence: creative, playful, animated, with exam tips during it | checkout | todo — built around Razorpay's sheet, which is theirs, and over the real verification wait |
| Success: creative, animated, warm, good wishes, downloads, expiry warning, the details | success | todo |
| Designed error states with visuals and copy that make them feel handled | errors, failed payment, other issues | todo |

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
