# B4 — Slim backend image: plan and pre-committed criteria

Written 2026-11-04 before any B4 change or image build.

## Facts that shape the design (checked before writing this plan)

- Current image: `FROM pgkb/pharmcat:3.4.0` (5.96 GB base; 6.01–6.02 GB built,
  linux/arm64, per `docker image ls` today and the Dockerfile's own 2026-08-13 note).
- Inside that base: Temurin **25.0.3+9** (a full JDK), Python **3.14.6**, Debian 13
  (trixie), bcftools 1.24, `/pharmcat/pharmcat.jar` (sha256 9317ef63…, the jar every
  validation used) plus the preprocessor wrapper, positions files and data.
- The served path never runs the preprocessor (B3 AC6): only a JRE, the jar, Python
  with `backend/requirements.txt`, the app, `rag-corpus` and `tini` are needed.
- The jar is not tracked in git; today it comes from the base image.
- `infra/Dockerfile` is in the scientific core, so this item needs an evaluation
  re-bind. `scripts/compatible_bundle.py` records "the production image" from the
  FIRST `FROM`, which a multi-stage file would misreport; it must read the final stage.
- No `.dockerignore`: Render builds from a clean clone, but a local build sends the
  whole working tree (multi-GB untracked audit files).
- Baselines on Render (Part A, audit/phase9/SUMMARY.md): cold start 82.4 s (n=1,
  plus one cold request lost after > 300 s); warm /analyze p50 58.0 s (n=5); peak
  memory not measured. Production JAVA_TOOL_OPTIONS today: -Xmx208m -XX:MaxMetaspaceSize=68m.

## Design

Multi-stage `infra/Dockerfile`: the jar is copied from `pgkb/pharmcat:3.4.0` (same
bytes, same source as today) and sha-checked; the JRE is copied from the Temurin 25.0.3
JRE image; the final stage is `python:3.14.6-slim-trixie` (same Python and Debian
release as today) with `tini`, uid 1000, `/home/user/app`, the same ENV, entrypoint
and CMD. `.dockerignore` becomes an allowlist of what the image copies.

## Acceptance criteria (pre-committed)

Local, linux/arm64, colima (4 CPU, 8 GB); both images built from the same commit via
`git archive` (tracked files only, as Render builds):

| id | criterion |
|---|---|
| AC1 | Slim image size < 700 MB (`docker image ls`) |
| AC2 | Identical outputs: the 74 PharmCAT test VCFs run with the jar inside each container give identical report.json `genes` sections (74/74); S1–S6 through each container's /analyze give identical JSON apart from `timestamp` and `processing_time_ms` (6/6) |
| AC3 | Peak container memory (cgroup v2 `memory.peak`) over the S1–S6 run, JAVA_TOOL_OPTIONS as production: slim ≤ old × 1.05 and < 512 MiB |
| AC4 | Served path in the slim image: no `pharmcat_pipeline`, jar sha 9317ef63…, PID 1 is tini, runs as uid 1000, /health reports PharmCAT available |
| AC5 | Build hygiene: the build fails if the jar digest differs; `.dockerignore` admits every COPY source and nothing else (static test) |

Production — only after the owner authorises pushing and deploying the Part B commits:

| id | criterion |
|---|---|
| AC6 | Render cold start after verified eviction (≥ 20 min idle, shutdown seen in Render's log), n=2: each < 82.4 s |
| AC7 | Warm /analyze p50 (n=5, demo_confident.vcf, clopidogrel), measured on the current deploy and then on the slim deploy in the same session: slim ≤ current × 1.10 |
| AC8 | Render memory metric over the measurement window < 512 MiB; no OOM events |

Zero-regression: B3 harness unchanged (no application code changes) and AC2.

Sabotage: (a) a wrong jar digest makes the slim build fail; (b) without the JRE the
build-time `java -jar … -version` check fails the build; (c) dropping `rag-corpus/`
from `.dockerignore` makes the static test red.

If a criterion fails, stop and report rather than adjust it.
