# Platform State

**Last updated: 2026-08-05.** Branch `feat/upload-platform-pivot`, pushed and
green. It was renamed from `feat/pivot`, and `origin/feat/pivot` still points at
the same commit until it is deleted.

What this file is: the state a new session cannot reconstruct from the diff.
Not a session note — keep it current rather than replacing it with a fresh one.

Read alongside:

| File | What it carries |
|---|---|
| `HANDOFF-INVARIANTS.md` | How composition work is done here: the invariant sweep, the ratchet, the planner/validator defect class, the verification sequence |
| `docs/08_DECISION_LOG.md` | DEC-029..046. **Living** — amend an entry when implementation moves; never bend implementation to fit a stale one |
| `docs/EXAM_RULE_GAP_REGISTER.md` | Generated. Which examinations are encoded, which are not, and why |
| `AGENTS.md` | The binding operating contract |

---

## Direction

The product is pivoting from photograph preparation to **exam-first application
upload preparation**: the candidate selects an examination, sees every file it
requires, and receives the ones the platform can prepare. Two source documents
drive this — a product-direction report and a 48-examination deliverables
report, both dated 2026-08-05, held outside the repository.

What that changes, in one line: the photograph is roughly a quarter of what an
application asks for. Across 50 stage-specific records the research counts ~48
signature items, 44 photographs, 15 thumb impressions, 13 handwritten
declarations and ~40 certificate or identity scans.

Landed so far (DEC-047, DEC-048, DEC-049): the rule record carries the full
deliverable inventory, interim placeholder values are structurally
distinguishable from evidence, and the encoder writes both from versioned
research. All 39 encoded examinations now carry an inventory — 155 requirements,
of which 39 are supported (the photographs), 16 guidance-only and 100 not yet
supported, with 55 interim placeholders on signature and thumb-impression sizes
and formats.

**No non-photograph deliverable is served yet.** Every such requirement reads
`not_yet_supported` and a test enforces it, because the ink engine below is not
yet wired to the rule pipeline. The specifications are written and waiting.

The ink-on-paper engine (`exam_photo.ink`, DEC-050) exists and is the opposite
of the photograph rule: paper is driven to pure white and ink to full strength,
because paper carries no information in its tones and the mark's identity is its
shape — which nothing in it touches. Signature, thumb impression and handwritten
declaration all use it. **No OCR, no declaration text comparison** — the owner
ruled that out; a declaration is prepared as a plain file.

What it does on the reference set: paper to median 255 on all five inputs, the
mark's own colour kept, both approved signatures reproduced closely, both thumb
captures cropped tight, receipt show-through removed, the hand holding the sheet
rejected. What it does not do: frame a small sheet in a large frame tightly —
the crop comes out ~1.7× the mark's extent because the sheet's own edge reads as
ink. Held by a ratcheted test; the file is usable, just loose.

Two consequences of the pivot that contradict statements elsewhere in this file:

- **The four SSC examinations were dropped for the wrong reason.** "Live capture
  only, nothing to deliver" is true of the photograph and false of the
  examination — SSC requires an uploaded signature at 10-20 KB. The same applies
  to several of the 11 not-encoded records, dropped for missing *photograph*
  fields while carrying signature and certificate requirements.
- **M19 is no longer the product blocker**, only the blocker for one deliverable
  type. The deliverables report adds no photograph specifications: spot-checked
  against UPPSC, MHT-CET and RPSC, the M19 tail gaps are unchanged.

Handwriting OCR and declaration text-comparison are **out of scope** at the
owner's direction. A declaration is prepared as a plain file — format, size,
filename — with no content understanding.

## What the platform does today

A candidate selects an examination, uploads a photograph, and receives a
compliant file. End to end, that works:

- **Crop** — one composition for every examination: the tightest crop that keeps
  hair, ears and the chin/beard boundary intact, with the bottom edge anchored
  just under the chin. Verified against the product owner's ten
  `perfect`-labelled photographs; below-chin space runs 0.081–0.146 of frame
  height against an approved-reference median of 0.102.
- **Background** — BiRefNet matting (the pipeline default), re-run on the crop
  region at native resolution, composited onto the required colour.
- **Sizing** — from the examination's published dimensions where they exist,
  from the body's published *preferred* size where it names one, and otherwise
  from the photograph's own crop geometry inside a 240–1200 px envelope.
- **Compression** — binary-searched to land just under the byte ceiling.
  Measured 30–88% of ceiling across the encoded examinations.
- **Naming** — the body's required filename where published, otherwise a
  PII-free default.

Verified end to end across five rules spanning every dimension mode: 20 of 20
outputs correct on pixel dimensions, byte ceiling, format and filename.

## What it demonstrably cannot do

State these plainly rather than discovering them again:

- **Serve a live-capture-only examination.** All four SSC examinations
  photograph the candidate through the portal. There is no upload, so there is
  nothing to prepare. Dropped from the catalogue at the owner's direction.
- **Print a name or date onto the photograph.** TNPSC and Kerala PSC require it.
  Both records are marked `partially_supported` with the reason stated, so no
  caller can read a complete success into them.
- **Detect a beard line.** Three signals were tried and rejected on measured
  evidence (DEC-035). The engine approximates with a uniform chin-plus-margin.
- **Detect sunglasses, head coverings or closed eyes to a publishable standard.**
  Eye-blink scoring was built, measured, found not to separate, and removed.
  Milestone 23.
- **Measure a delivered photograph against its own invariants.**
  `check_composition_invariants` has no pipeline consumer — the sweep is its only
  caller, so the planner is gated but a real upload is never checked. See the
  gap note in `HANDOFF-INVARIANTS.md`.

## The examination catalogue

39 encoded, 11 not. Statuses reflect what the evidence supports:

| Status | Count | Meaning |
|---|---|---|
| `verified` | 17 | Official dimensions, file size and format |
| `verified_with_ambiguity` | 15 | Official size and format; the body publishes no pixel dimensions, so the engine sizes from the crop |
| `provisional` | 7 | Values found only on secondary sources. Kept servable at the owner's direction, with the aggregator citation visible in `source_evidence` |

**Rule records are generated, never hand-written.** `scripts/encode_exam_rules.py`
reads the versioned research in `packages/exam-rules/research/` and rebuilds the
whole catalogue plus the gap register. The script owns every file matching its
prefix, so a re-run replaces rather than adds. It takes two sidecars — the
photograph specifications, and the deliverable inventory produced from the
report by `scripts/extract_deliverables.py`:

```bash
python scripts/extract_deliverables.py --report packages/exam-rules/research/indian_exam_registration_deliverables_report_2026.md --out packages/exam-rules/research/exam_deliverables_2026.json
python scripts/encode_exam_rules.py --specs packages/exam-rules/research/exam_photo_specs_2026.json --deliverables packages/exam-rules/research/exam_deliverables_2026.json --out examples/rules --report docs/EXAM_RULE_GAP_REGISTER.md
```

The consequence matters: **to change a rule, change the evidence and re-run.**
Editing `examples/rules/exam_*.json` by hand works until the next regeneration
silently discards it, and in the meantime the record asserts something no source
supports.

## Load-bearing decisions

These are not incidental. Undoing one changes what the product is, so undo it
deliberately and amend the decision log rather than quietly.

1. **One composition, no per-exam profile** (DEC-045). Every examination gets the
   tight crop. No researched body publishes a coverage maximum it would breach;
   all publish minima it clears. The loose presets were removed because they
   also omitted four settings the tight one carries.
2. **Produce, never refuse for appearance or composition** (DEC-041, DEC-045).
   Only an undecodable file, no detectable face, or a genuinely ambiguous
   subject may block. A refusal and a silent failure are the same outcome to a
   candidate, and refusing delivers strictly less than the compromise it
   rejects.
3. **Never distort to hit a target.** The output preparer refuses on an aspect
   mismatch beyond 1% rather than stretching, on both the exact and range paths.
   The delivered aspect always follows the crop.
4. **Absent is not permissive.** A rule the research recorded as `not_found` is
   omitted, never defaulted. An absent rule and a permissive rule are different
   statements and only the first is true.

## Open risks, in priority order

1. **M24 throughput.** 16–24 s per photograph on CPU, roughly doubled by the
   crop-region rematte, so 30–40 s each. At national examination-cycle
   concurrency this is not viable. **Probe it before investing in matte
   quality** — a forced model change invalidates part of M22.
2. **M22 matte defects.** The owner's outstanding flags on the reviewed set:
   photo 17 a detached hair fragment (the default matte path does no
   connectivity cleanup at all), photos 18 and 19 soft hair edges where dark
   hair meets a dark background, photo 8 under-enhancement. The fragment fix is
   backend-independent and safe to do now; the soft-edge fix is
   matte-resolution-dependent and should wait on the throughput probe.
3. **Invariants unwired.** See above — the detector exists and nothing calls it.
4. **M19 tail.** Confirm the 15 size-only examinations genuinely publish no
   pixel dimensions. UPPSC and MHT-CET are one field short each (most likely
   JPEG); CTET and MPSC publish a physical size with no DPI, and either would
   convert to exact pixels if a stated DPI is found.
5. **RRB transposition** (DEC-046). Both RRB records publish a
   self-contradictory figure and are recorded upright as a judgement. Re-check
   against the live notification before either leaves `verified`.

## Verifying

`.github/workflows/image-engine-ci.yml` is the source of truth. `pytest` alone
does not cover the eleven `mandatory_*` marker suites.

```bash
cd services/image-engine && ruff format --check . && ruff check . && .venv/Scripts/python.exe -m mypy src tests
```

Current: format, lint and mypy clean across 118 files; 176 core tests passing,
15 skipped; all eleven marker suites green; invariant sweep at 0 violations of
960.

Model assets are present under `model-assets/`. Run marker suites from the repo
root with `EXAM_PHOTO_FACE_MODEL_PATH` / `EXAM_PHOTO_SEGMENTER_MODEL_PATH` and
their `*_SHA256` set as the workflow sets them.

## Reference material — local only, never commit

The ink-on-paper reference set is at `C:\Users\dmbar\Pictures\other-exam-uploads`
— `signature/good` holds two approved outputs (the target), `signature/bad` and
`thumb impression/` hold real captures. Five images, and every constant in
`exam_photo.ink` is calibrated against them with the measurement recorded beside
it. **Known gaps in the set: no pencil or faint-pen sample, and no handwritten
declaration at all.**

The 40-photo labelled set at `C:\Users\dmbar\Pictures\new-test-images` is the
current specification; ten are labelled `perfect`. The outputs the owner last
reviewed are in `C:\Users\dmbar\Pictures\Engine Outputs - Clean Set` at 413×531.
**The 60-photo paired set is retired — do not use it**, and do not run
`scripts/benchmark_reference_pairs.py`, which targets it.

The working loop for any composition change: run the ten `perfect` photographs
through `process_rule`, measure head height, above-hair and below-chin on the
output, and diff against the reviewed set. The synthetic sweep alone is not
sufficient — it read zero while a photograph the owner had flagged by eye was
still visibly wrong, because synthetic head boxes do not extend past the jaw the
way real ones do.
