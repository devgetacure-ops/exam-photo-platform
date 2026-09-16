# Prompt for the next session: security hardening

Paste everything below the line as the first message of a fresh session, from
`C:\Projects\exam-photo-platform` so `CLAUDE.md` and `AGENTS.md` load.

---

You own this repository and the production server. **The site is live and
taking real payments** at `https://examuploadkit.com`. Local branch
`feat/upload-kit-ui` and `main` are the same commit, and both are pushed.

Read `HANDOFF.md` first: *Live Operations* at the top is the current state of
the server, what runs where, where the secrets live, and how to reach it. Then
`deploy/README.md`, `deploy/docker-compose.yml`, `deploy/Caddyfile`, and DEC-063,
DEC-064, DEC-066, DEC-069 to DEC-073, DEC-097 and DEC-102 in
`docs/08_DECISION_LOG.md`. Check `git status` before anything else.

## What this session is for

**A deep security hardening of the whole live system**: the server, the edge,
the application, the secrets, the data and the repository. Nothing new gets
built until this is done.

## How we will work, which matters more than anything else here

1. **Audit first, read-only.** Read code and configuration; on the server, run
   only commands that change nothing (`ss`, `ls -l`, `sshd -T`, `docker inspect`,
   `curl` against the public site, and so on). No edits, no restarts, no key
   changes, no commits.
2. **Report one list**, ranked by severity: each finding with its evidence (a
   command's output or `file:line`), what an attacker could do with it, the fix,
   what the fix could break on a live site, and whether it needs me: a click in
   the Cloudflare, Razorpay, Resend, Vultr or GitHub dashboard, or a secret only
   I can issue.
3. **Wait for my word.** Then fix everything in one pass, verify each fix
   against the live site, and redeploy once. Tell me before anything that
   restarts the engine or the proxy, because a payment could be in flight.
4. Keep `docs/08_DECISION_LOG.md`, `docs/07_REQUIREMENTS_TRACEABILITY.md` and
   *Live Operations* in `HANDOFF.md` true as you go.

## A starting list, not a limit: find what it misses

**Secrets.** Several credentials went through a chat session on launch day: the
Resend API key, the Razorpay test key secret, the Razorpay live key id and
secret (read from a downloaded CSV, since deleted), the Turnstile secret, and
the Razorpay webhook secret (generated in the session). Plan to rotate each one,
and the operator token, in an order that never breaks payments or email. Remove
`/root/env.before-live.bak` and `/root/env.before-dec102.bak`, which hold
secrets. Decide how `deploy/.env` is backed up, if at all.

**The server.** SSH is key-only, but root logs in. Consider a non-root deploy
user, rate-limiting or `fail2ban`, and whether port 22 should be open to the
world or reached another way (my home IP changes). Check unattended security
upgrades, Docker's log rotation (container logs are unbounded by default), disk
headroom, and anything listening that should not be.

**The edge.** Cloudflare proxies the site, but the origin still accepts 80 and
443 from anyone, so the proxy can be bypassed by IP: consider allowing only
Cloudflare's ranges, or Authenticated Origin Pulls. Caddy sees Cloudflare's
addresses rather than the candidate's (`trusted_proxies`), which matters for
logs and for Turnstile. Check SSL/TLS **Full (strict)**, minimum TLS, HSTS, and
that nothing under `/v1/` is cached. **Make sure no bot or WAF setting can
challenge Razorpay's webhook POSTs**: a payment that never releases would look
exactly like that. Consider rate limits for order creation, preparation and
email.

**The application.** Security headers beyond the three Caddy sets now (a
Content-Security-Policy that still allows Razorpay Checkout, Turnstile and the
Cloudflare beacon; `Strict-Transport-Security`; `Permissions-Policy`). What a
stranger can do knowing only a `kit_id` or `job_id` (the browser mints kit ids),
including quotes, email sends to any address, previews and extensions. Webhook
replay. The operator surface. Upload handling and size limits at each layer.
Containers running as root, writable root filesystems, and memory limits on web
and proxy. `pip-audit` and `npm audit`, and CI's unpinned dependencies (DEC-100).

**Data and privacy.** That the 30-minute deletion (DEC-066) actually holds on
the server; that `_orders/` has no retention rule yet (DEC-071); what the logs
keep and for how long (IP addresses, kit ids); the `requests` volume's 30-day
promise; and whether Vultr automatic backups are on, since a backup would
capture candidates' files inside their window.

**The repository.** It is public so the server could clone it. Consider making
it private with a read-only deploy key on the server, GitHub secret scanning,
and branch protection on `main`.

**Monitoring.** Nothing tells me the site is down, the engine is unhealthy, the
disk is full, or payments have stopped releasing. Propose the smallest thing
that would.
