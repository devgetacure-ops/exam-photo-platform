import type { SearchEntry } from "./types";

/**
 * How a query is matched against the catalogue.
 *
 * Lives outside the picker so the server can use it too: the request page
 * checks whether the examination a candidate asked for is already here under
 * another spelling, or already on the list for a reason worth telling them.
 */

/** A match, plus how good it was, so exact and prefix hits outrank substrings. */
export interface Ranked {
  entry: SearchEntry;
  score: number;
  /** The alias that matched, when it was not the name. Shown so the candidate
   *  sees *why* a row came back for "CAT". */
  via: string | null;
}

function normalise(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

/**
 * The same string with every separator removed.
 *
 * Examination names are written inconsistently in the wild -- "MHT-CET" and
 * "MHT CET", "R.B.I." and "RBI", "CUET-UG" and "CUET UG" -- and a candidate
 * types whichever they saw. Comparing the compact forms as well as the spaced
 * ones makes all of those spellings find the same exam.
 */
function compact(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function escapeForRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * How well one haystack answers the query, 0 for not at all.
 *
 * Ranked rather than boolean so an exact or leading match outranks a substring
 * buried mid-string: typing "gate" should surface GATE, not every examination
 * whose description happens to contain "postgraduate".
 */
function rateOne(haystack: string, q: string): number {
  if (!haystack || !q) return 0;
  if (haystack === q) return 100;
  if (haystack.startsWith(q)) return 80;
  if (new RegExp(`\\b${escapeForRegExp(q)}`).test(haystack)) return 60;
  if (haystack.includes(q)) return 30;
  return 0;
}

/** Best score across the spaced and compact spellings of both sides. */
function rate(raw: string, query: string): number {
  const words = normalise(raw).split(" ");
  const tokens = normalise(query).split(" ");
  let position = -1;
  const orderedMatch = tokens.length > 1 && tokens.every(token => {
    position = words.findIndex((word, index) => index > position && word.startsWith(token));
    return position >= 0;
  });
  return Math.max(
    rateOne(normalise(raw), normalise(query)),
    rateOne(compact(raw), compact(query)),
    orderedMatch ? 45 : 0
  );
}

/**
 * Score one entry against the query.
 *
 * Abbreviations and full forms both have to work, and in this catalogue the
 * abbreviation usually lives in `aliases` ("CAT 2025") while the full form is
 * the name ("Common Admission Test 2025"). Both are searched, and a hit on
 * either is a hit.
 */
export function scoreEntry(entry: SearchEntry, query: string): Ranked | null {
  if (!normalise(query)) return null;

  let best = rate(entry.name, query);
  let via: string | null = null;

  for (const alias of entry.aliases) {
    const aliasScore = rate(alias, query);
    // The bonus applies only to an alias that actually matched. Adding it
    // unconditionally would give every examination a non-zero score for every
    // query, turning a search for "ssc" into a list of everything.
    if (aliasScore > 0 && aliasScore + 5 > best) {
      best = aliasScore + 5;
      via = alias;
    }
  }

  // The conducting body is searchable but weighted down: "Reserve Bank of
  // India" should find RBI Assistant, without every IIM exam ranking on
  // "Institutes".
  const bodyScore = rate(entry.body, query) * 0.5;
  if (bodyScore > best) {
    best = bodyScore;
    via = entry.body;
  }

  if (best <= 0) return null;
  return { entry, score: best, via };
}

/** Every matching entry, best first, ties broken alphabetically. */
export function rankEntries(rows: SearchEntry[], query: string): Ranked[] {
  return rows
    .map((entry) => scoreEntry(entry, query))
    .filter((row): row is Ranked => row !== null)
    .sort((a, b) => b.score - a.score || a.entry.name.localeCompare(b.entry.name));
}
