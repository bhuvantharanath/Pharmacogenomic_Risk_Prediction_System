---
title: PharmaGuard API
emoji: 🧬
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Pharmacogenomic risk prediction API — PharmCAT + CPIC. Not for clinical use.
tags:
  - pharmacogenomics
  - bioinformatics
  - fastapi
  - pharmcat
# The PharmCAT base image is ~2 GB, so a cold build can exceed the 30-minute
# default before the health check gives up. Field verified against
# https://huggingface.co/docs/hub/spaces-config-reference (2026-07-23).
startup_duration_timeout: 1h
---

# PharmaGuard API

> **Research/educational decision support only. Not a medical device. Not for
> clinical use.**

Backend for [PharmaGuard](https://github.com/bhuvantharanath/pharmaguard) — a
final-year academic project that predicts pharmacogenomic risk from a VCF.

Genotypes are called by **PharmCAT 3.4.0**; all clinical text comes from **CPIC**
and is passed through verbatim. Narrative explanations are pre-generated,
checked by a deterministic faithfulness guard, and served from a static file —
**this API needs no API key and makes no outbound calls.**

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness. Cheap, dependency-free — use this to wake the Space |
| `GET` | `/ready` | Readiness. Verifies PharmCAT, corpus, explanations, mapping |
| `GET` | `/` | Service metadata, CORS policy, rate limit, retention policy |
| `GET` | `/docs` | Interactive OpenAPI docs |
| `POST` | `/analyze` | Analyse a VCF against a drug list |

```bash
curl -F "file=@sample.vcf" \
     -F "drugs=clopidogrel,fluorouracil,codeine" \
     https://YOUR-SPACE.hf.space/analyze
```

## Cold starts

Free Spaces sleep when idle. The first request after a nap pays the full
container start — **up to about a minute**. `/health` is deliberately trivial so
it can absorb that cost as a wake-up ping; the web client fires it on load and
shows an honest "waking up" state rather than a bare spinner.

## Data privacy

**No genomic data is retained.** An uploaded VCF is held in memory and written
to a per-request temporary directory that is deleted in a `finally` block before
the response is returned. Nothing is logged, persisted, or sent anywhere else.
Spaces have an ephemeral filesystem in any case, but the deletion is explicit
and [asserted by a test](https://github.com/bhuvantharanath/pharmaguard/blob/main/backend/tests/test_deployment.py).

## Configuration

All optional. The defaults need no secrets.

| Variable | Default | Purpose |
| --- | --- | --- |
| `EXPLANATION_MODE` | `static` | `static` \| `live` \| `template` |
| `CORS_ALLOWED_ORIGINS` | *(localhost only)* | Comma-separated exact origins |
| `CORS_ALLOW_PAGES_PREVIEWS` | — | Cloudflare Pages project name for preview subdomains |
| `RATE_LIMIT_REQUESTS` | `10` | Analyses per window per client |
| `RATE_LIMIT_WINDOW_SECONDS` | `300` | Rate-limit window |

Set these under **Settings → Variables**. If you ever switch to
`EXPLANATION_MODE=live`, put `GEMINI_API_KEY` in **Settings → Secrets**, never
in a variable and never in the repo — the app refuses to start if it finds a
`.env` file inside the image.

## Limitations

- **CYP2D6 is never called.** Its star alleles depend on copy-number variation a
  VCF cannot express, so codeine returns `Unknown` with an explicit warning
  rather than a fabricated result.
- **GRCh38 only.** GRCh37/hg19 uploads are rejected with a clear message;
  liftover is out of scope.
- **5 MB upload limit.** Subset a whole-genome VCF to the PGx regions first.
