import Image from "next/image";
import Link from "next/link";

import { PHOTO_PAIRS, SIGNATURE_PAIRS } from "../home-story";
import { FindButton } from "./home-actions";

/**
 * The home, on a phone.
 *
 * Under three screens, and every one of them useful before a candidate has
 * decided anything: what this is, the search, three facts that answer "is
 * this going to cost me an account and a lot of money", the examinations most
 * people come for, and the difference the preparation makes. The long
 * argument is one link away at `/about`.
 *
 * Set left, not centred like the desktop hero. A centred block of four lines
 * on a 360px screen reads as a poster; set left it reads as the first screen
 * of an application, which is what it is.
 *
 * The before-and-after is four equal boxes, not the desktop band's
 * self-dragging frames and not a strip to swipe: a photograph pair over a
 * signature pair, each file shown whole inside a square. A swipe strip of a
 * tall photograph card beside a short signature card read as ragged, and hid
 * half of what it had to show. Nothing here moves by itself, so there is
 * nothing to pause and nothing drawing frames on a slow phone.
 */

interface Shortcut {
    id: string;
    label: string;
    name: string;
}

/** One of each: the difference, shown once, rather than a gallery to swipe. */
const COMPARE = [
    { ...PHOTO_PAIRS[0], kind: "Photograph", width: 720, height: 960 },
    { ...SIGNATURE_PAIRS[0], kind: "Signature", width: 960, height: 720 },
];

export function PhoneHome({
    examCount,
    shortcuts,
}: {
    examCount: number;
    shortcuts: Shortcut[];
}) {
    return (
        <section className="euk-m-only euk-mhome" aria-labelledby="mhome-title">
            <h1 id="mhome-title" className="euk-display euk-mhome-title">
                You prepare for the exam. We&rsquo;ll prepare{" "}
                <span className="euk-mark">the files.</span>
            </h1>
            <p className="euk-mhome-sub">
                Photograph, signature, thumb impression, declaration and
                certificates, each made to the rules your examination published.
            </p>

            <FindButton />

            <ul className="euk-mhome-facts">
                <li>
                    <strong>{examCount}</strong>
                    <span>examinations on file</span>
                </li>
                <li>
                    <strong>₹3</strong>
                    <span>a file, ₹5 the whole kit</span>
                </li>
                <li>
                    <strong>No</strong>
                    <span>account to make</span>
                </li>
            </ul>

            {shortcuts.length > 0 && (
                <div className="euk-mhome-block">
                    <p className="euk-mhome-label">Straight to one of these</p>
                    <ul className="euk-mhome-jumps">
                        {shortcuts.map((exam) => (
                            <li key={exam.id}>
                                <Link href={`/exam/${exam.id}`}>
                                    {exam.label}
                                    <span className="sr-only"> — {exam.name}</span>
                                </Link>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            <div className="euk-mhome-block">
                <p className="euk-mhome-label">What changes</p>
                <div className="euk-mhome-compare">
                    {COMPARE.map((pair) => (
                        <figure key={pair.id} className="euk-mhome-pair">
                            <figcaption>{pair.kind}</figcaption>
                            <div className="euk-mhome-frames">
                                <div>
                                    <Image
                                        src={pair.before}
                                        alt={pair.alt}
                                        width={pair.width}
                                        height={pair.height}
                                        sizes="46vw"
                                    />
                                    <span>Uploaded</span>
                                </div>
                                <div>
                                    <Image
                                        src={pair.after}
                                        alt=""
                                        width={pair.width}
                                        height={pair.height}
                                        sizes="46vw"
                                    />
                                    <span>Prepared</span>
                                </div>
                            </div>
                        </figure>
                    ))}
                </div>
                <p className="euk-mhome-note">
                    Representational. The faces and signatures are generated, and
                    these pairs were made to show the difference rather than
                    produced by our engine.
                </p>
            </div>

            <Link href="/about" className="euk-mhome-more">
                <span>
                    <strong>How it works, what it costs, and why it exists</strong>
                    <span>The whole story, for when you have a minute</span>
                </span>
                <svg width="9" height="15" viewBox="0 0 9 15" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M1.5 1 L7.5 7.5 L1.5 14" />
                </svg>
            </Link>
        </section>
    );
}
