# Prompt for the next session: the operator page

Paste everything below the line as the first message of a fresh session, from
`C:\Projects\exam-photo-platform` so `CLAUDE.md` and `AGENTS.md` load.

---

You own this repository and the production server. **The site is live and
taking real payments** at `https://examuploadkit.com`. Local branch
`feat/upload-kit-ui` and `main` are the same commit, and both are pushed.

Read `HANDOFF.md` first — *Live Operations* at the top is the current state of
the server, what runs where, where the secrets live and how to reach it. Then
DEC-063, DEC-066, DEC-069 to DEC-073 and DEC-102 to DEC-107 in
`docs/08_DECISION_LOG.md`. Check `git status` before anything else.

**Note on CI**: GitHub Actions is blocked by an account billing problem, not by
this repository, so every push shows red without running. Verify locally:
`cd apps/web && npm run lint && npx tsc --noEmit -p . && npx vitest run`, and
for the engine `ruff format --check . && ruff check . && mypy src tests` plus
the fast pytest subset in `CLAUDE.md`.

## What this session is for

**An operator page: a way for me to see my own business without a terminal.**
Today the only ways to answer "did this person pay and get their file?" are
`curl` with a bearer token and `ssh`. Four things are missing.

1. **Orders and refunds.** Every order: the examination, the amount, whether
   it was paid, the Razorpay payment reference, whether anything actually
   reached the candidate and how, and the masked address it went to. My refund
   rule is *paid, and not delivered*, and this page should answer that question
   without me reading JSON. The data is already there:
   `GET /v1/orders/{order_id}/evidence` (operator token) returns it per order,
   and the records live in the `artifacts` volume under `_orders/`, one JSON
   file each, never swept.
2. **Exam requests.** Candidates ask for examinations through the form on the
   site. Those are written to the `requests` volume by
   `apps/web/src/lib/request-store.ts` — and **nothing reads them**. Nobody is
   told one arrived. They carry a contact address and a message, and they
   delete themselves after 30 days. This is the most valuable missing thing on
   the page.
3. **How the business is going.** `GET /v1/metrics/usage` (operator token)
   already reports kits, preparations, kits that purchased, a conversion rate
   and a distribution of preparations per kit. Show it plainly. Money can come
   from the order records.
4. **Health.** `GET /ready` from inside (the engine reports warmup, matting
   backend, purchase gate, operator surface, payments, email), plus disk. The
   server already runs `deploy/ops/euk-watch.py` every five minutes and emails
   me when something breaks; the page should show the same truth at a glance.

## Two rules that are not negotiable

- **No candidate photographs, ever, and no full email addresses.** The privacy
  page promises a photograph is used only to prepare the file asked for and is
  erased within thirty minutes; a browsing surface over candidates' faces would
  make that false, and it is biometric data under the DPDP Act. Masked
  addresses only, as the engine already stores them.
- **The page is a new way in, so it must be shut.** It is read-only, it is
  never linked from the candidate site, and it is served only where the
  operator token is present. Put **Cloudflare Access** in front of `/admin`
  (free, emails me a one-time code) and keep the operator token on the server
  side of any request the page makes. The token must never reach the browser.

## How we will work

1. **Plan first.** Read the code, tell me what you will build, where each
   number comes from, and what you propose for authentication. Wait for my go.
2. Then build it in one pass, with tests, and verify against the live server
   before deploying. Tell me before anything that restarts the engine or the
   proxy — a payment could be in flight.
3. Keep `docs/08_DECISION_LOG.md`, `docs/07_REQUIREMENTS_TRACEABILITY.md` and
   *Live Operations* in `HANDOFF.md` true as you go.

## What already exists, so you do not rebuild it

- `apps/web/src/app/admin/` — today it only redirects to `/admin/rules`, the
  local rule console, which is gated by `NEXT_PUBLIC_ENABLE_RULE_ADMIN` and is
  **not** enabled in production. The operator page belongs beside it.
- `apps/web/src/lib/api-client.ts` talks to the engine; the browser and the
  engine share one origin behind Caddy, so there is no CORS to solve. A
  server-side route in the web app is the natural place to hold the operator
  token.
- `deploy/Caddyfile` already answers `/ready` and `/health` only on private
  addresses. Decide deliberately whether `/admin` is routed at the edge or in
  the web app, and write down why.
- `scripts/smoke_catalogue_photographs.py` is the before-deploy check that
  every examination still accepts a real photograph (DEC-104). Run it if you
  touch the engine or the rules.

## Worth deciding while you are here

- `_orders/` has **no retention rule** (DEC-071 left it open). An operator page
  is the moment to decide how long an order record lives, and to say it on the
  privacy page if it changes what candidates were told.
- Whether the page should let me **resend a delivery email** for an order whose
  files still exist, which is the one action that would save a support message.
  It is an action, not a view, so decide it deliberately rather than adding it
  quietly.
