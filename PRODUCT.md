# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Indian examination candidates preparing an online application, at the moment
they hit the upload step. **No segment boundary** — school entrance, higher
education and government recruitment are all served. Where attention has to be
prioritised, it goes to the examinations with the largest candidate volume.

The catalogue's present weight: 76 of 132 examinations are government
recruitment (Staff Selection Commission, Railway Recruitment Boards, UPSC,
IBPS, state public service commissions), 16 higher education, 5 school
entrance.

The situation is specific and shapes everything: a deadline, often the last
day, on a mid-range Android phone over mobile data. The candidate is not
browsing. They have a portal open in another tab that has just rejected a file.

The job: get every file an application demands into the exact shape that
application accepts — dimensions, byte size, format, background, filename —
without learning what any of those mean.

A candidate applies to several examinations in one season, so **the design
should invite return** without introducing accounts. No login, no server-side
identity.

## Product Purpose

The application is not one photograph. Across the researched set it is roughly
48 signature items, 44 photographs, 15 thumb impressions, 13 handwritten
declarations and 40 certificate or identity scans. Today a candidate assembles
these across several free tools, each solving one part and undoing another.

The product replaces that with one place that already knows what the
examination asks for. Success is a candidate who uploads once, pays ₹3, and
does not return to the portal a second time because a file was refused.

## Positioning

**The examination's own published rules drive the machine, not a generic
preset.** A rule record per examination — 132 of them, 418 requirements — is
read at build time and drives crop, matte, background, resize, compression and
filename. A neighbouring tool cannot truthfully copy this without doing the
same research and encoding it.

The second half is what the product refuses to do. It will not assert a
specification an authority never published; those values are marked as ours.
It will not claim a check it does not perform. That restraint is the position,
because the competing free tools tell a candidate their file is ready when it
is not.

## Operating Context

- The candidate arrives from search, usually naming one examination.
- Every examination page and rules page is generated at build time, so search
  and specifications work with the processing service switched off. Search is
  the primary acquisition channel and this is why.
- Preparation takes about ten seconds per photograph on a warm service.
- The candidate reviews a watermarked, half-resolution preview before paying.
  The clean file never reaches the browser before payment.
- Payment is Razorpay, at a price the server computes. No amount comes from
  the browser.
- Files are deleted **within 30 minutes, or within an hour if the candidate
  asks us to keep them**. The warning must appear before checkout, because an
  extension can only be taken before the deadline passes.
- Delivery is download or email. **WhatsApp carries a link, never the file.**

## Capabilities and Constraints

**Prepares:** photographs (crop, matte, background, size, compress, name),
signatures, thumb impressions, handwritten declarations, certificate and ID
scans, and multi-page PDF assembly — adding, reordering, omitting and rotating
pages.

**Catalogue:** 132 examinations, 418 requirements. 314 supported, 29
guidance-only, 3 partially supported, 72 not yet supported. **80 records carry
no photograph specification at all** and are served for a signature or
certificates alone.

**Four support states, never collapsed to a boolean:** `supported`,
`partially_supported`, `guidance_only`, `not_yet_supported`.
`partially_supported` means a file was produced that still needs something the
platform cannot do, and must never read as success.

**Pricing:** ₹3 for one chargeable image, ₹5 for two, ₹8 as a total ceiling
covering everything an examination asks for. Displayed against struck prices of
₹4, ₹8 and ₹10. PDF and document work is included free **only within a paid
image order** — a documents-only kit cannot check out. *Open: the engine still
prices a documents-only kit at zero, so this is enforced in the interface and
not yet on the server.*

**Cannot do, and must not be claimed:**
- Serve a photograph for an examination that captures it live through its own
  portal.
- Convert an existing PDF into an image. *Open: requested, not yet decided.*
- Detect sunglasses, head coverings, closed eyes or a beard line. These were
  built, measured, found not to separate, and removed.
- Run on GPUs. **Inference is CPU-only.** Any copy claiming otherwise is false.

**Language:** English only at present. Hindi, Odia, Bengali, the South Indian
languages, Punjabi, Gujarati and Marathi are planned, so anything durable must
survive a script change.

**Identity:** the candidate is anonymous. No account, no name collected, and
generated filenames carry no personal information. *Open: three examinations
(TNPSC ×2, Kerala PSC) require a name and date printed onto the photograph,
which would be the first personal data the product handles.*

**Open, not to be invented:** per-examination candidate volume is not in the
catalogue, so "most popular" cannot yet be ranked from data. Whether support is
a private ticket queue or a public forum. The domain, which is not yet bought.

## Brand Commitments

**Name: examuploadkit.** Settled 2026-09-10. No domain registered yet.

No logo, palette, typeface or identity asset exists. All of it is to be created
for this product and approved by the owner. Earlier documents referred to the
product as "UploadReady"; that name is superseded.

A quality contract borrowed from an unrelated product appears in historical
documents. Nothing from it — no branding, copy, scope or claim — is part of
this product, and its references have been removed.

**Voice, confirmed by what already ships and is to be preserved:** plain,
specific, and unwilling to overstate. *"You prepare for the exam. We'll prepare
the files."* Where the platform does not know something, it says so.

## Evidence on Hand

- **132 rule records** at `examples/rules/`, each with provenance and, where it
  exists, an official source URL.
- **Per-examination derived facts** at `examples/rules/candidate_facts.json`,
  covering all 132 — generated from the records, never authored.
- **63 interim placeholder values across 32 examinations**, marked
  `interim_default` and surfaced to the candidate as `est.` A redesign that
  drops that marker turns an honest disclosure into a silent claim.
- **A citable rejection source:** SSC's 2022 Ladakh selection-post notice,
  which lists unclear photographs and illegible signatures among rejection
  conditions.

**Absences that must not be filled with invention:**

- **There is no reliable public figure for how many candidates are disqualified
  for non-compliant uploads.** It was searched for and not found. No such
  statistic may be published.
- No customers, testimonials, case studies, press or usage numbers exist.
- The committed portrait examples have provenance that does not match the
  image. They are to be replaced with newly generated assets whose origin is
  documented. Real candidate photographs may never be used.

## Product Principles

1. **The boundary is carried three ways and never reduced to two.** Grouping,
   colour, and affordance — a requirement the platform does not prepare has no
   upload control at all. The worst failure this product can have is a
   candidate believing we prepared something we did not.
2. **Every claim carries evidence or does not appear.** This applies to
   marketing exactly as it applies to the catalogue.
3. **Produce, never refuse for appearance.** Only an undecodable file, no
   detectable face, or a genuinely ambiguous subject may block. To a candidate,
   a refusal and a silent failure are the same outcome.
4. **The candidate stays anonymous by default**, and any change to that is a
   product decision taken deliberately, not a convenience.
5. **The deadline outranks elegance.** The user is on a slow phone on mobile
   data with a portal open in another tab. Anything that costs them time is
   worse than anything that costs us polish.

## Accessibility & Inclusion

- Reduced motion must be honoured; motion is never the only carrier of meaning.
- Colour is one of three boundary signals and never the only one.
- Keyboard operation for every control, including the before/after comparison
  and page reordering.
- The interface must survive a script change to Devanagari, Bangla, Odia,
  Gurmukhi, Gujarati, Tamil, Telugu, Kannada and Malayalam without relayout
  failure.
- Target hardware is a mid-range Android phone on mobile data, not a laptop on
  broadband.
