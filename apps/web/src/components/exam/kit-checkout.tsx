"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import {
    getApiBaseUrl,
    jobOutputUrl,
    kitPackageDownloadUrl,
} from "../../lib/api-client";
import { getKit, type KitEntry } from "../../lib/kit-state";
import type { ExamDetail } from "../../lib/types";
import { publishCheckoutStage, publishJobs } from "./live-job-state";
import { bringIntoView, focusQuietly } from "../../lib/scroll";
import { EmailDelivery } from "./email-delivery";
import { PaymentScene } from "./payment-scene";
import { KitSuccess } from "./kit-success";
import { SimulatedCheckout } from "./simulated-checkout";
import type { ExamFact } from "./exam-facts";
import { FileTypeDrawing } from "../euk/doodles";
import { plainFindings } from "../../lib/finding-text";
import { PreviewThumb } from "./preview-thumb";
import { Note } from "../euk/note";

/**
 * Review, pay, receive.
 *
 * Five designed stages over one set of server contracts, so each moment of the
 * purchase looks like it was expected, including the ones that go wrong:
 *
 * - **review**: every file, the deletion clock, email delivery, the total and
 *   the acknowledgement. Nothing is payable that the candidate hasn't seen.
 * - **paying**: while Razorpay's window is open and while the payment is
 *   confirmed. The files are released only when the server says so; a closed
 *   window never counts as paid.
 * - **failed**: the provider reported a failed payment. Its own words, and the
 *   way back to review.
 * - **delivered**: the good wishes, the downloads, the clock, the receipt.
 *
 * The amount is the server's quote (DEC-070), and payment releases exactly the
 * files that were priced (DEC-071).
 */

// Additive engine contracts, kept in the UI lane pending shared-client coordination.
export interface LiveJob {
    job_id: string;
    status: string;
    entitlement?: string;
    expires_at?: string | null;
    extendable?: boolean;
    output_filename?: string | null;
    output_url?: string | null;
}
interface Quote {
    amount_paise: number;
    list_amount_paise: number;
    currency: string;
    is_payable: boolean;
    /** "simulator" on a test machine running the engine's payment simulator (DEC-089). */
    payment_mode?: string;
    included_free_count: number;
    lines: { job_id: string; reason: string }[];
}
interface Order {
    order_id: string;
    key_id: string;
    amount_paise: number;
    currency: string;
}
interface CheckoutOptions {
    key: string;
    order_id: string;
    amount: number;
    currency: string;
    name: string;
    description: string;
    handler: () => void;
    modal: { ondismiss: () => void };
}
interface CheckoutInstance {
    open: () => void;
    on: (event: string, callback: () => void) => void;
}
declare global {
    interface Window {
        Razorpay?: new (options: CheckoutOptions) => CheckoutInstance;
    }
}

async function request<T>(path: string, method = "GET"): Promise<T> {
    const response = await fetch(new URL(path, getApiBaseUrl()), {
        method,
        cache: "no-store",
        signal: AbortSignal.timeout(15000),
    });
    if (!response.ok)
        throw new Error(
            response.status === 404
                ? "This file or service is no longer available."
                : response.status === 409
                  ? "Your kit has changed or has nothing payable. Refresh the review."
                  : "We couldn’t reach this service. Please try again.",
        );
    return response.json() as Promise<T>;
}
function loadCheckout(): Promise<void> {
    if (window.Razorpay) return Promise.resolve();
    return new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "https://checkout.razorpay.com/v1/checkout.js";
        script.async = true;
        script.onload = () =>
            window.Razorpay
                ? resolve()
                : reject(
                      new Error("Checkout could not open. Please try again."),
                  );
        script.onerror = () => {
            script.remove();
            reject(
                new Error(
                    "Checkout could not load. Please check your connection.",
                ),
            );
        };
        document.head.appendChild(script);
    });
}
export function jobExpired(job: LiveJob, now: number): boolean {
    return (
        job.status.toLowerCase() === "deleted" ||
        (!!job.expires_at && Date.parse(job.expires_at) <= now)
    );
}
export function jobDownloadable(job: LiveJob, now: number): boolean {
    return (
        job.entitlement === "released" &&
        !!job.expires_at &&
        Number.isFinite(Date.parse(job.expires_at)) &&
        !jobExpired(job, now) &&
        !!job.output_url
    );
}
const money = (paise: number) =>
    new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
    }).format(paise / 100);

const clock = (ms: number) =>
    new Date(ms).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

interface Receipt {
    orderId: string;
    amountPaise: number;
}

type Stage = "empty" | "review" | "paying" | "failed" | "delivered";

/** How long the success moment holds before the page moves on to the downloads. */
const DOWNLOADS_AFTER_MS = 2000;

/** The file retention window a fresh preparation gets, for the clock's bar. */
const WINDOW_SECONDS = 30 * 60;

/** Each digit in a box of its own width, so the text beside the clock never moves. */
function Digits({ value }: { value: string }) {
    return (
        <>
            {value.split("").map((digit, i) => (
                <span key={i} className="euk-clock-digit">
                    {digit}
                </span>
            ))}
        </>
    );
}

export function ExpiryClock({
    seconds,
    at,
    delivered,
}: {
    seconds: number;
    at: number;
    delivered: boolean;
}) {
    const minutes = Math.floor(seconds / 60);
    const rest = seconds % 60;
    return (
        <div className="euk-clock" data-urgent={seconds < 5 * 60}>
            <div className="euk-clock-row">
                <p className="euk-clock-figure" aria-hidden="true">
                    <Digits value={String(minutes).padStart(2, "0")} />
                    <span className="euk-clock-colon">:</span>
                    <Digits value={String(rest).padStart(2, "0")} />
                </p>
                <div className="min-w-0">
                    <p className="euk-clock-title">
                        {delivered
                            ? `Download them before ${clock(at)}`
                            : `Deleted at ${clock(at)}`}
                    </p>
                    <p className="euk-clock-text">
                        {delivered
                            ? "After that they are deleted from our side and can’t be recovered. An emailed copy stays in your inbox."
                            : "Files are deleted within 30 minutes of being prepared, or within an hour if you ask us to keep them. Paying doesn’t extend that, so download or email them straight after."}
                    </p>
                </div>
            </div>
            <span className="euk-clock-bar" aria-hidden="true">
                <span
                    style={{
                        transform: `scaleX(${Math.min(1, seconds / WINDOW_SECONDS)})`,
                    }}
                />
            </span>
        </div>
    );
}

function FileRow({
    entry,
    job,
    now,
    name,
    partial,
    reason,
    extending,
    onExtend,
}: {
    entry: KitEntry;
    job?: LiveJob;
    now: number;
    name: string;
    partial: boolean;
    reason?: string;
    extending: string | null;
    onExtend: () => void;
}) {
    const expired = !!job && jobExpired(job, now);
    const available = !!job && jobDownloadable(job, now);
    const notes = plainFindings(entry.findings);
    const seconds =
        job?.expires_at && now > 0
            ? Math.max(0, Math.ceil((Date.parse(job.expires_at) - now) / 1000))
            : null;
    return (
        <li
            className="euk-order-file"
            data-state={expired ? "expired" : available ? "released" : "protected"}
            data-thumb={(entry.previewUrl && !expired) || undefined}
        >
            {entry.previewUrl && !expired ? (
                <PreviewThumb
                    src={new URL(entry.previewUrl, getApiBaseUrl()).toString()}
                    name={name}
                />
            ) : (
                <FileTypeDrawing type={entry.requirementType} className="euk-order-icon" />
            )}
            <div className="euk-order-body">
                <h3 className="euk-order-name">{name}</h3>
                <p className="euk-order-filename">
                    {job?.output_filename ?? entry.outputFilename}
                </p>
                <p className="euk-order-status">
                    {expired
                        ? "Expired — prepare this file again"
                        : available
                          ? "Released for download"
                          : job
                            ? "Protected until payment is confirmed"
                            : "Checking availability…"}
                    {!expired && seconds !== null && (
                        <span className="euk-order-countdown">
                            {" "}
                            · deletes in {Math.floor(seconds / 60)}m{" "}
                            {String(seconds % 60).padStart(2, "0")}s
                        </span>
                    )}
                </p>
                {reason === "document_work_is_free" && (
                    <p className="euk-order-free">
                        Document preparation included free with your purchase
                    </p>
                )}
                {entry.outputMediaType === "application/pdf" && !entry.previewUrl && (
                    <p className="euk-order-meta">PDF · no visual preview available</p>
                )}
                {partial && (
                    <p className="euk-order-meta">
                        Partly prepared — your exam still requires additional
                        steps. Review its instructions.
                    </p>
                )}
                {notes.length > 0 && (
                    <details className="euk-order-findings">
                        <summary>Worth a look ({notes.length})</summary>
                        <ul>
                            {notes.map((note) => (
                                <li key={note}>{note}</li>
                            ))}
                        </ul>
                    </details>
                )}
            </div>
            <div className="euk-order-actions">
                {available && (
                    <a className="primary-button" href={jobOutputUrl(entry.jobId)}>
                        Download file
                    </a>
                )}
                {job?.extendable && !expired && (
                    <button
                        type="button"
                        className="secondary-button"
                        disabled={extending !== null}
                        onClick={onExtend}
                    >
                        {extending === entry.jobId ? "Extending…" : "Keep for longer"}
                    </button>
                )}
            </div>
        </li>
    );
}

export function KitCheckout({
    exam,
    entries,
    onBusy,
    preparationBusy = false,
    selectedRequirements,
    facts = [],
}: {
    exam: ExamDetail;
    entries: Record<string, KitEntry>;
    onBusy: (value: boolean) => void;
    preparationBusy?: boolean;
    selectedRequirements?: string[];
    facts?: ExamFact[];
}) {
    const files = Object.values(entries).filter(
        (e) =>
            ["prepared", "prepared_with_findings"].includes(e.outcome) &&
            (!selectedRequirements ||
                selectedRequirements.includes(e.requirementId)),
    );
    const completeKitSelected =
        Object.values(entries).filter((e) =>
            ["prepared", "prepared_with_findings"].includes(e.outcome),
        ).length === files.length;
    const revisionKey = files.map((e) => `${e.jobId}:${e.updatedAt}`).join(",");
    const signature = files.map((e) => e.jobId).join(",");
    const [jobs, setJobs] = useState<Record<string, LiveJob>>({});
    const [quote, setQuote] = useState<Quote | null>(null);
    const [error, setError] = useState("");
    const [note, setNote] = useState("");
    const [busy, setBusy] = useState(false);
    const [pending, setPending] = useState(false);
    const [simOrder, setSimOrder] = useState<Order | null>(null);
    const [failed, setFailed] = useState(false);
    const [ack, setAck] = useState(false);
    const [now, setNow] = useState(0);
    const [extending, setExtending] = useState<string | null>(null);
    const [receipt, setReceipt] = useState<Receipt | null>(null);
    const revision = useRef(0);
    const mounted = useRef(true);
    const headingRef = useRef<HTMLHeadingElement>(null);
    const downloadsRef = useRef<HTMLHeadingElement>(null);
    const kitId = files.length ? getKit(exam.exam_id)?.kitId : undefined;
    const pendingKey = kitId ? `uploadready:pending:${kitId}` : null;
    const receiptKey = kitId ? `uploadready:receipt:${kitId}` : null;
    const refresh = useCallback(async () => {
        if (!kitId || !signature) return;
        const version = ++revision.current;
        const ids = signature.split(",");
        const results = await Promise.allSettled(
            ids.map((id) =>
                request<LiveJob>(`/v1/jobs/${encodeURIComponent(id)}`),
            ),
        );
        if (!mounted.current || version !== revision.current) return;
        const next: Record<string, LiveJob> = {};
        results.forEach((result, i) => {
            if (result.status === "fulfilled") next[ids[i]] = result.value;
        });
        setJobs(next);
        publishJobs(next);
        setNow(Date.now());
        if (results.some((r) => r.status === "rejected"))
            setError(
                "Some file statuses couldn’t be checked. Refresh before paying or downloading.",
            );
        else setError("");
        try {
            const value = await request<Quote>(
                `/v1/kits/${encodeURIComponent(kitId)}/quote?${new URLSearchParams(ids.map((id) => ["job_ids", id])).toString()}`,
            );
            if (mounted.current && version === revision.current)
                setQuote(value);
        } catch {
            if (mounted.current && version === revision.current) {
                setQuote(null);
                setError(
                    "Pricing is unavailable right now. Checkout is unavailable until the quote can be checked. You can refresh this review.",
                );
            }
        }
    }, [kitId, signature]);
    useEffect(() => {
        mounted.current = true;
        return () => {
            mounted.current = false;
        };
    }, []);
    useEffect(() => {
        let stopped = false;
        let poll: ReturnType<typeof setTimeout> | undefined;
        const check = async () => {
            await refresh();
            if (!stopped) poll = setTimeout(() => void check(), 5000);
        };
        const start = setTimeout(() => {
            setAck(false);
            setQuote(null);
            try {
                if (pendingKey && sessionStorage.getItem(pendingKey)) {
                    setPending(true);
                    setNote(
                        "An earlier checkout may still be confirming. Refresh the status before paying again.",
                    );
                }
                const saved = receiptKey && sessionStorage.getItem(receiptKey);
                if (saved) setReceipt(JSON.parse(saved) as Receipt);
            } catch {
                /* Session storage is optional. */
            }
            void check();
        }, 0);
        return () => {
            stopped = true;
            clearTimeout(start);
            clearTimeout(poll);
        };
    }, [refresh, pendingKey, receiptKey, revisionKey]);
    useEffect(() => {
        const tick = setInterval(() => setNow(Date.now()), 1000);
        return () => clearInterval(tick);
    }, []);
    const released = files.filter(
        (e) => jobs[e.jobId] && jobDownloadable(jobs[e.jobId], now),
    );
    const allReleased = files.length > 0 && released.length === files.length;
    const allLive =
        files.length > 0 &&
        files.every(
            (e) =>
                jobs[e.jobId]?.expires_at &&
                Number.isFinite(Date.parse(jobs[e.jobId].expires_at!)) &&
                !jobExpired(jobs[e.jobId], now),
        );
    const quoteCovered =
        !!quote &&
        files.every((file) =>
            quote.lines.some((line) => line.job_id === file.jobId),
        ) &&
        quote.lines.every(
            (line) =>
                ["expired", "nothing_prepared"].includes(line.reason) ||
                files.some((file) => file.jobId === line.job_id),
        );
    useEffect(() => {
        if (!allReleased) return;
        const timer = setTimeout(() => {
            setPending(false);
            setFailed(false);
            setBusy(false);
            onBusy(false);
            setNote("");
            try {
                if (pendingKey) sessionStorage.removeItem(pendingKey);
            } catch {
                /* Optional. */
            }
        }, 0);
        return () => clearTimeout(timer);
    }, [allReleased, onBusy, pendingKey]);

    const stage: Stage = !files.length
        ? "empty"
        : allReleased
          ? "delivered"
          : failed
            ? "failed"
            : pending || busy
              ? "paying"
              : "review";

    // Focus follows the stage, so a keyboard or screen-reader user lands on what
    // changed. Not on first render: arriving at the page is not a change.
    // Focus moves without the browser's own scroll, which put the section's
    // top under the sticky bar; the section is then brought to just under the
    // bar, and only if it is not already in view (testing notes 9, 11).
    //
    // Payment confirmed while the candidate watches: the success moment plays
    // (about a second), and two seconds in the page carries them on to the
    // downloads, which are what they came for. Arriving at an already-paid kit
    // is not a change, so it never pulls anyone down. Any touch, wheel or key
    // in those two seconds means they are reading, and the move is dropped.
    const shownStage = useRef<Stage | null>(null);
    useEffect(() => {
        publishCheckoutStage(exam.exam_id, stage);
        const previous = shownStage.current;
        const changed = previous !== null && previous !== stage;
        shownStage.current = stage;
        if (!changed) return;
        const heading = headingRef.current;
        focusQuietly(heading);
        bringIntoView(heading?.closest("section") ?? heading, { onlyIfNeeded: true });
        // Only a confirmation the candidate waited for. A paid kit that is
        // still loading passes through another stage on its way to delivered,
        // and that is arriving, not paying.
        if (stage !== "delivered" || previous !== "paying") return;
        const intents = ["wheel", "touchstart", "pointerdown", "keydown"] as const;
        const stop = () => {
            clearTimeout(timer);
            for (const name of intents) window.removeEventListener(name, stop);
        };
        const timer = setTimeout(() => {
            stop();
            const downloads = downloadsRef.current;
            bringIntoView(downloads?.parentElement ?? downloads);
            focusQuietly(downloads);
        }, DOWNLOADS_AFTER_MS);
        for (const name of intents)
            window.addEventListener(name, stop, { passive: true, once: true });
        return stop;
    }, [stage, exam.exam_id]);

    // One set of outcomes, whichever window took the payment: Razorpay's, or
    // the test sheet on a machine running the payment simulator (DEC-089).
    const paymentSubmitted = () => {
        setPending(true);
        setNote(
            "Payment submitted. We’re waiting for confirmed release of your files. Please don’t pay again.",
        );
        void refresh();
    };
    const checkoutClosed = () => {
        setBusy(false);
        setPending(true);
        onBusy(false);
        setNote(
            "Checkout closed. If you paid, wait for confirmation and refresh your files before trying again.",
        );
        void refresh();
    };
    const paymentFailed = () => {
        setBusy(false);
        setFailed(true);
        onBusy(false);
        setError(
            "Payment was not confirmed. Check its status with your payment provider before retrying.",
        );
    };

    const pay = async () => {
        if (
            !kitId ||
            !quote?.is_payable ||
            !quoteCovered ||
            !ack ||
            !allLive ||
            busy ||
            pending ||
            failed ||
            preparationBusy
        )
            return;
        setBusy(true);
        onBusy(true);
        setError("");
        setNote("");
        try {
            const simulated = quote.payment_mode === "simulator";
            // The test sheet needs no script; the live site always loads Razorpay.
            if (!simulated) await loadCheckout();
            const order = await request<Order>(
                `/v1/kits/${encodeURIComponent(kitId)}/order?${new URLSearchParams(files.map((file) => ["job_ids", file.jobId])).toString()}`,
                "POST",
            );
            if (
                order.amount_paise !== quote.amount_paise ||
                order.currency !== quote.currency
            ) {
                setAck(false);
                await refresh();
                throw new Error(
                    "The quote changed. Review the updated total before continuing.",
                );
            }
            const nextReceipt = {
                orderId: order.order_id,
                amountPaise: order.amount_paise,
            };
            setReceipt(nextReceipt);
            try {
                if (pendingKey)
                    sessionStorage.setItem(pendingKey, order.order_id);
                if (receiptKey)
                    sessionStorage.setItem(receiptKey, JSON.stringify(nextReceipt));
            } catch {
                /* Optional. */
            }
            if (simulated) {
                setSimOrder(order);
                return;
            }
            if (!window.Razorpay) throw new Error("Checkout could not open.");
            const checkout = new window.Razorpay({
                key: order.key_id,
                order_id: order.order_id,
                amount: order.amount_paise,
                currency: order.currency,
                name: "ExamUploadKit",
                description: exam.exam_name,
                handler: paymentSubmitted,
                modal: { ondismiss: checkoutClosed },
            });
            checkout.on("payment.failed", paymentFailed);
            checkout.open();
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Checkout is unavailable.",
            );
            setBusy(false);
            onBusy(false);
        }
    };
    const extend = async (id: string) => {
        setExtending(id);
        setError("");
        try {
            await request(`/v1/jobs/${encodeURIComponent(id)}/extend`, "POST");
            await refresh();
            setNote("The updated deletion deadline is shown below.");
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Could not extend this file.",
            );
        } finally {
            setExtending(null);
        }
    };
    const backToReview = () => {
        setPending(false);
        setFailed(false);
        setAck(false);
        setNote("");
        setError("");
        try {
            if (pendingKey) sessionStorage.removeItem(pendingKey);
        } catch {
            /* Optional. */
        }
        void refresh();
    };

    if (stage === "empty")
        return (
            <section className="euk-review-empty" aria-labelledby="review-empty-title">
                <h2 id="review-empty-title" className="euk-review-empty-title">
                    Nothing to review yet
                </h2>
                <p>
                    Prepare a file above and it lands here with its price. You
                    pay only after you have seen every file.
                </p>
            </section>
        );

    const deadlines = files
        .map((file) => Date.parse(jobs[file.jobId]?.expires_at ?? ""))
        .filter((value) => Number.isFinite(value));
    const earliest = deadlines.length ? Math.min(...deadlines) : null;
    const secondsLeft =
        earliest !== null && now > 0
            ? Math.max(0, Math.ceil((earliest - now) / 1000))
            : null;

    const rows = (
        <ol className="euk-order-files">
            {files.map((entry) => {
                const requirement = exam.requirements?.find(
                    (r) => r.requirement_id === entry.requirementId,
                );
                return (
                    <FileRow
                        key={entry.jobId}
                        entry={entry}
                        job={jobs[entry.jobId]}
                        now={now}
                        name={requirement?.requirement_name ?? entry.requirementType}
                        partial={requirement?.platform_support === "partially_supported"}
                        reason={quote?.lines.find((l) => l.job_id === entry.jobId)?.reason}
                        extending={extending}
                        onExtend={() => void extend(entry.jobId)}
                    />
                );
            })}
        </ol>
    );

    const clockBlock =
        secondsLeft !== null && earliest !== null ? (
            <ExpiryClock
                seconds={secondsLeft}
                at={earliest}
                delivered={stage === "delivered"}
            />
        ) : null;

    if (stage === "paying") {
        return (
            <PaymentScene
                examName={exam.exam_name}
                facts={facts}
                headingRef={headingRef}
                title={pending ? "Payment sent. Confirming it." : simOrder ? "Finish paying in the test payment window." : "Finish paying in the Razorpay window."}
                note={
                    note ||
                    (pending
                        ? "We’re waiting for the payment to be confirmed. Please don’t pay again."
                        : "It opens over this page. Close it and you’re straight back here.")
                }
            >
                {simOrder && (
                    <SimulatedCheckout
                        amount={money(simOrder.amount_paise)}
                        examName={exam.exam_name}
                        onPay={async () => {
                            await request(
                                `/v1/payments/simulator/${encodeURIComponent(simOrder.order_id)}/pay`,
                                "POST",
                            );
                            setSimOrder(null);
                            paymentSubmitted();
                        }}
                        onFail={() => {
                            setSimOrder(null);
                            paymentFailed();
                        }}
                        onClose={() => {
                            setSimOrder(null);
                            checkoutClosed();
                        }}
                    />
                )}
                <div className="euk-pay-actions">
                    <button
                        type="button"
                        className="secondary-button"
                        disabled={busy && !pending}
                        onClick={() => void refresh()}
                    >
                        Refresh status
                    </button>
                    {pending && !busy && (
                        <button type="button" className="quiet-link" onClick={backToReview}>
                            I did not pay — review again
                        </button>
                    )}
                </div>
                {error && (
                    <p className="euk-total-alert" role="alert">
                        {error}
                    </p>
                )}
            </PaymentScene>
        );
    }

    if (stage === "failed") {
        return (
            <section className="euk-failed" aria-labelledby="failed-title">
                <div className="euk-failed-art" aria-hidden="true">
                    <svg viewBox="0 0 160 140" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M22 20 H 118 L 138 40 V 124 H 22 Z" />
                        <path d="M118 20 V 40 H 138" />
                        <path d="M38 52 H 96 M38 66 H 90 M38 80 H 100" />
                        <g className="euk-failed-mark">
                            <rect x="52" y="92" width="64" height="24" />
                            <path d="M58 98 L 110 110 M110 98 L 58 110" />
                        </g>
                    </svg>
                </div>
                <div className="min-w-0">
                    <h2
                        id="failed-title"
                        ref={headingRef}
                        tabIndex={-1}
                        className="euk-display euk-failed-title"
                    >
                        The payment didn’t go through.
                    </h2>
                    {error && (
                        <p className="euk-failed-reason" role="alert">
                            {error}
                        </p>
                    )}
                    <p className="euk-failed-text">
                        If your bank or UPI app shows money taken for a failed
                        payment, it is reversed on their timeline, not ours.
                        {earliest !== null &&
                            ` Your files are still here until ${clock(earliest)}.`}
                    </p>
                    <div className="euk-pay-actions">
                        <button type="button" className="primary-button" onClick={backToReview}>
                            Review and try again
                        </button>
                        <Link className="quiet-link" href="/support">
                            Get help with a payment
                        </Link>
                    </div>
                </div>
            </section>
        );
    }

    if (stage === "delivered") {
        const deadline = earliest !== null ? clock(earliest) : null;
        const reminder = `My ${exam.exam_name} upload files are ready on ExamUploadKit.${deadline ? ` Download them before ${deadline}, in the browser I used.` : ""} ${typeof window !== "undefined" ? window.location.origin : ""}/exam/${exam.exam_id}`;
        return (
            <section className="euk-delivered" aria-labelledby="done-title">
                <KitSuccess examName={exam.exam_name} titleRef={headingRef} />
                <div className="euk-delivered-grid">
                    <div className="min-w-0">
                        {clockBlock}
                        <div className="euk-delivered-head">
                            <h3 id="kit-downloads" ref={downloadsRef} tabIndex={-1}>
                                Your downloads
                            </h3>
                            {completeKitSelected && kitId && (
                                <a className="primary-button" href={kitPackageDownloadUrl(kitId)}>
                                    Download everything (ZIP)
                                </a>
                            )}
                        </div>
                        {rows}
                        <Note className="euk-delivered-note">
                            Save them somewhere you will find on the day you
                            upload, not only in Downloads.
                        </Note>
                    </div>
                    <aside className="euk-delivered-side" aria-label="Delivery and receipt">
                        {kitId && (
                            <EmailDelivery
                                kitId={kitId}
                                jobIds={files.map((file) => file.jobId)}
                                released
                            />
                        )}
                        <div className="euk-whatsapp">
                            <a
                                className="secondary-button"
                                href={`https://wa.me/?text=${encodeURIComponent(reminder)}`}
                                target="_blank"
                                rel="noreferrer"
                            >
                                Send yourself a reminder on WhatsApp
                            </a>
                            <p>
                                WhatsApp carries the link and the deletion time,
                                not the files themselves.
                            </p>
                        </div>
                        <dl className="euk-order-receipt">
                            <div>
                                <dt>Examination</dt>
                                <dd>{exam.exam_name}</dd>
                            </div>
                            <div>
                                <dt>Files</dt>
                                <dd>{files.length}</dd>
                            </div>
                            {receipt && (
                                <>
                                    <div>
                                        <dt>Paid</dt>
                                        <dd>{money(receipt.amountPaise)}</dd>
                                    </div>
                                    <div>
                                        <dt>Order</dt>
                                        <dd className="euk-order-ref">{receipt.orderId}</dd>
                                    </div>
                                </>
                            )}
                        </dl>
                        <p className="euk-order-help">
                            Something missing?{" "}
                            <Link className="euk-link" href="/support">
                                Write to support
                            </Link>{" "}
                            with the order reference.
                        </p>
                    </aside>
                </div>
            </section>
        );
    }

    return (
        <section className="euk-review" aria-labelledby="review-title">
            <header className="euk-review-head">
                <div className="min-w-0">
                    <h2
                        id="review-title"
                        ref={headingRef}
                        tabIndex={-1}
                        className="euk-display"
                    >
                        Review before you pay
                    </h2>
                    <p>
                        These are the files you are buying. Once payment is
                        confirmed they download without the watermark.
                    </p>
                </div>
                <button
                    type="button"
                    className="secondary-button"
                    disabled={busy && !pending}
                    onClick={() => void refresh()}
                >
                    Refresh status
                </button>
            </header>

            <div className="euk-review-grid">
                <div className="min-w-0">
                    {rows}
                    {clockBlock}
                    {kitId && (
                        <div className="euk-delivery">
                            <EmailDelivery
                                kitId={kitId}
                                jobIds={files.map((file) => file.jobId)}
                                released={false}
                            />
                            <p className="euk-delivery-whatsapp">
                                WhatsApp can’t carry files, so we don’t send them
                                there. Once you have paid, you can send yourself a
                                reminder with the link and the deletion time.
                            </p>
                        </div>
                    )}
                </div>

                <aside className="euk-review-side" aria-label="Total">
                    <div className="euk-review-total">
                    <p className="euk-total-name">
                        {files.length} file{files.length === 1 ? "" : "s"}
                    </p>
                    <p className="euk-total-row">
                        {quote ? (
                            <>
                                <span className="euk-total-figure">
                                    {money(quote.amount_paise)}
                                </span>
                                {quote.list_amount_paise > quote.amount_paise && (
                                    <del>{money(quote.list_amount_paise)}</del>
                                )}
                            </>
                        ) : (
                            <span className="euk-total-figure euk-total-figure--unknown">
                                ₹–
                            </span>
                        )}
                    </p>
                    {quote && quote.included_free_count > 0 && (
                        <p className="euk-total-free">
                            {quote.included_free_count} document file
                            {quote.included_free_count === 1 ? "" : "s"} included free
                        </p>
                    )}
                    <label className="euk-consent euk-total-ack">
                        <input
                            type="checkbox"
                            checked={ack}
                            disabled={busy}
                            onChange={(e) => setAck(e.target.checked)}
                        />
                        <span>
                            I have reviewed the files and any remaining
                            steps, and I understand files must be downloaded
                            before deletion.
                        </span>
                    </label>
                    <button
                        className="primary-button euk-total-pay"
                        type="button"
                        onClick={() => void pay()}
                        disabled={
                            !quote?.is_payable ||
                            !quoteCovered ||
                            !ack ||
                            !allLive ||
                            busy ||
                            pending ||
                            preparationBusy
                        }
                    >
                        {busy
                            ? "Opening checkout…"
                            : quote?.is_payable
                              ? `Pay ${money(quote.amount_paise)}`
                              : "Checkout unavailable"}
                    </button>
                    <p className="euk-total-fine">
                        Payment through Razorpay. No account needed.
                    </p>
                    {quote && !quote.is_payable && (
                        <p className="euk-total-note">
                            No payable items in this quote. Free documents
                            require a chargeable prepared image in the same
                            purchase.
                        </p>
                    )}
                    {quote && !quoteCovered && (
                        <p className="euk-total-alert" role="alert">
                            The server quote includes a file outside this
                            review. Refresh this page before paying.
                        </p>
                    )}
                    {error && (
                        <p className="euk-total-alert" role="alert">
                            {error}
                        </p>
                    )}
                    {note && (
                        <p className="euk-total-note" role="status">
                            {note}
                        </p>
                    )}
                    </div>
                </aside>
            </div>
        </section>
    );
}
