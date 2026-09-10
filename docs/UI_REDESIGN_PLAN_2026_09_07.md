# UploadReady redesign — 7 September 2026

## Confirmed brief and scope
Candidate landing, exam workspace, rules pages, preparation, protected review,
checkout and delivery. Preserve official citations, estimate markers, rejection
conditions and all four support states. Work in app/components; engine work and
shared API contracts are coordination requests. Existing admin logic is preserved.

## Direction and reference research
Evolve the existing Clear Companion direction: Instrument Sans, cobalt actions,
navy typography, white/pale-blue surfaces, deliberate paper illustration and
restrained motion. Mobile gets a compact task selector and vertically composed
review; desktop gets a persistent requirement rail and generous review area.
The product is UploadReady, not getAcure: apply the supplied quality contract
without importing healthcare claims or an unrelated logo.

- Linear live homepage and [interface refresh](https://linear.app/now/behind-the-latest-design-refresh): predictable action placement, reduced visual noise, product demonstrations. Observed live in browser 7 September.
- [Stripe Payments](https://stripe.com/in/payments): aligned editorial grid, visible product explanation and progressive detail. Observed live in browser 7 September.
- [SSC official notice, section 20.1.3](https://ssc.nic.in/SSCFileServer/PortalManagement/UploadedFiles/notice_rhqladakh_23052022.pdf): an example of unclear-photo/signature rejection conditions. No verified aggregate rejection count found; do not invent one or generalise an old exam's rules to all exams.

## Phases
1. Rebuild catalogue: completed baseline build, 52 exam and 52 rules routes.
2. Landing story, illustration, comparison interaction, honest pricing and footer.
3. Candidate workflow, source comparison, partial support, retention and delivery.
4. Server quote/order integration with entitlement polling; no browser release.
5. Responsive, accessibility and error-state QA; lint, typecheck, tests and build.

## Dependencies, risks and recommendations
- Current engine source implements quote/order and expiry extension. Keep typed
  integration in the candidate component lane; propose shared-client consolidation
  in the handoff rather than editing shared contracts without coordination.
- No current public lighting-toggle, staged-progress, facts or email contract
  was found. Requested engine coordination. Do not invent enabled controls,
  percentage progress, exam facts or email delivery. Design pending states honestly.
- Live payment tests require configured provider and webhook. Never charge for QA.
- PDF has no image preview; disclose this before purchase.
- Existing portrait provenance needs confirmation from its author before merge.
  New illustration was generated in this run with the built-in ImageGen tool,
  without reference photographs or candidate uploads. Source:
  `exec-7648edc8-bd62-4d6a-ab7d-571a37ed57d1.png`; copied to
  `apps/web/src/app/assets/upload-kit-illustration.png`. It is fictional editorial
  art, not engine output or an official accepted example.
- No git history rewriting, deployment or changes to the concurrent engine lane.
- Retention: deleted within 30 minutes, or within an hour if extended before expiry.
  Returning to this browser can recover job references; clearing browser storage cannot.

## Verification checkpoint
The implemented candidate UI, exact checks and remaining engine dependencies are
recorded in UI_REDESIGN_QA_2026_09_07.md. All 104 exam/rules routes returned HTTP 200
from the production preview; the withdrawn BPSC route returned 404. This is a
local UI completion checkpoint, not a live-payment or full-feature launch claim.
