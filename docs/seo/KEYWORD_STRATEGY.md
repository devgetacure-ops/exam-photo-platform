# Keyword strategy

**Written 13 September 2026.** How to use `keywords.csv` and `KEYWORD_MAP.md`,
and what they can and cannot do. DEC-088.

## What this is

A map of the searches we want to be found for, generated from the 132
examination records plus a hand-written list of generic tool searches. Each row
says what the person searching wants (`intent`), which page should answer it
(`target_url`), and whether that page can:

| `coverage` | Meaning | What to do |
|---|---|---|
| `prepares` | The page does the thing searched for | Keep the page answering it; watch its ranking |
| `explains` | The page answers the question but cannot do the task on its own | Fine for questions; for tool searches, consider a real tool |
| `gap` | No page answers it | `target_url` is the page to build |

`priority` is a rule of thumb, not measured search volume: short forms, the
photograph and the signature first; long tails, questions and translations
last. Real volumes replace it once Search Console and Keyword Planner have data.

## What it cannot do

**No site appears first for everything, and no list of keywords makes one.**
Search engines rank the page that best answers a search, from signals that
include what the page says, how fast and usable it is, and how many trusted
sites link to it. A keyword list is the plan for which pages to build and what
each should answer. It is not something to paste into a page.

Three things would hurt rather than help, and are ruled out:

- **Keyword stuffing**: repeating these phrases in text, hidden text or meta
  tags. Search engines demote it.
- **Doorway pages**: thousands of near-identical pages, one per phrase ("SSC
  CGL photo resize", "SSC CGL photo resizer", "resize SSC CGL photo"). One
  good page answers all of those. The CSV has 30,000 rows; the site should
  have a few hundred pages.
- **Promising what the product does not do**. A page titled "remove
  background from any photo" must actually do that on its own, or it loses the
  visitor and, over time, the ranking.

## How the searches group, and which page answers each group

| Cluster | Answered by | State |
|---|---|---|
| `exam-file-size`, `exam-question`, `exam-rejection`, `exam-application` | `/exam/{id}/rules`, with its "In short" block (DEC-087) | Built |
| `exam-file-prepare` | `/exam/{id}`, which prepares the file | Built |
| `pdf-convert` | `/pdf`, whose converter runs in the browser | Built |
| `generic-exam-form`, `brand` | `/`, the home page | Built |
| `exam-hinglish` | the English exam pages today | Partly: a Hindi page would answer these better |
| `pdf-work` | `/pdf` describes it; the work runs inside a kit | Partly |
| `compress-image-to-size` | `/compress-image` | **Gap: a standalone tool** |
| `compress-pdf-to-size` | `/compress-pdf` | **Gap: a standalone tool** |
| `spec-value` | `/resize/{file}-to-{size}` | **Gap: one page per figure an examination published** |
| `exam-family` | `/exams/{family}` | **Gap: hub pages** |
| `background-and-crop` | `/background-remover`, `/crop-photo` | **Gap: standalone tools** |
| `generic-exam-info` | `/photo-size-for-exams` | **Gap: one guide page** |
| `exam-hindi`, `generic-hindi` | `/hi/...` | **Gap: Hindi pages** |
| `exam-not-yet-covered` | `/exam-request` | Gap until the examination is encoded |

`KEYWORD_MAP.md` lists every gap with how many searches are waiting on it.

## What to build, in order

1. ~~**A standalone "compress to size" tool**~~ **Built** (DEC-096):
   `/compress-image`, free, in the candidate's browser.
2. ~~**Hub pages by family**~~ **Built** (DEC-096): eight hubs at
   `/exams/{family}`, grouped in `lib/exam-families.ts`.
3. **Hindi pages** for the examinations candidates most often search in Hindi,
   starting with the family hubs and the highest-priority examinations. The
   typeface already covers Devanagari.
4. ~~**A standalone PDF compressor** and **pages per published figure**~~
   **Built** (DEC-098): `/compress-pdf`, and 42 `/resize/{size}` pages from
   `specTargets`, each a working tool.
5. **Background and crop tools**, only if the product decides to offer them
   outside a kit.

## Keeping it true

- Re-run `npm run seo:keywords` in `apps/web` whenever the catalogue changes.
  The CSV is generated; editing it by hand is lost on the next run.
- The generator only names a file an examination asks for, and only uses a
  figure a record published (`seo-keywords.test.ts`).
- Once the site is live, compare against Search Console's real queries every
  month: promote what people actually search, and drop what nobody does.
