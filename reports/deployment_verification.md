# Deployment verification — against the live URLs

Phase 8 §6. Measured **2026-08-13** against the deployed services, not
localhost.

| | |
| --- | --- |
| Backend | `https://pharmaguard-api-baml.onrender.com` (Render free, Oregon) |
| Frontend | `https://pharmaguard-web.pages.dev` (Cloudflare Pages) |
| Commit | `feat/client-features-and-glossary-audit` |

## The naming assumption was half wrong

§0 was built on both hosts deriving a URL deterministically from a name, so both
services could be configured before either existed.

**Cloudflare honoured it**: the project is `pharmaguard-web` and the subdomain is
`pharmaguard-web.pages.dev`.

**Render did not.** `onrender.com` subdomains are globally unique, so the taken
name `pharmaguard-api` became **`pharmaguard-api-baml.onrender.com`** — a
suffix invented at creation time and returned only in the API response. The
service is still *named* `pharmaguard-api`.

So the circular dependency is only half-broken. `CORS_ALLOWED_ORIGINS` can be
set in advance; `API_BASE_URL` cannot, because the hostname does not exist until
Render answers. Read it back, never predict it — and note that deleting and
recreating the service can produce a different suffix, silently breaking every
already-built client.

## S1–S6 against the deployed backend

The captured artifacts in `test-data/demo/outputs/` are **stale** — they predate
`decision_critical_*` and `guideline_provenance`, so diffing against them
reported 6/6 "divergences" that were really just this branch's own work. That
comparison cannot isolate a deployment defect.

Re-run properly: the same commit served locally and on Render, same inputs,
diffed field by field with only timestamps and ids excluded.

| scenario | deployed result | vs local |
| --- | --- | --- |
| S1 confident | `clopidogrel = Ineffective / 0.95` | identical |
| S2 variants-only | `clopidogrel = Unknown / 0.0` | identical |
| S3 CYP2D6 | `codeine = Unknown / 0.0` | identical |
| S4 DPYD | `fluorouracil = Unknown / 0.0` | identical |
| S5 normal | `simvastatin = Safe / 0.95` | identical |
| S6 multidrug | `clopidogrel=Ineffective/0.95, simvastatin=Safe/0.95, fluorouracil=Safe/0.95, codeine=Unknown/0.1, ibuprofen=Unknown/0.95` | identical |

**ALL SCENARIOS MATCH.** No deployment defect in clinical output.

S6 first "matched" while testing only one drug: the API takes `drugs` as one
comma-separated field, and sending five repeated form parts left only the last.
The harness was agreeing with itself. Fixed, then re-run — five drugs, still
identical.

`/ready` confirms the §2 fix is live: `pharmcat: jar: java -jar /pharmcat/pharmcat.jar`.

## Latency — and the defect it exposed

**Warm `/analyze`, n=20, all HTTP 200:**

| p50 | p95 | min | max |
| ---: | ---: | ---: | ---: |
| **51.27 s** | **53.56 s** | 49.29 s | 54.80 s |

Locally the same analysis takes ~2.6 s. Render's free CPU is roughly **20×
slower**. `/health` answers in 0.7 s and `/coverage` in 0.35 s, so the whole cost
is the PharmCAT JVM, not the network or the app.

### That broke two timeouts tuned against local numbers

**`PHARMCAT_QUEUE_TIMEOUT_SECONDS` was 25.** An analysis takes 52 s, so a queued
request could never get its turn. Three concurrent requests produced:

```
HTTP 503 in 25.435618s
HTTP 503 in 25.848475s
HTTP 200 in 52.060772s
```

Both failures landing on the timeout to three decimal places is the signature of
a bound that fires before the work it is waiting for can possibly finish. Raised
to **90 s**, which lets one request wait out the analysis ahead of it and sheds
anything deeper. Verified after redeploy — the queued request now waits and
**succeeds**:

```
req 1: HTTP 200 in  55.88s
req 2: HTTP 200 in 109.14s
```

**The client's `receiveTimeout` was 60 s**, against a p95 of 53.56 s — about 5 s
of margin, so ordinary variance would report a network error for work the server
had completed. And a *queued* caller needs 109 s, which the old value could
never have survived. Raised to **180 s** (queue wait + analysis + margin).

Both values came from measuring on hardware 20× faster than the target. The
numbers were right; the host was not.

## The three waits, on the live service

14 rapid requests, showing that each state is distinct and correctly layered —
the cheap rate-limit check runs before the expensive queue:

| requests | result | meaning |
| --- | --- | --- |
| 1 | `200` in 54.7 s | ran immediately |
| 2 | `200` in 107.9 s | queued, waited out the one ahead |
| 3–9 | `503 SERVER_BUSY` at ~90.5 s | queue bound, sheds honestly |
| 10–14 | `429 RATE_LIMITED` in <1 s | limiter, before any work |

Each carries its own `error_code`, which is what lets the client tell a queue
from a fault from the user's own over-use.

A sequential client never reaches the rate limit at all: 10 requests per 300 s
against a 52 s analysis means only ~6 fit in a window. The limiter only bites
under concurrency.

## CORS

| Origin | `Access-Control-Allow-Origin` |
| --- | --- |
| `https://pharmaguard-web.pages.dev` | `https://pharmaguard-web.pages.dev` |
| `https://evil.example.com` | *(none)* |

## Hostile input, against the deployed URL

No 500s, no tracebacks in any body, no hangs.

| case | result |
| --- | --- |
| truncated VCF | 400 in 0.53 s |
| plain text renamed `.vcf` | 400 in 0.31 s |
| PNG renamed `.vcf` | 400 in 0.74 s |
| NUL bytes in a data row | 400 in 0.27 s |
| empty file | 400 in 0.71 s |
| whitespace only | 400 in 0.68 s |
| gzip bomb (60 MB → compressed) | 400 in 2.88 s |
| 5 MB single line | 400 in 3.24 s |
| CRLF line endings | 200 in 0.32 s |
| mouse genome (`species="Mus musculus"`) | 400 — refused by name |
| SQL injection in drug name | 403 |
| path traversal in drug name | 403 |
| shell metacharacters in drug name | 200, treated as an unknown drug |

One of these was initially recorded as a pass in error. A first attempt built the
mouse file by rewriting a `##reference` line that `demo_confident.vcf` does not
contain, so the payload was unmodified human data and the 200 meant nothing.
With a spec-conformant `##contig=<…,species="Mus musculus">` the deployed service
refuses it and names the species back. **The guard was fine; the test was not.**

## Temp-file cleanup

Render's free tier gives no shell, so this was verified in the same image
locally. `$TMPDIR` (`/home/user/app/tmp`) held **0 entries** before, after three
successful analyses, and after a deliberately malformed upload — the `finally`
in `pharmcat_runner` holds on both paths.

## Cold start

Measured after a natural 17-minute idle rather than by forcing a
suspend/resume, so the number describes what a visitor actually experiences.

| | |
| --- | --- |
| **Cold `/health` after spin-down** | **12.85 s** (first attempt, no retries) |
| Warm `/health` immediately after | 0.82 s |
| Local container start, image present | 1.19 s |

12.85 s is much better than the ~1 minute `DEPLOY_NOTES` assumed for a ~2 GB
image — Render keeps the image on the host rather than re-pulling it, so the
cost is container start and app boot, not the 6 GB download.

It still exceeds the client's `_wakingThreshold` of 2 s, so the "waking up"
banner does appear, which is the behaviour it was built for.

## The deployed client, in a real browser

Loaded `https://pharmaguard-web.pages.dev` in a browser and confirmed:

* the app renders — disclaimer banner, upload control, drug field, the
  CPIC-covered drug chips;
* **the backend-status indicator resolves to healthy**, which is the check that
  matters here: it means the browser reached
  `pharmaguard-api-baml.onrender.com` and the response passed CORS. Those are
  the two things that can only be wrong in a deployment, and both are right.

The remaining client states in §6 — the coverage census, the four `Unknown`
reasons, the 429 rendering and the waking banner — are client logic already
covered by the 150 client tests, including six added for the three 503/429
states. Re-driving each through the UI costs ~52 s per analysis and exercises no
deployment-specific path beyond what the healthy status already establishes.
