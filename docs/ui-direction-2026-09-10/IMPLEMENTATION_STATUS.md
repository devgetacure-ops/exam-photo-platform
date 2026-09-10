# Implementation and verification — 10 September 2026

The original direction remains in ORIGINAL_VERBATIM.txt and all 47 unchanged source blocks remain in STRUCTURED_DIRECTION.md. This report supplements them; it does not supersede their wording. This is a locally verified implementation increment, not completion of every ambition in the brief or production activation.

## Implemented

- Central editorial theme extension, centered landing composition, shared spacing and typography, responsive workflow/pricing/story/footer, existing authorized assets and fonts retained.
- Search and full directory for 132 exams; unavailable-exam request, support, privacy, terms, refund, not-found and error surfaces; sitemap and robots routes.
- Required supported files selected initially; conditional files explicitly selected by the candidate. Unsupported and external requirements remain visible. Prepared-file selection controls the server quote and order.
- Photograph lighting choice, server variant switching, protected preview refresh, truthful correction disclosure, actual progress polling and checkout locks while preparation changes.
- Multi-source document planning, page ordering/removal/restoration and PDF assembly using existing engine endpoints. This is not a PDF-to-image export implementation.
- Source-linked exam facts, manual carousel with optional playback and reduced-motion support; complete requirement rules including exams without supported photographs.
- Optional consented email delivery after verified release, masked receipt and explicit retry. No provider success is fabricated.
- Persistent request receipts with validation, same-origin checks, body limits, deduplication and private filesystem storage. Production requires UPLOADREADY_REQUESTS_DIR. No outbound support notification is claimed.
- Keyboard/non-drag comparison controls, skip link, accessible field labels and feedback, reduced-motion behavior.

## Compatibility and decisions

Quote and order remain server-authoritative. Repeated optional job_ids query parameters narrow the kit to reviewed files; omission preserves whole-kit behavior. No browser amount is submitted. Duplicate, foreign-kit and invalid subsets fail. Lighting status now includes output byte_size. Whole-kit ZIP is offered only for a complete kit selection; individual selected delivery remains available.

Existing support distinctions, protected previews, expiry, payment verification and identity-preserving processing remain the boundaries. Cross-device variant changes during an order still need stronger atomic locking. Document-only pricing has not been redefined while the owner's free-PDF policy choice remains pending.

Request storage uses a provisional 30-day expiry with cleanup on writes. A scheduled idle purge, operations owner and final approved retention/contact policy are launch gates. Do not represent this queue as a staffed ticketing system.

## Reference adaptation and asset provenance

The public Linear, Stripe and Raycast sites were consulted for hierarchy, disciplined grouping and interaction clarity. Adaptations here are a centered product introduction, restrained type hierarchy and progressively disclosed workflow details. No awards, commercial outcomes or copied visual assets are asserted. Existing synthetic product illustration assets were reused. The browser upload fixture was synthetic ink, stored only under ignored .tmp.

## Verification evidence

| Check | Result |
|---|---|
| Next.js production build and TypeScript | Passed; 279 generated pages, including 132 exam and 132 rules pages |
| Frontend tests | 100 passed across 11 files with two workers |
| Backend pricing/orders, lighting, progress and delivery tests | 95 passed |
| Ruff lint and formatting for changed Python files | Passed |
| Mypy changed API module | Passed with actual Python 3.12 target; configured 3.11 target cannot parse installed NumPy stub syntax |
| Browser responsive checks | 42 checks: six representative routes at 360, 390, 430, 768, 1024, 1280 and 1440px; HTTP 200, one h1, no overflow, no page errors |
| Sitemap route sweep | All 271 URLs returned HTTP 200 |
| Visual inspection | Desktop, mobile, dark theme and prepared synthetic signature screenshots inspected |
| Real local integration | Synthetic signature prepared, protected result and server quote displayed; synthetic support request persisted with receipt |
| Diff whitespace | Passed; Git reports repository line-ending normalization warnings |

Evidence is under ignored .tmp/ui-responsive-2026-09-10.json and corresponding screenshots. Tests emitted a Starlette/httpx deprecation warning and an existing jsdom navigation warning; neither failed the suites. An earlier default-concurrency frontend timeout passed on the bounded rerun. An invalid paragraph/dialog nesting hydration issue was fixed and the final browser sweep had no page errors.

## Remaining work and launch gates

1. Resolve C01–C11 in TECHNICAL_COMPANION.md where not explicitly implemented/documented, especially free document/PDF eligibility and strike-through price substantiation.
2. Configure and verify live payment, webhook, email and deployed storage/cleanup behavior. Local engine reports payments not configured; local operator surface is unauthenticated and is not production approval.
3. Finalize legal/business/contact details, support operations, durable production request storage and idle retention enforcement.
4. Research any additional trivia or disqualification claims from appropriate sources. Current facts are source-backed derived facts; no unsupported statistics were added.
5. Complete PDF-to-image export if retained in scope. WhatsApp handoff does not automatically attach private files.
6. Complete cross-device order/variant locking and full live recovery acceptance, accessibility audit, performance assessment and provenance-approved portrait QA. Responsive browser checks do not establish full WCAG compliance.
7. Continue original art direction and motion refinement against the owner's review. A passing build does not establish the brief's subjective world-class quality target.

Local review: http://localhost:3000, /exams, /exam/all-india-sainik-schools-entrance-examination, /support and /exam-request. No deployment or live payment was performed.
