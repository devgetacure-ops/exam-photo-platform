# Design tooling

Installed 10 September 2026 for the UI/UX rebuild. **None of it is committed.**
It is per-machine tooling, reinstalled by the commands below.

## Why it is gitignored

`npx impeccable install` writes a **15 MB `windows-x64` binary into each of
three harness directories** — `.claude`, `.agents`, `.github` — 45 MB of
identical, platform-specific executable. Committing that would put it in git
history permanently and hand a Linux CI runner or a macOS collaborator three
copies of a binary they cannot run.

`skills-lock.json` **is** committed. It pins every skill to a source repo and a
content hash, so the install is reproducible from a small text file rather than
from vendored bytes.

## Reinstalling

```bash
npx skills add LottieFiles/motion-design-skill
npx skills add iart-ai/web-animation-skills
npx impeccable install          # answer: [1] detected only, then: project
```

Then `/impeccable init` **inside the agent session**, not the terminal — it runs
a multi-round discovery interview and writes the project's design context.

SlopMonster has no installer:

```bash
git clone --depth 1 https://github.com/ItsssssJack/SlopMonster.git
cp -r SlopMonster ~/.claude/skills/slopmonster && rm -rf ~/.claude/skills/slopmonster/.git
```

It is installed **globally** at `~/.claude/skills/slopmonster`, unlike the
others, which are project-local. Its `tools/deslop.py` needs Python 3 (3.11.1
present).

## What each is for

**impeccable** — 23 commands, 61 deterministic detector rules, live browser
iteration. Engine binary reports `4.0.0`. The ones that map onto this brief:

| Command | Use here |
|---|---|
| `shape` | Plan UX/UI before code. Multi-round discovery, visual probes |
| `typeset` | Typography — font choice, hierarchy, sizing, weight |
| `adapt` | Desktop and mobile as separate designs, which the owner requires |
| `animate` | Purposeful motion and micro-interactions |
| `onboard` | Empty states — the 80 examinations with no photograph specification |
| `clarify` | UX copy, error messages, microcopy, labels |
| `bolder` / `colorize` / `delight` | The "not another competent template" problem |
| `distill` / `quieter` | Restraint, once there is something to restrain |
| `audit` / `optimize` | Accessibility, performance, theming, responsive |
| `harden` | Text overflow and i18n — matters before the Indic scripts land |
| `live` | Select an element in the browser, pick an action, get variants |
| `document` / `extract` | Writes DESIGN.md, pulls repeated patterns into tokens |

Also installs a guarded `postToolUse` hook (`.github/hooks/impeccable.json`)
that runs the engine after edit/create/apply_patch with a 5 s timeout, and four
subagents under `.claude/agents/`. The hook no-ops if the binary is absent, and
its wrapper target was verified present rather than assumed.

**motion-design** (LottieFiles) — motion *direction* rather than syntax: timing,
easing, choreography, emotional intent. Implementation-agnostic.

**web-animation-skills** (iart-ai) — nine skills with deliver-and-verify loops:
`60fps-animation`, `accessible-animation`, `ascii-animation`, `glassmorphism`,
`gsap-web`, `lottie-animation`, `micro-interaction`,
`page-transition-animation`, `svg-animation`.

Only the frontend pack was installed. The other 14 packs in that repository
target TikTok creators, YouTubers, e-commerce sellers and math animators, and
would be noise in the skill list.

**Two of the nine will not be used, and this is deliberate.** `glassmorphism`
is refused by the direction — `backdrop-filter: blur()` is the most expensive
common effect on the slow Android the brief names as the real user, and its
legibility depends on what sits behind it. `ascii-animation` has no application
here. They arrived as part of the pack; their presence is not an endorsement.

**slopmonster** — scores copy out of 5 against five violation categories: AI
vocabulary, sentence construction, punctuation cadence, rule-of-three rhythm,
and **unverifiable marketing claims**. That last category is the one that earns
its place: this product already refuses to assert a file size no authority
published, and the marketing must be held to the same standard.

## Untitled UI React — decided: behaviour, not skin

Compatible on paper. It wants React 19.2 and Tailwind v4.3; this project runs
**19.2.4 and 4.3.1**, and Tailwind utilities are genuinely in use (21 of 34
component files). MIT for the open-source components; PRO is a separate paid
agreement.

**Not adopted as a component library.** It is a design system with a
recognisable look, and the brief's first requirement is that the result not
read as generic. Importing its visual defaults would import the exact template
appearance the rebuild exists to escape.

**What is worth taking is what it is built on: React Aria.** Accessible
keyboard behaviour, focus management and screen-reader semantics for
comboboxes, dialogs, sliders and file inputs — precisely the components this
product needs and the ones most easily got wrong. The search over 132
examinations, the before/after comparison slider, and the PDF page-reordering
interface are all in that set.

```bash
npm i react-aria-components   # 1.21.1, peer-compatible with React 19
```

**Not installed yet, on purpose.** Unlike the design tooling above, this ships
to the candidate. The hardest constraint in the brief is performance on a slow
Android on mobile data, and speculative runtime dependencies are how bundles
grow. It is tree-shakeable, so it goes in when the first component needs it and
costs only what is imported.

Untitled UI's own source stays useful as a **reference** for how a given
pattern is wired, read rather than installed.
