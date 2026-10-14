# Phase 6 resource ownership, privacy, and failure-path audit

Measured locally with harmless synthetic inputs on 2026-09-24. No public
deployment was exercised.

## Reproduction before correction

- Cancellation: cancelling `_exec_unguarded` left **2/2 owned processes alive**
  (the direct child and its descendant). The cancellation exception bypassed
  timeout-only cleanup.
- Logging: PharmCAT/logback used the backend launch directory. Three historical
  `backend/pharmcat*.log` files were found there. They were not deleted because
  they pre-date this phase and may be historical user artifacts.
- Proxy identity: with direct peer `203.0.113.10`, an untrusted
  `X-Forwarded-For: 198.51.100.77` selected `198.51.100.77` as the rate-limit
  key.
- Uploads: both upload endpoints called unbounded `UploadFile.read()` before
  applying the existing 5 MiB application cap.
- `/coverage`: it shared validation semantics but had no public workload budget
  and performed synchronous validation/parsing on the event loop.

## Corrected invariant and controls

- Every PharmCAT invocation starts in its own POSIX process group. Normal
  completion, timeout, unexpected failure, and task cancellation terminate any
  remaining descendants and reap the direct child.
- SIGTERM has a documented 2-second ceiling before SIGKILL escalation. This is
  a cleanup grace period; the existing 120-second analysis timeout is unchanged.
- The JVM semaphore is held until the child has been reaped and the owned
  VCF/report/log temporary tree has been removed.
- PharmCAT's child working directory is the owned temporary tree, confining
  logback output to the same cleanup boundary.
- A declared upload over 5 MiB is rejected before application reading. Unknown
  sizes are read in 64 KiB chunks only to the cap plus one byte. The existing
  decompressed-output ceiling remains 100 MiB (20× the input cap).
- `/coverage` and `/analyze` use the same limited reader, decompression and VCF
  validator, and the same public request budget. Validation and coverage parsing
  execute in a worker thread so they do not stall the event loop.
- Forwarded identity is ignored unless the direct peer matches an explicit
  `TRUSTED_PROXY_CIDRS` entry. Invalid trust configuration fails startup.
- Static explanation mode remains the public/default configuration and makes no
  outbound explanation call. Runtime clinical prose remains disabled in live
  compatibility mode.

## E8-equivalent observations

| Path | Result |
| --- | --- |
| normal child completion | direct child reaped; daemonized descendant removed |
| rejection | bounded 4xx/413; upload closed; no owned temp residue |
| timeout | process group terminated/reaped; existing timeout message preserved |
| cancellation | process group terminated/reaped before slot release |
| gzip/malformed input | corrupt/truncated input rejected; 100 MiB expansion cap enforced |
| bounded concurrency | peak overlapping fake JVM invocations never exceeded configured limit |
| `/coverage` | same upload/decompression budget, shared request budget, event loop remained responsive |
| `/analyze` | shared gate plus one-JVM semaphore; existing scientific behavior preserved |
| synthetic temp residue | **0** `pharmaguard_pharmcat_*` directories after tests |
| newly created backend-root PharmCAT logs | **0**; the three historical files remained byte-identical |

The focused failure-path suite completed in 4.8 seconds. The containing pytest
process reached approximately 626 MiB peak RSS on macOS while deliberately
constructing/decompressing hostile inputs, including the existing 200 MiB gzip
bomb fixture. This is a test-process bound, not a production request estimate.
The production JVM concurrency basis remains the measured 322 MiB for one
analysis versus 594 MiB for two on a 512 MiB deployment target.

## Privacy boundary and limitations

The application does not persist uploaded VCFs or results and does not place raw
VCF content, sample identifiers, diplotypes, or detected variants in its guard
log. The guard log may contain drug, gene, phenotype, result label, and rejected
explanation prose. Reverse-proxy access logs, host crash dumps, backups, and
platform retention are outside the application cleanup guarantee and must be
configured by the operator.

Multipart parsing occurs in the ASGI framework before the endpoint receives its
`UploadFile`. The application now rejects from the framework-provided declared
size before reading and never allocates more than the cap plus one byte itself,
but this is not a universal transport-layer body-size firewall. Hosts should
also enforce request-body limits at the trusted proxy when available.

The in-memory request budget is abuse dampening, not authentication or a
distributed security boundary. It resets on restart and is per process. The
single-worker assertion remains required; multi-instance/shared-store security
architecture is outside this phase.
