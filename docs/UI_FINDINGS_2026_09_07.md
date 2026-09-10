# Session findings: what the rebuild exposed

> **Superseded, 10 September 2026.** Most findings here were fixed the same
> day (see `docs/ui-direction-2026-09-10/`). Kept as the record of what the
> rebuild exposed, not as a current defect list. Finding 7 (strike-through
> prices) is withdrawn — the owner has since specified them.

**Date**: 2026-09-07 · Branch `feat/upload-kit-ui` · Production build, served
with `next start -p 3007`, viewed at 1440 desktop and 390 mobile.

The build is green: **270 pages, 132 exams + 132 rules pages**. The stale
52-page figure in the QA notes is gone. Everything below was found by looking
at the running site, not by reading code.

Ordered by severity. Items 1–3 are correctness, not taste, and should not wait
behind a redesign.

---

## 1. Four shipped features are declared absent to the candidate

Not stale notes — the live copy actively tells the candidate these do not
exist. This is a false statement in the honest direction, which is unusual and
still wrong.

| Feature | Shipped | What the UI says |
|---|---|---|
| Lighting toggle | DEC-074, DEC-076 | `requirement-upload.tsx:295-310` — checkbox hardcoded `disabled` / `checked={false}`, copy reads *"Coming soon… The adjustment control is not available yet."* |
| Instant variant switch | DEC-076 | Not wired. `POST /v1/jobs/{id}/enhancement` unused |
| Staged progress | DEC-075 | `preparation-loader.tsx` is an indeterminate spinner with an elapsed-seconds counter. No `progress_token`, no `GET /v1/progress/{token}` |
| Email delivery | DEC-072 | `kit-checkout.tsx:619` — *"Email delivery is not available yet."* `POST /v1/kits/{id}/email` unused |
| Per-exam facts | DEC-077, DEC-078 | `candidate_facts.json` holds **132 exams** of derived facts. The web app does not reference the file anywhere |

## 2. 261 of 264 static pages are unreachable

The catalogue is generated at build time because **SEO is the primary channel**
(WEB-003). That reason is currently defeated:

- The homepage links to **3** exam pages (IBPS PO, NEET UG, GATE).
- There is **no exam index route**. Build output lists only `/`, `/_not-found`,
  `/admin`, `/admin/rules`, `/exam/[examId]`, `/exam/[examId]/rules`.
- **No `sitemap.xml`** (404), **no `robots.txt`** (404).
- Search is client-side and capped at **7** results
  (`exam-search.tsx:140`, written when the catalogue was 39–52).

So 261 pages have no inbound link and no sitemap entry. A crawler cannot find
them. This is the largest measurable gap on the site and it is not a design
question.

The same cap is the picker problem DEC-079 created: 132 examinations, 7
visible results, and no way to browse.

## 3. A machine token renders to the candidate

`/exam/all-india-sainik-schools-entrance-examination`, photograph panel:

> We can't prepare this file yet
> **not_found**

The raw enum is printed verbatim. It appears wherever a `not_yet_supported`
requirement carries that reason — which is now **72 requirements**.

## 4. The `est.` legend counts markers the page does not render

On the 80 no-photograph rules pages the legend reads:

> *est.* marks a figure this exam has not published, where we chose a sensible
> value. **There are 7 on this page.**

The record does carry 7 `interim_default` values. The page renders **zero**
`est.` markers and zero specifications — verified against the served HTML. A
candidate is told seven values on the page are our estimates and cannot find
one.

This is the estimate-marker invariant failing inside the new DEC-079 empty
state: the disclosure is honest in intent and false as displayed.

## 5. The no-photograph rules page is photograph-shaped

Same 80 pages. The `<title>` is *"… photo rules — what they accept and
reject"*, and the body contains only an appearance-rules disclaimer and a
provenance card. **Nothing about the signature, thumb impression or
certificates the platform can actually prepare** — the three requirements are
not named on the page at all.

The brief called this "degrades to empty, which is correct and looks like a
hole." It is worse than a hole: it is a page about the one thing this
examination does not have.

## 6. Kit numbering reads as a missing item

Same page, workspace: *"We prepare these"* is numbered **2, 3, 4** and *"You do
these yourself"* is numbered **1**. The numbers are catalogue positions, not
kit positions, so the prepared group starts at 2 and the candidate looks for a
missing first file.

The boundary itself is intact — grouping, colour and affordance all present,
and the unsupported photograph correctly has no upload control.

## 7. Pricing shows a strikethrough anchor the product never charged

`₹3` struck through `₹4`; `₹5` through `₹8`; `₹8` through `₹10`. DEC-070 sets
the prices at ₹3 / ₹5 / ₹8. A struck-through price asserts a former price. If
there was never a ₹4, this is an unevidenced claim on a page whose whole
argument is that we do not make unevidenced claims.

## 8. The static hero contradicts the state beneath it

Every exam workspace opens *"A good photo. A simpler application."* — including
the ones where the photograph is the single thing we cannot prepare.

## 9. Mobile is a reflow

Confirmed by eye at 390px: same section order, same content, stacked. **6,283px
of scroll** on the landing page. The owner asked for mobile as a separate
design.

---

## On the level, which is the actual brief

The landing page is 4,737px of the **same two-column split repeated seven
times**: eyebrow, two-line heading, paragraph on the left; a card or list on
the right. Seven section headings at effectively one size. One accent colour on
white, three pale-blue bands for variety. One illustration, used three times.

It is tasteful and it is a template. The previous session's own plan said
*"evolve the existing Clear Companion direction"* and that is exactly what
shipped. Nothing here is wrong; nothing here is chosen.

The direction proposed to fix it is in
[`UI_DIRECTION_RECOMMENDATION_2026_09_07.md`](UI_DIRECTION_RECOMMENDATION_2026_09_07.md).

---

## Still open, and not this session's to decide

`apps/web/public/examples/portrait-*.jpg` — shipping on all 52 photograph exam
pages as the "Good lighting" specimen and both "Avoid these" examples.
Provenance text describes an older European GAN asset; the shipping image is of
an Indian-looking person. Needs the owner's answer before merge.

---

## Note on tooling

The browser pane does not repaint after a programmatic or input scroll on this
page — screenshots come back as stale or blank frames. Verified it is a capture
artifact, not a site defect (`getComputedStyle` reports `opacity: 1` and
`elementFromPoint` hits the right section throughout). Workaround: set the
viewport tall enough to hold the document and capture without scrolling.
