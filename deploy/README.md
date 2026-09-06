# Deploying

One small VPS, ONNX-only, warmed at boot. Everything here is engine-lane
infrastructure; nothing in it changes what the product renders.

## Size the box first

These are measured on this codebase, not estimated:

| Fact | Figure |
|---|---|
| Warm resident memory, one worker | **~2.4 GB**, peaking near **2.9 GB** during inference |
| First inference in a process | **48.8 s** cold page cache, ~16 s warm |
| Second and subsequent inferences | **~7.7 s** |
| Per photograph, end to end, warm | **~10 s** |

**Workers are processes and each holds its own BiRefNet session, so memory is
per worker and not shared.**

| Workers | Engine alone | **Whole stack** | Notes |
|---:|---|---|---|
| 1 | 4 GB | **6 GB** | Below this it is killed mid-inference, not slowed |
| 2 | 7 GB | 10 GB | Roughly doubles throughput on a deadline-day spike |
| 4 | 12 GB | 16 GB | Past here, a GPU box is the better question |

**These were corrected by a real OOM, not estimated.** Running the stack in a
3.6 GB Docker VM killed uvicorn mid-inference at **3.1 GB resident**:

```
Out of memory: Killed process (uvicorn) anon-rss:3115756kB
```

So 4 GB is the floor for the **engine container alone**. The web app and the
proxy add a few hundred MB, and the host OS wants its own, which is why the
whole-stack column is what you should actually size against. A 4 GB VPS
running all three will be killed under load.

Disk: ~2.5 GB for the model volume, ~3 GB for images, plus artifacts (each job
is an upload, an output and a preview, deleted on the TTL).

## First run

From the **repository root**, not from `deploy/`:

```bash
cp deploy/.env.example deploy/.env
# edit deploy/.env -- at minimum set EXAM_PHOTO_OPERATOR_TOKEN and SITE_ADDRESS
```

Fill the model volume. This is a one-off: it downloads ~1.4 GB of weights and
exports the ~940 MB ONNX graph. It takes a while and it is the only step that
needs torch.

```bash
docker compose -f deploy/docker-compose.yml --profile setup run --rm model-fetch
```

Then bring it up:

```bash
docker compose -f deploy/docker-compose.yml up -d --build
```

The engine will report unhealthy for the first minute or two. **That is
correct** — it is warming, and the proxy deliberately waits for
`service_healthy` before sending it anything. Watch it:

```bash
docker compose -f deploy/docker-compose.yml logs -f engine
curl -s localhost/ready | python -m json.tool     # from the host, not the internet
```

### If you already have the weights locally

This machine already has a populated `model-assets/`. Copying it into the
volume is far faster than re-downloading, and skips building the 2 GB torch
image entirely:

```bash
docker run --rm -v exam-upload_models:/dst -v "$PWD/model-assets:/src:ro" \
  alpine sh -c "cp -r /src/. /dst/"
```

## The shape, and why

**One origin.** Caddy serves the app at `/` and routes `/v1/*` to the engine,
so the browser never makes a cross-origin request and there is no CORS to
configure. Leave `EXAM_PHOTO_ALLOWED_ORIGINS` unset. Splitting them onto
separate hostnames works too, but then you are maintaining an origin list for
no benefit.

**Readiness, not liveness.** The proxy waits on the engine's healthcheck and
that healthcheck calls `/ready`, never `/health`. `/health` answers 200 the
moment the process binds, while the model may still be 50 s away; pointing an
orchestrator at it is what sends the first candidate of every deploy into a
gateway timeout (DEC-064).

**The probes are private.** `/ready` reports the matting backend, the
purchase-gate state and whether the operator surface is authenticated — useful
to you, useful to an attacker. Caddy answers 404 for both probe paths from
public addresses and proxies them from private ranges.

**Models are a volume, not an image layer.** They are ~2.5 GB that never
change between deploys. Baking them in makes every deploy a multi-gigabyte
pull for identical bytes.

**Read-only weights.** Nothing at runtime should write to them, and a corrupt
model fails its sha256 check rather than degrading quietly.

**Two targets, one Dockerfile.** `runtime` installs the `matting-onnx` extra;
`modelfetch` installs `matting` as well because the export needs the PyTorch
checkpoint. That split is the entire point of the ONNX export (DEC-054) — a
serving container has no use for torch.

## Before you point a domain at it

- [ ] `EXAM_PHOTO_OPERATOR_TOKEN` set to something from `openssl rand -hex 32`.
      Confirm with `curl -s localhost/ready | grep operator_surface` — it must
      say `authenticated`.
- [ ] `SITE_ADDRESS` set to the real hostname, so Caddy gets a certificate.
- [ ] **`EXAM_PHOTO_JOB_TTL_SECONDS` settled.** It is 3600 and
      `docs/UI_ENGINE_HANDOFF.md` contemplates a 30-minute deletion guarantee,
      which is half that. The sweeper makes either real; the published claim
      and this number must match. DEC-058 records that this is a privacy
      decision taken on its own evidence.
- [ ] `EXAM_PHOTO_PURCHASE_GATE_ENABLED` **not** set to false. False serves
      clean files to anyone holding a job id.
- [ ] Backups, if artifacts matter to you. They are meant to expire, so
      probably not — but decide it rather than discover it.

## What this does not do

- **No payment.** `release_job` is the seam and nothing calls it, so the
  candidate path prepares and previews files and cannot deliver one
  (DEC-063). Deploying before Razorpay serves previews and takes no money.
- **No edge abuse filtering.** The engine caps concurrency and upload size,
  and Caddy caps body size. Anything beyond that — bot filtering, per-network
  rate limiting — belongs at Cloudflare in front of this. There is
  deliberately no per-IP limit in the application: carrier-grade NAT puts
  thousands of Indian mobile candidates behind one address (DEC-064).
- **No log shipping, metrics or alerting.** `docker compose logs` is the whole
  observability story today.
- **No zero-downtime deploy.** `up -d --build` restarts the engine, and the
  next request waits for warmup. With two workers and a real orchestrator the
  readiness endpoint makes a rolling restart possible; compose alone does not.
