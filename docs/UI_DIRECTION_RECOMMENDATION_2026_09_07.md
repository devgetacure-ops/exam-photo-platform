# UI direction: what to commit to, and what to refuse

> **Superseded, 10 September 2026.** Written before the owner's full UI/UX
> brief arrived. The brief's point 19 already contained the selection
> instruction this document argues for, so its framing — that the style list
> could not be satisfied — was uncharitable. Current direction and rulings
> live in `docs/ui-direction-2026-09-10/`.

**Date**: 2026-09-07 · **Status**: Proposed, awaiting product owner approval ·
**Precondition**: nothing in `apps/web` is restyled until this is approved.

---

## Why this document exists instead of code

The style list — Bauhaus, neumorphism, glassmorphism, neobrutalism,
claymorphism, aurora, retro-futurism, minimalism — cannot be satisfied as
written. Not because it is long, but because half of it names a **structure**
(Bauhaus, brutalism, minimalism: grid, hierarchy, what goes where) and half
names a **surface texture** (neumorphism, glass, clay: what a single element
feels like). You can hold one structure and one texture at a time. Three
textures at once is not a style, it is noise — and two of the ones listed are
formal opposites: neumorphism is defined by soft dual shadows on a mid-grey
ground, neobrutalism by hard edges and flat fills with the shadows removed.

Read as a specification the list is unbuildable. Read as a **complaint** it is
precise and correct, and I think this is what it is: *the site looks like every
other SaaS template.* It does. That is a true observation about the current
build and it is the thing worth fixing.

So this proposes one structure, one texture, and one place to spend the visual
budget — and refuses the rest by name, with the reason.

---

## What the choice is actually constrained by

These are not preferences. Each one eliminates candidates.

1. **₹3 for a file a career depends on.** Premium here means *trustworthy*, not
   decorated. Anything that reads as a toy costs conversions directly.
2. **A slow Android phone, mobile data, deadline morning.** That is the user.
   Effects that cost frames are worse than no effects.
3. **SEO is the primary channel** (WEB-003, and the reason 264 pages are
   statically generated). The design must be *text*, server-rendered and
   crawlable. A hero that depends on canvas or WebGL is invisible to the
   channel that pays for the product.
4. **Colour is already semantic, deliberately** (`globals.css`). It carries
   support state and which side of the boundary a requirement is on. It is not
   available for mood.
5. **The three-way boundary and the four support states must survive**
   (grouping, colour, affordance; `supported` / `partially_supported` /
   `guidance_only` / `not_yet_supported`).
6. **Typography carries most of it.** The owner said so and is right — the
   Instrument Sans setting is the strongest thing on the current page.

---

## Commit to these

### 1. Swiss editorial structure — the primary commitment

A visible grid, a **type scale with real contrast**, hairline rules as
structure, asymmetry, and content set like a published document rather than
floated in cards.

This is what Bauhaus actually is when taken seriously: grid, hierarchy and
function-first form — not primary-coloured circles. It is on the owner's list
already.

Why it wins here:

- **It is the trust argument.** A rules page that looks like a published
  specification is more credible than one that looks like an app. We are
  competing with the authority's own PDF; looking like a considered document is
  an asset, not a compromise.
- **It costs nothing at runtime.** Type, rules and grid are the cheapest things
  a browser draws. It is the fastest option on the list, on the phone that
  matters.
- **It is entirely text**, so the SEO channel gets everything.
- **It fixes the specific failure.** The current page has seven section
  headings at effectively one size and one two-column split repeated seven
  times. There is no hierarchy to read, only rhythm to skim. A real scale — a
  page-defining figure, a section head, a standfirst, a caption, a specimen
  label — is what makes a page feel authored.

**This is explicitly not "minimalism".** See the refusals.

### 2. Flat, hard-edged blocks — the texture commitment

Neobrutalism's *structural* half and nothing else: 1px hard borders instead of
soft shadows, flat blocks of colour, no gradients, honest edges, oversized type
where it earns it.

Dialled to editorial, not to toy. I take the hard edges and flat fills; I
refuse the register — the clashing saturated pinks and limes, the rotated
sticker labels, the comic offset shadows. At ₹3 for a career document that
register reads as unserious, which is the one thing we cannot afford.

Why this texture and not another:

- **It is the cheapest thing on the list to paint.** Solid fills, no blur, no
  gradient, no shadow spread — one compositing pass. On a mid-tier Android it
  is effectively free, where glass and neumorphism are not.
- **It makes the boundary easier, not harder.** "We prepare these" versus "You
  do these yourself" wants to be two *blocks* with an edge between them. Flat
  colour with a hard border is the most legible possible expression of a
  boundary; soft shadow is the least.
- **It gives the page a point of view** without asking colour to stop being
  semantic.

Structure + texture together: strict grid, strong type, hard-edged flat blocks.
That is a look with an argument behind it, and it is the *fast* option.

### 3. Show the actual file being made — where the visual budget goes

Not a style. A decision about what to spend ambition on.

The landing page currently shows no evidence of the product's own output. The
comparison slider is captioned *"Illustration only · not an engine result."* We
sell a file and we show a drawing of one.

The single most striking thing this product could put on screen is the real
work: the crop frame drawn on the photograph, the specification annotated on
the output, the before and after at the exam's actual pixel dimensions, the
filename the portal expects. That is what makes somebody stay and explore, and
it is simultaneously the strongest trust argument available — far stronger than
any surface treatment.

This has a blocker and it is a real one: see *Open, not mine to decide* below.

---

## Refuse these, by name

**Neumorphism.** Three reasons and any one is enough. (a) Its contrast failure
is documented and structural — controls defined only by shadow depth cannot
meet contrast requirements. (b) It would make "this requirement has an upload
control" versus "this one deliberately has none" a difference of shadow depth,
which is exactly the boundary signal I am forbidden to weaken. (c) It is the
formal opposite of the texture that serves us, so it cannot coexist with it.

**Glassmorphism.** `backdrop-filter: blur()` is the most expensive common
effect on the exact device class named as the real user; it forces a
compositing layer per element and drops frames while scrolling on mid-tier
Android. Its legibility also depends on what sits behind it, which varies by
exam and cannot be controlled. Cost with no compensating argument.

**Claymorphism.** Soft, inflated, high-saturation, rounded — the aesthetic of a
children's app. Directly opposed to the product's proposition.

**Aurora, synthwave, retro-futurism.** All three are colour-as-decoration.
Colour here already means support state and boundary side. Adding a decorative
colour field means either abandoning that or running two colour languages that
compete for the same signal. Animated gradients are also continuous GPU work
that carries no information.

**Minimalism, as a named direction.** Refused because it is what the site
already is, and it is what produced the result the owner is unhappy with.
Minimalism is an absence; absence is not a point of view, which is why the
previous attempt could retreat into it and still call the brief satisfied. The
restraint is kept — inside the Swiss direction, as a means. It is not the goal.

---

## What must survive, and how it is expressed in this direction

| Invariant | Expression |
|---|---|
| Boundary carried **three** ways | Grouping → two hard-edged blocks with a real edge. Colour → semantic, unchanged. Affordance → unchanged; no control where we do not prepare |
| Four support states, never a boolean | Four distinct block treatments, not one badge with four colours. `partially_supported` must never read as success |
| Every claim carries evidence | Unchanged. No invented statistics, no "our GPUs" (inference is CPU-only), no claiming removed detections |
| Retention wording | "deleted within 30 minutes, or within an hour if you ask us to keep it" — and the warning stays **before** checkout |
| The `est.` marker | Kept and made *more* prominent, not less. See the defect below — it is currently broken |

---

## Open, not mine to decide

`apps/web/public/examples/portrait-*.jpg` ships on all 52 photograph exam
pages, as the "Good lighting" specimen and both "Avoid these" examples. The
provenance text describes an older European GAN asset; the image actually
shipping is of an Indian-looking person. They do not match. AGENTS.md forbids
committing real candidate photographs and these are now in history (`27bf5a3`).

**This must be answered before the branch merges, and it gates commitment 3** —
"show the actual file being made" is a stronger idea if the specimen imagery is
sound and an unshippable one if it is not.

---

## Sequencing, if approved

1. Fix the four shipped-but-denied features and the defects listed in the
   session findings — these are correctness, not taste, and they should not
   wait behind a redesign.
2. Type scale and grid first. Everything else follows from it.
3. Re-cut the landing page against the new scale; the section rhythm is the
   thing that reads as templated.
4. The three DEC-079 states — the 80 no-photograph rules pages, the 72
   `not_yet_supported` requirements, the 132-exam picker.
5. Mobile as its own design, per the owner. It is currently a reflow.
