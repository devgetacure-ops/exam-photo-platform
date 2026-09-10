# Candidate UI verification — 7 September 2026

## Preview
- Production Next.js preview: http://localhost:3001 (started in this run).
- Existing development server on port 3000 was left running.
- No public deployment, commit, push or real payment was performed.

## Implemented
- Landing story, generated editorial art, comparison control, pricing, FAQ and footer.
- Shared theme toggle and candidate journey tokens; existing Instrument Sans retained.
- Dedicated mobile requirement selector with support optgroups, visible support label,
  distinct guidance colour and no upload for unsupported requirements.
- Original-file display while preparing; real protected-preview comparison afterward.
- Partially supported files and invalid outputs never receive a clean success state.
- Server quote/order integration, review acknowledgement, job entitlement polling,
  reload recovery of pending checkout references, unavailable/error states.
- Authoritative countdown, retention warning before checkout, extension, expiry state,
  individual released downloads and released-kit ZIP, warm delivery message.
- WhatsApp public exam-page share, explicitly distinguished from sending attachments.
- Shared headers/footers on exam and rules families; citations and estimates preserved.
- Removed unused upload-card.tsx and processing-status.tsx. result-preview.tsx and
  validation-report.tsx remain referenced by existing regression tests, not candidates.

## Files
- app/page.tsx; app/layout.tsx; app/globals.css; app/journey.css.
- app/exam/[examId]/page.tsx and rules/page.tsx.
- app/assets/upload-kit-illustration.png and exact-asset .gitignore exception.
- components/site-header.tsx, site-footer.tsx, theme-toggle.tsx, file-comparison.tsx.
- components/exam/kit-workspace.tsx, kit-checkout.tsx, kit-checkout.test.tsx,
  live-job-state.ts, requirement-panel.tsx, requirement-upload.tsx,
  preparation-loader.tsx, outcome-result.tsx.
- docs/UI_REDESIGN_PLAN_2026_09_07.md, UI_ENGINE_HANDOFF.md,
  07_REQUIREMENTS_TRACEABILITY.md, 08_DECISION_LOG.md and this report.

## Checks actually performed
- Production build: PASS, including TypeScript; 110 generated pages, containing
  52 exam routes and 52 rules routes.
- Standalone TypeScript check: PASS; final build also rechecked TypeScript.
- ESLint: PASS, no reported errors/warnings.
- Prettier check on changed UI files: PASS. Invoked via npm exec without adding a dependency.
- Vitest: PASS, 92 tests in 10 files. Existing admin test emits jsdom's
  'navigation to another Document' diagnostic but passes. No backend suite was run;
  engine code was outside this lane and concurrently modified elsewhere.
- New tests verify unpaid/expired/invalid-deadline download refusal; server-priced
  checkout, mandatory acknowledgement, callback not granting release; unavailable
  quote; and rejection of a quote containing an undisplayed file.
- HTTP smoke against production preview: home 200; all 104 exam/rules paths 200;
  withdrawn bpsc-current-recruitment-photograph-specification route 404.
  Raw local route results: .tmp/ui-route-smoke.json (ignored).
- Landing, NEET workspace and NEET rules DOM layout checks at 360, 390, 430,
  768, 1024, 1280 and 1440 px: no horizontal overflow. Visual screenshots inspected
  at representative desktop/mobile sizes; not a screenshot of every catalogue page.
- Keyboard comparison slider advanced from 50 to 51; FAQ retention disclosure opened;
  mobile requirement selection and dark-mode toggle operated successfully.
- Browser-prepared a fictional signature-good.jpg through the running API. Engine
  returned signature.jpg, 348 x 152 px, 11 KB, protected preview and normalisation
  findings. Original/preview comparison rendered; clean downloads remained gated.
- Extended that synthetic job using the UI: server deadline advanced from 15:54
  to 15:56 local time, leaving ~30 minutes from extension. No release was granted.
- Fresh production homepage console inspection: no errors. Earlier development
  logs included transient compilation/hot-reload errors while editing; those were fixed.
- git diff --check for UI: PASS; git status reviewed. Only the documented generated
  editorial illustration was added as media; no candidate uploads were added.

## Still pending / practical limits
- Running API OpenAPI has prepare and extend, but no quote/order endpoints, despite
  newer source and handoff implementing them. Checkout correctly stays unavailable.
  Provider order creation, actual payment, webhook release and real downloads have
  not been verified against a live payment configuration; release gating is tested.
- Lighting-toggle API, real staged progress, sourced per-exam facts and email delivery
  contracts are absent. These are explicit engine requests, not simulated features.
- A prepared-kit subset purchase requires engine support. Current purchase explicitly
  covers the full prepared kit; users choose services by choosing what to prepare.
- Original upload bytes are not persisted. After reload the kit/delivery review can
  recover through stored job references, but the original comparison cannot.
- Legacy portrait asset provenance is not confirmed. Existing provenance text describes
  an older European GAN asset; current Indian-looking portrait needs author evidence.
- Full assistive-technology/contrast audit and exhaustive visual state screenshots for
  all 104 generated routes are not claimed. Admin was not redesigned; its tests pass.
- No reliable aggregate exam-upload disqualification statistic was found. Copy uses
  a specific official notice instead of an invented number or competitor accusation.
