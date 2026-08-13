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
# SIZE — MEASURED 2026-08-13, linux/arm64
#   Built image  6.01 GB
#   Base alone   5.96 GB   (pgkb/pharmcat:3.4.0)
#   Our layers   ~45 MB    (43 MB of it pip; the rest is app code and corpus)
#
#   The "~1.97 GB" this comment used to quote is Docker Hub's COMPRESSED figure.
#   On disk it is three times that, which is the number that matters to a host
#   with a build-disk or pull-time limit. The base image is essentially the
#   whole cost, and it is the cost of having PharmCAT at all.
#   Re-measure with:  docker images pharmaguard-api

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

# POINT AT THE JAR EXPLICITLY. Without this the container silently ran a
# DIFFERENT code path from every test.
#
# `find_jar()` searches for `pharmcat-*-all.jar` under a fixed list of
# directories. The base image installs `/pharmcat/pharmcat.jar` — a name the
# glob does not match, in a directory that is not on the list — so resolution
# fell through to the `pharmcat_pipeline` wrapper. Both "work", which is why
# nothing caught it: `/ready` was green and analyses returned results. But the
# wrapper runs PharmCAT's VCF preprocessor first, and the suite validates
# `java -jar` with no preprocessing. The deployed image was exercising an
# invocation the test suite has never covered.
#
# Found by Phase 8 §2, which exists to ask exactly this question.
ENV PHARMCAT_JAR=/pharmcat/pharmcat.jar

# Fail the BUILD if that jar is ever not the one we validated.
#
# The version is already pinned by the base image tag, but a tag is a promise
# about a name, not about bytes — and this jar decides clinical output. The
# digest below was taken from `pgkb/pharmcat:3.4.0` on 2026-08-13 and is
# byte-identical to `test-data/reference/tools/pharmcat-3.4.0-all.jar`, the jar
# every validation number in this repository was produced with.
#
# If this step fails, do not "fix" it by updating the hash. Find out what
# changed, re-run the validation, and update the numbers with it.
RUN echo "9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741  /pharmcat/pharmcat.jar" \
      | sha256sum -c - \
 && java -jar /pharmcat/pharmcat.jar -version | grep -q "PharmCAT 3.4.0"

# Phase 3/4 defaults. `static` serves pre-generated, guard-checked explanations:
# no API call, no key, nothing to leak. Set EXPLANATION_MODE=live only for a
# demo, and only with GEMINI_API_KEY supplied as a platform secret at RUNTIME —
# never as a build arg, which would bake it into an image layer.
# Kept as its own ENV: a comment inside a line continuation is a parser trap.
ENV EXPLANATION_MODE=static \
    PHARMAGUARD_CORPUS_DIR=/home/user/app/rag-corpus/mechanisms

# CORS. Deliberately left EMPTY here rather than given a placeholder default:
# a baked-in wrong origin would be silently useless, whereas an empty value now
# makes the app REFUSE TO START on a hosted platform (see
# app/security.py::assert_cors_configured). Set it per-deployment:
#
#   Hugging Face Spaces : Settings -> Variables and secrets
#   Cloud Run           : --set-env-vars CORS_ALLOWED_ORIGINS=https://<you>.pages.dev
#   Render              : Environment -> Add Environment Variable
#
# Local containers should set PHARMAGUARD_ENV=development instead (compose does).
ENV CORS_ALLOWED_ORIGINS=""

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
