# Prompt for the next session

Paste everything below the line as the first message of a fresh session, from
`C:\Projects\exam-photo-platform` so `CLAUDE.md` and `AGENTS.md` load.

---

You own this repository. **All of it.** The two-lane split with Codex is
retired as of 2026-09-07 — there is no other agent, no coordination protocol,
no staging commits by path, and `apps/web/src/lib/types.ts` is now simply
yours to change.

Read `HANDOFF.md` first, then `docs/08_DECISION_LOG.md` from DEC-063 to
DEC-079. Branch `feat/upload-kit-ui`. Check `git status` before you start.

## What this session is for

**The interface.** The engine is complete for everything the product owner has
asked for: payment end to end with server-computed prices, delivery by
download and email, retention with a candidate-controlled extension, real
staged progress, an instant lighting toggle, per-examination facts, and a
capacity guard. 794 fast tests, 127 model-backed, all green.

The interface is *correct* and *conservative*. The owner asked for world-class
and got competent. That gap is the work.

## Do these two things before anything else

**1. Rebuild the site.** It generates 52 exam pages against a
132-examination catalogue (DEC-079), and its own QA notes call four shipped
engine features "absent" — the lighting toggle, staged progress, exam facts
and email delivery all exist. Nothing you assess is real until you rebuild.

```bash
cd apps/web && npm run build && npx next start -p 3007
```

**2. Look at it.** Open it in the browser pane and screenshot desktop and
mobile. Do not form an opinion from the code. The previous agent's failure was
not sloppiness — it was choosing continuity over ambition, explicitly, in
writing — and you will only see that by looking.

## The first deliverable is not code

The owner's style list — Bauhaus, neumorphism, glassmorphism, neobrutalism,
claymorphism, aurora, retro-futurism, minimalism, and more — **cannot be
satisfied.** Neubrutalism and neumorphism are opposites. Minimalism and
synthwave cannot coexist. Implementing all of it produces noise, and it is
very likely why the last attempt retreated to safe: given a list that cannot
be satisfied, committing to nothing is defensible.

So: **write a short recommendation naming the two or three directions to
commit to, the argument for them, and why the rest are refused.** Get it
approved before building. The owner has agreed to this sequencing. Judge
yourself on the quality of that refusal more than on the pixels.

Constraints on whatever you choose:

- **Typography carries most of it.** The owner said so and they are right; the
  current Instrument Sans setting is the strongest thing on the page.
- **The product takes ₹3 for a file a candidate's career depends on.** Premium
  here means *trustworthy*, not decorated. Every effect has to survive that.
- **It must work on a slow Android phone on mobile data**, on the morning of a
  deadline. That is the actual user. Motion that costs frames is worse than
  no motion.

## What must survive any redesign

**The boundary is carried three ways, not one.** Grouping ("We prepare these" /
"You do these yourself"), colour, and *affordance* — a requirement the platform
does not prepare has no upload control at all. Removing any one of the three
puts the product's worst failure mode back on the table: a candidate believing
we prepared something we did not. Express all three differently if you like.
Do not reduce them to two.

**Four support states, never collapsed to a boolean.** `supported`,
`partially_supported`, `guidance_only`, `not_yet_supported`.
`partially_supported` means we produced a file that still needs something we
cannot do — printing a name onto a photograph, for TNPSC and Kerala PSC. It
must never render as success.

**Every claim carries evidence or does not appear.** The catalogue refuses to
assert a file size no authority published; the marketing may not hold itself
to a lower standard. No invented statistics. No "our GPUs" — inference is
CPU-only. No claiming detections that were built, measured and removed
(sunglasses, head coverings, closed eyes, beard line).

**The published retention wording is "deleted within 30 minutes, or within an
hour if you ask us to keep it"** — not a flat thirty. And the warning must come
*before* checkout, because an extension can only be taken before the deadline.

**The estimate marker.** 63 values across 32 examinations are ours, not the
authority's. A redesign that drops the marker turns an honest disclosure into
a silent claim.

## Three UI problems DEC-079 just created

1. **80 of 132 examinations have no photograph specification** — served for a
   signature or certificates alone. Their *rules* page has almost nothing to
   show. It degrades to empty rather than breaking, which is correct and looks
   like a hole. Design that state.
2. **`not_yet_supported` now appears on 72 requirements**, up from a handful.
   Listed deliberately: the examination does ask for a photograph, and hiding
   it would tell the candidate otherwise. It must read as "we cannot prepare
   this yet", never as a failure.
3. **The picker went from 52 examinations to 132.** Search and the list should
   be looked at against that scale.

## One thing that is still open and is not yours to decide

`apps/web/public/examples/portrait-*.jpg` are committed. The previous agent
found that the provenance text describes an **older European GAN asset** while
the image actually shipping is of an **Indian-looking person**. Those do not
match. AGENTS.md forbids committing real candidate photographs. Ask the owner
before this branch merges; do not resolve it yourself.

## The thing you have lost, and must replace

There is no second agent reviewing your work any more. Three defects in the
2026-09-07 session were exactly what a second reader catches:

- a derived "fact" that contradicted the fact printed directly beside it;
- a variant swap that would have delivered `..__alt.jpg` to portals that
  reject on filename alone;
- a generated sidecar named inside the `exam_*` namespace the encoder deletes,
  which would have vanished silently on the next run.

Each was caught by a test, and only because the test was written to attack the
change rather than confirm it. **Write the negative test first.** It is now the
only thing standing where the second reader used to be.

## Verifying

From `services/image-engine`, with nothing else running — the machine has
7.4 GB and the engine wants 2.4 GB, so a live `serve-api` alongside pytest
produces numpy allocation failures that read exactly like real defects:

```bash
ruff format --check . && ruff check . && mypy src tests && pytest
```

From `apps/web`: `npm run lint && npm run typecheck && npm test && npm run build`.

Current: 166 files clean, 794 passed / 15 skipped, 127 marker-gated passed,
92 Vitest passing, production build green.

## Traps that will cost you time

- **Never benchmark through the CLI.** Every invocation reloads a 941 MB ONNX
  model. Measure through the warm service. Warm is ~10 s per photograph.
- **`model-assets/` is gitignored but populated on this machine.** Do not
  re-download. If a `mandatory_*` test fails oddly, check the model is there
  before suspecting the code.
- **Judging output quality needs the purchase gate off.** Run with
  `EXAM_PHOTO_PURCHASE_GATE_ENABLED=false`, or `/test` shows you the
  watermarked half-resolution preview and you are judging the wrong thing.
- **`/ready` is not `/health`.** The deployment depends on the distinction.
- **Do not re-run `extract_deliverables.py` after a research merge** — it
  regenerates the deliverables file and discards everything merged since.
- **Regenerate `candidate_facts.json` after every encode**
  (`python scripts/generate_exam_facts.py`). A test fails if it is stale.
- **INT8 quantisation is closed**, measured and rejected. Do not re-try.
- **DEC-040's second matte is not on the table.** Half the runtime, and a real
  quality trade the owner has ruled out.
