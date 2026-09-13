# The mobile build — a design of its own

**Written 12 September 2026**, after the owner pointed out, again, that what has
been delivered is responsive CSS rather than a mobile design.

## What is wrong today, stated plainly

Every surface was drawn for a wide screen and then folded down: 27 rules open at
`min-width: 768px`, 16 more at 1000px, and the phone gets whatever falls out of
that. The result is one long scroll per page, actions that sit wherever the
document put them, and nothing a thumb can reach without travel. There is no
app shell, no manifest, and no screen that was designed at 390px first.

Since most candidates arrive on a phone, that is backwards. The phone build is
the product; the desktop build is the variant.

## The principles this is built to

1. **One decision per screen.** On the paid path a candidate should never be
   scrolling to find what to do next.
2. **The thumb does the work.** Primary actions live in a fixed bar at the
   bottom, inside the safe area. Nothing important sits in the top corners.
3. **Sheets, not pages.** Rules, specimens, facts and sources open as bottom
   sheets over the current screen, so a candidate never loses their place.
4. **The same design system.** Identical tokens, type, 3px rules and offset
   shadows. This is not a second visual language — it is the same one, set for
   a different device.
5. **It must feel handled, not browsed.** Screen-to-screen transitions, instant
   tap feedback, state that survives a backgrounded browser.
6. **Nothing hover-only, ever.** Every affordance works on first touch.

## The shell

- **Top bar, 48px.** Back, the examination's name, and nothing else. It hides
  as you scroll down and returns as you scroll up.
- **Bottom action bar.** The primary action and the live price, fixed, padded
  for the home indicator (`env(safe-area-inset-bottom)`). It is the only place
  a primary action ever appears on a phone.
- **Screen transitions.** 180–220ms slide, paired with the browser's own back
  gesture so Android's back button steps the flow rather than leaving the site.
- **Full height done properly.** `100dvh`, not `100vh`, so the address bar
  cannot cut the action bar off.

## The flows

**Home.** Under three screens of scroll: the headline, the search, three facts,
the before-and-after as one swipeable card, and a short footer. The long
argument (the problem, why it exists, the story) moves behind one link, because
on a phone it is scroll a candidate pays for and rarely reads.

**Search.** Full screen on focus: a big field, results as you type, recent
searches, and "not on the list" at the foot. No dropdown squeezed under a hero.

**The examination — the money path, as four steps.**

1. **What you need.** The file checklist, each row a tap target with its own
   price effect. The bar shows the running total.
2. **Add your files.** One file at a time, camera or gallery, with that file's
   rules a tap away in a sheet. Progress is shown per file, not as one bar.
3. **Check.** The watermarked preview, the findings in plain words, the
   deletion clock.
4. **Pay, then keep.** Razorpay, then the success screen with the downloads.

Progress sits under the top bar as four marks. Steps are addressable, so the
back button and a refresh both behave.

**PDF tools.** A grid of tools; each opens its own focused screen with the file
picker first and the options after, rather than a page of controls.

**Support and the policies.** Sections collapsed by default with a search at the
top, because a wall of legal text on a phone is unreadable and unread.

## What changes in the code

- **CSS inverts.** The base stylesheet becomes the phone. Desktop moves into
  `@media (min-width: 900px)`. This is a rewrite of the existing stylesheets'
  structure, not a new theme.
- **Two shells, one set of logic.** Where the structures genuinely differ — the
  examination workspace above all — the state and the API calls stay in shared
  hooks, and only the presentational shell differs. Large trees are never
  rendered twice and hidden with CSS; small exclusive pieces (the bottom bar,
  the desktop sidebar) may be.
- **Static rendering stays.** No user-agent branching on the server: the 279
  prerendered pages and their SEO are worth more than a device-perfect first
  paint, and the shell difference is handled in the client.
- **Installable.** A web app manifest, icons, `display: standalone` and a theme
  colour, so "add to home screen" gives a real app window. An offline shell can
  follow once the flows settle.

## Order of work

| Phase | What | Why first |
|---|---|---|
| 1 | The shell (top bar, action bar, sheets, transitions) and the examination flow | It is the paid path and the hardest part |
| 2 | Home and search | The way in |
| 3 | PDF tools, support, policies | Volume surfaces, lower risk |
| 4 | Manifest and install, plus a pass on a real mid-range Android | Needs the rest to exist |

## Where it stands, 13 September 2026

| Phase | State | Where |
|---|---|---|
| 1 | **Shipped.** App bar, action bar, sheets, the four-step flow, the phone exam file list | `components/m/`, `app/mobile.css`, `app/exam/[examId]/prepare` |
| 2 | **Shipped.** The phone bar and its menu on every page with the site header; the short home; search as a full-screen screen with recents; `/about` for the long argument; the short footer | `m/phone-bar.tsx`, `m/search-screen.tsx`, `m/home.tsx`, `components/home-story.tsx`, `app/about/`, DEC-081 |
| 3 | **Shipped.** The PDF work as rows, with the converter on its own screen and the rest in sheets; support's answers searchable; each policy collapsed with a search; one bottom-bar action per page | `m/pdf-home.tsx`, `m/pdf-tool.tsx`, `app/pdf/to-image/`, `m/answer-search.tsx`, `m/policy-phone.tsx`, DEC-083 |
| 4 | **Install prompt shipped** (asked once after a useful moment, a card above the bottom bar, Share steps on an iPhone, "Install the app" in the menu). **The owner's first test on a real phone** found every scripted control dead, because the dev server refused its scripts to the LAN address; fixed, with every sideways strip replaced by a layout that fits (DEC-085). The owner's retest, and a pass on a production build, remain | `lib/install.ts`, `m/install-card.tsx`, `next.config.ts`, DEC-084, DEC-085 |

**Where the build departs from this plan, and why.** "CSS inverts" was not done. The
desktop build was signed off after this plan was written, and inverting every
stylesheet is a rewrite of that signed-off CSS. The phone build is additive
instead: its own components and rules, switched at 900px, with the desktop
markup verified unchanged (DEC-081). The top bar on the pages outside the flow
keeps a search button and a menu in its right corner; nothing that completes a
task lives there, which is what "nothing important in the top corners" was for.

## How it will be checked

- Every screen looked at at **360, 390 and 430px**, not one "mobile" width.
- Tap targets measured at 44px minimum, inputs at 16px or larger so iOS does
  not zoom.
- The design detector run at a phone viewport, not only at desktop.
- Throttled to mid-range hardware for the upload and preparation screens.
- No horizontal scroll anywhere, checked by measurement rather than by eye,
  and no sideways strip either: content that does not fit is laid out to fit.
- Checked through the machine's LAN address with touch input, not only
  `localhost`, since a page that never hydrates looks fine on `localhost`.
