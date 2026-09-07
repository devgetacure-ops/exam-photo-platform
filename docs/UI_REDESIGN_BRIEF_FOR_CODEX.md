# UI/UX redesign — engine contract and constraints

Hand this to Codex alongside the product owner's design brief. **The design
brief is the ambition; this is what the engine will and will not give you, and
the handful of things that would quietly break the product or cost real money
if they were got wrong.** Nothing here argues with the design direction.

---

## 0. First, before anything else

**Rebuild the site.** The catalogue is read at build time and it changed today:
**52 examinations, not 39**, plus 52 rules pages. BPSC was withdrawn and its
page must disappear — the authority photographs candidates through a web
camera, so we never had a photograph to prepare for it. Until the rebuild runs,
the live site and the catalogue disagree.

**Your lane is unchanged**: `apps/web/src/app/**`, `apps/web/src/components/**`,
`globals.css`. `apps/web/src/lib/types.ts` and `api-client.ts` are the shared
contract — edit them as a request to the engine lane, and say so.

## 1. Three things that lose money or trust if they are got wrong

**a. The Razorpay order must carry `job_id` or `kit_id` in its `notes`.**

The payment webhook is built and live-tested. It verifies Razorpay's signature
and releases exactly the files the order's notes name:

- `notes: {"kit_id": "kit_abc"}` releases every live file in that kit — the
  bundle case.
- `notes: {"job_id": "job_xyz"}` releases one file. A comma-separated list
  works too.

**A verified payment naming neither takes the candidate's money and delivers
nothing.** The engine answers `no_targets` and logs it loudly, and there is no
recovery — it cannot guess which files a payment was for. This is the single
most expensive thing on this page.

**b. Do not compute the price in the browser.**

Prices are Rs 3 / Rs 5 / Rs 8. A price the browser decides is a price a
candidate can edit. The engine will expose an order-creation endpoint that
computes the amount server-side; call that and pass its `order_id` to Razorpay
Checkout. Until that endpoint exists, keep payment on **test keys**.

**c. After checkout, poll `GET /v1/jobs/{job_id}`.**

`entitlement` flips from `"preview_only"` to `"released"` when the webhook
lands. That is how the UI learns the download is available. There is
deliberately no route that releases a job from the browser.

## 2. The boundary that must survive the redesign

The product's worst failure mode is a candidate believing we prepared something
we did not — a live-capture photograph, a portal declaration, a document only
they can produce.

That boundary is currently carried **three ways at once**: grouping ("We
prepare these" / "You do these yourself"), colour, and **affordance** — a
requirement we do not prepare has no upload control at all. **Removing any one
of the three puts the failure mode back on the table.** A redesign may express
all three differently. It may not reduce them to two.

Related: `platform_support` has four values —`supported`,
`partially_supported`, `guidance_only`, `not_yet_supported` — and they are
deliberately never collapsed into a boolean. `partially_supported` means we
produce a file that still needs something we cannot do (printing a name or date
onto the photograph, for TNPSC and Kerala PSC). Do not render it as success.

## 3. What the engine serves today

| You need | Endpoint / field | Notes |
|---|---|---|
| Exam list and specs | build-time, `lib/catalogue.server.ts` | 52 exams, works with the engine switched off |
| Prepare a file | `POST /v1/exams/{exam}/requirements/{req}/prepare` | **Blocks ~10 s.** See §4 |
| Watermarked preview | `preview_url`, `preview_watermarked` | Half resolution, mark burned into pixels |
| Clean file | `GET /v1/jobs/{id}/output` | **402 until paid** |
| Job state | `GET /v1/jobs/{id}` | carries `entitlement`, `expires_at`, `extendable` |
| Kit checklist | `GET /v1/kits/{id}/package` | readable before payment; the ZIP is gated |
| Extend retention | `POST /v1/jobs/{id}/extend` | see §5 |
| Service state | `GET /ready` | `payments`, `purchase_gate`, `matting_backend` |

**The before/after slider (design item 7) works client-side.** Compare the file
the candidate just uploaded, which the browser already has, against
`preview_url`. **Do not expect a clean "after" before payment** — the preview is
half resolution with a watermark burned in, and that is the whole purchase gate.
If you want an ungated before/after for the landing page, use a synthetic pair
we author, never a candidate's photograph.

**A PDF deliverable has no preview at all.** `preview_url` is null and
`preview_watermarked` is false, honestly, because rasterising a PDF page needs a
library this repository deliberately does not carry. A candidate currently buys
a certificate scan unseen. Design for that state rather than assuming an image.

## 4. Live progress (design item 13) — not yet available, and being built

Preparation currently **blocks for about 10 seconds and returns the finished
job**. There is no progress stream, so a loader that claims percentages today
would be inventing them.

The engine lane is adding staged progress so the ring can be real. **Design the
interaction now, but drive it from real events when they land, not from a
timer.** A progress bar that is secretly a `setTimeout` is the kind of detail
that makes a premium interface feel fake the first time the network is slow.

The honest interim is an indeterminate state with real stage *names* — the
engine already reports stage timings — rather than a fabricated percentage.

## 5. Retention: the wording is a promise, not copy

Files are deleted **30 minutes** after preparation. This is enforced, not
asserted: access ends at the deadline itself and the artifacts are erased.

A candidate may extend once, to a ceiling of **one hour from preparation**, via
`POST /v1/jobs/{id}/extend`. `extendable` on the job status says whether another
extension would buy anything, so the button can be hidden before it starts
refusing.

**So the published wording is "deleted within 30 minutes, or within an hour if
you ask us to keep it" — not a flat 30 minutes.** Writing the flat version
beside a button that extends to sixty is exactly the mismatch we spent a
decision closing.

**The warning must come before checkout**, and this is not a nicety: an
extension can only be taken *before* the deadline, so a candidate who is never
told the file expires will never extend it and will meet expiry as a 404 on a
download they paid for.

## 6. Claims — the same evidence bar as the rest of the product

The design brief asks for real facts about candidates disqualified for
non-compliant uploads. **Every statistic must carry a source the reader can
check, or must not appear.** We reject values in our own examination data when
only coaching sites publish them; publishing an unsourced number on the landing
page would hold our marketing to a lower standard than our rule records.

Two specifics:

- **Do not claim GPUs.** The service runs CPU-only inference today. "Compute
  cost" is fine and true; "our GPUs" is not.
- **Do not claim we detect what we do not.** We do not detect sunglasses, head
  coverings, closed eyes or a beard line — those signals were built, measured,
  found not to separate, and removed. We *do* check face count, face coverage,
  blur, exposure and geometry, and we flag rather than silently pass.

What is honestly ours to claim, and strong: the exam's own published rules drive
every output; the file is renamed as the portal expects; size and format are met
exactly; and we say when something is wrong instead of returning a crop and
calling it done.

## 7. Reject-gallery and example imagery

**Real candidate photographs may never ship.** Examples must be synthetic,
drawn, or commissioned.

`apps/web/public/examples/portrait-*.jpg` are photorealistic portraits of an
identifiable-looking person and are now committed to the repository. Your own
handoff calls them fictional guidance assets. **Confirm and record how they were
produced before this branch merges** — an untracked file is deleted, a committed
one has to be rewritten out of history.

## 8. Scope notes

- **Mobile is a separate design**, per the product owner — not a responsive
  reflow of the desktop composition.
- `upload-card.tsx`, `result-preview.tsx`, `validation-report.tsx` and
  `processing-status.tsx` survive from the pre-pivot flow and are unused by the
  candidate path. Fold in what is useful or delete them.
- Keep every piece of information the current pages carry — published rejection
  conditions, source citations, the "platform estimate" marker on figures we
  chose rather than read. **The estimate marker especially**: 63 values across
  32 examinations are still ours rather than the authority's, and a redesign
  that drops the marker turns an honest disclosure into a silent claim.

## 9. Coming from the engine lane, so design for it

- **Intelligent lighting adjustment** with a candidate-facing toggle, decided
  **before** payment and applied to what they buy. The engine will expose it on
  the prepare call and report what it changed. Design the toggle and the
  explanation of what it does; the model is ours.
- **Per-exam facts** for the carousel, as a researched, sourced field on the
  examination record — not hand-written strings in the front end, for the same
  reason the rules are not hand-written.
- **Email delivery.** The `wa.me` share link is yours and needs nothing from us;
  emailing the file is ours.
- **Server-side order creation**, as in §1b.

Ask before assuming any of these exist. If a design depends on one, say which,
and it moves up the queue.
