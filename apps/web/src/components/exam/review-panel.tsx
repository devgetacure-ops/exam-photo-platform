"use client";

import { useEffect, useState } from "react";
import { getApiBaseUrl } from "../../lib/api-client";

/**
 * "How did we do?", under the downloads, once the payment is confirmed (DEC-112).
 *
 * Stars first, because that is what a candidate in a hurry will give; then a
 * few ready-made words that change with the rating; then their own. Nothing
 * is public until the owner approves it and the candidate allowed it. While
 * the owner runs the offer, a review returns a single-use code that makes the
 * next examination's files free.
 */

interface ReviewState {
    review: { rating: number; tags: string[]; comment: string; name: string; may_publish: number } | null;
    reward_code: string | null;
    offer: boolean;
    tags: { good: string[]; bad: string[] };
}

const STAR_WORDS = ["", "Poor", "Not good", "Okay", "Good", "Excellent"];

/**
 * Opened either from the downloads screen, where the kit proves the purchase,
 * or from the delivery email, where the link's signature does.
 */
export function ReviewPanel({ kitId, orderId, token }: { kitId?: string; orderId: string; token?: string }) {
    const [state, setState] = useState<ReviewState | null>(null);
    const [rating, setRating] = useState(0);
    const [tags, setTags] = useState<string[]>([]);
    const [comment, setComment] = useState("");
    const [name, setName] = useState("");
    const [mayPublish, setMayPublish] = useState(false);
    const [sending, setSending] = useState(false);
    const [error, setError] = useState("");
    const [sent, setSent] = useState(false);
    const [reward, setReward] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        let live = true;
        const base = getApiBaseUrl();
        const load: Promise<ReviewState | null> = kitId
            ? fetch(new URL(`/v1/kits/${encodeURIComponent(kitId)}/review?order_id=${encodeURIComponent(orderId)}`, base), {
                  cache: "no-store",
              }).then((response) => (response.ok ? (response.json() as Promise<ReviewState>) : null))
            : Promise.all([
                  fetch(new URL("/v1/review-options", base)).then((r) => r.json() as Promise<{ tags: ReviewState["tags"] }>),
                  fetch(new URL("/v1/offers", base)).then((r) => r.json() as Promise<{ review_reward: boolean }>),
              ]).then(([options, offers]) => ({ review: null, reward_code: null, offer: offers.review_reward, tags: options.tags }));
        load
            .then((value) => {
                if (!live || !value) return;
                setState(value);
                setReward(value.reward_code);
                if (value.review) {
                    setRating(value.review.rating);
                    setTags(value.review.tags);
                    setComment(value.review.comment ?? "");
                    setName(value.review.name ?? "");
                    setMayPublish(Boolean(value.review.may_publish));
                    setSent(true);
                }
            })
            .catch(() => undefined);
        return () => {
            live = false;
        };
    }, [kitId, orderId]);

    if (!state) return null;
    const options = rating >= 4 ? state.tags.good : rating > 0 ? state.tags.bad : [];

    const submit = async () => {
        if (!rating || sending) return;
        setSending(true);
        setError("");
        try {
            const path = kitId ? `/v1/kits/${encodeURIComponent(kitId)}/review` : "/v1/feedback";
            const response = await fetch(new URL(path, getApiBaseUrl()), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    order_id: orderId,
                    ...(token ? { token } : {}),
                    rating,
                    tags: tags.filter((t) => options.includes(t)),
                    comment,
                    name,
                    may_publish: mayPublish,
                }),
                signal: AbortSignal.timeout(15000),
            });
            if (!response.ok) throw new Error();
            const body = (await response.json()) as { reward_code: string | null };
            setReward(body.reward_code);
            setSent(true);
        } catch {
            setError("That didn’t send. Please try again.");
        } finally {
            setSending(false);
        }
    };

    return (
        <section className="euk-rate" aria-labelledby="rate-title">
            <h3 id="rate-title">{sent ? "Thank you for your review" : "How did we do?"}</h3>
            {state.offer && !reward && (
                <p className="euk-rate-offer">Rate us and your next examination&rsquo;s files are free.</p>
            )}
            {reward && (
                <div className="euk-rate-reward" role="status">
                    <p>Your code for free files on your next examination:</p>
                    <p className="euk-rate-code">
                        <strong>{reward}</strong>
                        <button
                            type="button"
                            className="quiet-link"
                            onClick={async () => {
                                try {
                                    await navigator.clipboard.writeText(reward);
                                    setCopied(true);
                                } catch {
                                    /* The code stays on screen to copy by hand. */
                                }
                            }}
                        >
                            {copied ? "Copied" : "Copy"}
                        </button>
                    </p>
                    <p className="euk-rate-fine">Enter it under &ldquo;Have a code?&rdquo; before you pay. It works once.</p>
                </div>
            )}

            <fieldset className="euk-rate-stars">
                <legend>Your rating</legend>
                {[1, 2, 3, 4, 5].map((star) => (
                    <label key={star} data-on={star <= rating ? "true" : undefined}>
                        <input
                            type="radio"
                            name="euk-rating"
                            value={star}
                            checked={rating === star}
                            onChange={() => {
                                setRating(star);
                                setTags([]);
                            }}
                        />
                        <span aria-hidden="true">★</span>
                        <span className="sr-only">
                            {star} star{star === 1 ? "" : "s"}, {STAR_WORDS[star]}
                        </span>
                    </label>
                ))}
                {rating > 0 && <span className="euk-rate-word">{STAR_WORDS[rating]}</span>}
            </fieldset>

            {options.length > 0 && (
                <fieldset className="euk-rate-tags">
                    <legend>{rating >= 4 ? "What went well?" : "What went wrong?"}</legend>
                    {options.map((tag) => (
                        <label key={tag} data-on={tags.includes(tag) ? "true" : undefined}>
                            <input
                                type="checkbox"
                                checked={tags.includes(tag)}
                                onChange={(event) =>
                                    setTags((now) => (event.target.checked ? [...now, tag] : now.filter((t) => t !== tag)))
                                }
                            />
                            {tag}
                        </label>
                    ))}
                </fieldset>
            )}

            {rating > 0 && (
                <>
                    <label className="euk-rate-field">
                        <span>In your own words (optional)</span>
                        <textarea value={comment} onChange={(e) => setComment(e.target.value)} maxLength={500} rows={3} />
                    </label>
                    <label className="euk-rate-field">
                        <span>First name (optional)</span>
                        <input value={name} onChange={(e) => setName(e.target.value)} maxLength={40} autoComplete="given-name" />
                    </label>
                    <label className="euk-consent">
                        <input type="checkbox" checked={mayPublish} onChange={(e) => setMayPublish(e.target.checked)} />
                        <span>You may show this review on the site, with my first name if I gave one.</span>
                    </label>
                    <button type="button" className="primary-button" onClick={() => void submit()} disabled={sending}>
                        {sending ? "Sending…" : sent ? "Update my review" : "Send my review"}
                    </button>
                    {error && (
                        <p className="euk-total-alert" role="alert">
                            {error}
                        </p>
                    )}
                </>
            )}
        </section>
    );
}
