# Platform State

**Last updated: 2026-09-04.** Branch `feat/upload-kit-ui`, merged up to date
with `main` (which carries the ONNX matting backend, DEC-054). The kit API is
built (DEC-055..058), and so is the read half of the web app: a candidate can
search 39 examinations and see everything each one asks for, on statically
generated pages. Not yet pushed.

**The next session is payment and delivery.** Upload and preparation are
built and verified against the running engine; what is missing is Razorpay,
the watermark, and getting the file to the candidate. Start at
*[Where to start: the web app](#where-to-start-the-web-app)*.

What this file is: the state a new session cannot reconstruct from the diff.
Not a session note — keep it current rather than appending to it. It has drifted
into a chronology twice; if you find yourself writing "then X, then Y", rewrite
the section as what is true now.

Read alongside:

| File | What it carries |
|---|---|
| `AGENTS.md` | The binding operating contract |
| `docs/08_DECISION_LOG.md` | DEC-029..058. **Living** — amend an entry when implementation moves; never bend implementation to fit a stale one |
| `HANDOFF-INVARIANTS.md` | How composition work is done here: the invariant sweep, the ratchet, the planner/validator defect class |
| `docs/EXAM_RULE_GAP_REGISTER.md` | Generated. Which examinations are encoded, which are not, and why |

---

## What this product is

**Exam-first application upload preparation.** A candidate picks an
examination, sees every file that examination requires, provides the source
material, and receives the ones the platform can prepare.

It is no longer a photograph tool. The photograph is roughly a quarter of what
an application asks for: across the researched set there are ~48 signature
items, 44 photographs, 15 thumb impressions, 13 handwritten declarations and
~40 certificate or identity scans.

Two source documents drive the pivot — a product-direction report and a
48-examination deliverables report, both dated 2026-08-05. The deliverables
report is committed at
`packages/exam-rules/research/indian_exam_registration_deliverables_report_2026.md`;
the product-direction report is held outside the repository.

## What works, end to end

The engine is essentially complete for the deliverable types below. Give it an
upload and a requirement, get back a compliant file.

| Deliverable | Treatment | Notes |
|---|---|---|
| Photograph | Face pipeline | Crop, matte, background, size, compress, name |
| Signature | Ink `MARK` | Page cleared around the strokes, ink deepened |
| Thumb impression | Ink `IMPRESSION` | Lighting corrected, cropped, **not** masked |
| Handwritten declaration | Ink `PAGE` | The whole sheet, never cropped to its writing |
| Certificate / ID scan | Ink `PAGE` + PDF | Image→PDF, or an existing PDF restructured |
| Multi-page document | `pdf/document.py` | Add pages, reorder, rotate, omit, repeat |

**Catalogue: 39 examinations, 155 requirements.** 135 supported, 16
guidance-only (live capture and portal declarations — correctly never ours), 2
partially supported (need a name/date printed on the photograph, which the
engine cannot render), 2 not yet supported.

**86 interim placeholder values** are in the catalogue, all marked
`interim_default` in provenance. They are signature and thumb-impression sizes
and formats, plus a 400 KB certificate ceiling set by the product owner. When
real per-exam research lands, `type == interim_default` finds every one.

## Where to start: the web app

**The read half of the product is built.** A candidate can find their
examination and see everything it asks for. What is missing is the half that
takes money and produces files.

Two architectural facts a new session must not re-derive:

**The catalogue is read at BUILD time, not over the API.** `lib/catalogue.server.ts`
reads `examples/rules/` from disk and every exam page is statically generated —
39 of them. This is deliberate (WEB-003): the pricing strategy makes SEO the
primary channel, and a page whose content arrives by client-side `fetch` is an
empty document to a crawler. It also means search and specifications work with
the processing service switched off. `api-client.ts` is for *preparing* files,
which is the one thing that cannot be precomputed. Re-running the encoder
requires a rebuild to show up.

**The boundary is carried three ways, not one.** Grouping ("We prepare these" /
"You do these yourself"), colour, and affordance — a requirement the platform
does not prepare has no upload control at all. Removing any one of the three
puts the product's worst failure mode back on the table.

### Built

| Piece | Where |
|---|---|
| Design tokens, both themes | `src/app/globals.css` — semantic colours are deliberately not the accent |
| Landing page — the search **is** the page | `src/app/page.tsx`, `components/exam-search.tsx` — one screen, focused on arrival |
| Exam workspace, 39 static pages | `src/app/exam/[examId]/page.tsx` + `components/exam/kit-workspace.tsx` — fixed file list left, one file's detail right |
| Rules & sources, 39 more pages | `src/app/exam/[examId]/rules/page.tsx` — reference split off the workspace |
| Real accepted/rejected examples | `scripts/generate_guidance_examples.py` → `public/examples/` |
| Specification rendering | `lib/spec-format.ts` — published figures over our byte conversion; `est.` marks a value we chose |
| Photograph rules per exam | `lib/appearance-rules.ts` — spectacles, headwear, expression, imprint, from the record only |
| Honest citation | `components/exam/source-note.tsx` — 7 of 39 exams have no official source |
| Published rejection conditions | `scripts/encode_exam_rules.py` routes them (DEC-059); shown per requirement, attributed to the exam |
| Upload and preparation | `components/exam/requirement-upload.tsx` — client island, records the job against the kit |
| Three outcome states | `components/exam/outcome-result.tsx` — clean / with-findings / blocked |

### Not built, in order

1. **The watermark.** `outcome-result.tsx` already tells the candidate the
   preview is watermarked, and **it is not** — the service returns the clean
   file. Either watermark server-side at reduced resolution before payment, or
   change the copy. Do not ship the current pairing.
2. **Payment.** Razorpay, decided. The ordering is already right: preparation
   happens first and the candidate decides against the real result.
3. **Delivery.** Download, email, and a `wa.me` share link — the candidate
   sends it themselves, which needs no WhatsApp Business integration and routes
   no candidate photograph through Meta.
4. **Multi-page documents** via `planDocument` → arrange → `assembleDocument`.
5. **The package.** Nothing calls `getKitPackage` yet, so there is no ZIP and
   no checklist at the end. The rail's price button is a placeholder.
6. **Mobile.** Explicitly out of scope as a responsive pass — the product owner
   wants a separate design for it, not a reflow of this one. The workspace is
   built for desktop and its two-pane grid assumes that.

`upload-card.tsx`, `result-preview.tsx`, `validation-report.tsx` and
`processing-status.tsx` still survive from the pre-pivot flow, now unused by
the candidate path. Fold in what is useful or delete them.

### Running it locally

The catalogue is build-time, so `npm run dev` needs nothing else. Preparing a
file needs the engine, **and the engine ships with browser access off**:

```bash
EXAM_PHOTO_LOCAL_CORS_ENABLED=true .venv/Scripts/python.exe -m exam_photo serve-api --host 127.0.0.1 --port 8000
```

Without it every upload fails as an ordinary network error, because a blocked
cross-origin request and a dead server are the same `TypeError` to a browser.

### Decided, not yet built

- **Identify a session by an unguessable token, never by IP.** Carrier-grade
  NAT on Indian mobile networks puts thousands of candidates behind one address:
  an IP-keyed cache would serve one candidate another's face photograph and
  signature, and would simultaneously lose files for anyone whose IP rotates.
  `kit-state.ts` already mints a `kit_id` for exactly this.
- **No right-click blocking.** It stops nobody and reads as cheap. The
  protection that works is that the clean file never reaches the browser before
  payment; the preview is watermarked server-side at reduced resolution.
- **Reject-gallery examples are synthetic.** Real candidate photographs may
  never ship. The SVG diagrams already cover framing; anything richer is drawn
  or commissioned, never a real candidate.

**The API is done.** `GET /v1/exams`, `GET /v1/exams/{exam_id}`,
`POST /v1/exams/{exam_id}/requirements/{requirement_id}/prepare`, the document
pair (`.../requirements/{id}/documents` then `/v1/documents/{job_id}/assemble`),
and `GET /v1/kits/{kit_id}/package(/download)`. Contracts in `api/contracts.py`,
catalogue reader in `orchestration/rule_catalogue.py`. The support gate returns
409 with the requirement's own vocabulary before the upload is read.

**Not verified locally:** every `mandatory_*` marker suite needs the model
assets and env vars from `image-engine-ci.yml`, and `model-assets/` is empty in
this checkout — so is the ONNX weight the default matting backend now wants.
The one failure in the fast subset
(`test_crop_cli_save_preview_overwrite_protection`) needs the face model for the
same reason and is unrelated to this branch. Fetch the assets before trusting a
local run: `python scripts/download_model.py --variant short_range --yes`,
`python scripts/download_segmenter.py --variant <variant> --yes`, and
`python scripts/export_birefnet_onnx.py` for the ONNX graph.

## What it demonstrably cannot do

State these plainly rather than discovering them again.

- **Serve a live-capture-only examination's photograph.** All four SSC
  examinations photograph the candidate through the portal. Their *signatures*
  are deliverable and currently are not encoded — see the gap register's
  "examinations not encoded that still have deliverables". A rule record
  requires a photograph specification, and that is what blocks them.
- **Print a name or date onto a photograph.** TNPSC and Kerala PSC require it.
  Marked `partially_supported` with the reason, so no caller reads a complete
  success into them.
- **Convert an existing PDF into an image.** Deliberate (DEC-052). Rasterising
  a digitally issued certificate destroys what makes it verifiable.
- **Detect a beard line**, or **sunglasses, head coverings, closed eyes** to a
  publishable standard. Signals were built, measured, found not to separate,
  and removed.
- **Measure a delivered photograph against its own invariants.**
  `check_composition_invariants` has no pipeline consumer. See
  `HANDOFF-INVARIANTS.md`.
- **Write text into a PDF**, or OCR anything. No declaration text comparison —
  ruled out by the owner.

## Rule records are generated, never hand-written

`scripts/encode_exam_rules.py` reads the versioned research in
`packages/exam-rules/research/` and rebuilds the whole catalogue, the gap
register, and `examples/rules/unavailable_examinations.json` — the
machine-readable list of the eleven examinations it could not encode, which the
picker needs so a candidate searching SSC CGL is told the examination exists
rather than shown nothing. It owns every file matching its prefix, so a re-run
replaces rather than adds.

```bash
python scripts/extract_deliverables.py --report packages/exam-rules/research/indian_exam_registration_deliverables_report_2026.md --out packages/exam-rules/research/exam_deliverables_2026.json
python scripts/encode_exam_rules.py --specs packages/exam-rules/research/exam_photo_specs_2026.json --deliverables packages/exam-rules/research/exam_deliverables_2026.json --out examples/rules --report docs/EXAM_RULE_GAP_REGISTER.md
```

**To change a rule, change the evidence and re-run.** Editing
`examples/rules/exam_*.json` by hand works until the next regeneration silently
discards it, and meanwhile the record asserts something no source supports.

## Load-bearing decisions

Undoing one changes what the product is. Undo it deliberately and amend the
decision log rather than quietly.

1. **Produce, never refuse for appearance or composition** (DEC-041). Only an
   undecodable file, no detectable face, or a genuinely ambiguous subject may
   block. A refusal and a silent failure are the same outcome to a candidate.
2. **Absent is not permissive** (DEC-049). A rule the research recorded as
   `not_found` is omitted, never defaulted.
3. **Never distort to hit a target.** Aspect mismatch is padded or refused,
   never stretched. A stretched signature is not the candidate's signature.
4. **One composition for every examination** (DEC-045). No per-exam crop
   profile.
5. **A scan may be re-encoded; a document may not be re-rendered** (DEC-052).
   The single most important rule in the PDF path.
6. **Support is a promise.** `platform_support: supported` requires a
   specification behind it, and a submission method the platform cannot execute
   can never be marked supported. Both enforced in the model.
7. **On paper, correct aggressively; on a face, barely at all** (DEC-043,
   DEC-050). Opposite rules for opposite subjects, in separate packages so
   neither gets "simplified" into the other.

## The recurring failure mode

Recorded because it happened four times in one session and cost real rework.

**Every metric that improves by removing content reads as an improvement.**
Paper got whiter as the thumb impression was destroyed. Ink coverage looked
correct while a finger was rendered across the output. Crop tightness improved
while letters lost their strokes. In each case the numbers being watched stayed
green and only looking at the image caught it.

So: **bring pictures, not numbers.** And before tuning a constant against a new
photograph, add a case to `tests/ink/test_ink_robustness.py` — the reference set
is five photographs and is not a safety net. That sweep has already caught two
defects the reference set could not.

## Open risks, in priority order

1. **Cold start is 100–150 s and nothing warms the process.** onnxruntime pays
   a one-time thread-pool and arena spin-up on its *first* inference in a
   process, then never again (DEC-054). Both segmenters keep their session warm
   across calls, but nothing creates it at boot: there is no `lifespan` or
   startup hook, and `/health` returns `healthy` immediately regardless. So the
   first candidate to reach a fresh worker waits over two minutes, and a load
   balancer has no way to tell a warm process from a cold one. Needs a warmup
   call at boot plus a readiness signal distinct from liveness. Not built,
   because there is no deployment machinery yet to build it against — no
   Dockerfile, no compose file, nothing. **Do this before the first deploy, not
   after.**
2. **Throughput is 10.64 s per photograph**, mean over the ten `perfect`
   photographs at 413×531, warmed (DEC-054, measured 2026-08-06 — it was 21.38 s
   before the ONNX backend). The product owner has taken further speed work as
   their own item — **do not spend engineering effort on it unasked.** The
   remaining obvious target is DEC-040's double matte: BiRefNet runs twice per
   photograph, once whole-frame and once on the crop region, and the first pass
   only feeds crop planning. That is a real quality trade, not free.
3. **Synchronous preparation has a deployment ceiling** (DEC-055). `prepare`
   blocks on the pipeline; nginx defaults to 60 s and Cloudflare cuts at 100 s.
   At 10.64 s plus upload this is no longer close, so the 202-plus-polling
   escape hatch — return a job id and let the client poll `GET /v1/jobs/{id}` —
   is a scale-later decision rather than an urgent one. It stops being
   comfortable if the cold-start warmup above is skipped.
4. **Ten examinations dropped for a photograph reason** while carrying 23
   non-photograph deliverables between them, including all four SSC. Fixing it
   means letting a rule record exist without a photograph specification.
5. **Service hardening and privacy.** The API is local-only by design — no TLS,
   auth or rate limiting — and candidate face photographs are sensitive personal
   data under the DPDP Act. Both precede anything public.
6. **Invariants unwired**, and the remaining **M22 matte defect**: a detached
   hair fragment on photo 17 (a disconnected mask region). Its soft/smudged
   hair-edge half (18, 19, and the non-fragment part of 17) is fixed --
   DEC-033's trusted-alpha path was skipping an anti-halo contrast correction
   the coarse-mask path already had.

## Verifying

`.github/workflows/image-engine-ci.yml` is the source of truth. `pytest` alone
covers neither the eleven `mandatory_*` marker suites nor `ink_robustness`.

```bash
cd services/image-engine && ruff format --check . && ruff check . && .venv/Scripts/python.exe -m mypy src tests
```

Current: format, lint and mypy clean across 142 files. 382 fast tests passing,
15 skipped, and one failing **only for want of a model asset** in a checkout
with an empty `model-assets/` (`test_crop_cli_save_preview_overwrite_protection`
needs the face detector). `ink_robustness` (~100 synthetic captures) green as
its own CI stage. Marker suites green in CI. Invariant sweep 0 violations of 960.

Model assets are under `model-assets/`. Run marker suites from the repo root
with `EXAM_PHOTO_FACE_MODEL_PATH` / `EXAM_PHOTO_SEGMENTER_MODEL_PATH` and their
`*_SHA256` set as the workflow sets them.

## Reference material — local only, never commit

| What | Where |
|---|---|
| Ink-on-paper set (5 images) | `C:\Users\dmbar\Pictures\other-exam-uploads` |
| 40-photo labelled set | `C:\Users\dmbar\Pictures\new-test-images` (ten `perfect`) |
| Reviewed photo outputs | `C:\Users\dmbar\Pictures\Engine Outputs - Clean Set` at 413×531 |

Every constant in `exam_photo.ink` is calibrated against the ink set, with the
measurement recorded beside it. Two gaps are closed by owner ruling rather than
by samples: **a pencil signature is out of scope**, and **a handwritten
declaration is an ordinary photographed sheet** needing no separate sample.

**The 60-photo paired set is retired — do not use it**, and do not run
`scripts/benchmark_reference_pairs.py`, which targets it.

For any composition change: run the ten `perfect` photographs through
`process_rule`, measure head height, above-hair and below-chin on the output,
and diff against the reviewed set. The synthetic sweep alone is not sufficient
— it read zero while a photograph the owner had flagged by eye was visibly
wrong, because synthetic head boxes do not extend past the jaw the way real
ones do.
