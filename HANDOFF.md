# Platform State

**Last updated: 2026-08-06.** Branch `feat/upload-platform-pivot`, pushed and
green. Renamed from `feat/pivot`; `origin/feat/pivot` still points at an old
commit until someone deletes it.

**The next session is UI work.** Start at *[Where to start: the web app](#where-to-start-the-web-app)*.

What this file is: the state a new session cannot reconstruct from the diff.
Not a session note — keep it current rather than appending to it. It has drifted
into a chronology twice; if you find yourself writing "then X, then Y", rewrite
the section as what is true now.

Read alongside:

| File | What it carries |
|---|---|
| `AGENTS.md` | The binding operating contract |
| `docs/08_DECISION_LOG.md` | DEC-029..053. **Living** — amend an entry when implementation moves; never bend implementation to fit a stale one |
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

`apps/web` is the pre-pivot flow and it is the gap. It does: pick a rule →
upload one photograph → see validation → download. It has no concept of an
examination's *inventory*, which is now the product.

What exists and is worth keeping:

- `src/components/upload-card.tsx`, `result-preview.tsx`, `validation-report.tsx`,
  `processing-status.tsx` — sound parts, wrong composition.
- `src/app/admin/rules/` — the local rule console. Independent of the pivot and
  still works.
- `src/lib/api-client.ts` — talks to the local FastAPI service.

What the UI now has to express, in rough order of value:

1. **The kit.** Select an examination, see all its requirements with their
   status. The data is already in each rule record's `requirements[]`.
2. **The boundary.** `platform_support` distinguishes `supported` from
   `guidance_only` and `physical_stage`. These must never look alike — a
   candidate believing the platform completed their SSC live capture is the
   product's worst failure mode, and it is a labelling problem, not a technical
   one.
3. **Per-item upload and preparation**, including multi-page documents with
   reordering (`pdf/document.py` is built for exactly this).
4. **Package delivery** — the ZIP, checklist and validation report.

**The API does not yet expose any of this.** `api/app.py` serves
`/v1/process` for a single photograph plus job status, output and rule
validation. Deliverable preparation
(`orchestration/deliverable_pipeline.prepare_deliverable`) and document
assembly (`pdf.assemble_document`) are library calls with no endpoint. Adding
those endpoints is the first engineering step of the UI work.

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

1. **Throughput.** 30–40 s per photograph on CPU. The product owner has taken
   this as their own item — **do not spend engineering effort on it unasked.**
2. **The API surface for deliverables.** Everything new is library-only. The UI
   cannot start without endpoints.
3. **Ten examinations dropped for a photograph reason** while carrying 23
   non-photograph deliverables between them, including all four SSC. Fixing it
   means letting a rule record exist without a photograph specification.
4. **Service hardening and privacy.** The API is local-only by design — no TLS,
   auth or rate limiting — and candidate face photographs are sensitive personal
   data under the DPDP Act. Both precede anything public.
5. **Invariants unwired**, and the **M22 matte defects** (a detached hair
   fragment on photo 17; soft hair edges on 18 and 19).

## Verifying

`.github/workflows/image-engine-ci.yml` is the source of truth. `pytest` alone
covers neither the eleven `mandatory_*` marker suites nor `ink_robustness`.

```bash
cd services/image-engine && ruff format --check . && ruff check . && .venv/Scripts/python.exe -m mypy src tests
```

Current: format, lint and mypy clean across 137 files. 274 fast tests passing,
15 skipped. `ink_robustness` (~100 synthetic captures) green as its own CI
stage. Marker suites green. Invariant sweep 0 violations of 960.

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
