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
# WHY MULTI-STAGE (Phase 9 B4)
#   This image used to be `FROM pgkb/pharmcat:3.4.0`: 5.96 GB of base for a
#   ~45 MB application, because that image carries a full JDK, PharmCAT's VCF
#   preprocessor, bcftools, its own Python stack and data the served path never
#   touches. `/analyze` runs `java -jar pharmcat.jar` and nothing else
#   (app/pharmcat_runner.py, PHARMCAT_JAR below). So the final stage now holds
#   only that: a JRE, the jar, Python with backend/requirements.txt, the app,
#   the mechanism corpus and tini. Every free-tier cold start pulls the image,
#   which is what the size costs.
#
#   The runtimes are deliberately the SAME versions the old base shipped —
#   Temurin 25.0.3+9 and Python 3.14.6 on Debian 13 (trixie) — so the change is
#   the packaging, not the software. Measured in audit/phase9/B4.log.
#   Re-measure with:  docker images pharmaguard-api

# Pinned by tag AND digest, never :latest — a floating tag would silently
# change allele definitions and therefore clinical output between deploys.
#
# Stage 1: the jar, from the same image and bytes as before.
FROM pgkb/pharmcat:3.4.0@sha256:bc498d55c33094002bd7e14221a6b3fcd7243a587675369bc1a5ecf6ac0e5319 AS pharmcat

# Stage 2: a JRE of the Java release PharmCAT 3.4.0's own image runs.
FROM eclipse-temurin:25.0.3_9-jre@sha256:7c1c6297dc3a3ff947922f3ab14ecd326e29083b9edaa8dbff3b94fef1688311 AS jre

# Final stage: what is served.
FROM python:3.14.6-slim-trixie@sha256:7bec7ddcddeff7975d6ba9b4be7dd6f6b2f55e7491539145e2978f7f97ce9144

ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=$JAVA_HOME/bin:$PATH
COPY --from=jre /opt/java/openjdk /opt/java/openjdk
COPY --from=pharmcat /pharmcat/pharmcat.jar /pharmcat/pharmcat.jar

# Consumed by app/pharmcat_runner.py.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PHARMCAT_TIMEOUT_SECONDS=120

# POINT AT THE JAR EXPLICITLY. `find_jar()` globs `pharmcat-*-all.jar`, which
# `/pharmcat/pharmcat.jar` does not match, and when the old base image was in
# use resolution fell through to its `pharmcat_pipeline` wrapper — a code path
# (the VCF preprocessor) the test suite never covers. Found by Phase 8 §2. This
# image no longer contains the wrapper at all, so the jar is the only path.
ENV PHARMCAT_JAR=/pharmcat/pharmcat.jar

# Fail the BUILD if that jar is ever not the one we validated, or if the JRE
# cannot run it.
#
# The digest is byte-identical to `test-data/reference/tools/pharmcat-3.4.0-all.jar`,
# the jar every validation number in this repository was produced with.
# If this step fails, do not "fix" it by updating the hash. Find out what
# changed, re-run the validation, and update the numbers with it.
RUN echo "9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741  /pharmcat/pharmcat.jar" \
      | sha256sum -c - \
 && java -jar /pharmcat/pharmcat.jar -version | grep -q "PharmCAT 3.4.0"

# Public/default mode. `static` serves only approved compatible prose or the
# deterministic template: no API call and no key. Runtime clinical generation
# remains disabled even if the legacy `live` value is selected. Do not change
# this release default without a separate owner-approved privacy review.
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
# Created by NUMBER rather than trusting a name.
# Verified against https://huggingface.co/docs/hub/spaces-sdks-docker (2026-07-23).
# --------------------------------------------------------------------------- #
# The app launches PharmCAT as a child process. PID 1 must reap orphaned
# descendants after cancellation/timeout; uvicorn itself does not act as init.
RUN apt-get update \
 && apt-get install -y --no-install-recommends tini \
 && rm -rf /var/lib/apt/lists/*
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

# User site-packages, as before. requirements-dev.txt and requirements-llm.txt
# are deliberately NOT installed — no pytest, no google-genai. The deployed path
# calls no LLM, so shipping its SDK would be dead weight and a needless
# supply-chain surface.
RUN pip install --no-cache-dir --user -r requirements.txt

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
ENTRYPOINT ["tini", "--"]
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1"]
