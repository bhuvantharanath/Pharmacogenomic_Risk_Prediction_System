# B7 — Client honesty about connectivity

Part B item 7 of the Phase 9 brief:

> - Add `GET /health` returning version + data hashes, CORS-permissive for that one
>   endpoint only, so the client can tell "asleep" from "blocked" from "error".
> - Allow Cloudflare Pages preview origins via a strict regex
>   (`^https://[a-z0-9-]+\.pharmaguard-web\.pages\.dev$`), with a test that a
>   look-alike domain is rejected.
> - Distinct UI states for: waking (with countdown honest to the 180 s budget),
>   blocked/misconfigured, server error, analysis declined.

It addresses two findings:

- **F-11:** a sleeping server and a CORS-blocked origin look the same for 180 s.
  The blocked case is then reported as "The server responded but did not report
  healthy". The wake bar measures 90 s against a 180 s wait.
- **F-12:** the client-side half. Five documents promise a 12.85 s cold start, and
  a health ping on Android can be held for 180 s.

Written 2026-11-05 before any B7 code. Its sha256 goes into `audit/phase9/B7.log`
before the first edit. Nothing here is edited after measurement.

## State at B6 (1360a7c, live)

| Area | Code | Behaviour |
|---|---|---|
| Health endpoint | `GET /health` | Returns `{"status": "ok"}`, under the same CORS allowlist as every other endpoint. A browser on a disallowed origin gets no readable response, so asleep and blocked look the same. |
| Health ping | `PharmaGuardApi.health()` | Returns false for every `DioException` and every non-ok body. |
| Final message | `BackendStatusController` | Ends in `unreachable` with "The server responded but did not report healthy". |
| Wake bar | `backend_status_banner.dart` | Divides by a hard-coded 90 s. The client waits `kWakeupBudget` = 180 s. |
| Preview origins | `security.allowed_origin_regex` | Allowed only when `CORS_ALLOW_PAGES_PREVIEWS` names the project. Production does not set it, so `https://<hash>.pharmaguard-web.pages.dev` is blocked (F-11 b). |
| Error panel | home screen | One `_ErrorBox` covers a declined file (400/413), a server failure (5xx) and a network failure alike. |
| Analysing copy | home screen | Says "roughly 50–60 seconds" and does not mention the queue. Measured since B4: warm p50 67.3 s, and live S1–S6 today ran 58–68 s. |
| Cold-start figure | `README.md:203`, `docs/DEMO_SCRIPT.md:21,45`, `infra/DEPLOY_NOTES.md:94`, `reports/deployment_verification.md:169` | All quote 12.85 s. B4 measured 22.40 s and 22.45 s on the slim image. |
| Android ping timeout | `PharmaGuardApi` | `connectTimeout` is 10 s, but `receiveTimeout` is 180 s, so a ping that connects can be held for 180 s. |

## Design

### 1. `GET /health`

The response body is:

```json
{
  "status": "ok",
  "commit": "...",
  "commit_short": "...",
  "data": {
    "cpic_guidance_sha256": "...",
    "allele_definitions_sha256": "...",
    "allele_definitions_version": "..."
  },
  "origin_allowed": true | false | null
}
```

- **Data hashes** come from B2's `knowledge_identity()`, which reads the jar once
  and caches the result. `data` is `{}` when no jar is present.
- **`origin_allowed`** is the same decision the CORS middleware makes for the
  request's `Origin` header. It is null when the request has no `Origin` (curl, or
  Render's health checker).
- **Cost** stays trivial: no subprocess and no disk access after the first call.

A small ASGI middleware, outermost, makes this one path CORS-permissive:

| Request | Response |
|---|---|
| `GET /health` (and HEAD) | `Access-Control-Allow-Origin: *` |
| `OPTIONS /health` | 204 with `*`, `GET, OPTIONS` and the requested headers, from any origin |

No other path changes: a disallowed origin still gets no
`Access-Control-Allow-Origin` header on `/analyze`, `/coverage` or `/ready`, and
its preflight to `/analyze` is still refused.

### 2. Preview origins

For every exact origin in `CORS_ALLOWED_ORIGINS` of the form
`https://<project>.pages.dev`, the regex also allows
`^https://[a-z0-9-]+\.<project>\.pages\.dev$`. For production that is
`^https://[a-z0-9-]+\.pharmaguard-web\.pages\.dev$`.

- **Why derive it:** previews of a project only its owner can deploy to are as
  trusted as its production origin. Deriving the regex from the configured origin
  needs no change to Render's environment.
- **Unchanged:** `CORS_ALLOW_PAGES_PREVIEWS` keeps working for any other project.
- **Still never allowed:** a bare `*.pages.dev`, or any other project.

### 3. Client states

`PharmaGuardApi.healthCheck()` classifies each ping. The ping has a 10 s receive
timeout on every platform, so Android behaves like web.

| Ping outcome | Phase | When |
|---|---|---|
| No response (timeout, connection error) | waking | Keeps trying until the budget runs out. |
| HTTP 502, 503 or 504 (Render's edge while the app starts) | waking | Keeps trying until the budget runs out. |
| 200 `ok`, `origin_allowed` true or null | `ready` | Immediately. |
| 200 `ok`, `origin_allowed` false | `blocked` (new) | Terminal at once, with no 180 s wait. |
| Any other HTTP status, or a 200 without `ok` | `serverError` (new) | Terminal at once. |

- **Blocked copy:** names the server, says this page's address is not on its
  allowed list, and says it is a deployment setting, not something the user can
  fix by waiting.
- **Server error copy:** names the HTTP status and says the file is not the
  cause.
- **Budget expiry:** if the budget runs out with only non-answers, the phase is
  `unreachable`. Its copy no longer claims the server responded.
- **Wake bar:** shows elapsed time against the real budget (`kWakeupBudget`,
  180 s) and how long is left before it gives up. Progress is `elapsed / budget`,
  capped below full.
- **Analysis declined:** `ApiException.kind` separates four cases, each with its
  own panel heading:
  - declined: 400, 413, 415 or 422 with an `error_code` (the file);
  - server error: 5xx other than `SERVER_BUSY`;
  - network failure: no status;
  - plain local messages: no heading, as now.

  `SERVER_BUSY` and 429 keep their existing panels.

### 4. Honest timing copy

- **Analysing panel:** says "about a minute" and that a request queued behind
  another analysis waits for it to finish first. It states no queue length,
  because that is a deployment setting.
- **`kColdStartExpectation`:** "usually 20–30 seconds, occasionally longer if the
  server image has to be fetched again". Measured cold starts: 22.40 s and
  22.45 s (B4), and 28.4 s end to end (B6). Its comment and tests cite these.
- **The five documents** quote B4's measured cold starts instead of 12.85 s,
  dated.

## Acceptance criteria

| # | Criterion |
|---|---|
| AC1 | `/health` returns `status`, `commit`, the three data-identity fields and `origin_allowed` (null without `Origin`; true for an allowed origin; false for a disallowed one), and answers `GET` with `Access-Control-Allow-Origin: *` and `OPTIONS` preflight with 204 + `*` for a disallowed origin. For the same disallowed origin, `/analyze`, `/coverage` and `/ready` carry no `Access-Control-Allow-Origin` and the `/analyze` preflight is refused (tests). `origin_allowed` agrees with the CORS middleware's own decision for every origin tested |
| AC2 | With `CORS_ALLOWED_ORIGINS=https://pharmaguard-web.pages.dev`, `https://6bc16810.pharmaguard-web.pages.dev` (the F-11 origin) and `https://main.pharmaguard-web.pages.dev` are allowed. Rejected look-alikes (a test): `https://pharmaguard-web.pages.dev.evil.com`, `https://evil-pharmaguard-web.pages.dev`, `https://a.b.pharmaguard-web.pages.dev`, `http://abc.pharmaguard-web.pages.dev`, `https://abc.pharmaguard-web.pages.dev.`, `https://abcpharmaguard-web.pages.dev`, `https://abc.other-project.pages.dev`, `https://abc.pharmaguard-web.pages.dev:8443`. A bare `*.pages.dev` is never allowed |
| AC3 | Client, by test: an awake allowed backend → `ready` on the first ping; `origin_allowed` false → `blocked` after one ping with no further pings; HTTP 500 → `serverError` after one ping naming 500; 503 then 200 → waking, then `ready`; no answer until the budget → `unreachable`, whose text does not contain "responded". The bar's progress at 90 s elapsed is 0.5 of the 180 s budget, and the banner shows the remaining time. The health ping sets a 10 s receive timeout |
| AC4 | Each `ApiException` maps to its kind (400 and 413 with a code → declined; 500 → server error; no status → network), and the home screen's panel shows a distinct heading for each, by widget test |
| AC5 | No document outside `audit/` and git history quotes a 12.85 s cold start as current (grep, logged). `kColdStartExpectation` quotes only measured figures within the budget. The analysing copy names the queue |

## Zero-regression

- **S1–S6, cohort, 74 PharmCAT VCFs, A4:** identical to B6 in labels, statuses and
  warnings. B7 does not touch the analysis path.
- **Suites:** backend and Flutter pass.
- **External evaluation:** the re-bind shows no eligibility or discrepancy change
  against B6's package.

## Sabotage

Each must turn a test red, and the files are restored byte-identical afterwards.

| id | sabotage |
|---|---|
| SB7-a | the `/health` middleware stops adding `*` |
| SB7-b | the preview regex loses its anchors |
| SB7-c | the `*` header is applied to every path |
| SB7-d | the client treats `origin_allowed` false as ready |
| SB7-e | the wake bar divides by 90 s again |
| SB7-f | a declined 400 is shown with the server-error heading |

## After deploy (only if the owner approves a deploy)

Live criteria, to be logged before measuring:

- From the production origin, `/health` has `origin_allowed` true.
- From `https://6bc16810.pharmaguard-web.pages.dev`, the `/analyze` preflight is
  allowed.
- From `https://evil.example`, `/health` answers with `*` and `origin_allowed`
  false, and the `/analyze` preflight is refused.
- The production page reaches "ready".

## Out of scope

- Client-side queue position (needs server streaming).
- The stale-client reload after a deploy. That is a service-worker update, noted
  in B5.log; it is listed as a follow-up.
