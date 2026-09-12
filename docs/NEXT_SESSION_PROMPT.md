# Prompt for the next session

Paste everything below the line as the first message of a fresh session, from
`C:\Projects\exam-photo-platform` so `CLAUDE.md` and `AGENTS.md` load.

---

You own this repository. All of it. Branch `feat/upload-kit-ui`, clean and
pushed as of 2026-09-12.

Read `HANDOFF.md` first — particularly *The design direction, settled* and
*Current UI state* — then `docs/ui-direction-2026-09-10/MOBILE_PLAN.md`, which
is the plan for this session's work, and `docs/08_DECISION_LOG.md` from DEC-063
to DEC-080. Check `git status` before you start.

## What this session is for

**The phone build, as a design of its own.** The owner has said this twice and
was unhappy the first time it was delivered as a reflow:

> "the mobile-view design is just like another responsive design, just
> everything stacked upon each other. but clearly i strictly wanted you not to
> do that. i always wanted a mobile first design for mobile-view unlike
> responsive, completely dedicated and special design… more than 70% of people
> would use it in mobile."

The desktop view is finished and signed off across two rounds of the owner's
notes. **Do not regress it.** This work is additive: a phone build beside it,
switched by width, not a rewrite of what exists.

### The owner's four answers, already given

- A **four-step flow** for preparing files, with a sticky bar.
- An **action-only bottom bar**, plus a subtle top bar.
- A **short home**, with the rest behind a link.
- **Include the PWA install.**

And: *"also consider iphones."* Safe-area insets, `dvh` with a `vh` fallback,
16px inputs so iOS does not zoom, and the iOS 15.0–15.3 `showModal` guard are
all already handled in `components/m/sheet.tsx` — follow that file's lead
rather than reinventing it.

### Where it stands

**Phase 1 shipped**: `apps/web/src/components/m/` holds the app bar, action
bar, sheet, prepare flow, prepare CTA and the phone examination file list;
`app/mobile.css`, `app/manifest.ts` and the icons exist; the flow has tests in
`src/tests/prepare-flow.test.tsx`. Phases 2, 3 and 4 of MOBILE_PLAN's order of
work are unstarted — home and search, then PDF/support/policies, then install
plus a pass on real mid-range hardware.

One trap already paid for: hiding the desktop workspace on a phone means
hiding `.euk-kit`, not its grid wrapper `.euk-kit-layout`. Hiding the wrapper
left the upload panels behind, so the page offered two ways to upload the same
file.

## How the owner works

They send screenshots with issues, one at a time, and expect you to **ingest
and plan without acting** until they say to start. When they do, they expect
all of it fixed in one pass, verified, and committed. Say plainly when
something they reported was your own earlier mistake — twice now the real cause
was a fix that never applied, and saying so quickly was worth more than the
fix.

## What is binding

- **The design system.** Flat by contract: hard borders, solid offset shadows,
  no radius, no blur, no gradient. Tokens on `.euk` in `src/app/system.css`,
  one signal colour, nothing invents a colour.
- **One class name, one owner.** The stylesheets are global.
  `src/tests/stylesheet-namespace.test.ts` fails on a name defined in two
  sheets without a stated reason — three collisions in one session once
  shipped a line drawing as a solid orange block.
- **Motion is transform and opacity only**, gated on `prefers-reduced-motion`,
  and anything that moves by itself needs a pause control (WCAG 2.2.2).
- **Nothing invented.** No statistic without a source, no exam alias that is
  not a real short form, no fictional testimonial. Where a figure is ours and
  not the examination's, it is marked `est.`
- **`--bar`** in `system.css` is the single height token anything sticky or
  anchor-scrolled positions against. Use it; do not add a second number.

## Verification that is not optional

- **Headless virtual time does not drive `requestAnimationFrame`, and the
  Browser pane does not paint while it is hidden.** A screenshot proves layout
  and nothing else. Motion is proven by stepping a stubbed clock in a test, or
  by reading `getAnimations()` and seeking it.
- **Never run `npm run build` while the preview dev server is up.** It writes
  into the same `.next` and the dev server then serves a stale stylesheet
  silently, which reads exactly like a CSS bug in the code you just wrote.
  Clear `.next` and restart if it happens.
- **Port 3000 is taken on this machine by a different project.** Use the
  `web-3100` entry in `.claude/launch.json` (`preview_start` with that name).
  It binds `0.0.0.0`, so a real phone on the same network can reach it at
  `http://<machine-ip>:3100`.
- Check every screen at **360, 390 and 430px**, measure tap targets at 44px,
  and run the design detector at a phone viewport:
  `bash .claude/skills/impeccable/scripts/impeccable detect <url>`.
- Done means: `npm run lint`, `npx tsc --noEmit`, `npm test` (169 passing
  now), `npm run build` (416 pages), and the detector showing no new finding.

## Still open, and not yours to invent

The owner still owes: the exam facts file for "Worth knowing" (the current one
is generated and filtered), business details and a named grievance officer for
the policy pages, and a decision on the `examupload.com` domain. Ask; do not
fill them in.
