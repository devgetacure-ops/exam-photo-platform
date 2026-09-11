import { ExamSearch } from "../components/exam-search";
import { SiteFooter } from "../components/site-footer";
import { SiteHeader } from "../components/site-header";
import { Note } from "../components/euk/note";
import { loadSearchIndex } from "../lib/catalogue.server";

/**
 * The specimen is drawn, not photographed, and deliberately so: a real
 * candidate's face may never ship here, and a stock portrait pretending to be
 * an engine result would be the one claim this page cannot make. The silhouette
 * reads as a placeholder because it is one.
 */
function Specimen({ w, h, prepared }: { w: number; h: number; prepared: boolean }) {
    const cx = w / 2;
    const headR = w * 0.24;
    return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="block" aria-hidden="true">
            <rect width={w} height={h} fill={prepared ? "#ffffff" : "#b8b4ac"} />
            <g fill={prepared ? "#111110" : "#6e6a62"}>
                <ellipse cx={cx} cy={h * 0.41} rx={headR} ry={headR * 1.22} />
                <path
                    d={`M${cx} ${h * 0.69} C ${cx - w * 0.28} ${h * 0.69}, ${cx - w * 0.4} ${h * 0.83}, ${cx - w * 0.43} ${h} L ${cx + w * 0.43} ${h} C ${cx + w * 0.4} ${h * 0.83}, ${cx + w * 0.28} ${h * 0.69}, ${cx} ${h * 0.69} Z`}
                />
            </g>
        </svg>
    );
}

const TOOL_TABS = ["resize", "remove bg", "compress", "convert", "rename"];

const SPECS = [
    { w: 84, h: 97, label: "200×230" },
    { w: 100, h: 100, label: "1200×1200" },
    { w: 75, h: 100, label: "150×200" },
    { w: 100, h: 78, label: "413×319" },
];

export default async function Home() {
    const { exams, unavailable } = await loadSearchIndex();

    return (
        <div className="euk">
            <SiteHeader />
            <main id="main-content">

                {/* hero */}
                <section className="px-5 pt-8 md:px-12 md:pt-13">
                    <div className="flex flex-col gap-10 md:flex-row md:items-start md:gap-10">
                        <div className="flex shrink-0 flex-col gap-4 md:w-[520px] md:gap-[22px]">
                            <h1 className="euk-display text-[52px] md:text-[78px]">
                                You prepare
                                <br />
                                for the exam.
                                <br />
                                We&rsquo;ll prepare
                                <br />
                                <span className="euk-mark">the files.</span>
                            </h1>
                            <p className="text-[17px] font-medium leading-snug md:text-[19px]">
                                The photo. The signature. The right size, format
                                and filename.
                            </p>
                            <p className="max-w-[420px] text-[15px] leading-relaxed text-[var(--ink-70)] md:text-base">
                                One place that already knows what your
                                examination asks for &mdash; and prepares every
                                file to its own published rules.
                            </p>
                        </div>

                        <div className="relative h-[252px] grow md:h-[372px]">
                            <div className="euk-block absolute left-0 top-10 -rotate-[4deg] p-2 pb-1.5 shadow-[5px_5px_0_var(--ink)] md:top-11 md:p-2.5 md:pb-2 md:shadow-[7px_7px_0_var(--ink)]">
                                <div className="hidden md:block">
                                    <Specimen w={150} h={172} prepared={false} />
                                </div>
                                <div className="md:hidden">
                                    <Specimen w={106} h={122} prepared={false} />
                                </div>
                                <p className="euk-label pt-1.5 text-[10px] text-[var(--ink-55)] md:text-[10px]">
                                    AS UPLOADED
                                </p>
                            </div>
                            <div className="euk-block euk-block--signal absolute right-0 top-0 rotate-[2.5deg] p-2.5 pb-2 md:right-1.5 md:p-3 md:pb-2.5">
                                <div className="hidden md:block">
                                    <Specimen w={186} h={214} prepared />
                                </div>
                                <div className="md:hidden">
                                    <Specimen w={140} h={161} prepared />
                                </div>
                                <div className="flex items-baseline justify-between pt-1.5 md:pt-2">
                                    <span className="euk-label text-[10px] md:text-[10px]">
                                        200×230 · 48 KB
                                    </span>
                                    <span className="euk-label text-[10px] text-[var(--signal-deep)] md:text-[10px]">
                                        PREPARED
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* the primary action */}
                <section className="px-5 pb-11 pt-7 md:px-12 md:pb-12">
                    <div className="euk-block euk-block--drop euk-lift">
                        <ExamSearch exams={exams} unavailable={unavailable} />
                    </div>
                </section>

                {/* the problem — the band inverts against the page */}
                <section
                    className="euk-invert px-5 py-9 md:px-12 md:py-12"
                    id="how"
                >
                    <div className="flex flex-col gap-6 md:flex-row md:items-start md:gap-11">
                        <div className="md:w-[470px] md:shrink-0">
                            <h2 className="euk-display text-[42px] md:text-[58px]">
                                Six tabs.
                                <br />
                                Four tools.
                                <br />
                                And the photo is
                                <br />
                                <span className="euk-mark">still wrong.</span>
                            </h2>
                            <p className="pt-4 text-[17px] font-medium leading-snug text-[var(--ink-70)] md:text-[19px]">
                                It was never your photograph. It was the
                                specification.
                            </p>
                        </div>
                        <div className="flex grow flex-col gap-5">
                            <div>
                                <div className="flex items-end gap-1 overflow-x-auto">
                                    {TOOL_TABS.map((t) => (
                                        <span
                                            key={t}
                                            className="euk-label shrink-0 border-2 border-b-0 border-[var(--paper)] bg-[var(--paper-2)] px-2.5 py-1.5 text-[10px] text-[var(--ink-70)] md:text-[11px]"
                                        >
                                            {t}
                                        </span>
                                    ))}
                                    <span className="euk-label shrink-0 border-2 border-b-0 border-[var(--paper)] bg-[var(--signal)] px-2.5 py-1.5 text-[10px] font-bold text-[var(--signal-ink)] md:text-[11px]">
                                        STILL WRONG
                                    </span>
                                </div>
                                <div className="h-[3px] bg-[var(--paper)]" />
                            </div>
                            <p className="text-[15px] leading-relaxed text-[var(--ink-70)] md:text-base">
                                Resize on one site. Remove the background on
                                another. Compress somewhere else, convert the
                                format, rename it yourself &mdash; then find the
                                background was never actually removed, and start
                                again.
                            </p>
                            <p className="text-[15px] leading-relaxed text-[var(--ink)] md:text-base">
                                None of those tools ever read your
                                examination&rsquo;s rules. That is the whole
                                problem, and it is the only thing we do &mdash;
                                and the PDF work those other tabs were for
                                comes free with it.
                            </p>
                        </div>
                    </div>
                </section>

                {/* the variance strip — the one gridded surface */}
                <section className="euk-gridded px-5 py-9 md:px-12 md:py-11">
                    <div className="flex flex-col gap-2 pb-6 md:flex-row md:items-end md:justify-between">
                        <div>
                            <h2 className="euk-display text-[36px] md:text-[44px] md:leading-[0.92]">
                                One face.
                                <br />
                                Six examinations.
                            </h2>
                            <p className="pt-2 text-[15px] leading-relaxed text-[var(--ink-70)] md:text-base">
                                No preset fits all six. Each one is read from
                                what that exam actually published.
                            </p>
                        </div>
                        <p className="euk-label text-[11px] leading-relaxed text-[var(--ink-55)] md:text-right">
                            418 REQUIREMENTS
                            <br className="hidden md:inline" /> ACROSS{" "}
                            {exams.length} EXAMS
                        </p>
                    </div>
                    <div className="flex items-end gap-3 overflow-x-auto md:gap-4">
                        {SPECS.map((s) => (
                            <div
                                key={s.label}
                                className="flex shrink-0 flex-col items-center gap-1.5"
                            >
                                <div
                                    className="border-2 border-[var(--ink)] bg-white"
                                    style={{ width: s.w, height: s.h }}
                                />
                                <span className="euk-label text-[10px]">
                                    {s.label}
                                </span>
                            </div>
                        ))}
                        <div className="flex shrink-0 flex-col items-center gap-1.5">
                            <div className="relative h-[92px] w-[78px] border-2 border-[var(--signal)] bg-white">
                                <div className="euk-label absolute inset-x-0 bottom-0 flex h-[22px] items-center justify-center border-t-2 border-dashed border-[var(--signal)] bg-[#fde7e0] text-[10px] text-[var(--signal-deep)]">
                                    NAME + DATE
                                </div>
                            </div>
                            <span className="euk-label text-[10px] text-[var(--signal-deep)]">
                                TNPSC
                            </span>
                        </div>
                        <div className="flex shrink-0 flex-col items-center gap-1.5">
                            <div className="h-[78px] w-[78px] border-2 border-dashed border-[var(--notyet-line)] bg-[var(--notyet-fill)]" />
                            <span className="euk-label text-[10px] text-[var(--ink-55)]">
                                NOT YET
                            </span>
                        </div>
                    </div>
                </section>

                {/* the boundary, as the form's own two parts */}
                <section className="px-5 py-9 md:px-12 md:py-12">
                    <h2 className="euk-display pb-6 text-[36px] md:text-[44px] md:leading-[0.92]">
                        What we do.
                        <br />
                        What stays yours.
                    </h2>
                    <div className="flex flex-col gap-5 md:flex-row md:gap-[18px]">
                        <div className="euk-block euk-block--drop grow">
                            <p className="euk-label bg-[var(--ink)] px-3.5 py-2 text-[10px] text-[var(--paper)] md:text-[11px]">
                                PART A — WE PREPARE THESE
                            </p>
                            <div className="p-3.5">
                                {[
                                    "Candidate photograph",
                                    "Signature",
                                    "Thumb impression",
                                ].map((item, i, arr) => (
                                    <div
                                        key={item}
                                        className={`flex items-center justify-between ${i < arr.length - 1 ? "mb-2.5 border-b-2 border-[var(--hairline)] pb-2.5" : ""}`}
                                    >
                                        <span className="text-[15px]">
                                            {item}
                                        </span>
                                        <span className="euk-label border-2 border-[var(--ink)] bg-[var(--signal)] px-3 py-2 text-[11px] font-bold text-[var(--signal-ink)]">
                                            ATTACH
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="euk-block euk-block--dashed grow">
                            <p className="euk-label bg-[var(--ink-40)] px-3.5 py-2 text-[10px] text-[var(--paper)] md:text-[11px]">
                                PART B — YOU COMPLETE THESE
                            </p>
                            <div className="p-3.5">
                                <div className="mb-2.5 border-b-2 border-[var(--hairline)] pb-2.5">
                                    <p className="text-[15px] text-[var(--ink-70)]">
                                        Live photo capture
                                    </p>
                                    <p className="text-[13px] text-[var(--ink-55)]">
                                        The portal takes this through your
                                        webcam
                                    </p>
                                </div>
                                <div className="mb-2.5 border-b-2 border-[var(--hairline)] pb-2.5">
                                    <p className="text-[15px] text-[var(--ink-70)]">
                                        Declaration text
                                    </p>
                                    <p className="text-[13px] text-[var(--ink-55)]">
                                        Typed into the form, not uploaded
                                    </p>
                                </div>
                                <p className="euk-label text-[11px] italic text-[var(--ink-55)]">
                                    No attach box appears in Part B — on
                                    purpose.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* four states, never a boolean */}
                    <div className="grid grid-cols-2 gap-2.5 pt-6 md:grid-cols-4">
                        {[
                            {
                                k: "READY TO PREPARE",
                                d: "We have the specification.",
                                line: "--ok-line",
                                fill: "--ok-fill",
                                dashed: false,
                            },
                            {
                                k: "ONE STEP IS YOURS",
                                d: "Never shown as done.",
                                line: "--partial-line",
                                fill: "--partial-fill",
                                dashed: false,
                            },
                            {
                                k: "GUIDANCE ONLY",
                                d: "The portal captures this.",
                                line: "--guide-line",
                                fill: "--guide-fill",
                                dashed: false,
                            },
                            {
                                k: "CANNOT PREPARE YET",
                                d: "Not a failure.",
                                line: "--notyet-line",
                                fill: "--notyet-fill",
                                dashed: true,
                            },
                        ].map((s) => (
                            <div
                                key={s.k}
                                className={`border-[3px] p-3 ${s.dashed ? "border-dashed" : ""}`}
                                style={{
                                    borderColor: `var(${s.dashed ? s.line : "--ink"})`,
                                    background: `var(${s.fill})`,
                                }}
                            >
                                <p
                                    className="euk-label pb-1 text-[10px] font-bold md:text-[10px]"
                                    style={{ color: `var(${s.line})` }}
                                >
                                    {s.k}
                                </p>
                                <p className="text-[12px] leading-snug text-[var(--ink-70)]">
                                    {s.d}
                                </p>
                            </div>
                        ))}
                    </div>
                    <Note className="pt-4 text-[15px] md:text-base">
                        Four states, never a boolean — and never red, because
                        &ldquo;not yet&rdquo; is not a failure.
                    </Note>
                </section>

                {/* pricing */}
                <section
                    className="border-t-[3px] border-[var(--ink)] bg-[var(--paper-2)] px-5 py-9 md:px-12 md:py-12"
                    id="pricing"
                >
                    <h2 className="euk-display pb-6 text-[36px] md:text-[44px] md:leading-[0.92]">
                        Three rupees.
                        <br />
                        One less thing to fix.
                    </h2>
                    <div className="grid gap-4 md:grid-cols-3 md:gap-[18px]">
                        {[
                            { n: "₹3", was: "₹4", t: "One file", d: "One chargeable image — photograph, signature or thumb impression." },
                            { n: "₹5", was: "₹8", t: "Two files", d: "Two chargeable images, such as your photograph and signature." },
                            { n: "₹8", was: "₹10", t: "Everything", d: "Three or more. The price stops here, whatever the exam asks for." },
                        ].map((p) => (
                            <div key={p.n} className="euk-block euk-block--drop p-4">
                                <p className="euk-label pb-2 text-[10px] text-[var(--ink-55)]">
                                    {p.t.toUpperCase()}
                                </p>
                                <p className="flex items-baseline gap-2">
                                    <span className="euk-display text-[46px]">
                                        {p.n}
                                    </span>
                                    <span className="euk-label text-[13px] text-[var(--ink-40)] line-through">
                                        {p.was}
                                    </span>
                                </p>
                                <p className="pt-2 text-[14px] leading-relaxed text-[var(--ink-70)]">
                                    {p.d}
                                </p>
                            </div>
                        ))}
                    </div>
                    <Note className="pt-5 text-[15px] md:text-base">
                        Everything the other sites charge for, or make you open
                        a fourth tab for — merging PDFs, reordering or removing
                        pages, turning an image into a document, getting a file
                        under a size limit — is free here with any prepared
                        file.
                    </Note>
                    <p className="euk-label pt-3 text-[11px] leading-relaxed text-[var(--ink-55)]">
                        FILES ARE DELETED WITHIN 30 MINUTES — OR WITHIN AN HOUR,
                        IF YOU ASK US TO KEEP THEM.
                    </p>
                </section>
            </main>
            <SiteFooter />
        </div>
    );
}
