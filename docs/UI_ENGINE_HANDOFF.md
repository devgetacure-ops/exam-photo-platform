# UI and engine coordination — 6 September 2026

## Ownership

Codex: candidate app pages, components and styling. Claude Code: image engine, scripts, exam-rule packages and catalogue examples. Changes to `apps/web/src/lib/types.ts` or `api-client.ts` require explicit coordination.

## Shared contract request

The UI added optional `preview_url` and `preview_watermarked` to `PrepareRequirementResponse`. Claude confirmed implementation in the engine lane (DEC-063). No new API-client methods have been introduced by this UI pass.

The UI renders a preview only when `preview_url` exists AND `preview_watermarked === true`. It never falls back to displaying `output_url`; the earlier clean-output fallback has been removed. Right-click and dragging are disabled on the displayed preview, but only server watermarking and entitlement enforcement provide protection.

## Preserved semantics

- Distinct prepared, prepared-with-findings, blocked and not-produced outcomes.
- Five known routine input-normalisation codes remain quiet expandable notes. Unknown findings remain visible caveats.
- HTTP 409 remains requirement-specific guidance, not a transport error.
- Support eligibility is used only to decide whether to offer upload; unsupported requirement guidance remains visible and the five support values are not collapsed into a boolean.
- Loader is indeterminate, with elapsed time rather than invented pipeline stages. It explains approximately 10 seconds for warm photographs and slower service startup.
- Missing BiRefNet weights is an intentional service configuration failure. The UI does not work around it by selecting a coarse mask, and candidate-facing wording does not expose developer commands.

## Current checkpoint and outstanding work

Option 3 is implemented as the initial landing and exam workspace direction. Mobile has a separate requirement selector; desktop has a kit rail. Predictive search now handles separated abbreviations such as IBPS PO within IBPS CRP PO/MT-XVI. Visual rules, sources, reporting dialog and individual/bundle pricing are present.

Responsive design QA now passes at 1440 × 1024 and 390 × 844, including the separate desktop and mobile compositions recorded in `design-qa.md`.

Not launch-complete: all expiry/reload states, payment, delivery, a genuine reporting endpoint, PDF previews and verified 30-minute deletion remain outstanding. Checkout deliberately cannot charge. Reporting explicitly says nothing has been sent unless the user sends an email draft themselves. Do not describe preparation as authority-guaranteed acceptance.

Retention must be enforced by the server and reflected using authoritative expiry. An IP alone must not grant access: shared networks and changing mobile IPs make that unsafe. Recommend a secret guest-session capability, subject to product/engine approval. Do not claim the requested 30-minute deletion guarantee until it is verified end-to-end.

The generated portrait, thumb impression and declaration graphics are fictional guidance assets, not customer uploads or official examples. They are not engine compliance fixtures.
