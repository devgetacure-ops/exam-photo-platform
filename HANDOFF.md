### Testing the engine locally

`model-assets/` is gitignored, so a fresh clone starts empty and every
`mandatory_*` suite skips silently. **Fetch all four, and both segmenter
variants** -- the golden-image test loads `selfie_segmentation.tflite` while
the pipeline default uses `selfie_multiclass_256x256.tflite`, and fetching only
one makes `test_golden_images_regression` fail in a way that reads exactly like
a composition regression:

```bash
python scripts/download_model.py --variant short_range --yes
python scripts/download_segmenter.py --variant selfie_multiclass_256x256 --yes
python scripts/download_segmenter.py --variant selfie_bin_general --yes
python scripts/download_face_landmarker.py --yes
python scripts/download_birefnet.py --yes          # 425 MB
python scripts/export_birefnet_onnx.py             # 940 MB, needs the `matting` extra
```

There is a browser test bench at **`/test`** on the running service: any exam
crossed with any file, input beside output, stage timings and the raw report.
Served by the engine itself, so it is same-origin and needs no CORS toggle.
Start the service with `EXAM_PHOTO_PURCHASE_GATE_ENABLED=false` when using it to
judge quality, or the bench shows the watermarked preview instead of the output
(DEC-063) -- it says which one it is showing.

Batch a folder with `python scripts/run_photo_set.py --input-dir "<folder>"
--contact-sheet`. Note it spawns a process per photo, so its per-photo times
include a cold start each and overstate the real cost.

**Two traps that cost real time here.**

*A stale venv silently breaks the ONNX export.* `onnx` and
`deform_conv2d_onnx_exporter` are in the `matting` extra, but a venv created
before they were added will not have them, and the export then fails two
dependencies deep with errors naming neither. Re-run
`pip install -e ".[dev,face,matting]"`.

*Never judge output on the MediaPipe backend.* Its 256px mask leaves blocky
edges with pieces missing from the ear and hair. It is no longer reachable
through `auto` at all (DEC-060) and is selectable only for diagnostics.

## Performance: what is actually true

**~10 s per photograph, warm.** Two BiRefNet inferences at roughly 5 s each,
plus about 1.3 s for everything else.

The engine was never slow. The *service* was: it rebuilt the pipeline on every
request and reloaded a 940 MB ONNX model each time (DEC-062). Fixing that took
22.4 s to 10.1 s. **Every timing taken through the CLI is misleading for the
same reason** -- a fresh process per invocation -- which is why 413x531 once
measured slower than 1200x1200 and no resolution-based explanation ever fit.
Measure through the warm service, never the CLI.

### Reducing it further, without trading quality

Ranked, and the constraint is the product owner's: **no quality compromise.**

1. **A GPU execution provider.** Same graph, same weights, same maths,
   different hardware -- the only lever here with zero quality risk. The
   installed onnxruntime is CPU-only (`AzureExecutionProvider`,
   `CPUExecutionProvider`), and this machine has integrated AMD graphics with
   512 MB, which will not hold a 940 MB model. On a deployment box with a
   discrete GPU this is the big one.
2. **Throughput over latency.** At Rs 4 a photograph the thing that actually
   bites is a deadline-day spike, and that is photographs per hour, not the
   latency of one. Several worker processes each holding a warm pipeline
   scales close to linearly -- which the DEC-062 caching finally makes
   possible, since before it every request paid a model load.
3. ~~INT8 quantisation~~ **— tried and rejected on measurement, 2026-09-05.**
   DEC-054 ruled it out a priori as a quality trade; it was worth putting
   through the same numerical-equivalence gate the ONNX export passed rather
   than assuming. It never reached the accuracy question, because it failed on
   size and speed first: `quantize_dynamic(QInt8)` produced a **larger** graph
   (941 MB to 1063 MB) and inference became so much slower that four passes did
   not finish in ten minutes, against roughly 5 s each for fp32. BiRefNet's
   graph is mostly ops dynamic quantisation cannot fold, so it inserts
   quantise/dequantise pairs around them and pays the conversion without ever
   getting the integer arithmetic. Static quantisation with a calibration set
   might behave differently, but it is a much larger undertaking and would
   still have to clear the equivalence gate. Do not re-try the dynamic form.

**Not on the table: removing DEC-040's second matte.** It is half the runtime
and the obvious cut, and it is a real quality trade -- the crop-region re-matte
is what spends the model's resolution on the part of the frame that survives
into the delivered photograph. Do not take it to hit a latency number.

# Platform State

**Last updated: 2026-09-15.** Branch `feat/upload-kit-ui`, with no pull request
yet. `b9eaa3f` and everything before it are on `origin`; **the fixing session's
commits after it are local and not pushed** (the owner pushes). The whole
candidate path works locally on a desktop and on a real phone, across **131
examinations** (DEC-093 removed a duplicate): search, every file an examination
asks for, preparation, **one agreement** before the first upload (DEC-086,
amended), a sharp watermarked preview that names its file (DEC-063, amended),
checkout (Razorpay, or the local simulator, DEC-089), and delivery.

**Where the work is now.** The owner tested the whole product by hand and sent
about fifty issues (screenshots in `C:\Users\dmbar\Downloads\errors-euk`, notes
in the session). The owner's rule for this phase: **build everything that needs
no input from them, and ask for every input at once** (memory:
`build-now-ask-later`). Built and committed: DEC-090 (never stretch, never refuse
a small photo, file names, ZIP, prices Rs 3 / Rs 5), DEC-091 (a photograph
uploaded as a signature is refused), DEC-092 (the landing band; impression paper
left alone), DEC-093 (catalogue audit, 131 examinations), DEC-094 (plain words,
scroll, paid state, previews in review, draggable comparison, clock, email,
ExamUploadKit, stacked logo), DEC-095 (the owner's research checked and
imported, 413 x 531 est. where no pixel size is published, the lighting switch
only when it changes something), DEC-096 (eight exam family hubs, and a free
compress-to-size tool that runs in the browser), DEC-097 (the deployment
blockers fixed, cookieless analytics, `docs/LAUNCH_GUIDE.md`), DEC-098 (a free
PDF compressor, an exact-size crop frame and 42 published-size pages). See "Waiting on the owner" below for what is not
done and why.

**Built on 13–14 September, beyond the phone phases:**

| What | Decision |
|---|---|
| The phone works over the LAN (`allowedDevOrigins`), nothing scrolls sideways on a phone, exam rows are real links | DEC-085 |
| Agreements above the upload: terms and privacy, a parent or guardian on 28 examinations, the thumb impression. Policy pages carry independence, liability, disputes, rights, grievance timelines and refund days. The seller's details come from the environment only | DEC-086 |
| Search, answer engines and link previews: one metadata helper, JSON-LD, an "In short" block on every rules page, generated preview cards, `/llms.txt`, `en-IN` | DEC-087 |
| A generated map of 30,018 search keywords in `docs/seo/`, each tied to the page that answers it | DEC-088 |
| A payment simulator for walking checkout on a test machine, through the real release path | DEC-089 |

**A brand kit exists outside the repository**, at
`C:\Users\dmbar\Documents\examuploadkit-brand-kit`: wordmark and icon (SVG and
PNG), palette, type specimen, the 13 drawings, social banners and posts,
product screenshots, messaging and claims, and an 8-page guidelines PDF, all
rendered from the site's own assets on 13 September. Its build scripts were in
a session scratch folder and are gone; regenerate from the site if it goes
stale.

### Running the test setup

Start the `engine` and `web-3100` launch configurations (`preview_start`).
**The desktop app stops both whenever its window or Browser pane closes, or the
machine sleeps** — when the owner says the engine is off, restart both, then
confirm `GET http://127.0.0.1:8000/ready` says `ready` and `payments: simulated`.

- `services/image-engine/.env.local` (git-ignored): `EXAM_PHOTO_PAYMENT_SIMULATOR=true`,
  `EXAM_PHOTO_BIND_HOST=0.0.0.0`, and `EXAM_PHOTO_ALLOWED_ORIGINS` for
  `localhost:3100`, `127.0.0.1:3100` and the LAN address.
- `apps/web/.env.local` (git-ignored): `NEXT_PUBLIC_EXAM_PHOTO_API_BASE_URL=http://192.168.29.72:8000`,
  and the owner's private `EUK_BUSINESS_*` values, which never go into git.
- **Check the Wi-Fi address first** (`Get-NetIPAddress -InterfaceAlias WiFi`).
  If it is no longer `192.168.29.72`, update both files and restart both servers;
  `NEXT_PUBLIC_*` is read when the dev server starts.
- **Memory is the constraint on this machine**: 7.4 GB in all, the engine holds
  about 2.4 GB warm and peaks near 2.9 GB. With the ChatGPT and Codex apps open
  there was under 1.5 GB free and the first photograph took 69 s; ask the owner
  to close them rather than closing anything yourself.
- The owner opens `http://localhost:3100`, or `http://192.168.29.72:3100` on the
  phone. Windows may ask to allow Python through the firewall for the phone.

## One agent now, both lanes

**The two-lane split is retired.** Codex owned UI/UX and this lane owned the
engine from DEC-055 until 2026-09-07; the product owner has consolidated both
into one agent. There is no coordination protocol left to follow, no
`types.ts` change that is "a request to the other side", and no reason to
stage commits by path any more.

What that costs, and it is worth naming: **this work no longer has an
independent reviewer.** Three defects in the 2026-09-07 session were the kind
a second agent catches -- a derived fact that contradicted the fact printed
beside it, a variant swap that would have delivered `..__alt.jpg` to a portal
that rejects on filename, and a generated sidecar named inside the `exam_*`
namespace the encoder deletes. Each was caught by a test, but only because
the test was written adversarially. **Write the negative test first.** It is
now the only thing standing where the second reader used to.

### What Codex left behind, assessed honestly

Its process discipline was good and is worth continuing rather than
replacing. `docs/UI_REDESIGN_QA_2026_09_07.md` records what was and was not
checked, refuses to claim an audit it did not run, and -- the hardest
instruction in the brief -- **found no reliable disqualification statistic and
said so**, citing a specific official notice instead of inventing a number.
It also found that the committed portrait's provenance text describes an older
European GAN asset while the image actually shipping is of an Indian-looking
person. That is a sharper finding than the one this lane recorded, and it is
still open.

The copywriting is good and should mostly survive: *"You prepare for the exam.
We'll prepare the files."*, *"A surprising number of open tabs."*

**Where it fell short of the brief, in one sentence:** its own plan says
*"Evolve the existing Clear Companion direction"*, and it did -- producing a
clean, competent, conservative SaaS layout where the brief asked for something
immersive and visually striking. Lots of white space, plain cards, almost no
motion, one illustration. Tasteful and safe. Not the thing that makes somebody
stay and explore.

### The design direction, settled

The owner's original style list -- Bauhaus, neumorphism, glassmorphism,
neobrutalism, claymorphism, aurora, retro-futurism, minimalism -- was
internally contradictory, and the agreed sequencing was a written
recommendation before any code. **That happened, it was approved, and it is
built.** What shipped is one committed direction, and a new session should
extend it rather than reopen the question:

**Flat by contract.** Hard borders, solid offset shadows, no radius, no blur,
no gradient. One signal colour (`--signal`), and nothing carries meaning by
hue alone. A drawn, editorial world -- inline SVG line drawings in the ink,
stroke-only, that are made to carry information rather than decorate: a
drawing that says nothing does not ship. Motion is transform and opacity only,
gated on `prefers-reduced-motion`, with a pause control wherever something
moves by itself.

The tokens live on `.euk` in `src/app/system.css`; `.euk-invert` flips them for
a dark band and `.euk-light` back again inside one. **Nothing invents a
colour.** The stylesheets are global, so one class name has one owner --
`src/tests/stylesheet-namespace.test.ts` fails the build if a name is defined
in two sheets without a stated reason, after three collisions in one session
shipped a line drawing as a solid orange block.

### Current UI state, verified 2026-09-14

**Desktop is built and the owner has signed off on two rounds of notes.** The
landing page (hero search, eighteen examination shortcuts, the kit, a steps
track, a self-dragging before/after band for a photograph and a signature, a
drawn browser window, a measured sheet of six frames, four principles that
perform their own refusal, pricing, the story), the examination workspace with
the three-way boundary intact, rules pages, the PDF page at `/pdf`, checkout,
delivery, policies and every error state. **552 static pages** (418, plus a
preview card for each examination, the site card and `/llms.txt`), 232 Vitest
tests, production build clean.

**The bar is sticky, full-bleed, and carries the search.** On the landing page
and the directory it appears only once the page's own search scrolls away; on
an examination page it is there from the start wearing that exam's name. It is
a real field -- type in it, the predictive list drops out of it -- fed by
`/search-index.json`, a statically built route fetched on first focus rather
than embedded in 415 documents. One height token, `--bar`, is the only number
anything positions against; five sticky blocks and the anchor scroll-padding
all read it.

**Verification that is worth repeating rather than re-deriving.** Headless
virtual time does not drive `requestAnimationFrame`, and the Browser pane does
not paint while it is hidden -- so a screenshot proves layout and nothing else.
Motion is proven by stepping a stubbed clock in a test, or by reading
`getAnimations()` and seeking it. And **never run `npm run build` while the
preview dev server is up**: it writes into the same `.next` and the dev server
then serves a stale stylesheet silently, which reads exactly like a CSS bug in
the code you just wrote. Clear `.next` and restart if it happens.

**A phone layout can only be proven on a real phone viewport, and neither
browser here gives one.** The Browser pane's viewport emulation reports
`innerWidth` at the pane's own width, so fixed elements measure wrong and
scrolled screenshots break up; headless Chrome on Windows will not make a
window narrower than about 500px, so a `--window-size=360` screenshot is
silently a 500px layout, cropped. `apps/web/scripts/phone-check.mjs` drives
Playwright's `chrome-headless-shell` over the DevTools protocol with true
mobile emulation — navigate, click, evaluate, screenshot — and needs no
package. The thing to measure on every phone screen is that `innerWidth`
equals `clientWidth`: when they differ, something overflows, the browser has
widened its layout viewport to fit it, and every fixed bar has stretched off
screen with it. Three of those were found on 13 September (DEC-081).

**Port 3000 is occupied on the owner's machine by a different project.** The
`web-lan` launch entry binds it and is then shadowed; `web-3100` in
`.claude/launch.json` is the one that actually serves this app.

What this file is: the state a new session cannot reconstruct from the diff.
Not a session note — keep it current rather than appending to it. It has drifted
into a chronology twice; if you find yourself writing "then X, then Y", rewrite
the section as what is true now.

Read alongside:

| File | What it carries |
|---|---|
| `AGENTS.md` | The binding operating contract |
| `docs/08_DECISION_LOG.md` | DEC-029..101. **Living** — amend an entry when implementation moves; never bend implementation to fit a stale one |
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

**Catalogue: 131 examinations, 405 requirements** (DEC-093, DEC-095). 303
supported, 28 guidance-only (live capture and portal declarations — correctly
never ours), 4 partially supported (a name/date printed on the photograph, or
WBSSC's signature on it, which the engine cannot write), 70 not yet supported.
39/155 before DEC-068 folded six research deliveries in additively, 52 after it,
132 once DEC-079 let a record exist without a photograph specification, 131
after the audit removed a duplicate. **Most records carry no photograph rule**
and serve a signature or certificates alone.

**289 interim placeholder values** are in the catalogue, all marked
`interim_default` in provenance: 264 in requirements (signature and
thumb-impression sizes and formats, a 400 KB certificate ceiling set by the
product owner) and 25 photograph sizes (413 x 531 or 354 x 472 est., the
owner's DEC-095 decision for notices that publish none). A photograph rule
carrying one is "Verified, with gaps", never "Verified". When real per-exam
research lands, `type == interim_default` finds every one.

## Where to start: the web app

**The whole candidate path is built and works locally.** Find the
examination, upload, watch it prepare, review a watermarked preview, pay
against a server-computed price, download or email the result. What is missing
is not a feature but a *level*: see "One agent now, both lanes" above.

Two architectural facts a new session must not re-derive:

**The catalogue is read at BUILD time, not over the API.** `lib/catalogue.server.ts`
reads `examples/rules/` from disk and every exam page is statically generated —
**132 of them** since DEC-079, plus 132 rules pages. This is deliberate (WEB-003): the pricing strategy makes SEO the
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
| Design tokens, both themes | `src/app/system.css` — one signal colour; `globals.css`/`journey.css`/`editorial.css` are gone |
| Landing page, problem story, before/after band, pricing, story, footer | `src/app/page.tsx`, `app/story.css`, `components/euk/wipe-demo.tsx`, `components/site-footer.tsx` |
| Checkout, entitlement polling, retention countdown, extension, delivery | `components/exam/kit-checkout.tsx`, `live-job-state.ts` |
| The sticky bar, its search and the predictive list | `components/site-header.tsx`, `header-search.tsx`, `exam-results.tsx`, `lib/use-exam-picker.ts`, `app/search-index.json/route.ts` |
| The PDF page and the in-browser converter | `src/app/pdf/page.tsx`, `app/pdf.css`, `components/exam/pdf-to-image.tsx`, `lib/pdfjs.ts` |
| The phone build — phases 1 to 4 | `components/m/` (bar, menu, full-screen search, home, flow, file list, PDF work, converter screen, support search, policies), `components/home-story.tsx`, `app/about/`, `app/pdf/to-image/`, `app/mobile.css`, `app/manifest.ts` |
| Exam workspace, 132 static pages | `src/app/exam/[examId]/page.tsx` + `components/exam/kit-workspace.tsx` — fixed file list left, one file's detail right |
| Rules & sources, 132 more pages | `src/app/exam/[examId]/rules/page.tsx` — reference split off the workspace |
| Real accepted/rejected examples | `scripts/generate_guidance_examples.py` → `public/examples/` |
| Specification rendering | `lib/spec-format.ts` — published figures over our byte conversion; `est.` marks a value we chose |
| Photograph rules per exam | `lib/appearance-rules.ts` — spectacles, headwear, expression, imprint, from the record only |
| Honest citation | `components/exam/source-note.tsx` — some exams have no official source and say so |
| Published rejection conditions | `scripts/encode_exam_rules.py` routes them (DEC-059); shown per requirement, attributed to the exam |
| Upload and preparation | `components/exam/requirement-upload.tsx` — client island, records the job against the kit |
| Three outcome states | `components/exam/outcome-result.tsx` — clean / with-findings / blocked |
| The watermarked preview and the purchase gate | Engine: `src/exam_photo/preview/`, `api/app.py` (`/v1/jobs/{id}/preview`, 402 on `/output`). UI already wired by Codex |

### Waiting on the owner (updated 15 September 2026)

The owner answered on 15 September and the answers are built (DEC-095):
413 x 531 est. where no pixel size is published, the lighting switch only when
it changes something, the research imported where its passage is on the page,
and the public address `Pune, Maharashtra 411014` set in `apps/web/.env.local`
(git-ignored; `EUK_BUSINESS_NAME` and `EUK_BUSINESS_ADDRESS` are still there,
unread). What is still open:

1. **Photographs**: the SBI Junior Associates original is not available, so the
   minimum-KB floor (item 1) stays proven by tests only; the "crop failed"
   photograph (note 19) was not supplied. The loosely cropped original was run
   through the engine on 15 September (DEC-099): under the old per-photograph
   rule it came out 900 x 1200 with the head under half the frame; under the
   413 x 531 est. rule it came out tight (head height 0.87). No crop constant
   was changed. The Mode B calibration still governs range and preferred-size
   records; measure it on the ten `perfect` photographs before touching it.
2. **Email: Resend now, SES later.** Delivery is plain SMTP, so either is six
   settings in `services/image-engine/.env.local` and no code:
   `EXAM_PHOTO_SMTP_HOST=smtp.resend.com`, `EXAM_PHOTO_SMTP_PORT=587`,
   `EXAM_PHOTO_SMTP_USE_TLS=true`, `EXAM_PHOTO_SMTP_USERNAME=resend`,
   `EXAM_PHOTO_SMTP_PASSWORD=<the owner's Resend API key>` and
   `EXAM_PHOTO_SMTP_FROM` on a domain verified in Resend. The owner puts the key
   in; it never goes into git.
3. **Decision: who reviews Hindi pages.** The owner does not know yet (maybe
   the owner, maybe a native speaker); Hindi pages are not built until someone
   can review them. The hubs and the compress tool were built on 15 September
   (DEC-096).
6. **Going live** (DEC-097): buy the domain and an 8 GB server, and follow
   `docs/LAUNCH_GUIDE.md`. The Resend key waits on the live domain. Ads are
   not recommended now; the guide says why.
4. **The rest of the research sheet**: `docs/research-requests/missing-information.csv`
   is 218 rows now. The owner's pass mostly gave values without the notice's
   passage; each still needs its passage before it can be imported. Re-read on
   15 September: NEET-PG imported (DEC-099); MHT-CET and MAH-MBA/MMS-CET lack a
   format, KVS a size, UPPSC a format; most other cited pages did not carry the
   figure.
5. **Machine time**: the owner asked this to be managed on the machine as it
   is. It had 0.4-1 GB free on 15 September, below the engine's 2.4 GB, so the
   slow-photograph timing (note J) and the phone walk against the engine are
   still not run.

**Not reproduced**: NEET UG's rules page (note 12) answers 200 on the dev server
; the owner's 404 was most likely a dev-server
compile under memory pressure.

### Open, older

1. **The four deployment blockers are fixed** (DEC-097): same-origin uploads,
   build-time settings passed to the web image, a requests volume, and a `www`
   redirect. Still before a deploy: merge the branch to `main` and push (the
   owner's call), and run `caddy validate` on the server, because this machine
   could not run Docker to check the Caddyfile. **`docs/LAUNCH_GUIDE.md` is the
   owner's step-by-step**: one 8 GB x86 server running the compose stack,
   Cloudflare DNS, Turnstile, Resend, Razorpay, Search Console and Bing.
3. **Regional languages are not ready**, and the owner intends them soon. No
   translation layer; copy is written into about 30 components; Big Shoulders
   and Petrona are Latin-only; 40 uppercase, 30 letter-spacing and 51
   sub-1.0 line-height rules would break Indian scripts; the engine returns
   some English sentences rather than codes; the records hold no Hindi names and
   search matches a–z only. Cheap preparation meanwhile: new copy in one place,
   codes rather than sentences from the engine, Hindi names gathered in research.

### What is actually left, in order

The engine side of the 2026-09-07 brief is complete, and so is the desktop
design. What follows is UI/UX and operations.

1. **The phone build, as its own design.** This is the next session's work and
   the owner has been explicit about it twice: more than 70% of candidates will
   arrive on a phone, and a reflowed desktop page is not what was asked for.
   `docs/ui-direction-2026-09-10/MOBILE_PLAN.md` holds the plan and the owner's
   four answers (a four-step flow with a sticky bar; an action-only bottom bar
   plus a subtle top bar; a short home with the rest behind a link; include the
   PWA install). **Phases 1 to 3 have shipped** (DEC-081, DEC-083): the flow,
   the phone bar and menu on every page, the short home, search as its own
   screen, `/about` for the long argument, a short footer, the PDF work with
   the converter on its own screen, searchable support, and collapsed
   searchable policies, and the install prompt (DEC-084): asked once after a
   useful moment, never on arrival. **The owner's first real-phone test found
   every scripted control dead**: the dev server refused its scripts to the
   LAN address, so the page never hydrated (DEC-085; `allowedDevOrigins` now
   admits private addresses, and a phone check must load the LAN address, not
   `localhost`). The same pass removed every sideways strip on a phone. **The
   owner has since checked the prepare flow on a real phone against a
   production build (2026-09-13); the phone build is complete.**
2. **Design the empty state for 80 examinations.** DEC-079 encodes records with
   **no photograph specification** -- served for a signature or certificates
   alone. Their *rules* page has almost nothing to show. It degrades to empty
   rather than breaking, which is correct and looks like a hole.
3. **`not_yet_supported` is now on 72 requirements**, up from a handful. It is
   listed deliberately -- the examination does ask for a photograph and hiding
   it would say otherwise -- but the workspace shows that state far more often
   now and it must read as "we cannot prepare this yet", never as a failure.
4. **The pages Razorpay onboarding requires now exist** (DEC-086): terms,
   privacy and refunds carry the limits, the grievance officer and the dispute
   terms, and the upload asks for the agreements the law needs. **The seller's
   details render only when `EUK_BUSINESS_NAME`, `EUK_BUSINESS_ADDRESS`,
   `EUK_BUSINESS_PHONE` and `EUK_BUSINESS_HOURS` are set**: in
   `apps/web/.env.local` locally, and on the host at deploy. Never commit the
   values. The domain is bought and a lawyer has read the pages (owner,
   2026-09-13). Consent is recorded only in the browser; recording it with the
   job on the server is the open item.
   **Search and previews (DEC-087)** need `NEXT_PUBLIC_SITE_URL` set on the
   host at build time, and `GOOGLE_SITE_VERIFICATION` /
   `BING_SITE_VERIFICATION` once the owner adds the site to Search Console and
   Bing Webmaster Tools; then submit `/sitemap.xml` to both.
   **The keyword map (DEC-088)** is `docs/seo/`: regenerate it with
   `npm run seo:keywords` after any catalogue change, and build the gap pages
   in the order `KEYWORD_STRATEGY.md` gives, starting with a standalone
   compress-to-size tool.
5. **Multi-page documents** via `planDocument` -> arrange -> `assembleDocument`.
   The engine pair exists; the arranging interface does not.
7. **A preview for a PDF deliverable.** `preview_watermarked` is false and
   `preview_url` null, honestly, so a candidate currently buys a certificate
   scan unseen. Rendering a page needs a rasteriser this repository
   deliberately does not carry (PyMuPDF is AGPL). DEC-052 governs the
   *delivered* file, not a preview, so this is allowed -- it is a dependency
   decision, not a rule change.
8. **Refund processing.** DEC-072 makes a claim *decidable* -- paid, delivered,
   when, by which route -- but nothing issues money. Razorpay refunds are a
   separate integration, and the policy question in DEC-067 is still the
   owner's: what happens when someone pays and their file expires.

### Running it locally

The catalogue is build-time, so `npm run dev` needs nothing else. Preparing a
file needs the engine, **and the engine ships with browser access off**:

```bash
EXAM_PHOTO_LOCAL_CORS_ENABLED=true .venv/Scripts/python.exe -m exam_photo serve-api --host 127.0.0.1 --port 8000
```

Without it every upload fails as an ordinary network error, because a blocked
cross-origin request and a dead server are the same `TypeError` to a browser.

**Walking the whole flow, including checkout, before Razorpay exists (DEC-089).**
Start the `engine` and `web-3100` launch configurations. The engine reads
`services/image-engine/.env.local` (git-ignored): `EXAM_PHOTO_PAYMENT_SIMULATOR=true`
opens a labelled test sheet where Razorpay's window would be, and paying there
releases files through the real release path; `EXAM_PHOTO_BIND_HOST=0.0.0.0` and
`EXAM_PHOTO_ALLOWED_ORIGINS` let a phone on the same Wi-Fi use it, with
`NEXT_PUBLIC_EXAM_PHOTO_API_BASE_URL` in `apps/web/.env.local` pointing the site at the
machine's LAN address. The engine and the dev server together need about 4 GB of
free memory. When Razorpay arrives, remove the simulator line and add the three
Razorpay values; the simulator refuses to run beside them.

### Deploying it

Every hardening knob is off or permissive by default so local development is
unchanged; a public host must set all of these (DEC-064):

```bash
EXAM_PHOTO_ALLOWED_ORIGINS=https://your-domain      # or serve same-origin behind a proxy and leave unset
EXAM_PHOTO_OPERATOR_TOKEN=<long random secret>      # gates /v1/process, /v1/rules/validate, /v1/cleanup-expired, /test
EXAM_PHOTO_MAX_CONCURRENT_PREPARATIONS=<~core count>
EXAM_PHOTO_CLEANUP_INTERVAL_SECONDS=300
EXAM_PHOTO_JOB_TTL_SECONDS=1800                     # DEC-066: a published promise
```

Point the load balancer's readiness probe at **`/ready`**, not `/health`.
`/health` is liveness only and answers 200 while the model is still loading;
that distinction is the whole reason a rolling deploy does not take the fleet
cold. `/ready` also reports `operator_surface: "unauthenticated"` when no token
is set, which is the one place an open operator surface is visible.

**The purchase gate is on by default** (DEC-063), so `/v1/jobs/{id}/output`
answers 402 and the browser gets `/v1/jobs/{id}/preview` — the finished file at
half resolution with the mark burned into it. That is the correct behaviour for
the product and the wrong one for judging engine output, so add
`EXAM_PHOTO_PURCHASE_GATE_ENABLED=false` for any quality work. Judging a matte
on a watermarked half-resolution copy is judging it on the wrong thing, the same
trap as the MediaPipe backend. The `/test` bench asks for the clean file, falls
back to the preview on a 402, and says which one it is showing.

### Decided, not yet built

- **Identify a session by an unguessable token, never by IP.** Carrier-grade
  NAT on Indian mobile networks puts thousands of candidates behind one address:
  an IP-keyed cache would serve one candidate another's face photograph and
  signature, and would simultaneously lose files for anyone whose IP rotates.
  `kit-state.ts` already mints a `kit_id` for exactly this.
- **No right-click blocking.** It stops nobody and reads as cheap. The
  protection that works is that the clean file never reaches the browser before
  payment; the preview is watermarked server-side at reduced resolution. **Both
  halves of that are now built** (DEC-063) — see the purchase gate below.
- **Reject-gallery examples are synthetic.** Real candidate photographs may
  never ship. The SVG diagrams already cover framing; anything richer is drawn
  or commissioned, never a real candidate.

**The API is done.** `GET /v1/exams`, `GET /v1/exams/{exam_id}`,
`POST /v1/exams/{exam_id}/requirements/{requirement_id}/prepare`, the document
pair (`.../requirements/{id}/documents` then `/v1/documents/{job_id}/assemble`),
`GET /v1/jobs/{job_id}/preview`, and `GET /v1/kits/{kit_id}/package(/download)`. Contracts in `api/contracts.py`,
catalogue reader in `orchestration/rule_catalogue.py`. The support gate returns
409 with the requirement's own vocabulary before the upload is read.

### Testing the engine locally

`model-assets/` is populated on this machine (it is gitignored, so a fresh
clone starts empty and every `mandatory_*` suite skips):

```bash
python scripts/download_model.py --variant short_range --yes
python scripts/download_segmenter.py --variant selfie_multiclass_256x256 --yes
python scripts/download_face_landmarker.py --yes
python scripts/download_birefnet.py --yes          # 425 MB
```

Run a folder of photographs and get a contact sheet:

```bash
python scripts/run_photo_set.py --input-dir "<folder>" --contact-sheet
```

**Always judge output on `--matting-backend birefnet`.** The mediapipe
segmenter is a 256 px mask: on a real photograph it leaves blocky, stair-
stepped edges with chunks bitten out of the ear, and output judged on it is
being judged on the wrong thing. It is a fallback for machines without the
weights, not a quality setting.

**A stale venv silently breaks the ONNX export.** `onnx` and
`deform_conv2d_onnx_exporter` are declared in the `matting` extra but a venv
created before they were added will not have them, and
`export_birefnet_onnx.py` then fails two dependencies deep with unrelated-
looking errors. Re-run `pip install -e ".[dev,face,matting]"` first.

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

**Regenerate the facts sidecar after every encode**: `python
scripts/generate_exam_facts.py` rewrites `examples/rules/candidate_facts.json`
from the records (DEC-077). It is named outside the `exam_*` namespace on
purpose -- the encoder deletes everything matching that prefix, so a sidecar
called `exam_facts.json` disappears on the next run with no error. A test
fails if the sidecar is stale.

**Researched facts are curated before they are committed, never merged as
delivered** (DEC-082). The first delivery's sentences were templates, a
quarter of its "quotes" were database fields, and one figure was wrong. What
shipped was fetched page by page, rewritten from the passage on the page, and
refused by a check unless every figure is in its passage and every passage is
on its page: 127 of 169 facts. `exam_trivia_2026_curation.md` lists what was
dropped and why. The brief (`DEEP_RESEARCH_BRIEF_TRIVIA.md`) now asks for the
passage and the publisher up front, so the next delivery should need less of
this, not none.

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

**A delivery is merged, never adopted** (DEC-068). `scripts/merge_research_delivery.py`
folds a new delivery into the research corpus field by field: a `not_found`
never displaces an established value, rejection conditions are unioned, and
deliverables union on a punctuation-insensitive name with the deeper entry
winning. Replacing the corpus with the newest delivery would have cost 204
rejection conditions and five working examinations. Values read straight from
an authority document go in a versioned overlay, applied last. **Do not re-run
`extract_deliverables.py` after a merge** — it regenerates
`exam_deliverables_2026.json` from the 2026 markdown report and discards
everything merged since.

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

1. ~~**Cold start and nothing warms the process.**~~ **Fixed (DEC-064).** A
   `lifespan` hook warms the model on a background thread at boot and
   `GET /ready` reports `warming` / `ready` / `failed`, 503 on the first and
   last, while `/health` stays liveness-only. Measured on this machine: the
   first inference in a process costs **48.8 s** and the second **7.7 s**, so
   warmup absorbs roughly 41 s that used to fall on the first candidate.
   Verified live — the process binds and answers `/health` at 200 while
   `/ready` is 503 `warming` with an elapsed count. Deployment machinery now
   exists in `deploy/` (DEC-065) and the compose healthcheck reads `/ready`.
   **Both images are built and the stack has run**, which found three
   things listed under *Deployment* below.
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
4. ~~**81 examinations dropped for a photograph reason.**~~ **Closed
   (DEC-079).** `image_requirements` is optional now, so an examination whose
   photograph cannot be encoded is served for its signature and certificates
   instead of being dropped whole. **The catalogue went from 52 encoded
   examinations to 132**, supported requirements from 189 to 314, and stranded
   deliverables from 135 to **one**. All four SSC examinations are served, and
   BPSC is back with both its signatures. The invariant that replaced the
   requirement: a record without a photograph specification may *list* a
   photograph but never offer it as supported, so an uploaded photograph the
   platform prepares still has exactly one specification.
5. **Service hardening and privacy — partly done (DEC-064).** An operator token
   now gates `/v1/process`, `/v1/rules/validate`, `/v1/cleanup-expired` and
   `/test`; the candidate surface stays open because a browser cannot hold a
   secret, and its CPU is protected by a global concurrency cap (429 with
   `Retry-After`) rather than a per-IP quota, which CGNAT makes unusable. The
   expired-artifact sweeper now actually runs, so retention is enforced rather
   than merely asserted. **Still outstanding: TLS** (assumed terminated at the
   proxy — make sure it is), edge abuse filtering, and the question below.
6. ~~**`job_ttl_seconds` is 3600 and the interface contemplates 30
   minutes.**~~ **Settled at thirty minutes (DEC-066).** `job_ttl_seconds`
   defaults to 1800 and the guarantee may be published. Settling it exposed
   the real defect, which neither DEC-058 nor DEC-064 had noticed: **expiry
   was enforced only by the sweeper**, so nothing on the read path consulted
   `expires_at` and an expired -- and *paid* -- job returned **200 with the
   clean file** for up to `cleanup_interval_seconds` past its deadline.
   Access now ends at the deadline itself: `is_expired()` is checked on all
   six job routes, which erase the job on the way to refusing it, expired
   jobs leave their kit, and the sweeper is the backstop for jobs nobody
   reads again. One product question is left open and named in
   `docs/UI_ENGINE_HANDOFF.md`: a candidate who pays and returns after thirty
   minutes has bought a file that no longer exists. **Settled by DEC-067:**
   warn before checkout, and let the candidate extend once, to a ceiling of
   one hour from creation -- which is what every file used to get
   unconditionally, so the option cannot lengthen the worst case. The engine
   serves `POST /v1/jobs/{id}/extend` and an `extendable` flag; **the warning
   is the UI lane's and the feature is inert without it**, because an
   extension can only be taken before the deadline. The published claim is
   now "within thirty minutes, or an hour if you ask" and must be written
   that way.
7. **Invariants unwired**, and the remaining **M22 matte defect**: a detached
   hair fragment on photo 17 (a disconnected mask region). Its soft/smudged
   hair-edge half (18, 19, and the non-fragment part of 17) is fixed --
   DEC-033's trusted-alpha path was skipping an anti-halo contrast correction
   the coarse-mask path already had.
8. ~~**`apps/web/public/examples/portrait-*.jpg` are committed, and their
   provenance is unconfirmed.**~~ **Closed (12 September 2026).** Every
   unverified image under `apps/web/public/examples/` was deleted:
   `portrait-*.jpg`, `photo-*.jpg`, `signature-*.jpg`, `hero-*.jpg` and the two
   guide PNGs. Nothing referenced them any more. The landing band now runs on
   owner-supplied generated pairs under `public/examples/demo/`, recorded in
   `docs/ui-direction-2026-09-10/DEMO_ASSETS.md`: fictional people, invented
   signatures, no candidate's file, and labelled on the page as
   representational rather than as engine output. They remain in git history;
   rewriting that is the owner's call and blocks nothing.

## Verifying

`.github/workflows/image-engine-ci.yml` is the source of truth. `pytest` alone
covers neither the eleven `mandatory_*` marker suites nor `ink_robustness`.

```bash
cd services/image-engine && ruff format --check . && ruff check . && .venv/Scripts/python.exe -m mypy src tests
```

Current (2026-09-15, DEC-100): CI runs two jobs, **engine** (format, lint, mypy,
core unit tests, ink sweep, the ten integration marker suites, package build) and
**web** (Node 22). The June fixture benchmarks and CLI smoke checks carry
expectations from before the August engine changes and run by hand from
`engine-quality-full.yml`; do not treat their verdicts as defects until the
annotations are re-derived from the labelled 40-photograph set.

Model assets are under `model-assets/`. Run marker suites from the repo root
with `EXAM_PHOTO_FACE_MODEL_PATH` / `EXAM_PHOTO_SEGMENTER_MODEL_PATH` and their
`*_SHA256` set as the workflow sets them.

## Deployment

`deploy/` holds the whole of it (DEC-065): a two-target Dockerfile for the
engine, one for the web app, a compose file, a Caddyfile and `.env.example`.
Read `deploy/README.md` before the first deploy.

**The number that decides the box: a warm worker holds ~2.4 GB resident and
peaks near 2.9 GB during inference**, measured on this codebase. So a 2 GB VPS
— the ordinary reading of "one small VPS" — cannot run this; **4 GB is the
floor for one worker**. It also corrects the throughput plan above: workers are
processes and each holds its own session, so "several worker processes each
holding a warm pipeline" costs 2.4 GB *each*, and four workers is a 16 GB box
rather than a configuration change.

### What building it actually found

Written, then built, then run. The build found nothing; **running a real
photograph found two defects and one hard limit.**

1. **The canonical JSON Schema was unreachable from any installed copy.**
   `rule_validation.py` located `exam-rule.schema.json` by walking four
   directories up from `__file__` — the repository root in a checkout, and
   `site-packages`' grandparent anywhere else. Every rule then failed with
   `RULE_VALIDATION_SCHEMA_UNAVAILABLE`, so **every job failed**. This was a
   latent defect affecting the wheel build too, not a packaging slip. It now
   honours `EXAM_PHOTO_REPO_ROOT` first and keeps the relative walk as the
   checkout fallback (`tests/test_rule_schema_resolution.py`).
2. **mediapipe needs `libGLESv2.so.2` to *run*, not to import.** It `dlopen`s
   the GLES libraries only when a detector executes, so the package imported
   cleanly and the first real photograph failed with a message naming nothing
   to do with faces. `libgles2` and `libegl1` are now in the base image. **An
   import smoke test does not catch this** — only a real inference does.
3. **The stack does not fit in 4 GB.** Running it in a 3.6 GB Docker VM killed
   uvicorn mid-inference at **3.1 GB resident** (`anon-rss:3115756kB`, a global
   OOM). 4 GB is the floor for the **engine container alone**; the whole stack
   wants **6 GB**. The sizing table in `deploy/README.md` was corrected from
   this, not estimated.

Also measured: **container warmup is 186–316 s**, against 48.8 s for the same
inference natively — the model file is on a volume. The healthcheck's
`start_period` is 600 s for that reason; 300 s was tried and one run only
survived on the retries. Too short means a crash loop, not a slow start.

**Verified working end to end**: engine image 1.21 GB with torch correctly
absent, web image generating **39 exam pages and 39 rules pages**, Caddyfile
`Valid configuration`, same-origin routing, the operator gate (401/200), and
the proxy holding until the engine reported *ready*. **Not verified**: a
photograph completing inside the container — it needs 3.1 GB and this machine
cannot give it. That belongs on the VPS.

Three things the shape depends on, none of them obvious from the files:

- **Weights live in a named volume**, filled once by the `model-fetch` profile,
  never baked into an image. They are ~2.5 GB that never change between
  deploys.
- **Caddy gives one origin**, so `EXAM_PHOTO_ALLOWED_ORIGINS` stays unset and
  there is no CORS to configure. `/health` and `/ready` are answered only from
  private ranges, because `/ready` reports the matting backend, the
  purchase-gate state and whether the operator surface is authenticated.
- **The web image reproduces the repository layout** rather than flattening the
  app, because `catalogue.server.ts` resolves the catalogue as
  `process.cwd()/../../examples/rules`. Flatten it and every exam page vanishes
  from the build with no error worth the name, so the build asserts they exist.

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
