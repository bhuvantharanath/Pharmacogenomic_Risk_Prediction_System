# B8 — L4-ii amendment, by owner decision

Recorded 2026-11-06, after measurement, at the owner's explicit instruction. The plan
(`audit/phase9/B8_PLAN.md`, sha256 243ad4c6…) and the live criteria in
`audit/phase9/B8.log` (the log's sha256 was 5a2ce2ca… when they were written) are left
unedited, so their hashes still prove what was pre-committed.

## What happened

L4-ii sent one upload with a forged `CF-Connecting-IP: 192.0.2.77` straight after the
eleventh upload got 429. The criterion expected 429.

It got 403 from Cloudflare (`partb/B8/live_forged_edge_diagnostic.json`):

- `Server: cloudflare`;
- a 17-byte plain-text body;
- Cloudflare error code 1000;
- no Render or application header.

Cloudflare refused the request before it reached Render. The next upload, with a
forged `X-Forwarded-For`, got 429 with the same Retry-After as the eleventh: the same
bucket.

## Why the clause did not fit

The plan assumed a forged header would reach the application, and that the application
would either ignore it (429) or key on it (200, forgeable). It did not consider the edge
refusing the request outright. L4-iv read any failed L4-ii as "forgeable". But a request
the edge refuses never reaches the key at all.

Two options were put to the owner:

- accept the result and amend the clause;
- roll back the environment change as L4-iv was written.

The owner's answer, verbatim:

> Accept, amend L4-ii

## Original clauses

From the plan's "After deploy" table:

> L4-ii: Then one more with a forged `CF-Connecting-IP: 192.0.2.77` (TEST-NET-1): still
> 429. The forged value does not reach the key

> L4-iv: If L4-i fails, the header is absent; if L4-ii fails, it is forgeable. Either way
> the environment change is rolled back to the previous values and reported, never left
> half-working

## Amended clauses

**L4-ii.** Send one more upload with a forged `CF-Connecting-IP: 192.0.2.77`
(TEST-NET-1). It passes if the forged value does not reach the key, shown by either:

- (a) 429 `RATE_LIMITED` as JSON from the application: it received the request and kept
  the visitor's own bucket; or
- (b) a refusal at Cloudflare's edge before Render: not JSON, `Server: cloudflare`, and
  no Render header (`rndr-id`) or application header (`x-content-type-options`).

Any 2xx, or any other answer, fails it.

**L4-iv.** If L4-i fails, the header is absent. If L4-ii fails, the header is forgeable
or the answer is unexplained. Either way the environment change is rolled back to the
previous values and reported, never left half-working.

**L5** stays as written in `B8.log`, and is now the deciding positive check. If L5 fails,
the L4-iv rollback applies.

## Effect

L4-ii passes under (b). Nothing else in the plan or the live criteria changes.
