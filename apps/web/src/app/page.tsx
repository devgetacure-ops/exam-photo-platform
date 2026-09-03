import { ExamSearch } from "../components/exam-search";
import { loadSearchIndex } from "../lib/catalogue.server";

/**
 * The landing page is the search box.
 *
 * A candidate arrives with one thing in mind — the name of their examination —
 * and one job to do. An earlier version put a hero, a three-card feature grid
 * and a pricing block above and around that, which meant scrolling past three
 * screens of pitch before anything could be typed. Nobody came here to read
 * about us.
 *
 * So: the search field is the first and largest thing, focused on arrival, and
 * the only supporting text is the two facts that decide whether to bother —
 * how many exams we cover and what it costs.
 */

export default async function Home() {
  const { exams, unavailable } = await loadSearchIndex();

  return (
    <main className="flex min-h-dvh flex-col">
      <header className="flex items-center justify-between px-8 py-5">
        <span className="font-semibold tracking-tight">
          Upload<span className="text-accent">Ready</span>
        </span>
        <span className="spec text-xs text-muted">
          ₹4 a file · ₹8 the set
        </span>
      </header>

      <div className="flex flex-1 items-center justify-center px-6 pb-32">
        <div className="w-full max-w-2xl">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-[2.6rem] sm:leading-[1.1]">
            Which exam are you applying for?
          </h1>
          <p className="mt-3 text-ink-soft">
            We prepare every file it asks for, to that exam&rsquo;s own published
            rules.
          </p>

          <div className="mt-7">
            <ExamSearch exams={exams} unavailable={unavailable} autoFocus />
          </div>

          <p className="mt-4 text-sm text-muted">
            {exams.length} exams covered. Full names and short forms both work —
            try <span className="spec text-ink-soft">CAT</span>,{" "}
            <span className="spec text-ink-soft">IBPS PO</span>,{" "}
            <span className="spec text-ink-soft">RBI Assistant</span>.
          </p>
        </div>
      </div>

      <footer className="px-8 py-6 text-xs text-muted">
        You see every file before you pay. Uploads deleted after 30 minutes.
      </footer>
    </main>
  );
}
