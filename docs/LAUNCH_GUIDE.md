# Launching ExamUploadKit, on as little money as possible

Written 15 September 2026 for the owner (DEC-097). Prices move; each one here
says where to check it. Nothing in this guide goes live by itself: every step
that creates an account, spends money or publishes the site is yours.

> **Status, 16 September 2026: live.** Deployed on Vultr (Mumbai, 8 vCPU / 16 GB,
> on the promotional credit) with Cloudflare proxying, Turnstile, Resend and live
> Razorpay payments; the move to Hostinger KVM 4 comes before 11 October. What
> runs where, and what is still open, is in *Live Operations* at the top of
> `HANDOFF.md`. Still to do from this guide: Bing. Search Console and Web
> Analytics were finished on 24 September. The steps below are kept for the Hostinger move, with what launch
> day taught added where it applies.

## What runs where, and why not Vercel alone

The site has two halves:

| Half | What it is | What it needs |
|---|---|---|
| Web app | Next.js pages, the free tools, the checkout | Small: a few hundred MB |
| Engine | Python, the face and background models | **About 2.4 GB warm, 2.9 GB peak**, measured |

Vercel, Netlify and Cloudflare Pages host the web half well and for free, but
none of them runs a process holding 3 GB of models for ten seconds a
photograph. So the engine needs a server of its own, and once you have that
server the simplest thing is to run **both halves on it** with the
`deploy/docker-compose.yml` that is already in the repository: one machine, one
bill, one origin (so no CORS), and Caddy obtaining the HTTPS certificate on its
own.

**Size: 8 GB of memory, x86.** `deploy/README.md` shows why: a 4 GB box was
killed mid-photograph.

**Where** (check prices on the day). **Chosen on launch day**: Vultr on its
promotional credit for the first month, then Hostinger KVM 4 (India, 16 GB) for
the long run. 16 GB rather than 8 so the one-off model export has room (it ran
clean on 16 GB). The options first considered:

- **Hetzner Cloud, Singapore, CPX31 (4 vCPU, 8 GB)**: the cheapest reliable
  8 GB box near India. Hetzner raised prices several times in 2026, and its
  Singapore plans include only 0.5 TB of traffic a month. Pricing:
  <https://www.hetzner.com/cloud>.
- **DigitalOcean or AWS Lightsail in Mumbai / Bangalore**: closer to
  candidates, noticeably dearer for 8 GB.
- **Oracle Cloud Always Free (ARM)**: not now. Since June 2026 it gives 2 cores
  and 12 GB, which is enough memory, but it is ARM, and the face-detection
  library the engine uses (mediapipe 0.10.35) publishes no ARM Linux build. It
  would need an upgrade and a full re-test first, and free ARM capacity in India
  is often unavailable anyway.

## Before the first deploy

1. **Merge the work branch into `main` and push it.** Everything built since
   September is on `feat/upload-kit-ui`, unpushed. Say the word and it is done.
2. **Buy the domain.** Cloudflare Registrar sells at cost (a `.com` is about
   US$10 a year). Any registrar works; the DNS goes to Cloudflare either way.
3. **Add the domain to Cloudflare** (free plan).

## Deploying, step by step

1. Create the server: **Ubuntu 24.04** (not a newer release; everything here is
   tested on 24.04), your SSH key, and a firewall allowing only ports 22, 80
   and 443. Then turn off password login for SSH in a file under
   `/etc/ssh/sshd_config.d/` whose name sorts **before** the cloud provider's
   own (for example `01-hardening.conf`), because sshd keeps the first value it
   reads.
2. In Cloudflare DNS add two `A` records to the server's IP address, `@` and
   `www`, set to **DNS only (grey cloud)** for now, so Caddy can obtain its
   certificate directly.
3. On the server: install Docker (<https://docs.docker.com/engine/install/ubuntu/>),
   then clone the repository. It is private: create a key on the server
   (`ssh-keygen -t ed25519 -f /root/.ssh/github_deploy`), add its public half in
   GitHub → Settings → Deploy keys **without** write access, point `github.com`
   at it in `/root/.ssh/config`, and clone over SSH. Then from its root:

   ```bash
   cp deploy/.env.example deploy/.env
   ```

4. Fill `deploy/.env`. The file explains every line; the ones a launch needs:

   | Setting | Value |
   |---|---|
   | `SITE_ADDRESS` | `yourdomain.com` |
   | `WWW_ADDRESS` | `www.yourdomain.com` |
   | `CANONICAL_ORIGIN` | `https://yourdomain.com` |
   | `NEXT_PUBLIC_SITE_URL` | `https://yourdomain.com` |
   | `EXAM_PHOTO_OPERATOR_TOKEN` | the output of `openssl rand -hex 32` |
   | `EUK_BUSINESS_PHONE`, `EUK_BUSINESS_HOURS`, `EUK_BUSINESS_PUBLIC_ADDRESS` | your details; they live only in this file on the server |
   | Turnstile keys, Razorpay keys, SMTP | as below, when you have them |

5. Fill the model volume once (downloads about 1.4 GB), then start everything:

   ```bash
   docker compose -f deploy/docker-compose.yml --profile setup run --rm model-fetch
   docker compose -f deploy/docker-compose.yml up -d --build
   ```

6. The engine warms (12 seconds on the Vultr box). Then open the domain on your
   phone and prepare a file. Any `NEXT_PUBLIC_*` or business change later needs
   `up -d --build`, because those are written into the pages when they build.
7. **Once the certificate is issued, turn on Cloudflare's proxy** (orange cloud)
   for both records. **First** set Cloudflare → SSL/TLS to **Full (strict)**:
   on the default "Flexible" setting the site loops between HTTP and HTTPS.

## The free services, in the order you need them

### Cloudflare Turnstile (stops scripts, free)

Cloudflare dashboard → Turnstile → add a widget for your domain. Put the site
key in `NEXT_PUBLIC_TURNSTILE_SITE_KEY` and the secret in
`EXAM_PHOTO_TURNSTILE_SECRET`, then rebuild.

### Email with Resend (free tier), SES later

1. Sign up at <https://resend.com> and add your domain. Resend lists DNS records
   (SPF, DKIM); add them in Cloudflare and wait for Resend to show "verified".
2. Create an API key.
3. In `deploy/.env`:

   ```
   EXAM_PHOTO_SMTP_HOST=smtp.resend.com
   EXAM_PHOTO_SMTP_PORT=587
   EXAM_PHOTO_SMTP_USE_TLS=true
   EXAM_PHOTO_SMTP_USERNAME=resend
   EXAM_PHOTO_SMTP_PASSWORD=<the API key>
   EXAM_PHOTO_SMTP_FROM=files@yourdomain.com
   ```

   And how the message presents itself (DEC-102):

   ```
   EXAM_PHOTO_SMTP_FROM_NAME=ExamUploadKit
   EXAM_PHOTO_SMTP_REPLY_TO=support@yourdomain.com
   EXAM_PHOTO_SITE_URL=https://yourdomain.com
   ```

   The sending address should be a real mailbox or alias at your mail provider,
   so a candidate's reply does not bounce.

4. `docker compose -f deploy/docker-compose.yml up -d`. The email box appears on
   the site once the engine reports email configured. Moving to Amazon SES later
   changes the SMTP lines and nothing else.

### Razorpay (payments)

Razorpay reviews a live site: it wants the terms, privacy, refund and contact
pages, which exist at `/terms`, `/privacy`, `/refund-policy` and `/support`.
After approval, put the key id and secret in `deploy/.env`, create a webhook to
`https://yourdomain.com/v1/payments/razorpay/webhook` for `payment.captured` and
`order.paid`, and put its secret in `EXAM_PHOTO_RAZORPAY_WEBHOOK_SECRET`.
**The payment simulator must be off** (`EXAM_PHOTO_PAYMENT_SIMULATOR` unset) on
this server.

Learned on launch day: **Razorpay keeps a separate webhook list for Test Mode and
Live Mode.** A webhook made in Live Mode never fires for a test payment, so a
test payment takes the money and releases nothing. Test keys need a test-mode
webhook; live keys need a live-mode one. The same secret can serve both.

### Visit counts: Cloudflare Web Analytics (free, no cookies)

Cloudflare dashboard → Analytics & Logs → Web Analytics → add the site, copy
the token into `NEXT_PUBLIC_CF_BEACON_TOKEN`, rebuild. It sets no cookies and
stores nothing on the visitor's device, so no cookie banner is needed; the
privacy page gains a sentence about it automatically once the token is set.
It counts pages, referrers, countries and devices, not individual journeys.

### Google Search Console (free)

1. <https://search.google.com/search-console> → **Add property** → **Domain** →
   enter the domain. Google shows a TXT record; add it in Cloudflare DNS and
   press Verify. (If you prefer the URL-prefix property, put the tag's content
   value in `GOOGLE_SITE_VERIFICATION` and rebuild.)
2. **Sitemaps** → submit `https://yourdomain.com/sitemap.xml`. It lists the home
   page, every examination and its rules, the eight family hubs, the free tools
   and every published-size page.
3. **URL inspection** → request indexing for the home page, `/exams`,
   `/compress-image` and the hubs, so the first crawl starts there.
4. Once a week: **Pages** (what is and is not indexed, and why) and
   **Performance** (the searches people actually used). Those searches are the
   real keyword volumes the keyword map could only estimate.

### Bing Webmaster Tools (free)

<https://www.bing.com/webmasters> → sign in → **Import from Google Search
Console**. One click brings the site and its sitemap across. Bing's index also
feeds DuckDuckGo and several AI answer engines, which is why the site already
serves `/llms.txt`.

## What it costs

| Item | Cost |
|---|---|
| Domain | about US$10 a year |
| Server, 8 GB | the one real monthly cost; see Hetzner's page |
| Cloudflare DNS, Turnstile, Web Analytics | free |
| Search Console, Bing Webmaster Tools | free |
| Resend | free tier to start |
| Razorpay | a fee per payment; nothing monthly |

## Cookies

The site sets **no cookies of its own**. What it keeps in the browser (the
theme, the kit so a candidate can come back, the agreement given at upload) is
local storage, which never travels to the server. Cloudflare Web Analytics sets
none. Cloudflare's security check before a preparation and Razorpay's payment
window may set their own, to do those jobs. So there is no cookie banner, and
the privacy page says exactly this.

## Ads

Not recommended now, for four reasons:

1. **Google's ads bring cookies and tracking**, which needs a consent banner
   (Google's Consent Mode, and explicit consent under India's DPDP Act). That is
   the banner the product has so far avoided.
2. **They slow the page** on the mid-range phone over mobile data that most
   candidates use, which costs both search ranking and sales.
3. **Earnings per view from Indian traffic are low**, and there is no reliable
   figure to plan on; one kit sale at Rs 3 or Rs 5 is worth many ad views.
4. **They cost trust** beside a candidate's photograph and a payment, and a
   competitor's ad could appear on your own page.

If traffic grows large, the place to test ads is the free tool and family hub
pages only, never an examination page, the prepare flow or checkout, and only
with a consent banner in place.
