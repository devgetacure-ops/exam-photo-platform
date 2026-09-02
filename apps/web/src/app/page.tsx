import Link from "next/link";
import { ExamSearch } from "../components/exam-search";
import { loadSearchIndex } from "../lib/catalogue.server";

/**
 * The landing page.
 *
 * The copy leads with proof rather than persuasion. This audience is
 * frightened, not browsing — a rejected photograph can cost a year — so the
 * thing that converts is evidence that we know their examination's rules
 * better than they do. Every claim on this page is a number we can defend from
 * the catalogue, and the price is visible before anything is asked of them.
 *
 * Rendered from the catalogue on disk, so it is real HTML for a crawler and it
 * works with the processing service switched off.
 */

export default async function Home() {
  const { exams, unavailable } = await loadSearchIndex();

  const prepared = exams.reduce((sum, exam) => sum + exam.prepares, 0);

  return (
    <main className="flex flex-1 flex-col">
      {/* ---------------------------------------------------------------- */}
      <header className="border-b border-line">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-5 py-4 sm:px-8">
          <span className="font-semibold tracking-tight">
            Upload<span className="text-accent">Ready</span>
          </span>
          <nav className="flex items-center gap-5 text-sm text-ink-soft">
            <Link href="/coverage" className="hover:text-ink">
              Exams we cover
            </Link>
            <Link href="/pricing" className="hover:text-ink">
              Pricing
            </Link>
          </nav>
        </div>
      </header>

      {/* --- Hero: the search is the product, so it opens the page ------- */}
      <section className="mx-auto w-full max-w-3xl px-5 pt-14 pb-10 sm:px-8 sm:pt-24">
        <p className="label mb-5">
          {exams.length} examinations · {prepared} uploads we prepare
        </p>

        <h1 className="text-4xl leading-[1.08] font-semibold sm:text-6xl">
          Your exam has rules
          <br />
          about the files you upload.
          <br />
          <span className="text-accent">We already know them.</span>
        </h1>

        <p className="mt-6 max-w-xl text-lg leading-relaxed text-ink-soft">
          Pick your examination and we prepare every file it asks for —
          photograph, signature, thumb impression, declaration, certificates —
          cropped, sized, compressed and named to that exam&rsquo;s own published
          specification.
        </p>

        <div className="mt-9">
          <ExamSearch exams={exams} unavailable={unavailable} />
        </div>

        <p className="mt-4 text-sm text-muted">
          Try{" "}
          <span className="spec text-ink-soft">CAT</span>,{" "}
          <span className="spec text-ink-soft">IBPS PO</span> or{" "}
          <span className="spec text-ink-soft">RBI Assistant</span> — full names and
          abbreviations both work.
        </p>
      </section>

      {/* --- The specificity proof -------------------------------------- */}
      <section className="border-y border-line bg-surface">
        <div className="mx-auto max-w-5xl px-5 py-14 sm:px-8 sm:py-20">
          <h2 className="max-w-2xl text-2xl font-semibold sm:text-3xl">
            Every exam wants something different, and none of them says so
            clearly.
          </h2>
          <p className="mt-4 max-w-2xl text-ink-soft">
            These are real specifications from three examinations in our
            catalogue. They have nothing in common — which is exactly why a
            generic resizer cannot help you.
          </p>

          <div className="mt-10 grid gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-3">
            {[
              {
                exam: "CAT 2025",
                body: "Indian Institutes of Management",
                rows: [
                  ["Dimensions", "1200 × 1200 px"],
                  ["File size", "up to 1 MB"],
                  ["Format", "JPEG"],
                  ["Recency", "within 180 days"],
                ],
              },
              {
                exam: "RBI Assistant 2025",
                body: "Reserve Bank of India",
                rows: [
                  ["Signature", "10–20 KB"],
                  ["Thumb impression", "20–50 KB"],
                  ["Declaration", "50–100 KB"],
                  ["Live photo", "at the centre"],
                ],
              },
              {
                exam: "SSC CGL 2026",
                body: "Staff Selection Commission",
                rows: [
                  ["Photograph", "captured by portal"],
                  ["Signature", "still required"],
                  ["Our status", "not yet covered"],
                  ["We say so", "up front"],
                ],
              },
            ].map((card) => (
              <div key={card.exam} className="bg-surface p-6">
                <p className="font-medium">{card.exam}</p>
                <p className="mt-0.5 text-xs text-muted">{card.body}</p>
                <dl className="mt-5 space-y-2.5">
                  {card.rows.map(([term, value]) => (
                    <div
                      key={term}
                      className="flex items-baseline justify-between gap-4 border-b border-line pb-2.5 last:border-0"
                    >
                      <dt className="text-sm text-muted">{term}</dt>
                      <dd className="spec text-sm text-ink">{value}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* --- Price, stated before anything is asked ---------------------- */}
      <section className="mx-auto w-full max-w-5xl px-5 py-14 sm:px-8 sm:py-20">
        <div className="grid gap-10 lg:grid-cols-[1.1fr_1fr] lg:gap-16">
          <div>
            <h2 className="text-2xl font-semibold sm:text-3xl">
              See the finished file before you pay for it.
            </h2>
            <p className="mt-4 text-ink-soft">
              Upload, and we prepare your file straight away — you see exactly
              what you are getting, watermarked, before any payment. If it is
              not right, you have not spent anything.
            </p>
            <ul className="mt-6 space-y-3 text-sm text-ink-soft">
              {[
                "No account. No password. Nothing to sign up for.",
                "We ask only where to send the file.",
                "Everything you upload is deleted after 30 minutes.",
              ].map((line) => (
                <li key={line} className="flex gap-3">
                  <svg
                    className="mt-0.5 size-4 shrink-0 text-accent"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    aria-hidden="true"
                  >
                    <path d="m5 13 4 4L19 7" />
                  </svg>
                  {line}
                </li>
              ))}
            </ul>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
            <div className="rounded-xl border border-line bg-surface p-6">
              <p className="label">Photo Ready</p>
              <p className="mt-2 text-3xl font-semibold">
                ₹4
                <span className="ml-1 text-sm font-normal text-muted">final</span>
              </p>
              <p className="mt-3 text-sm text-ink-soft">
                Your photograph, prepared to your exam&rsquo;s specification.
              </p>
            </div>

            {/* The bundle is the economic engine, so it is the visually
                preferred choice — but the anchor is the real work it
                replaces, never an invented "worth ₹99" figure. */}
            <div className="rounded-xl border-2 border-accent bg-accent-soft p-6">
              <p className="label text-accent-ink">Complete kit · best value</p>
              <p className="mt-2 text-3xl font-semibold text-accent-ink">
                ₹8
                <span className="ml-1 text-sm font-normal text-accent-ink/70">
                  final
                </span>
              </p>
              <p className="mt-3 text-sm text-accent-ink/90">
                Every supported upload your exam asks for, prepared together and
                packaged.
              </p>
            </div>
          </div>
        </div>

        <p className="mt-8 text-sm text-muted">
          Final price shown. No fee added at checkout.
        </p>
      </section>

      {/* --- The boundary, stated on the landing page -------------------- */}
      <section className="border-t border-line bg-sunk">
        <div className="mx-auto max-w-5xl px-5 py-12 sm:px-8">
          <h2 className="text-lg font-semibold">What we will not pretend to do</h2>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-ink-soft">
            Some exams photograph you at the centre, or take your declaration
            through their own portal. Those are never files we can make, and we
            will tell you so on your exam&rsquo;s page rather than quietly leaving
            them off your list. {unavailable.length} examinations we have
            researched are not covered yet — they are in the search results too,
            marked, so you find out here and not on the application deadline.
          </p>
        </div>
      </section>

      <footer className="mt-auto border-t border-line">
        <div className="mx-auto flex max-w-5xl flex-col gap-2 px-5 py-8 text-xs text-muted sm:flex-row sm:justify-between sm:px-8">
          <p>Specifications are researched per exam and dated. Report anything wrong.</p>
          <p>Uploads deleted after 30 minutes.</p>
        </div>
      </footer>
    </main>
  );
}
