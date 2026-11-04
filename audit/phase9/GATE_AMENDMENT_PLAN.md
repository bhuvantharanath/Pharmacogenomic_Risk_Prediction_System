# Release-gate amendment — plan and pre-committed acceptance criteria

Written 2026-11-04, before any code was changed. Decision by the project owner
on 2026-11-04 after Phase 9 Part A ("Amend gate, ship HEAD").

## Why

Phase 9 Part A found that production runs `0a8b129` (2026-08-14) and serves the
20 stored LLM explanations, none of them approved, under a disclaimer the project
has since retracted (FLAWS F-01, F-03). HEAD withholds all unapproved stored prose
and serves the deterministic template instead, so HEAD is strictly safer than
production. HEAD cannot deploy, because the release gate
(`scripts/release_status.py --run-required`) requires *every* stored entry to be
human-adjudicated and approved before *any* release — a state that needs a
clinician this project does not have. The gate therefore keeps the less safe
build serving indefinitely.

## The amendment

Policy `human_review_all_stored_generated_entries` becomes
`withhold_unapproved_stored_prose`:

- A release is allowed when **no stored generated prose would be served**
  (`releasable_generated_entries == 0`, decided by the runtime's own approval
  function for every stored entry), *or* when the full content-review condition
  already required today holds (adjudication complete, no rejected/outstanding
  claims, all entries approved, approved entries human-bound).
- The mixed state — some stored entries servable, others not — remains blocked.
  This amendment does not enable partial release of stored prose.
- Every non-content prerequisite stays blocking, unchanged: required checks,
  approval-manifest compatibility, scientific-bundle compatibility, tested =
  candidate artifact hash, tested = candidate revision, no clinical-expert claim.
- Content review is still computed and reported (`content_ready`), and
  `--content-only` is unchanged: it keeps exiting non-zero until adjudication is
  done, so the `test` workflow keeps showing the content gap.

## Acceptance criteria (pre-committed)

| id | criterion | how checked |
|---|---|---|
| AC1 | `evaluate_release` returns `release_ready: True` when `releasable_generated_entries == 0` and every non-content prerequisite passes, even with adjudication incomplete | new unit test |
| AC2 | `release_ready: False` whenever any stored entry would be served without the full content-review condition | new unit test (releasable = 1, adjudication incomplete) |
| AC3 | `release_ready: False` when any single non-content prerequisite fails, in the template-only state | new parametrised unit test over all six |
| AC4 | `--content-only` behaviour unchanged (exit 1, `release_ready` false) | existing `test_only_authoritative_tool_emits_release_ready` stays green |
| AC5 | the payload names the policy actually applied and lists outstanding content review as non-blocking, not as absent | unit test on payload + human-readable output |
| AC6 | on the real repository data, `served_stored_prose_reviewed` is true because 0 entries are releasable | real-data unit test |
| AC7 | full backend suite, Flutter analyze/test, provenance, label-mapping and bundle verification pass; `scripts/release_status.py --run-required --candidate-sha <new commit>` exits 0 locally | local run |
| AC8 | after deploy: live `/ready` reports the new commit; a live S1 request reports `source=template` (no stored prose served) and HEAD's disclaimer; live S1–S6 labels equal local HEAD's | live checks after the Deploy workflow |

Zero-regression condition: no clinical label may change. The amendment touches
only the release decision, not the engine; S1–S6 labels on live after deploy must
equal local HEAD's (AC8), and the 105-row mapping validation must still report
92/105 with the same 13 accepted divergences (AC7).

Sabotage (rule 4): (a) revert the amendment so `ready = all(prerequisites)` →
AC1's test must go red; (b) make `served_stored_prose_reviewed` always true →
AC2's test must go red. Both are run before committing.

The existing test `test_release_status_describes_fallback_without_declaring_release_ready`
pins the old policy (template-only ⇒ not ready). It is replaced by AC1's test
because the policy changed by owner decision, not because it was failing.

If any criterion fails, stop and report rather than adjust the criterion.
