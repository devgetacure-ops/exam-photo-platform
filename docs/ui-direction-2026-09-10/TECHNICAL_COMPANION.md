# Technical companion — added interpretation, not original wording

This document supplements STRUCTURED_DIRECTION.md. Its recommendations are proposed implementation requirements; unresolved business choices are not silently approved. Original prose remains authoritative as the user's requested direction, including requests that need further implementation or evidence. This is a planning artifact, not a claim of launch readiness.

## Project compatibility and evidence

The product is the Indian Exam-Photo Compliance Platform. Apply the supplied design contract's quality, accessibility, reuse and verification requirements, but do not import getAcure healthcare copy, pharmacy scope, logo or healthcare branding into this exam product. The exact exam-product brand, logo and font direction must be established from its own assets and approved art direction.

Reviewed current repository references: docs/00_PRODUCT_DECISIONS.md, 01_MVP_SCOPE.md, 02_TECHNICAL_ARCHITECTURE.md, 03_EXAM_RULE_SCHEMA.md, 04_IMAGE_PIPELINE_SPEC.md, 05_PRIVACY_SECURITY.md, 06_QA_STRATEGY.md, 07_REQUIREMENTS_TRACEABILITY.md, 08_DECISION_LOG.md, 09_DEVELOPMENT_ROADMAP.md, UI_ENGINE_HANDOFF.md and UI_REDESIGN_BRIEF_FOR_CODEX.md; current api-client.ts and engine api/pricing.py. Historical documents contain superseded statements. Read later decisions alongside older specifications, and verify the running API before integration. This documentation pass did not verify live providers or run application tests.

The existing Next.js candidate app is under apps/web; processing and APIs are under services/image-engine; exam evidence and schemas span examples/rules and packages/exam-rules; shared contracts belong in packages/shared-contracts and the coordinated client types. Preserve the framework and working engine. Respect the engine/client coordination boundary in UI_ENGINE_HANDOFF.md when updating types or API methods.

DEC-079 records 132 catalogue examinations and nullable image_requirements, superseding the older 52-exam baseline. This is a documented snapshot, not a fresh catalogue count or a claim every exam supports photographs. Read catalogue records dynamically; support signatures/documents for live-capture-only exams without inventing photo upload support.

## Complete page and journey structure

| Surface | Required experience | Technical acceptance |
|---|---|---|
| Landing / | Centered bold hero, large exam search; editorial problem story, services, how it works, comparison, value, pricing, our story; expressive footer | Search keyboard operable; no invented exam availability; source-backed claims; existing facts preserved; responsive compositions |
| Search results | Names, aliases, cycles and clear relevant results | Normalize spaced abbreviations; distinguish loading, no match, unavailable and service failure; no promise of all exams |
| Missing exam page (new route, proposed /exam-request) | Dedicated explanation, searched exam name and email notification request | Persistent endpoint, validation, consent, duplicate handling, spam controls, submission receipt; never claim submission succeeded without server acceptance; no unverified delivery date |
| Exam /exam/[examId] | Complete purposeful information, supported work and external tasks, illustrated do/don't guidance, exam facts, kit selection | Preserve exact rules, sources, estimates, applicability, rejection conditions and all five platform_support values |
| Rules /exam/[examId]/rules | Dedicated visual rules and full source details | Handle null photograph rules; show supported non-photo requirements and live-capture guidance rather than blank page |
| Requirement workspace (existing exam route) | Photo, signature, thumb/declaration and document treatments; shared design language with task-specific composition | Upload limits/types from contracts, identity preservation, independent per-file progress/outcomes; no artificial splitting into new routes required |
| Review and checkout (existing workspace, dedicated view if useful) | Selected files, previews, checks, itemized price, contact options, expiry warning and extension | Exact paid inventory; selected variant persisted; changed file/amount requires review again; payment success cannot be simulated |
| Delivery | Warm exam wishes, purposeful celebration, individual/archive downloads, email, WhatsApp option, expiry, receipt and support | Confirm release on server, show delivery channel status separately, handle partial failure and expired files |
| Policies (proposed /privacy, /terms, /refund-policy) | Legible complete policy family | Match actual retention, delivery and refund operations; substantive policy drafting and review are separate work |
| Support (proposed /support) | Queries, issues, grievances and requests | Recommend private tickets with reference and status; public forum is a separate unresolved scope choice; persistent submission and human ownership |
| Shared states | Loading, empty, offline, validation refusal, unsupported item, expired session, unsuccessful/cancelled/pending payment, provider failure, not found | Purposeful visuals and creative recovery copy; correct next action, retained safe context and accessible announcements |

Admin routes already exist. Keep operational functionality and permissions intact; candidate redesign does not authorize a new admin or healthcare product scope.

## Design and research specification

Research is a future execution workstream retained from the source, not research completed by this restructuring task. Study acclaimed SaaS experiences and official exam upload examples: record URL, visit date, screenshots where permitted, observed interaction, why it helps, and the original adaptation proposed here. Verify acclaim if describing a site as acclaimed. Compare actual flow quality, mobile behavior, typography, motion, detail and performance, not only home-page screenshots.

Build an original coherent art direction from the entire named style list in the source. Do not implement every aesthetic simultaneously. Evaluate each: Bauhaus, Dark mode/Light mode, Bold Typography, Neumorphism, Glassmorphism, animation/motion design, illustrations, doddles, micro-interactions, micro-handling animations, Material Design, Claymorphism, Neobrutalism, Aurora UI, Minimalism, Retro-Futurism (Synthwave/Cyberpunk). Keep the user's exact list in the source. Recommendation: editorial composition, distinctive licensed typography, meaningful illustration and restrained motion as the foundation; selective experiments for the remaining styles. Neumorphism conflicts with the supplied contract; decorative glass, aurora and cyberpunk treatments also need compatibility review. Record an explicit direction decision rather than silently deleting them.

Define shared semantic color, typography, spacing, radius, shadow and motion tokens. Explore fonts before selection; recommend one primary family and only a centrally defined complementary display family if justified. Verify license, Indian-script coverage where needed, loading cost, fallback metrics and legibility. Bold centered hero must still leave search usable on small screens. No decorative section labels or numbering in the product. Document IDs in this brief are internal navigation only.

Create a component family for search, requirement selection, upload, rule evidence, source references, comparison, progress, price summary, expiry, alerts, dialogs, carousel and delivery. Keep page sections distinct where purpose differs without fragmented styling. Design light/dark themes deliberately; avoid flash or hydration mismatch. Illustrations must be licensed, synthetic or consented; clearly distinguish illustrative examples from official references and real engine outputs.

Preserve existing content through a before/after inventory of text, sources, estimates, rejection wording, links, actions and conditional states. New marketing copy is a separate authored artifact. Do not treat the unchanged source as ready-to-publish factual copy.

## Engine and data contracts to integrate

| Capability | Repository contract / requirement |
|---|---|
| Catalogue and facts | GET /v1/exams; GET /v1/exams/{exam_id}; facts carry source and kind. Preserve empty facts. DEC-078 adds official-source, as_of and cycle rules for researched trivia; do not equate derived upload facts with completed trivia research. |
| Preparation | POST /v1/exams/{exam_id}/requirements/{requirement_id}/prepare; multipart file, kit_id, enhancement_enabled, progress_token, cf_turnstile_response as supported by the actual API. Current shared client does not expose all newer fields. |
| Progress | GET /v1/progress/{token}; fraction, stage, label, finished, failed. Run polling while preparation is pending; stop on terminal state/unmount; back off on errors. Unknown token 404 is not 0%. Use indeterminate feedback when progress unavailable, never fabricated percentages. |
| Lighting | Photograph-only control; enhancement_enabled, enhancements_applied, enhancement_switchable. POST /v1/jobs/{job_id}/enhancement with enabled. DEC-076 supersedes earlier re-preparation requirement: prepared variants switch server-side. Refresh preview/status and handle 409 when no alternate exists. |
| Documents | Existing planDocument and assembleDocument client methods: upload sources, inspect pages, submit explicit page order. Reorder/omit/merge need undo and keyboard alternatives. PDF-to-image export is a separate capability to verify, not implied by PDF page extraction or image-to-PDF support. |
| Quote and order | GET /v1/kits/{kit_id}/quote then POST /v1/kits/{kit_id}/order. Display server paise amounts/currency and free line reasons; browser sends no amount. Verify selected-subset ordering before advertising purchase of only checked prepared items. |
| Release | GET /v1/jobs/{job_id}; server entitlement released is the gate. Razorpay callback is notification, not proof. Verified webhook controls release; orders pin file IDs. |
| Retention | Authoritative expires_at; POST /v1/jobs/{job_id}/extend; extendable. Existing documented policy: 30 minutes, extension from now bounded at one hour from creation; 404 after expiry and 409 at ceiling. Extension never unlocks payment. |
| Delivery | Job output and kit package/download routes; POST /v1/kits/{kit_id}/email with address and optional job_ids. Confirm masked address only after success. Provider delivery/bounce tracking must not be equated with API acceptance. |

API presence in code or handoff is not proof that the deployed process serves it. Check OpenAPI/readiness and complete representative end-to-end flows before enabling UI promises. Consolidate duplicate checkout contracts through the shared contract owner. Do not bypass failures with mocked compliant output.

## Processing, validation and file integrity

Exam cycle and requirement configure each transformation. Preserve exact dimensions versus range/unspecified crop modes; preserve hair, ears, beard, jaw and natural head framing. Never stretch. Approximately 75–80% face coverage is a diagnostic, not a universal hard rejection rule; preserve each exam's definition and provenance.

Allow only restrained identity-preserving correction: exposure, contrast, color balance, sharpening and supported mild noise reduction. No whitening, beauty retouching, reshaping or generated facial detail. An enabled model may legitimately apply no correction. Verify actual supported operations before describing them as available.

Every edit, page assembly, replacement or variant change must yield validated current deliverables. Review must refer to the exact variant/file later released; define immutable artifact version or equivalent server enforcement to prevent late-toggle/payment races. Invalidate stale preview caches after a switch. Never silently modify paid contents under an old preview.

Validate actual decoded format, dimensions, size, filename, final readability and applicable engine checks; distinguish passed checks, findings, blocked, not produced and manual/authority-only checks. Partial support is not complete compliance or guaranteed exam acceptance. Live capture, recency, eligibility and other uncheckable rules remain guidance. Protect unpaid previews server-side with watermarking and entitlement; do not expose clean output as fallback. Before/after labels must reflect actual result, not presume the original invalid or the result accepted.

Document processing needs bounded input count, page count, decoded pixels and memory; clear corrupted/encrypted/oversized-file outcomes; no automatic alteration of certificate text or marks. Revalidate readability and exam constraints after compression. Specify JPG/PNG conversion eligibility by the exam requirement, not a universal converter promise.

## Commercial and operational decisions requiring explicit resolution

| ID | Original intent / compatibility issue | Recommendation before dependent implementation |
|---|---|---|
| C01 | Free PDFs only with purchase in original; engine pricing.py says document-only kit is genuinely free | Preserve original request; explicitly settle this difference and coordinate backend entitlement/quote changes if paid dependency wins. Do not silently use old policy. |
| C02 | Single price later mentions Rs.5 or 4 as crossed-out price; item 8 specifies Rs.4 | Item 8 plus DEC-070/current code align on 3/4, 5/8, 8/10. Record this as recommended interpretation, not altered original wording. Verify basis for public strike-through prices before publication. |
| C03 | Thumb/other conversion at Rs.8 could mean surcharge versus whole-kit tier | Existing engine charges 3+ chargeable deliverables at total Rs.8 ceiling, including photograph/signature/thumb/declaration; recommend retaining that clear total, subject to explicit reconciliation. Other conversions are not automatically chargeable. |
| C04 | Everything preselected; conditional, external and unsupported requirements exist | Recommend default-select supported applicable required files, keep other requirements visibly explained, request applicability when needed, and make deselection easy. Decide conditional defaults explicitly. Do not charge or offer uploads for external tasks. |
| C05 | User can deselect prepared files | Existing handoff says checkout purchases prepared kit; selected-subset ordering needs server support. Define quote/order selection contract before promising deselection changes payment. |
| C06 | GPU compute-only cost, seconds, disqualification counts, crores, career/fee savings, competitor failures | Require evidence ledger and measured deployment data. Current repository describes CPU serving. Preserve these source statements but do not publish them as verified claims; research exact populations/time periods and avoid invented statistics or guarantees. |
| C07 | All exams available; missing exams added soon | Search only recorded availability; distinguish missing record from unsupported requirement. Notification request does not guarantee release date. |
| C08 | Email/WhatsApp entered before payment should ensure delivery | Define consent, temporary contact retention, automatic send trigger, retries, deduplication and expiry interaction. Existing email API is a send action, not proof of automatic post-payment delivery. wa.me text/link sharing does not send attachments automatically. Authenticated expiring links need an explicit secure handoff design. |
| C09 | Paid but expired/undelivered | Set recovery/refund handling for payment near expiry, late webhook, partial delivery and provider failure. Existing refund assessment is not refund execution; never show refunded until verified. |
| C10 | Support/redressal/request forum | Recommend private ticket workflow initially; decide whether public discussion is actually required before adding moderation and public data exposure. |
| C11 | Broad aesthetic exploration conflicts with generic getAcure rules | Keep every reference; choose an exam-specific coherent visual system explicitly. Do not copy healthcare restrictions as exam product features. |

These choices are documented for the next implementation stage. They do not require interrupting this documentation task or changing production behavior now.

## Payment, privacy, reliability and scale details

Model distinct idle/uploading/processing/prepared-with-findings/blocked/reviewing/order-creating/checkout-open/payment-pending/released/expired states; use backend enums where available and frontend view states separately. Handle dismissal without claiming failure, late verified success without double charge, duplicate callbacks/webhooks, refresh recovery, uncertain network results and mixed file expiries. Recommend idempotent order creation and delivery operations with explicit retry behavior. Never poll forever; provide a recoverable pending state and support reference.

Show extension warning before payment and expiry on delivery per file, using the earliest deadline for kit urgency. Countdown cannot reset on reload or payment. Clarify access expiry versus physical cleanup and external email copies; verify actual deletion and backup/CDN behavior before promising it. Do not promise downloaded or emailed copies disappear when server files expire.

Use secret scoped session/capability authorization for private jobs and kits; identifiers or IP address alone must not be treated as authentication. Verify this boundary rather than assume implemented. Never put photographs, contacts, private artifact URLs or capability tokens into analytics, logs, commits or public support posts. Define consent and retention for notification requests, tickets, contacts, orders and delivery evidence separately from image TTL. No training on uploads without explicit consent.

Validate bytes and safely decode uploads server-side; bound resources, sanitize filenames, restrict file access, enforce CORS and protect operator endpoints. Turnstile integration must precede enabling its server requirement; handle 403 retry and 429 Retry-After without punishing shared Indian mobile IPs. Client checks improve UX but do not replace server validation.

Set measured capacity goals before scale promises: concurrent preparation cap/queue behavior, warmup readiness, saturation, retries, worker memory, cleanup, durable state across workers, provider outage recovery and alert ownership. Measure throughput and latency on target hardware. Avoid per-frame heavy work, unnecessary inference, oversized animated assets and layout-shifting fonts. Proposed frontend targets: p75 LCP <=2.5s, INP <=200ms, CLS <=0.1 on representative devices; these are proposed budgets, not current measurements. Test low-bandwidth and low-memory mobile devices.

## Accessibility, motion and quality acceptance

Verify 360, 390, 430, 768, 1024, 1280 and 1440px. Intentionally compose mobile requirement selection, upload, review and sticky actions. No horizontal overflow or clipped content. WCAG 2.2 AA target; visible focus, semantic controls, labeled inputs/errors, approximately 44px touch targets, contrast in both themes, keyboard/focus-managed dialogs and meaningful screen-reader status.

Comparison needs keyboard/touch control and a non-drag alternative. Carousel needs pause, keyboard controls, stable layout and reduced-motion support; no critical instructions only on a changing slide. Decorative animation must not delay payment/download or announce every progress tick. Use transform/opacity, approved easing where appropriate, and reduced-motion/static alternatives. Wish the candidate well without implying admission or acceptance.

Acceptance includes: all original source blocks accounted for; preserved content/source inventory; unavailable exams; conditional and unsupported files; no-photo exam rules; full/individual kit semantics; PDF operations; lighting/no-change/off cases; honest progress failure; preview findings; itemized server pricing; payment success/cancel/failure/pending/reload; expired/extended files; late payment; download/email failure; WhatsApp truthfulness; support receipt; legal links; all error states and responsive/keyboard behavior.

Run relevant formatting, lint, type checks, tests and production build once code changes occur; engine checks when its contracts change. Browser-test all routes in scope, console errors, responsive states and performance. Use synthetic/consented fixtures, never committed customer photos. Separately verify live order -> verified webhook -> entitlement -> download/email, cleanup, and deployed readiness before launch claims. Record failures/skips honestly and update traceability to actual evidence.

## Implementation sequence and completion evidence

1. Reconcile C01–C11 as applicable; inventory all current content, routes and capabilities; verify current API and nullable catalogue records.
2. Execute reference/claim/exam research with sources; establish art direction, typography, copy and original asset provenance.
3. Build tokens/shared components and implement landing/search/missing-exam/policy/support page families with real submission contracts.
4. Integrate exam inventory, selection, document editing, photograph lighting, real progress and protected validation review.
5. Integrate exact reviewed order, verified release, expiry, contact consent, delivery and recovery; settle atomic variant and subset contracts.
6. Complete responsive, accessibility, functional, performance and live-provider acceptance with evidence. Keep implementation status separate from research and production configuration.

Required handoff: content preservation map, reference/adaptation board, approved token/type specification, route/state inventory, API contract deltas, asset provenance, resolved decision log, acceptance results and explicit remaining gates. No part of this document establishes a successful implementation by description alone.
