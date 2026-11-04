# B4 — AC4 amendment, by owner decision

Recorded 2026-11-04, AFTER the local measurement, at the owner's explicit
instruction. `audit/phase9/B4_PLAN.md` (sha256 66355c90…) is left unedited.

## Why

AC4 named the wrong endpoint. In this application `/health` is a liveness check
that returns `{"status":"ok"}` and never reports PharmCAT, in the old image and
the slim one alike, so the clause could not hold for any image. PharmCAT
availability is what `/ready` reports. The owner's answer, verbatim:

> Amend AC4, push, deploy

## Original AC4

Served path in the slim image: no `pharmcat_pipeline`, jar sha 9317ef63…, PID 1 is
tini, runs as uid 1000, /health reports PharmCAT available.

## Amended AC4

Served path in the slim image: no `pharmcat_pipeline`, jar sha 9317ef63…, PID 1 is
tini, runs as uid 1000, **/ready** reports PharmCAT available.
