# B8 — Abuse and privacy hardening

Part B item 8 of the Phase 9 brief:

> - Per-IP rate limit and queue cap (single PharmCAT slot means one abuser =
>   outage); 429 with retry-after.
> - Guarantee VCF deletion on every path (try/finally + a test that injects a
>   failure mid-run); strip genotypes/rsIDs from logs.
> - Fix any critical/high CVEs from A9.

It addresses three findings:

- **F-04 (high, availability).** The per-client limit keys on Render's internal
  proxy hops. One client's requests spread over several buckets, and everyone
  behind the same hop shares one. A client sending one analysis per minute can
  hold the only slot.
- **F-07 (high, availability).** There are HIGH advisories in python-multipart
  and Starlette, the two packages that parse every upload.
- **F-16 (low).** The PharmCAT exit status is captured and never checked.

Written 2026-11-05 before any B8 code. Its sha256 goes into `audit/phase9/B8.log`
before the first edit. Nothing here is edited after measurement.

## State at B7 (a5c06f2, live)

### Rate limiting (F-04)

- `security.client_key` uses the direct peer, unless the peer is inside
  `TRUSTED_PROXY_CIDRS`; then it uses the first `X-Forwarded-For` entry.
- Production sets no `TRUSTED_PROXY_CIDRS`, so the key is a Render-internal
  `10.x` hop. Part A saw four such hops for one client in 16 minutes.

### Queueing

- `AnalysisMemoryGateMiddleware` admits one `/analyze` or `/coverage` upload at a
  time, in arrival order (a ticket deque).
- Every other upload waits up to `PHARMCAT_QUEUE_TIMEOUT_SECONDS` (90 s in
  production), then gets 503 `SERVER_BUSY` with `Retry-After`.
- Nothing caps the number of waiters. Nothing stops one client from having
  several uploads waiting at once.

### Rate-limit response

`InMemoryRateLimiter` allows 10 uploads per 300 s per key; past that it answers
429 with `Retry-After`.

### Deletion

- `run_pharmcat` deletes its temporary directory in a `finally`, with
  `shutil.rmtree(..., ignore_errors=True)`, so a failed delete is silent.
- Part A measured 0 leftover directories after about 50 analyses and an injected
  timeout.
- Tests cover process reaping and log confinement on success. No test injects
  each failure point and then counts directories.

### Logs

Part A found no genotype, rsID, sample ID or filename in 260+ production log
lines. No test guards this.

### Dependencies (pip-audit 2.10.1, 2026-11-05, `backend/requirements.txt`)

| Package | Advisories | Fixed by |
|---|---|---|
| python-multipart 0.0.20 | 6 (CVE-2026-24486, -40347, -42561, -53538, -53539, -53540) | 0.0.31 |
| starlette 0.49.3 | 5 (CVE-2026-48710, -48817, -48818, -54282, -54283) | 1.3.1 |

Starlette is not pinned; FastAPI 0.121.2 holds it below 0.50. FastAPI 0.140 and
later accept Starlette 1.x.

### Exit status (F-16)

`run_pharmcat` records `returncode` but serves any report that exists.

### Fact not yet established

Which request header carries the visitor's address on Render, and whether a
visitor can forge it. Render's documentation does not say. Community reports
(Render staff and users) say:

- Render puts the real client first in `X-Forwarded-For`, but appends to a
  client-supplied value, so the first entry is forgeable;
- Render's edge runs through Cloudflare, which sets `CF-Connecting-IP`.

This is not assumed. It is measured live (L4 below).

## Design

### 1. Client identity

`CLIENT_IP_HEADER` (env) names one header — for example `cf-connecting-ip` —
whose value is the client key when, and only when, the direct peer is inside
`TRUSTED_PROXY_CIDRS`.

- The value must be exactly one valid IP address. Anything else (missing, a
  list, junk) falls back to the peer.
- Without the setting, behaviour is exactly as today.
- `render.yaml` documents the intended production values
  (`TRUSTED_PROXY_CIDRS=10.0.0.0/8`, `CLIENT_IP_HEADER=cf-connecting-ip`).
- `render.yaml` is not auto-applied, so the live setting is a Render environment
  change made only with the owner's approval at deploy time.
- The startup log names the identity source, not any address.

### 2. One upload in flight per client

When the client identity is trusted (the header is configured and the peer is a
trusted proxy), a client that already has an upload waiting or running gets 429
with `Retry-After` and `error_code` `ONE_AT_A_TIME` for a second concurrent
upload. The memory gate tracks keys of waiting and running uploads.

- **Why it needs a trusted identity:** keyed on Render hops it would refuse
  strangers who happen to share one, so with no trusted identity it is off.
- **Why it is enough:** with one upload per client and first-come service, a
  client sending back to back can no longer hold the slot. Every waiter is next
  after at most the one running analysis.

### 3. Queue cap

`MAX_WAITING_UPLOADS` (env, default 2): an upload that would wait behind that
many others gets 503 `SERVER_BUSY` with `Retry-After` at once, instead of waiting
out the queue timeout. At about a minute per analysis and a 90 s timeout, a third
waiter could not start in time anyway; saying so at once is the honest answer.

### 4. PharmCAT exit status

A non-zero exit is an execution failure: `PharmcatExecutionError`, which becomes
503 `PHARMCAT_UNAVAILABLE` with the user message that already exists. That holds
even if a report file was written. The status reaches the operator log, not the
response.

### 5. Deletion

- The temporary directory is removed in the `finally` with errors surfaced: one
  retry, then an operator-log line naming the directory, never its contents.
- A test injects a failure at each point and asserts that no
  `pharmaguard_pharmcat_*` directory survives. The points are:
  - before PharmCAT starts;
  - a non-zero exit with a report present;
  - a timeout;
  - cancellation;
  - an unreadable report;
  - an exception while building the response.

### 6. Logs

A test captures every log record emitted across a successful analysis and each
failure path above. It asserts that none contains:

- an rsID (`rs\d{3,}`);
- a diplotype (`*N/*N`) or VCF genotype (`0/1`, `1|1`);
- the uploaded filename or the sample ID.

Any leak found is fixed at its source.

### 7. Dependencies

- Pins: `fastapi==0.162.0`, `starlette==1.10.0` (now explicit),
  `python-multipart==0.0.33`.
- `pip-audit -r backend/requirements.txt` shows no advisory.
- Any code the upgrade breaks is fixed, with each change recorded.
- The image is rebuilt and checked as in B4 (`/ready` and S1–S6 in the
  container).

## Acceptance criteria

| # | Criterion |
|---|---|
| AC1 | Identity, by test: with `TRUSTED_PROXY_CIDRS=10.0.0.0/8` and `CLIENT_IP_HEADER=cf-connecting-ip`, a request from peer `10.1.2.3` carrying `CF-Connecting-IP: 198.51.100.7` is keyed `198.51.100.7`. The same header from an untrusted peer is ignored. A list, junk or missing value falls back to the peer. Without the setting, today's keys exactly. `X-Forwarded-For` is never used when `CLIENT_IP_HEADER` is set |
| AC2 | One in flight, by test: with a trusted identity, a second concurrent upload from the same client gets 429 `ONE_AT_A_TIME` with `Retry-After`, while another client's upload queues normally. Without a trusted identity no such 429 is ever given |
| AC3 | Queue cap, by test: with `MAX_WAITING_UPLOADS=2` and the slot held, a third waiting upload gets 503 `SERVER_BUSY` with `Retry-After` in under 1 s. Waiters are still admitted first-come, first-served |
| AC4 | Exit status, by test: PharmCAT exiting non-zero with a report on disk gives 503 `PHARMCAT_UNAVAILABLE`, not a result |
| AC5 | Deletion, by test: no `pharmaguard_pharmcat_*` directory survives any of the six injected failures, nor a success; a failed delete is retried and logged |
| AC6 | Logs, by test: no rsID, diplotype, genotype, filename or sample ID in any record across the success and failure paths |
| AC7 | Dependencies: pip-audit on `backend/requirements.txt` reports 0 advisories (logged); the full backend and Flutter suites pass; the rebuilt image passes `/ready` and S1–S6 in a container |

## Zero-regression

- **S1–S6, cohort, 74 PharmCAT VCFs, A4:** identical to B7 in labels, statuses
  and warnings.
- **External evaluation:** the re-bind shows no eligibility or discrepancy change
  against B7's package.

## Sabotage

Each must turn a test red, and the files are restored byte-identical afterwards.

| id | sabotage |
|---|---|
| SB8-a | `client_key` trusts the header from any peer |
| SB8-b | the in-flight check is removed |
| SB8-c | the queue cap is removed |
| SB8-d | the exit status is ignored again |
| SB8-e | the delete swallows errors again and skips the retry |
| SB8-f | a log line carries the uploaded filename |

## After deploy (only if the owner approves a deploy and the Render environment change)

Live criteria, to be logged before measuring. They are privacy-preserving: no
address is logged or recorded, only the limiter's observable answers.

| # | Criterion |
|---|---|
| L4-i | Eleven `/coverage` uploads from this machine within 300 s: the eleventh gets 429. One stable key per client, where Part A saw four |
| L4-ii | Then one more with a forged `CF-Connecting-IP: 192.0.2.77` (TEST-NET-1): still 429. The forged value does not reach the key |
| L4-iii | The same with a forged `X-Forwarded-For: 192.0.2.78`: still 429 |
| L4-iv | If L4-i fails, the header is absent; if L4-ii fails, it is forgeable. Either way the environment change is rolled back to the previous values and reported, never left half-working |

## Out of scope

- A shared store for multiple instances: one instance, as documented.
- Per-client fairness without a trusted identity.
