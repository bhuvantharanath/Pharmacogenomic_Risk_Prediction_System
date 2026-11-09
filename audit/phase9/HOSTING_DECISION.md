# Hosting — a decision for the owner, with measured numbers

The Phase 9 brief, "Explicitly NOT recommended":

> **Moving off Render right now**: Oracle Cloud Always Free Arm was cut in June
> 2026 to 2 OCPU / 12 GB (still far more than Render's 512 MB) but needs card
> verification and has capacity/idle-reclaim risk; Cloud Run needs a billing
> account. Present this as a decision for me with measured numbers after B4,
> don't migrate.

B4 measured the numbers on 2026-11-04, but nothing on disk records the decision
being put to the owner. Written 2026-11-09. Nothing has been migrated.

## What is measured on Render today

Every figure below is read from an artifact. Nothing about another host is
measured, because measuring one means deploying there.

| | Old 6.02 GB image (Part A, or B4's own baseline before deploy) | Now (584 MB image) | Source |
|---|---|---|---|
| Cold start after ~15 min idle | **82.4 s**, and one cold request lost after >300 s | **22.40 s, 22.45 s** (two verified) | `SUMMARY.md`; `B4.log` AC6 |
| Peak memory on Render (60 s points) | 308.8 MiB | **306.8 MiB** of 512 MB | `B4.log` AC8 |
| Warm `/analyze`, one input repeated | p50 63.10 s (n=5) | **p50 67.30 s** (n=5) | `B4.log` AC7 |
| Warm `/analyze`, the six demo files | — | **median 64.61 s**, range 60.8–65.5 s | `partb/F20/live-after-s1s6/` |
| The same six files on local uvicorn | — | median 1.37 s, so live is **about 47×** | `partb/F20/s1-s6/` |
| A second request queued behind the first | 114.7 s | not re-measured | `SUMMARY.md` |

What these say:

- **The brief's main trigger is gone.** An 82 s cold start, with a request lost
  outright, was the strongest reason to move. B4 cut it to 22 s, verified twice.
- **Memory is not the binding constraint.** The peak was 306.8 MiB against a
  512 MB limit, with the slim image.
- **What remains is analysis time.** About 65 s per analysis, against 1.4 s on
  a laptop for the same files. This is the only cost a move would plausibly
  reduce. B4's slim image was about 7% slower warm than the old one (67.30 s
  against 63.10 s), within the 10% B4 allowed.
- **The client already says what this costs.** README: "The client states the
  cost while you wait rather than hiding it behind a spinner".

## The options

The facts about other hosts are as the brief and `PROJECT_STATUS.md` record
them. They were not re-verified here.

| | Needs from you | Changes | Unknown until measured |
|---|---|---|---|
| **A. Stay on Render** | nothing | nothing | — |
| **B. Measured trial, Oracle Always Free Arm** (2 OCPU / 12 GB) | an Oracle account with card verification | nothing live: one throwaway instance, S1–S6 timed against Render's 64.61 s | the analysis time; how often the instance is reclaimed when idle |
| **C. Measured trial, Cloud Run** | a billing account | nothing live, as B | the analysis time; its own cold start |
| **D. Migrate without measuring** | as B or C | everything below | everything — and the brief says don't |

What a migration, as opposed to a trial, would have to change. Each item is
found in the repo, not assumed:

- **The deploy step.** `deploy-web.yml` deploys through Render's API
  (`RENDER_API_KEY`, `RENDER_SERVICE_ID`, polling `api.render.com`), and
  `infra/render.yaml` is the blueprint.
- **The proxy trust settings.** B8 keys the rate limit on `CF-Connecting-IP`
  and trusts Render's internal range (`TRUSTED_PROXY_CIDRS=10.0.0.0/8`).
  Another host fronts requests differently, and B8's live checks would need
  repeating.
- **The backend URL**, in three places: the client's `API_BASE_URL`, the
  keepalive's `BACKEND_URL`, and the live verification scripts.
- **Already portable:** `/ready`'s commit. `main.py` reads `RENDER_GIT_COMMIT`,
  then falls back to `GIT_COMMIT` and `SOURCE_COMMIT`.

## Recommendation

**A, stay on Render.** The reason to move was the cold start, and that is
fixed. Memory has headroom. Every alternative needs a payment method on file,
and the one thing it might improve, analysis time, has not been measured
anywhere but Render.

If analysis time becomes the priority, take **B or C as a trial, not a
migration**. The trial needs your account, after which I would deploy one
throwaway instance and time S1–S6 against Render's 64.61 s, so the decision
rests on a number rather than the spec sheet. Oracle's idle-reclaim risk
matters more for a demo that sits idle between viewings than raw speed does,
and only a trial would show how often it happens.

## Owner's decision

*(not yet made)*
