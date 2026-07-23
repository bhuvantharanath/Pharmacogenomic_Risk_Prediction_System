# PharmaGuard backend — deployment image.
#
# Build context is the REPO ROOT, not this directory:
#     docker build -f infra/Dockerfile -t pharmaguard-api .
#     docker run --rm -p 8000:7860 pharmaguard-api
# or:  docker compose -f infra/docker-compose.yml up
#
# ONE IMAGE, THREE HOSTS
#   HF Spaces expects the app on 7860. Cloud Run and Render inject $PORT
#   (usually 8080) and expect the app to honour it. The CMD below reads
#   ${PORT:-7860}, so the same image runs on all three with no rebuild.
#
# SIZE
#   The pgkb/pharmcat base is ~1.97 GB on Docker Hub; our layers add roughly
#   60-80 MB (FastAPI, Pydantic, uvicorn, PyYAML, plus ~300 KB of app code and
#   corpus). Nothing here meaningfully moves that number — the base image is the
#   cost, and it is the cost of having PharmCAT at all.
#   Measure after building with:  docker images pharmaguard-api

# Pinned, never :latest — a floating tag would silently change allele
# definitions and therefore change clinical output between deploys.
# Verified on Docker Hub 2026-07-22 (3.4.0, published 2026-07-14).
FROM pgkb/pharmcat:3.4.0

# The base image already provides:
#   /pharmcat/pharmcat.jar             the PharmCAT JAR
#   /pharmcat/pharmcat_pipeline        preprocessor + pipeline wrapper (on PATH)
#   /pharmcat/pharmcat_positions.vcf*  allele-definition positions
#   a JRE, python3, bcftools and bgzip
# Confirm with:  docker run --rm pgkb/pharmcat:3.4.0 pharmcat_pipeline --help

# Consumed by app/pharmcat_runner.py.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PHARMCAT_PIPELINE=pharmcat_pipeline \
    PHARMCAT_TIMEOUT_SECONDS=120

# Phase 3/4 defaults. `static` serves pre-generated, guard-checked explanations:
# no API call, no key, nothing to leak. Set EXPLANATION_MODE=live only for a
# demo, and only with GEMINI_API_KEY supplied as a platform secret at RUNTIME —
# never as a build arg, which would bake it into an image layer.
# Kept as its own ENV: a comment inside a line continuation is a parser trap.
ENV EXPLANATION_MODE=static \
    PHARMAGUARD_CORPUS_DIR=/home/user/app/rag-corpus/mechanisms

# --------------------------------------------------------------------------- #
# Non-root user.
#
# Hugging Face Spaces runs the container as UID 1000, and their Docker guide is
# explicit that you should create that user and set WORKDIR before any COPY.
# The pgkb base ships its own `pharmcat` user which may or may not be uid 1000,
# so we create/reuse uid 1000 by NUMBER rather than trusting a name.
# Verified against https://huggingface.co/docs/hub/spaces-sdks-docker (2026-07-23).
# --------------------------------------------------------------------------- #
USER root
RUN if ! id -u 1000 >/dev/null 2>&1; then \
        useradd -m -u 1000 user; \
    fi && \
    mkdir -p /home/user/app && \
    chown -R 1000:1000 /home/user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

USER 1000
WORKDIR /home/user/app

# Requirements first so the (slow) pip layer caches across application edits.
# --chown on COPY rather than a later chown: a recursive chown duplicates every
# affected file into a new layer, which HF's Docker docs call out explicitly.
COPY --chown=1000:1000 backend/requirements.txt ./requirements.txt

# --break-system-packages: the base image's python is a distro python marked
# externally managed (PEP 668). This is a single-purpose container, so
# installing into the user site-packages is fine and avoids a second venv layer.
# NOTE: requirements-dev.txt and requirements-llm.txt are deliberately NOT
# installed — no pytest, no google-genai. The deployed path calls no LLM, so
# shipping its SDK would be dead weight and a needless supply-chain surface.
RUN pip3 install --no-cache-dir --break-system-packages --user -r requirements.txt

COPY --chown=1000:1000 backend/app ./app
# The mechanism corpus is read at request time by app/retrieval.py. Without it
# every explanation silently loses its mechanism section, so it must be in the
# image — PHARMAGUARD_CORPUS_DIR above points here.
COPY --chown=1000:1000 rag-corpus ./rag-corpus

# PharmCAT writes working files per request. TMPDIR must be somewhere uid 1000
# can write. /tmp usually is, but being explicit means a platform that mounts
# /tmp read-only fails visibly at startup rather than at first analysis.
ENV TMPDIR=/home/user/app/tmp
RUN mkdir -p "$TMPDIR"

# HF Spaces convention. Cloud Run and Render ignore EXPOSE and use $PORT.
EXPOSE 7860

# Single worker: PharmCAT spawns a JVM per request and is the memory
# bottleneck, so concurrency is better limited here than discovered under load.
# `sh -c` so ${PORT:-7860} expands at runtime, not at build time.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1"]
