# Prompt 5: current candidate evaluation and compatibility receipt

This is a local, dirty-tree candidate receipt, not a release or clinical validation. The candidate was frozen from the working tree on 2026-10-04; base HEAD was recorded separately as `1dc7557da49f38e831b382545044b00a481507b6` on `main`. The initial status, full tracked diff, and 429-file byte inventory are `git-status-start.txt`, `git-diff-start.txt`, and `scope-before.json`. The five changes since the earlier 421-file candidate are in `prior-421-delta.json`. No historical benchmark, result, migration, or approval record was rewritten.

## Reproduction and invariant

The two specified compatibility tests failed 2/2 before the fix. The old checked manifest expected portable core `204c315389f97f8de688b8ac3219bcc27f0a95c6e8c699fc50fd8b0df361725c`, while the dirty candidate core was `38451a563c6f6cfb52257626d41700eeff3a5621ebe91b3358f878b375a6a691`. The validator and exact release gate also failed. These were real stale-evidence failures, not a reason to patch an expected hash. The September hash-only migration remains historical and its `migration_identity_matches` is correctly false for today's candidate.

The scientific core is SHA-256 of a domain separator plus each sorted, versioned POSIX path and raw bytes from `scripts/scientific_hash_policy.json` (policy v2). The self-referential `backend/app/data/compatible_bundle.json` is excluded from that core. The compatible bundle separately hashes policy, PharmCAT JAR/member definitions and guidance, positions, contract/label/capability files, explanation store and approval manifest, historical benchmark/migration, and the new evaluation manifest. The new evaluation manifest binds its source and output files by SHA-256 and size while excluding itself; the compatible bundle hashes that manifest separately. The release artifact identity also hashes a finite intended source/release inventory and explicitly includes the new evaluation files. Thus a changed evidence output invalidates release identity and bundle verification even when the scientific core is unchanged.

The pinned PharmCAT 3.4.0 JAR is `9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741`, with embedded CYP2C19 data version `2026-07-13-11-40`. Position VCF/index SHA-256 are `01a28fe31675c9e8a8b18bcab4afb82a62abdfea6606856aeca0e0378e7d6b58` and `eb536edd898613977e7429469e4a8fceb31afc85a839f98423272f90a9491ac4`. The current label mapping, capability registry, position requirements, explanation, and approval bindings are recorded in `backend/app/data/compatible_bundle.json` and `candidate-inventory.json`.

## Controlled evaluation

The original independent CDC GeT-RM/1000 Genomes protocol, truth workbook/table, 208-person cohort lock, combined source VCF, six genomic slices, pinned JAR, and all 208 raw caller reports were verified against frozen hashes. No truth or inclusion/exclusion rule was changed. `prepare`, `fetch --resume`, and `evaluate --resume` ran in `evaluation-copy` using the supported benchmark script. Fetch reused all byte-matched local genomic slices and made no new network acquisition. Evaluation reused all 208 independently hash-checked PharmCAT caller reports and freshly ran the current application's per-person projection/scoring over 208 individuals and 1,456 sample-gene rows. There were **zero new 208-person cohort PharmCAT executions**. The 596 evaluable truth rows remain repeated gene measures within 208 people, not 596 independent people.

The new evidence is `test-data/benchmark/current-candidate-2026-10-04/`, evaluation ID `pharmaguard-external-current-candidate-v2-2026-10-04`. Its manifest SHA-256 is `23a46b1070cd82b578c4f518ab77a0b87af71a30573513d87139328d61b7898a`. `evaluation_manifest.json` provides every source/output SHA-256, stage/reuse declaration, denominators, and the exclusion of its own bytes. `stage-command-receipts.json` and the audit `commands.json` provide executed commands and exit codes; `raw_benchmark_manifest.json` is the fresh application execution record. The original historical identity remains `9961033924dda2d4ab8e57d85450debeb98c4afdc392b3959d3d0ccf856f214c` and is not relabeled as current evidence.

Fresh scored per-gene results match the historical result fields except generation time. Exclusions, discrepancies, truth, cohort lock, and raw report manifest are byte-identical. All 1,456 `input_eligibility.tsv` rows differ only in the temporary VCF SHA-256. A same-input HG00111 reproduction generated 172 identical biological records under the two source paths; `bcftools` wrote different absolute paths into the VCF command header. The unavailable historical temporary VCF bytes prevent a direct bytewise historical projection comparison. This is a bounded provenance-header explanation, not a claim of independent genotype or clinical accuracy. Variant-only abstention remains expected; no actionability truth was inferred.

The two frozen read-backed F4 VCFs were separately replayed through the live local API and pinned PharmCAT caller: NA18526 CYP2C19 `*1/*1` normal and NA12878 `*1/*2` actionable under the bounded clopidogrel context. Their observed VCF SHA-256 matched frozen F4 artifacts and 14/14 receipt checks passed. This did not redo raw-read extraction or provide cohort-level truth. The API responses and checks are in `NA18526.fresh-api.json`, `NA12878.fresh-api.json`, and `f4-fresh-replay.json`.

## Candidate manifest, clean copy, and tests

The old current candidate compatible manifest was copied to `historical-compatible_bundle.json` before rebuilding. The new candidate bundle is schema 3, ID `pharmaguard-scientific-current-candidate-2026-10-04-v3`, SHA-256 `963a039ba16690d1c6ed772268ebb5c1512275beeb5fa117a6bef1c03aae7600`. The versioned evidence check requires exact candidate core, verified source/output hashes and denominators, compatible upstream report reuse, actual application-stage receipt, and F4 receipt. The historical migration is retained but no longer treated as evidence for changed bytes.

The clean `release-copy` contains 433 finite intended project/release files plus four pinned externally acquired artifacts; `candidate-inventory.json` lists every path, byte count, and SHA-256. It excludes secrets, actual env files, logs, caches, and unrelated data. Working tree and clean copy have the same scientific core `38451a563c6f6cfb52257626d41700eeff3a5621ebe91b3358f878b375a6a691` and release hash `0c1aa418159cc7e4456b058d37cbabf751ff0f2bf9a7050566e798d6e24fa92c`. The clean validator passes. A copy in a different parent directory has the same hashes. `.DS_Store`, editor backup, cache, log, and temporary files did not affect either identity. Mutations to scientific code, capability registry, position requirements, explanation store, approval manifest, and current benchmark output each failed verification as appropriate. All isolated changes were restored exactly; working candidate bytes were not touched by these mutation tests.

Targeted manifest/hash/benchmark tests: 36 tests, 0 failures, 0 skips (exit 0). Full backend: 921 tests, 919 passed, 2 skips, 0 failures (exit 0). The two skips are `test_documented_numbers.py` because README has no test count, and `test_glossary_audit.py` because no glossary decisions were recorded; neither was made green by invented content. Nine existing `PytestRemovedIn10Warning` class-scoped fixture warnings remain visible. `git diff --check` exited 0. The exact release gate passed all six automated required checks: compatible bundle, backend tests, provenance, label mapping, Flutter analyze, and Flutter tests (202 Flutter tests passed). Flutter dependency resolution reported 24 newer versions incompatible with current constraints; analyzer found no issues.

The release gate still exits 1 and says `not-ready`: 19 outstanding claims, 36 automated-only decisions, 20 unapproved stored entries, zero approved/releasable entries, and no author-read approvals. It reports `clinical_expert_review: NOT_OBTAINED`; automated checks are not human or clinical review. This human prerequisite is neither waived by deterministic fallback nor by the compatible scientific evidence. The remaining browser acceptance questions from Prompt 3, if still open, are not resolved by this backend evaluation. No unconditional clinical-readiness statement follows.

## Files changed during this task

From the starting 429-file scope, only these five existing files changed: `scripts/compatible_bundle.py`, `scripts/release_status.py`, `backend/tests/test_compatible_bundle.py`, `backend/tests/test_portable_scientific_hash.py`, and `backend/app/data/compatible_bundle.json`. New files are `backend/tests/test_current_candidate_evaluation.py`, the 11-file versioned evaluation directory, and this new audit directory. The original unrelated dirty changes remain. No UI rendering or biological definition was changed in this task. No commit, stage, push, merge, tag, release, deployment, redeployment, remote production change, reviewer contact, or external genomic submission occurred.

## Command and checksum indexes

`commands.json` records every named execution with exact argument vector, cwd, timestamps, exit code, and stdout/stderr receipt paths. The adjacent `<name>.stdout`, `<name>.stderr`, and pytest XML files are the untrimmed receipts. `candidate-inventory.json` is the finite handoff for Prompts 6 and 7. `preserved-manifests.json` lists frozen pre-change manifest hashes; `clean-copy-verification.json` records clean and mutation checks. The command table and final Git receipt are appended below.

### Exact command ledger

All commands ran from the repository root unless the receipt `cwd` says otherwise. Exit 1 in reproduction/red stages was expected evidence, and exit 1 for the final gate is the unresolved human prerequisite.

| Receipt | Exact command | Exit |
|---|---|---:|
| `validator` | `backend/.venv/bin/python scripts/verify_compatible_bundle.py --json` | 1 |
| `reproduce-failures` | `backend/.venv/bin/python -m pytest backend/tests/test_compatible_bundle.py::test_checked_manifest_matches_declared_environment backend/tests/test_portable_scientific_hash.py::test_clean_isolated_copy_passes_bundle_verification -q -ra --junitxml=audit-output/2026-10-04-prompt5-14c02de54f/reproduce-failures.xml` | 1 |
| `release-gate` | `backend/.venv/bin/python scripts/release_status.py --run-required --candidate-sha 1dc7557da49f38e831b382545044b00a481507b6 --json` | 1 |
| `prepare-evaluation-copy` | `backend/.venv/bin/python audit-output/2026-10-04-prompt5-14c02de54f/prepare_evaluation_copy.py` | 0 |
| `cohort-prepare` | `backend/.venv/bin/python audit-output/2026-10-04-prompt5-14c02de54f/evaluation-copy/scripts/benchmark_external.py prepare` | 0 |
| `cohort-fetch-resume` | `backend/.venv/bin/python audit-output/2026-10-04-prompt5-14c02de54f/evaluation-copy/scripts/benchmark_external.py fetch --resume` | 0 |
| `cohort-evaluate-resume` | `backend/.venv/bin/python audit-output/2026-10-04-prompt5-14c02de54f/evaluation-copy/scripts/benchmark_external.py evaluate --resume` | 0 |
| `compare-evaluation` | `backend/.venv/bin/python audit-output/2026-10-04-prompt5-14c02de54f/compare_evaluation.py` | 0 |
| `f4-fresh-replay` | `backend/.venv/bin/python audit-output/2026-10-04-prompt5-14c02de54f/replay_f4.py` | 0 |
| `write-evaluation-package` | `backend/.venv/bin/python audit-output/2026-10-04-prompt5-14c02de54f/write_evaluation_package.py` | 0 |
| `current-evidence-regression-red` | `backend/.venv/bin/python -m pytest backend/tests/test_current_candidate_evaluation.py -q -ra --junitxml=audit-output/2026-10-04-prompt5-14c02de54f/current-evidence-regression-red.xml` | 1 |
| `current-evidence-implementation-check` | `backend/.venv/bin/python -m pytest backend/tests/test_current_candidate_evaluation.py -q -ra --junitxml=audit-output/2026-10-04-prompt5-14c02de54f/current-evidence-implementation-check.xml` | 1 |
| `build-current-compatible-manifest` | `backend/.venv/bin/python scripts/build_compatible_bundle.py` | 0 |
| `manifest-targeted` | `backend/.venv/bin/python -m pytest backend/tests/test_current_candidate_evaluation.py backend/tests/test_compatible_bundle.py backend/tests/test_portable_scientific_hash.py backend/tests/test_external_benchmark.py -q -ra --junitxml=audit-output/2026-10-04-prompt5-14c02de54f/manifest-targeted.xml` | 0 |
| `manifest-targeted-final` | `backend/.venv/bin/python -m pytest backend/tests/test_current_candidate_evaluation.py backend/tests/test_compatible_bundle.py backend/tests/test_portable_scientific_hash.py backend/tests/test_external_benchmark.py -q -ra --junitxml=audit-output/2026-10-04-prompt5-14c02de54f/manifest-targeted-final.xml` | 0 |
| `validator-after` | `backend/.venv/bin/python scripts/verify_compatible_bundle.py --json` | 0 |
| `backend-full-after` | `backend/.venv/bin/python -m pytest backend/tests -q -ra --junitxml=audit-output/2026-10-04-prompt5-14c02de54f/backend-full-after.xml` | 0 |
| `clean-copy` | `backend/.venv/bin/python audit-output/2026-10-04-prompt5-14c02de54f/verify_clean_candidate.py` | 0 |
| `release-gate-after` | `backend/.venv/bin/python scripts/release_status.py --run-required --candidate-sha 1dc7557da49f38e831b382545044b00a481507b6 --json` | 1 |

### Final Git and file-scope receipt

The final working-tree snapshot is `git-status-final.txt` (4207 bytes); the full tracked diff is `git-diff-final.txt` (388056 bytes). The staged diff is empty (0 bytes). `scope-after.json` and `scope-changes.json` compare every one of the 429 starting files; exactly five changed. `new-candidate-files.json` gives the exact 12 new intended files and hashes. All other starting file bytes matched their recorded SHA-256.
