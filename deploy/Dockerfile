# The image-engine, in two targets (DEC-065).
#
# `runtime` is what serves traffic. It installs the `matting-onnx` extra and
# **not** `matting`: running the exported ONNX graph needs onnxruntime alone,
# while producing that graph needs torch, transformers and timm -- roughly
# 2 GB of dependencies that a serving container has no use for. Splitting them
# is the whole reason the ONNX export exists (DEC-054).
#
# `modelfetch` is the heavy one, run **once** to populate the model volume. It
# carries torch because the export reads the PyTorch checkpoint.
#
# Build context is the repository root, so `examples/rules/` and
# `model-manifests/` are reachable. Build from there:
#   docker build -f deploy/Dockerfile --target runtime -t exam-engine .

# ---------------------------------------------------------------------------
# Shared base
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS base

# mediapipe needs these even headless, and the two halves fail differently.
#
# `libgl1` and `libglib2.0-0` are needed to *import* it, via opencv.
# `libgles2` and `libegl1` are needed to *run* a detector: mediapipe's tasks
# API dlopens libGLESv2.so.2 when it probes for a GPU delegate, so without
# them the package imports cleanly and then fails on the first real photograph
# with "libGLESv2.so.2: cannot open shared object file" -- a message naming
# nothing to do with faces. An import smoke test does not catch this. Only
# running an actual inference does, which is how it was found.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgles2 \
        libegl1 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ---------------------------------------------------------------------------
# Runtime: what actually serves candidates
# ---------------------------------------------------------------------------
FROM base AS runtime

# Dependency install is its own layer, keyed on the packaging files, so an
# ordinary source edit does not reinstall onnxruntime and mediapipe.
COPY services/image-engine/pyproject.toml services/image-engine/README.md ./engine/
COPY services/image-engine/src ./engine/src
RUN pip install "./engine[face,matting-onnx]"

# `find_repo_root()` walks up from the package looking for `AGENTS.md` or
# `model-manifests/`, which cannot work once the package lives in
# site-packages. `EXAM_PHOTO_REPO_ROOT` is the escape hatch the code already
# provides for exactly this, and everything resolved against it is copied here.
COPY model-manifests ./model-manifests
COPY examples/rules ./examples/rules
# The canonical JSON Schema. `rule_validation` used to find it by walking four
# directories up from `__file__`, which works in a checkout and lands in
# site-packages' grandparent in any installed copy -- so every rule failed
# validation with RULE_VALIDATION_SCHEMA_UNAVAILABLE and every job failed.
# It now honours EXAM_PHOTO_REPO_ROOT, and this is what that points at.
COPY packages/exam-rules/schema ./packages/exam-rules/schema

# The catalogue and the manifests are read-only; artifacts are not. A named
# volume is mounted over this at runtime so candidate files never live in the
# container's writable layer.
RUN mkdir -p /app/.tmp/artifacts /app/model-assets \
    && useradd --system --uid 10001 --create-home --home-dir /home/engine engine \
    && chown -R engine:engine /app/.tmp

ENV EXAM_PHOTO_REPO_ROOT=/app \
    EXAM_PHOTO_ARTIFACT_ROOT=/app/.tmp/artifacts \
    EXAM_PHOTO_CATALOGUE_ROOT=/app/examples/rules

USER engine
EXPOSE 8000

# Readiness, not liveness (DEC-064). `/health` answers 200 while the model is
# still loading, so a healthcheck pointed at it would mark a cold worker
# healthy and send it the first candidate. `start-period` is 600 s because
# container warmup was measured at **186-316 s** on a volume-backed model
# file -- far above the 48.8 s the same inference costs natively. A 300 s
# period was tried and is marginal: one run exceeded it and only survived on
# the retries. Too short here means a crash loop, not a slow start.
HEALTHCHECK --interval=15s --timeout=10s --start-period=600s --retries=3 \
    CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=8).status == 200 else 1)"

# uvicorn directly rather than `python -m exam_photo serve-api`, because the
# CLI passes an app object and that forecloses `--workers`. Workers default to
# 1 deliberately: each holds its own warm BiRefNet session at roughly 2.4 GB
# resident, so this is the setting that decides how much RAM the box needs.
CMD ["sh", "-c", "exec uvicorn exam_photo.api.app:app --host 0.0.0.0 --port 8000 --workers ${EXAM_PHOTO_WORKERS:-1}"]

# ---------------------------------------------------------------------------
# Model fetch: run once to populate the model volume
# ---------------------------------------------------------------------------
FROM base AS modelfetch

COPY services/image-engine/pyproject.toml services/image-engine/README.md ./engine/
COPY services/image-engine/src ./engine/src
# `matting` as well as `matting-onnx`: the export reads the PyTorch checkpoint,
# and a venv missing `onnx` or `deform_conv2d_onnx_exporter` fails two
# dependencies deep with errors naming neither.
RUN pip install "./engine[face,matting,matting-onnx]"

COPY model-manifests ./model-manifests
COPY scripts ./scripts

ENV EXAM_PHOTO_REPO_ROOT=/app

# Both segmenter variants, deliberately: the golden-image regression loads
# `selfie_segmentation.tflite` while the pipeline default uses
# `selfie_multiclass_256x256.tflite`, and fetching only one fails in a way
# that reads exactly like a composition regression (DEC-062).
CMD ["sh", "-c", "set -e; \
    python scripts/download_model.py --variant short_range --yes; \
    python scripts/download_segmenter.py --variant selfie_multiclass_256x256 --yes; \
    python scripts/download_segmenter.py --variant selfie_bin_general --yes; \
    python scripts/download_face_landmarker.py --yes; \
    python scripts/download_birefnet.py --yes; \
    python scripts/export_birefnet_onnx.py; \
    echo 'Model assets ready.'"]
