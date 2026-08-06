# Output Invariants — Working Contract

**Read this before changing composition, crop geometry, or anything the
invariant sweep gates.** It is a standing document, not a session note: it
describes how invariant work is done here and why, and it should be amended
when the practice changes rather than deleted when a task finishes.

For what the platform does today, what it cannot do, the examination catalogue
and the open risks, see `HANDOFF.md`. This file is the narrower one: how
composition work is done.

---

## What the invariants are

`services/image-engine/src/exam_photo/orchestration/output_invariants.py` states
properties every **delivered** photograph must satisfy, whatever the input.

They exist because composition was previously constrained only *during* crop
planning, and every one of those constraints is waivable — the last relaxation
tier waives them, and the geometric-projection fallback applies none. Final
validation checked byte size, pixel dimensions, format and DPI: properties of
the file, not of the photograph. So nothing guaranteed anything about what the
candidate actually received, and a defect only surfaced when a human looked at
an output and said it was wrong. That does not scale.

Two properties of the invariants matter and are easy to erode:

- **They are stated over the result, not over the search.** They are
  deliberately far looser than the composition targets. Their job is to catch
  the grossly wrong, not to enforce the ideal. A photograph that satisfies every
  invariant may still be mediocre; one that violates an invariant is broken.
- **A violation reports, it never refuses** (DEC-041). The candidate still gets
  their photograph. The value is that the violation is *recorded*, so it can be
  counted across a population, alerted on, and regression-tested.

## The gate

```bash
cd services/image-engine && .venv/Scripts/python.exe -m pytest tests/orchestration/test_output_invariants.py -q
```

`tests/orchestration/test_output_invariants.py` sweeps 960 synthetic geometries
— source frame, face size, face placement, output aspect, and how far the head
box reaches above the face box — and ratchets the violation count in
`_KNOWN_VIOLATIONS`.

**The ratchet may fall. It may never rise.** Raising it to make a change pass
defeats the only mechanism that keeps the gate honest. If a change genuinely
requires more violations, that is a finding to argue in the decision log, not a
number to edit.

The sweep needs no model: the planner consumes geometry, so the sweep
constructs geometry directly. It runs in about 20 seconds.

`HEAD_ABOVE_FACE` is the axis that earns its place. The planner is fed a head
box derived from the subject mask, and that box varies enormously with
hairstyle. Sweeping only clean geometry tests the planner's arithmetic while
missing the input that actually varies in production.

## Rules of engagement

These are the working rules for this area. They were each learned the
expensive way.

1. **No per-photo fixes.** Fix the class of defect and prove it with the sweep.
   A change justified by one photograph will be undone by the next one.
2. **Every threshold comment must state the measurement on both sides of it.**
   A bound with only one side recorded cannot be checked by the next reader, and
   at least one bound in this codebase was originally placed *past* both of the
   values it was derived to separate — a bound outside the range it came from is
   not a bound.
3. **Do not ship a signal whose reliability you have not measured.** Two were
   written, measured, found not to separate, and removed: eye-blink scoring and
   the chroma-noise guard. Removing beats shipping a dead constant. The same
   applies to checks: a check that cannot fail is worse than no check, because
   it reads as evidence.
4. **Measure against the owner's labelled photographs, not against a
   self-derived threshold.** Deriving a target from first principles and then
   optimising toward it is the documented failure mode of an earlier session.
   The current set is the 40 adversarial photographs; see *Reference material*
   below, including which set is retired.
5. **Move the planner and its validator together.** See below — this is the
   recurring defect class here.
6. **Never commit real candidate photos, processed outputs, mattes or model
   weights.** Numeric measurements and issue codes only. The public-domain
   golden fixture under `tests/golden-images/` is the sole exception and is
   already committed.

## The recurring defect class

**The planner promises one region and the validator judges another.**

DEC-029, DEC-038 and DEC-044 are all instances of it. The crop planner works
with several nested regions and it is easy to enforce one in the candidate
search while validating against a different one afterwards. The symptom is
always the same shape: the search selects a crop that its own validation then
rejects as a blocking error, or — worse — a correctly framed crop is reported as
clipping a subject that was never there.

The regions, from generous to strict:

| Region | What it is | Status |
|---|---|---|
| `preserve_box` | head estimate / portrait composition box, trimmed at the crown. Extends below the jaw and absorbs hair spread — roughly 1.14× the real head height, 1.31× its width | A *preference*, and only on the crown and the two sides. It has **no bottom clause**: its bottom is a geometric expansion into the neck, not an observation |
| `mandatory_box` | crown − top margin → chin + beard margin, spanning the head core ± side margin, plus every landmark the detector actually located | The **guarantee**. The candidate search enforces containment as a hard constraint |
| `face_box` | the raw BlazeFace rectangle | A coarse proxy that misses real anatomy in both directions. Not used for containment in adaptive mode (DEC-038) |

Rules that follow:

- Box containment (`head_coverage_ratio`, `face_contained`) and margin
  reporting are judged against `mandatory_box`, under the search's own
  condition: adaptive planning with subject clipping disallowed. Not against
  `outer_hair_relaxation_used`, which is the weaker and different statement
  that no candidate happened to keep the whole preservation box.
- Pixel retention (`mask_preservation_ratio`) is deliberately measured against
  the *generous* box. Keyed to `mandatory_box` it would return 1.0 by
  construction on every crop the search can select. It earns its place by
  covering what the box test cannot: foreground the crop drops from the outer
  region.
- If you change one of these, change the others in the same commit and say so.

### A preference expressed as an override is not a preference

The strict/relaxed mechanism in the candidate search prefers a crop that keeps
the whole preservation box. It is applied as an override — a strict candidate
wins outright whenever one exists — so it ranks *above* tier and cost. Anything
folded into it is thereby promoted above every constraint in the relaxation
ladder, intended or not.

This is not hypothetical. A `b_cand < preserve_box.bottom` clause once sat
there, and on every reviewed photograph it was discarding a fully compliant
tier-0 crop in favour of one 4–9 points looser below the chin. The sweep read
zero the whole time, because synthetic head boxes do not extend past the jaw
the way real ones do. Before adding anything to `strict_violation`, ask whether
it should outrank the exam's own composition requirements — that is what you
are deciding.

## Verifying before claiming

`.github/workflows/image-engine-ci.yml` is the source of truth. Reproduce the
relevant subset locally; `pytest` alone does not cover the eleven
`mandatory_*` marker suites.

```bash
cd services/image-engine && ruff format --check . && ruff check . && .venv/Scripts/python.exe -m mypy src tests
```

The marker suites need real model assets and the matching env vars. All models
are present under `model-assets/`; run from the repo root with
`EXAM_PHOTO_FACE_MODEL_PATH` / `EXAM_PHOTO_SEGMENTER_MODEL_PATH` and their
`*_SHA256` set as the workflow sets them, once per marker:

```bash
services/image-engine/.venv/Scripts/python.exe -m pytest services/image-engine -m "mandatory_rule_pipeline" -q
```

The eleven markers are `mandatory_segmentation`, `mandatory_refinement`,
`mandatory_crop`, `mandatory_crop_b`, `mandatory_background`,
`mandatory_output_preparation`, `mandatory_output_compression`,
`mandatory_rule_pipeline`, `mandatory_api`, `mandatory_rule_admin`,
`mandatory_engine_quality`.

## Reference material — local only, never commit

| What | Where | Notes |
|---|---|---|
| 40 adversarial photos | `C:\Users\dmbar\Pictures\new-test-images` | **The current set.** Filenames carry human labels across 11 defect classes; ten are labelled `perfect` |
| Label map | `services/image-engine/tests/fixtures/adversarial_label_map.json` | Committed, numeric/label only. Records where the engine deliberately disagrees with a label |
| Reviewed outputs | `C:\Users\dmbar\Pictures\Engine Outputs - Clean Set` | The ten `perfect` photos as the owner last reviewed them, at 413×531. Use as the before-side of any comparison |

**Do not use `Test Images` / `Test Images- Ideal Outputs` (the 60-photo paired
set).** The product owner has retired it. Use the 40-photo set above.
`scripts/benchmark_reference_pairs.py` targets the retired set and should not be
run; the distribution figures quoted in `deterministic_crop_planner.py` and in
DEC-037 were measured from it while it was current and are kept as the record of
how those constants were derived, not as an instruction to re-measure.

The working loop for composition changes is: run the ten `perfect`-labelled
photographs at 413×531 through `process_rule`, measure head height, above-hair
and below-chin on the output, and compare against `Engine Outputs - Clean Set`.
It takes a few minutes, and it catches what the synthetic sweep structurally
cannot — see the note under **State** below.

### The owner's verdicts on the reviewed outputs

Accepted 4, 5 and 13. Flagged 31 and 35 as too loose below the chin, 17 for a
detached hair fragment, 18 and 19 for soft hair edges, and 8 for
under-enhancement. The two below-chin flags are fixed (DEC-044); M22 is
tracked as two separate defects. The soft/smudged-edge part (18, 19, and the
non-fragment part of 17) is fixed by DEC-033's amendment -- the trusted-alpha
path was skipping an anti-halo contrast correction the coarse-mask path
already had. The detached hair fragment on 17 is a different defect (a
disconnected mask region, not edge softness) and remains open. The
enhancement gap on 8 is DEC-043 work.

Those verdicts are also what the below-chin invariant is calibrated on: every
accepted photograph sat at or below 0.155 and the two rejected as too loose sat
at 0.188 and 0.190, so the bound is 0.175. It reports rather than refuses.

## State

Sweep at **0 violations** of 960 (2026-08-04). Delivered below-chin space across
the sweep measures min 0.075, median 0.103, p90 0.137, max 0.151, against an
approved-ideal median of 0.102.

On the ten photographs labelled `clean` in the 40-photo adversarial set, run at
413×531, below-chin space as a fraction of frame height:

| photo | before | after | | photo | before | after |
|---|---|---|---|---|---|---|
| 4 | 0.155 | **0.081** | | 18 | 0.151 | **0.117** |
| 5 | 0.124 | **0.104** | | 19 | 0.147 | **0.098** |
| 8 | 0.124 | **0.105** | | 27 | 0.111 | 0.111 |
| 13 | 0.117 | 0.117 | | 31 | 0.188 | **0.146** |
| 17 | 0.155 | **0.111** | | 35 | 0.190 | **0.111** |

Head height rose or held on all ten. All ten satisfy every invariant; two did
not before. 31 is the loosest at 0.146 because its subject's hair pins the
crop's sides — the strict preference doing the job it is actually for.

Note what the sweep alone would have told you: nothing. It read zero while
photograph 35 sat at 0.190, because synthetic head boxes do not extend past the
jaw the way real ones do. **Run the labelled photographs too.**

**Known gap: `check_composition_invariants` has no pipeline consumer.** Its only
caller is the sweep. The module's own docstring describes the invariants as
checks over the delivered photograph producing a finding per DEC-041, and that
half is not built: `orchestration/final_validation.py` does not call it, so a
real candidate upload is never measured against these bounds. The sweep gates
the *planner* against synthetic geometry, which is genuinely useful and is what
caught the below-chin defect, but it is not the population-level detector the
module was written to be. Wiring it into final validation — measuring crown,
chin and crop box on the finished image and attaching violations as findings —
is the obvious next step and is not done.

Open composition work is tracked in `docs/09_DEVELOPMENT_ROADMAP.md`,
Milestones 19–30. The product blocker is M19: all 11 encoded exams are
provisional with `dimensions.mode` `"unspecified"`, so the engine cannot yet
size a photograph for any real examination.
