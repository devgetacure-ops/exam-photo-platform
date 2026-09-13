# Prompt for the next session

Paste everything below the line as the first message of a fresh session, from
`C:\Projects\exam-photo-platform` so `CLAUDE.md` and `AGENTS.md` load.

---

You own this repository. All of it. Branch `feat/upload-kit-ui`; everything is
pushed except the payment simulator commit `b3762d8` and the handoff commit
after it. Do not push unless I ask.

Read `HANDOFF.md` first — *Platform State*, *Running the test setup* and *Open,
found while the owner tested* above all — then `docs/08_DECISION_LOG.md` from
DEC-081 to DEC-089. Check `git status` before anything else.

## What this session is for

**Fixing the issues I collected while testing the whole product by hand**, on
my computer and my phone, with the engine running and the payment simulator on.
I will bring them as screenshots and notes.

## How we will work — this matters more than anything else here

1. **I send issues, one or several at a time: screenshots, what I did, what I
   expected.** Screenshots may arrive as file paths or as a folder with the note
   in each file's name.
2. **For each one you investigate and plan. You do not change anything.** No
   edits, no commits, no fixes "while you are there". Read code, read logs, run
   read-only checks, reproduce against the running engine or site — that is all.
3. **Reply to each issue with**: what you understood I saw; the root cause, with
   the file and line; whether it was your own earlier mistake (say so plainly if
   it was); the fix you propose; what else it touches; and how you will prove it
   is fixed. Keep a running numbered list of every issue so far, so nothing is
   lost between messages, and repeat the list when I ask for it.
4. **If two issues share a cause, say so and plan them as one.** If a fix needs a
   decision that is mine — a product choice, a wording, a trade-off — ask it as a
   question in the plan instead of choosing for me.
5. **When I say to act, fix everything on the list in one pass**, verify all of
   it, and commit. Then report what changed, per issue, and anything you could not
   verify.

## Already diagnosed, waiting to be fixed

**A photograph under an examination's minimum KB is refused.** "We could not
prepare this one · Pipeline final byte size invalid", on SBI Junior Associates
and about 20 other records with a byte floor (IBPS, SBI, RBI, LIC, NABARD, NIACL,
GIC, XAT, TNPSC, KEAM, RRB). The diagnosis and the planned fix are in
`HANDOFF.md` under *Open, found while the owner tested*. It is item 1 on the list;
add my new issues after it.

## Starting the test setup when I ask for it

Start the `engine` and `web-3100` launch configurations with `preview_start`.
The desktop app stops both whenever its window closes or the machine sleeps, so
"the engine is off" means restart both. Before starting, check the Wi-Fi address
is still `192.168.29.72`; if not, update the two `.env.local` files the handoff
names and restart. Then confirm `/ready` says `ready` and `payments: simulated`,
and that the site loads at `http://localhost:3100` and `http://192.168.29.72:3100`.
This machine has 7.4 GB of memory; if less than about 2.5 GB is free, tell me
which apps to close — do not close them yourself.

## What is binding when you act

- **The phone comes first.** Most candidates are on phones. Nothing scrolls
  sideways on a phone; lay content out to fit. Check 360, 390 and 430px, tap
  targets at 44px, inputs at 16px, and test through the LAN address with touch
  input (`apps/web/scripts/phone-check.mjs` has `tap` and `drag` steps), never
  only `localhost`.
- **The design system.** Flat by contract: hard borders, solid offset shadows,
  no radius, no blur, no gradient. Tokens on `.euk` in `src/app/system.css`, one
  signal colour, nothing invents a colour. `--bar` is the single sticky-height
  token.
- **One class name, one owner.** `src/tests/stylesheet-namespace.test.ts` fails
  on a name defined in two stylesheets.
- **Motion is transform and opacity only**, gated on `prefers-reduced-motion`,
  with a pause control for anything that moves by itself.
- **Nothing invented.** No statistic, testimonial or figure without a source;
  a value that is ours is marked `est.`
- **Produce, never refuse for appearance** (DEC-041). A file with something to
  say about it is `prepared_with_findings`, not a failure.
- **No disclaimers in the flow.** Independence, acceptance and liability live on
  the policy pages; the flow carries only the agreements DEC-086 put there.
- **The owner's name, address and phone never go into git**, docs or commit
  messages. They come from `EUK_BUSINESS_*` in the environment.
- **The payment simulator stays local.** It must never run beside Razorpay keys,
  and nothing may be released except through `apply_release_instruction`.

## Done means

- Web (`apps/web`): `npm run lint`, `npm run typecheck`, `npx vitest run` (232
  passing before your changes).
- Engine (`services/image-engine`): `ruff format --check .`, `ruff check .`,
  `.venv/Scripts/python.exe -m mypy src tests`, and `pytest` for what you touched
  (the API suite had 262 passing). For a photograph or ink change, look at the
  output images, not only the numbers.
- **Never run `npm run build` while the dev server is up** — it writes into the
  same `.next` and the dev server then serves stale CSS. Build in a separate git
  worktree instead, and expect 552 pages.
- Run the design detector at a phone viewport on any page you changed:
  `bash .claude/skills/impeccable/scripts/impeccable detect --viewport 390x844 <url>`,
  and compare against the page before your change rather than assuming a finding
  is new.
- Re-test each fixed issue the way I found it: against the running engine and
  site, on a phone viewport where it was a phone issue.
- Update the decision log and `docs/07_REQUIREMENTS_TRACEABILITY.md` for anything
  that changes behaviour, keep `HANDOFF.md` current, and commit in conventional
  style.
