"use client";

import Link from "next/link";
import { EmailDelivery } from "./email-delivery";
import { useCallback, useEffect, useRef, useState } from "react";
import {
    getApiBaseUrl,
    jobOutputUrl,
    kitPackageDownloadUrl,
} from "../../lib/api-client";
import { getKit, type KitEntry } from "../../lib/kit-state";
import type { ExamDetail } from "../../lib/types";
import { publishJobs } from "./live-job-state";

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

export function KitCheckout({
    exam,
    entries,
    onBusy,
    preparationBusy = false,
    selectedRequirements,
}: {
    exam: ExamDetail;
    entries: Record<string, KitEntry>;
    onBusy: (value: boolean) => void;
    preparationBusy?: boolean;
    selectedRequirements?: string[];
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
    const [ack, setAck] = useState(false);
    const [now, setNow] = useState(0);
    const [extending, setExtending] = useState<string | null>(null);
    const revision = useRef(0);
    const mounted = useRef(true);
    const kitId = files.length ? getKit(exam.exam_id)?.kitId : undefined;
    const pendingKey = kitId ? `uploadready:pending:${kitId}` : null;
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
    }, [refresh, pendingKey, revisionKey]);
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
    const pay = async () => {
        if (
            !kitId ||
            !quote?.is_payable ||
            !quoteCovered ||
            !ack ||
            !allLive ||
            busy ||
            pending ||
            preparationBusy
        )
            return;
        setBusy(true);
        onBusy(true);
        setError("");
        setNote("");
        try {
            await loadCheckout();
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
            if (!window.Razorpay) throw new Error("Checkout could not open.");
            const checkout = new window.Razorpay({
                key: order.key_id,
                order_id: order.order_id,
                amount: order.amount_paise,
                currency: order.currency,
                name: "UploadReady",
                description: exam.exam_name,
                handler: () => {
                    setPending(true);
                    setNote(
                        "Payment submitted. We’re waiting for confirmed release of your files. Please don’t pay again.",
                    );
                    void refresh();
                },
                modal: {
                    ondismiss: () => {
                        setBusy(false);
                        setPending(true);
                        onBusy(false);
                        setNote(
                            "Checkout closed. If you paid, wait for confirmation and refresh your files before trying again.",
                        );
                        void refresh();
                    },
                },
            });
            checkout.on("payment.failed", () => {
                setBusy(false);
                setPending(true);
                onBusy(false);
                setError(
                    "Payment was not confirmed. Check its status with your payment provider before retrying.",
                );
            });
            try {
                if (pendingKey)
                    sessionStorage.setItem(pendingKey, order.order_id);
            } catch {
                /* Optional. */
            }
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
    if (!files.length)
        return (
            <section className="checkout-panel">
                <div className="checkout-heading">
                    <div>
                        <h2>Your kit starts with one file.</h2>
                        <p>
                            Choose a requirement above. Prepare only the files
                            you need.
                        </p>
                    </div>
                    <Link className="quiet-link" href="/#pricing">
                        See pricing ↗
                    </Link>
                </div>
            </section>
        );
    return (
        <section
            className="checkout-panel"
            aria-label="Review and download your kit"
        >
            {allReleased && (
                <div className="delivery-wish">
                    <p className="eyebrow">One small step, taken care of.</p>
                    <h2>
                        Your files are here.
                        <br />
                        Your next chapter is out there.
                    </h2>
                    <p>
                        Save your downloads, check them once more, and give that
                        exam your best. We’re rooting for you.
                    </p>
                </div>
            )}
            <div className="checkout-heading">
                <div>
                    <h2>
                        {allReleased
                            ? "Download your files"
                            : "Your files, ready for a closer look"}
                    </h2>
                    <p>
                        {allReleased
                            ? "Keep a copy before the deletion deadline."
                            : "This purchase covers the prepared files listed below."}
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
            </div>
            <div className="checkout-list">
                {files.map((entry) => {
                    const job = jobs[entry.jobId];
                    const expired = job && jobExpired(job, now);
                    const available = job && jobDownloadable(job, now);
                    const req = exam.requirements?.find(
                        (r) => r.requirement_id === entry.requirementId,
                    );
                    const seconds = job?.expires_at
                        ? Math.max(
                              0,
                              Math.ceil(
                                  (Date.parse(job.expires_at) - now) / 1000,
                              ),
                          )
                        : null;
                    const reason = quote?.lines.find(
                        (l) => l.job_id === entry.jobId,
                    )?.reason;
                    return (
                        <article className="checkout-file" key={entry.jobId}>
                            <div>
                                <h3>
                                    {req?.requirement_name ??
                                        entry.requirementType}
                                </h3>
                                <small>
                                    {job?.output_filename ??
                                        entry.outputFilename}
                                </small>
                                <small>
                                    {expired
                                        ? "Expired — prepare this file again"
                                        : available
                                          ? "Released for download"
                                          : job
                                            ? "Protected until payment is confirmed"
                                            : "Checking availability…"}
                                </small>
                                {!expired && seconds !== null && (
                                    <small>
                                        Deletes in {Math.floor(seconds / 60)}m{" "}
                                        {seconds % 60}s ·{" "}
                                        <time
                                            dateTime={
                                                job?.expires_at ?? undefined
                                            }
                                        >
                                            {new Date(
                                                job!.expires_at!,
                                            ).toLocaleTimeString([], {
                                                hour: "numeric",
                                                minute: "2-digit",
                                            })}
                                        </time>
                                    </small>
                                )}
                                {reason === "document_work_is_free" && (
                                    <small>
                                        Document preparation included free with
                                        your purchase
                                    </small>
                                )}
                                {entry.outputMediaType ===
                                    "application/pdf" && (
                                    <small>
                                        PDF · no visual preview available
                                    </small>
                                )}
                                {req?.platform_support ===
                                    "partially_supported" && (
                                    <p className="fine-copy">
                                        Partly prepared — your exam still
                                        requires additional steps. Review its
                                        instructions.
                                    </p>
                                )}
                                {entry.findings.length > 0 && (
                                    <details>
                                        <summary className="quiet-link">
                                            Review findings (
                                            {entry.findings.length})
                                        </summary>
                                        <ul>
                                            {entry.findings.map((f) => (
                                                <li
                                                    className="fine-copy"
                                                    key={f}
                                                >
                                                    {f}
                                                </li>
                                            ))}
                                        </ul>
                                    </details>
                                )}
                            </div>
                            <div className="file-actions">
                                {available && (
                                    <a
                                        className="primary-button"
                                        href={jobOutputUrl(entry.jobId)}
                                    >
                                        Download file
                                    </a>
                                )}
                                {job?.extendable && !expired && (
                                    <button
                                        type="button"
                                        className="secondary-button"
                                        disabled={extending !== null}
                                        onClick={() => void extend(entry.jobId)}
                                    >
                                        {extending === entry.jobId
                                            ? "Extending…"
                                            : "Keep for longer"}
                                    </button>
                                )}
                            </div>
                        </article>
                    );
                })}
            </div>
            {kitId && (
                <EmailDelivery
                    kitId={kitId}
                    jobIds={files.map((file) => file.jobId)}
                    released={allReleased}
                />
            )}
            <div className="retention-note">
                <strong>Save your files before they expire.</strong>
                <p>
                    Deleted within 30 minutes of preparation, or within an hour
                    if you ask us to keep them. Extend before the deadline.
                    Payment does not extend storage. Return in this browser
                    while your files are still available.
                </p>
            </div>
            {!allReleased && (
                <>
                    <label className="review-ack">
                        <input
                            type="checkbox"
                            checked={ack}
                            disabled={busy}
                            onChange={(e) => setAck(e.target.checked)}
                        />
                        <span>
                            I have reviewed the files, findings and any
                            remaining steps. I understand that PDFs have no
                            visual preview and files must be downloaded before
                            deletion.
                        </span>
                    </label>
                    <div className="checkout-total">
                        <div>
                            {quote && (
                                <>
                                    <del>{money(quote.list_amount_paise)}</del>
                                    <strong>{money(quote.amount_paise)}</strong>
                                    <p className="fine-copy">
                                        {quote.included_free_count} document
                                        files included free
                                    </p>
                                </>
                            )}
                        </div>
                        <button
                            className="primary-button"
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
                            {pending
                                ? "Waiting for confirmation…"
                                : busy
                                  ? "Opening checkout…"
                                  : quote?.is_payable
                                    ? `Pay ${money(quote.amount_paise)}`
                                    : "Checkout unavailable"}
                        </button>
                    </div>
                    {quote && !quote.is_payable && (
                        <p className="fine-copy">
                            No payable items in this quote. Free documents
                            require a chargeable prepared image in the same
                            purchase.
                        </p>
                    )}
                </>
            )}
            {allReleased && kitId && (
                <div className="file-actions">
                    {completeKitSelected && (
                        <a
                            className="primary-button"
                            href={kitPackageDownloadUrl(kitId)}
                        >
                            Download kit ZIP
                        </a>
                    )}
                    <a
                        className="secondary-button"
                        href={`https://wa.me/?text=${encodeURIComponent(`I'm preparing my ${exam.exam_name} application with UploadReady. ${typeof window !== "undefined" ? window.location.origin : ""}/exam/${exam.exam_id}`)}`}
                        target="_blank"
                        rel="noreferrer"
                    >
                        Share exam page on WhatsApp
                    </a>
                    <p className="fine-copy">
                        To send your files, download them and attach them in
                        WhatsApp. Email attachments are available through the
                        form above.
                    </p>
                </div>
            )}
            {quote && !quoteCovered && (
                <p className="retention-note" role="alert">
                    The server quote includes a file outside this review.
                    Refresh this page before paying.
                </p>
            )}
            {pending && !busy && (
                <button
                    type="button"
                    className="secondary-button"
                    onClick={() => {
                        setPending(false);
                        setAck(false);
                        setNote("");
                        try {
                            if (pendingKey)
                                sessionStorage.removeItem(pendingKey);
                        } catch {
                            /* Optional. */
                        }
                        void refresh();
                    }}
                >
                    I did not pay — review again
                </button>
            )}
            {note && (
                <p className="retention-note" role="status">
                    {note}
                </p>
            )}
            {error && (
                <p className="retention-note" role="alert">
                    {error}
                </p>
            )}
        </section>
    );
}
