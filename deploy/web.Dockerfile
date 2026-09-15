# The candidate-facing Next.js app.
#
# Kept here rather than in `apps/web/` because that tree belongs to the UI
# lane; this is deployment machinery and changes nothing the app renders.
#
# Build context is the repository root:
#   docker build -f deploy/web.Dockerfile -t exam-web .

FROM node:22-slim AS build

# The repository layout is reproduced rather than flattened, because
# `catalogue.server.ts` resolves the catalogue as
# `process.cwd()/../../examples/rules`. Flattening the app to `/app` would make
# that path escape the filesystem and every exam page would vanish from the
# build with no error worth the name.
WORKDIR /repo/apps/web

COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

COPY apps/web ./

# Values Next.js reads while it builds (DEC-097). NEXT_PUBLIC_* are written
# into the pages themselves, and the seller details and verification tags are
# read by pages rendered once, at build. Compose passes them from deploy/.env;
# changing one means rebuilding (`up -d --build`). Leaving them out was the
# reason the business details and the captcha never reached a deployed site.
ARG NEXT_PUBLIC_SITE_URL=
ARG NEXT_PUBLIC_TURNSTILE_SITE_KEY=
ARG NEXT_PUBLIC_CF_BEACON_TOKEN=
ARG GOOGLE_SITE_VERIFICATION=
ARG BING_SITE_VERIFICATION=
ARG EUK_BUSINESS_PHONE=
ARG EUK_BUSINESS_HOURS=
ARG EUK_BUSINESS_PUBLIC_ADDRESS=
ENV NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL \
    NEXT_PUBLIC_TURNSTILE_SITE_KEY=$NEXT_PUBLIC_TURNSTILE_SITE_KEY \
    NEXT_PUBLIC_CF_BEACON_TOKEN=$NEXT_PUBLIC_CF_BEACON_TOKEN \
    GOOGLE_SITE_VERIFICATION=$GOOGLE_SITE_VERIFICATION \
    BING_SITE_VERIFICATION=$BING_SITE_VERIFICATION \
    EUK_BUSINESS_PHONE=$EUK_BUSINESS_PHONE \
    EUK_BUSINESS_HOURS=$EUK_BUSINESS_HOURS \
    EUK_BUSINESS_PUBLIC_ADDRESS=$EUK_BUSINESS_PUBLIC_ADDRESS

# **The catalogue is read at build time, not over the API** (WEB-003). All 39
# exam pages are statically generated from `examples/rules/` on disk, because a
# page whose content arrives by client-side fetch is an empty document to a
# crawler, and SEO is the primary acquisition channel. So the rules must be
# present *before* `next build`, and re-running the encoder needs a rebuild to
# show up.
COPY examples/rules /repo/examples/rules

RUN npm run build

# Fail loudly rather than shipping a site with no examinations in it: a
# catalogue that failed to resolve produces a successful build and an empty
# product, which is the kind of defect that reaches production.
RUN test -d .next/server/app/exam || (echo "No exam pages were generated -- the catalogue did not resolve." && exit 1)

FROM node:22-slim AS runtime

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

WORKDIR /repo/apps/web

# `next start` rather than `output: "standalone"`. Standalone produces a much
# smaller image but requires a line in `apps/web/next.config.ts`, which is the
# UI lane's file. Worth asking them for; not worth taking unilaterally.
COPY --from=build /repo/apps/web/package.json /repo/apps/web/package-lock.json ./
RUN npm ci --omit=dev

COPY --from=build /repo/apps/web/.next ./.next
COPY --from=build /repo/apps/web/public ./public
COPY --from=build /repo/apps/web/next.config.ts ./
# Carried into the runtime stage too, so anything rendered on demand rather
# than at build time resolves the same catalogue by the same relative path.
COPY --from=build /repo/examples/rules /repo/examples/rules

RUN useradd --system --uid 10002 --create-home --home-dir /home/web web \
    # Where the exam-request form keeps what candidates send (DEC-097). A
    # named volume is mounted over it; creating it here, owned by the app's
    # user, is what lets Docker give the empty volume that ownership.
    && mkdir -p /data/requests \
    && chown web:web /data/requests
USER web

EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD node -e "require('http').get('http://127.0.0.1:3000/',r=>process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"

CMD ["npx", "next", "start", "--hostname", "0.0.0.0", "--port", "3000"]
