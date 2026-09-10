# Owner decisions on the UI/UX direction

**Recorded 10 September 2026.** These are rulings the product owner gave in
session, after `STRUCTURED_DIRECTION.md` and `TECHNICAL_COMPANION.md` were
written. Several resolve conflicts those documents left open; the resolutions
are marked with the C-ID they close.

Two kinds of statement appear below and they are kept apart deliberately:
**Decided** is the owner's ruling. **Reading** is this session's interpretation
of it, recorded so a wrong interpretation is visible and correctable rather
than buried in code. Where the owner has not spoken, the item sits under *Open*
and must not be inferred.

No implementation has begun. The owner has said explicitly to stand by.

---

## Scope

**Decided.** The work is **the frontend only**. *"do not play with the exams
and rules and all. i said you only about the UI/UX, the frontend."*

No engine changes, no rule-record changes, no changes to the catalogue or to
`pricing.py`.

**Decided.** The current site is scrapped, not evolved. *"scrape off the
current site it is trash. build it newly afresh."* Combined with *"scrape
whatever you want."*

**Reading.** Presentation is rebuilt from zero; the data and contract layer is
kept — catalogue reading, `api-client.ts`, `types.ts`, the job state machine,
and the server-quote/entitlement logic. Several decisions' worth of
correctness lives there and none of it is why the site looks bad. This line
was proposed and not contradicted, but it was also not confirmed in those
words.

**Decided.** Documents that obstruct the UI/UX plan may be modified.
*"if there is something previous handoff or documents or any files that comes
in the way of this new plan, modify it. i do not care."*

**This is standing authority, not a per-item release.** The owner has since
made that explicit: *"i cannot say you again and again — that you can change
the previous decisions according to what is decided now. no need to worry."*

So: where current direction conflicts with an earlier decision, handoff note
or document, the earlier one is amended as part of the work and the change is
reported. It is not raised as a blocker and permission is not sought. The
decision log, the handoff and the traceability matrix exist to carry context
forward, not to gate it.

---

## Design

**Decided.** **Desktop and mobile are designed separately**, not one
responsive layout reflowing.

**Decided.** **SEO and design are both to be served, with no trade-off between
them.** *"handle both seo and design- both should be taken care of well."*

**Reading.** One statically generated document per exam, as now, with desktop
and mobile as genuinely different compositions rather than breakpoints of each
other. The crawler sees one canonical page.

**Decided.** **Decoration is welcome.** The earlier reading — that *"everything
should be functional"* banned ornament — was an over-correction and is
withdrawn. *"do not take nothing decorative so hard. keep decoration, but i
hate those labeling and numbering."*

What remains banned: decorative section labels ("eyebrows"), section
numbering, and the other AI-default tells the original brief lists.

**Decided.** Performance is a **hard budget, not a caveat** — numeric targets
measured on representative hardware, not asserted. Motion, illustration and
micro-interaction are wanted; frame cost on a slow Android on mobile data is
the constraint they are spent against.

**Decided.** **Real output is shown. No fictionalism.**

**Reading.** The honest construction: the *subject* is synthetic and declared
as such, the *transformation* is real — a generated portrait put through the
actual engine, showing its actual before and after. Nothing about the result is
illustrated. This satisfies the owner's rule and the standing rule against
using a real candidate's face.

---

## Typography and language

**Decided.** **English only for now.** Hindi, Odia, Bengali, the South Indian
languages, Punjabi, Gujarati and Marathi are planned later.

**Consequence.** This decides typography before anything is drawn. A family
must carry, or have a well-matched sibling for, Devanagari, Bangla, Odia,
Gurmukhi, Gujarati, Tamil, Telugu, Kannada and Malayalam. It also rules out the
obvious safe answer, Noto, on the grounds the brief cares about most: it is the
generic default the owner says they can detect instantly.

Recorded as a lead, not a decision: Anek (Universal Thirst) is an openly
licensed variable family purpose-built across exactly that script range. The
real exploration happens when work starts.

---

## Pricing and entitlement

**Decided (closes C03).** **₹8 is a total ceiling**, not a surcharge.
*"in 8 we can give all the things that any exams ask for."* So ₹3 for one, ₹5
for two, ₹8 for everything an examination asks for. This agrees with DEC-070
and with the current engine.

**Decided (closes C01, against current engine behaviour).** **PDF work is
delivered only as part of a paid image order.** A candidate whose kit is
documents alone cannot check out or download; they are told to buy the image
service first.

**Reading.** At least one chargeable image in the kit — photograph, signature
or thumb impression — unlocks the free PDF work.

**Consequence, and it falls outside the frontend scope.** `pricing.py`
currently prices a document-only kit at zero and will let it through. The
interface can decline to offer checkout, but the server is authoritative on
quote and order, so until the engine refuses as well this is a soft gate and
bypassable. Recorded so it is not mistaken for enforced.

**Decided.** Strike-through prices are ₹4 / ₹8 / ₹10 against ₹3 / ₹5 / ₹8, as
specified in the original brief. The earlier objection to them is withdrawn.
C02's note stands: the basis for a publicly displayed former price should be
checked by someone qualified before publication.

---

## Text printed on the photograph

**Decided.** The platform will support it. *"if exam demands text on
photograph, we will do that too. we will do everything that is needed."*

**Decided — the layout, in the owner's own terms.** A margin strip along the
bottom of the image, with a white background or whatever colour the exam
specifies. The candidate's name on the first row; the date on a second row
below it, with spacing between the two. Where an exam requires it, the
interface presents text fields for name and date, and preparation runs with
those values.

**Frontend share of the work.** The fields, their validation, and a preview of
what will be printed.

**Outside the frontend scope, and therefore not this work.** Rendering the text
into the image. Recorded so it is not assumed done.

**Raised, not resolved.** The strip must sit *inside* the target dimensions —
exams of this class demand exact pixel sizes, so it cannot be added on top. It
comes out of the frame, which shrinks the portrait area and presses against the
head-coverage floor. Either the composition tightens or the strip stays thin.
This is an engine question and should be answered deliberately rather than
discovered during implementation.

**Also raised.** Printing a name means **collecting a name**. The platform
currently touches no PII at all — filenames are deliberately generated PII-free.
This changes the privacy posture, the DPDP surface and the retention wording.

Affected records: 3 requirements, all `candidate_photograph` — Kerala PSC one-
time registration, TNPSC Combined Civil Services IV (Group IV), TNPSC Combined
Technical Services 2025. Each encodes `imprint.policy: required` with fields
`candidate_name` and `photograph_date`, and **encodes no placement, size or
colour** — that evidence does not exist in the records today.

`partially_supported` remains a state in the model regardless of these three
being closed.

---

## Image assets

**Decided.** When an image is needed, this session writes a generation prompt
and the owner produces the asset with a capable model, rather than being asked
to supply one.

**Consequence — this closes the open portrait question by replacement rather
than by ruling.** `apps/web/public/examples/portrait-*.jpg`, whose provenance
text describes a European GAN asset while the shipping image is of an Indian-
looking person, get replaced with newly generated assets whose provenance is
known and documentable. The earlier request for an adjudication is withdrawn.

Prompts will be delivered as one batch once the design establishes what it
needs. Expected: specimens across a range of skin tones, lighting conditions
and framing errors; signature and thumb-impression sheets; a certificate page.

---

## Open — do not infer

| Item | State |
|---|---|
| **Support surface** (C10) | Unanswered. Private ticketing was recommended over a public forum, on the grounds that a public forum means moderation and candidates posting screenshots containing their own face and signature. The owner has not ruled. |
| **PDF → image** (DEC-052) | The original brief asks for it. Engine work, and therefore outside the current frontend scope — it is unbuilt because nobody is building it, not because it is awaiting a ruling. When it is picked up, DEC-052 is amended or upheld on its merits: rasterising a digitally issued certificate destroys what makes it verifiable, which is a reason to weigh, not a veto. |
| **What survives the scrape** | Working assumption recorded above under *Scope*. Not confirmed in the owner's words. |
| **Disqualification statistics** (C06) | No citable figure was found and none may be invented. An alternative was proposed — telling the story through the catalogue's own contradictions across 132 examinations and 418 requirements — and has not been ruled on. |
| **"our GPUs"** (C06) | The claim is false; inference is CPU-only. The sentence cannot be published as written. No replacement wording agreed. |
| **WhatsApp file delivery** (C08) | `wa.me` cannot attach a file. Real delivery needs WhatsApp Business API — separate integration, template approval, per-conversation cost. Not decided. |
