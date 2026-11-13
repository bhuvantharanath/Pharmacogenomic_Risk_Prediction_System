# Phase 10 — what a commit would stage, and the one decision it needs

Prepared 2026-11-13. Nothing is staged or committed. This exists because the
working lists live in a session scratchpad that is wiped daily, and because the
decision below is the owner's.

Verified by `git add --dry-run --pathspec-from-file=` with
`GIT_LITERAL_PATHSPECS=1`: **every listed path is stageable**, counts matching
exactly (54 / 28 / 3). That check is the one that matters, because the macOS
filesystem is case-insensitive and a wrong-case path passes an `-e` test while
git silently skips it.

Secret scan: **clean**. 84 paths against the 5 values in the root `.env` and
`infra/deploy.env`. The scanner was recreated today and self-tested first — it
loaded 5 values, reported nothing on a committed file, and caught a real value
planted in a throwaway file outside the repository. A scanner that had not been
shown to catch a planted value would have told us nothing by reporting clean.

## The decision

The AWS Open Data registry lists the licence for the DRAGEN 1kGP reanalysis as
**`License: "TBD"`** — confirmed today from the authoritative source,
`awslabs/open-data-registry/datasets/ilmn-dragen-1kgp.yaml`, not just the
rendered page. There is no licence, terms, or notice object anywhere in the
bucket.

What that covers and does not:

- The **samples** are 1000 Genomes participants, consented and openly
  published. The repository already states this position in
  `test-data/README.md`, and already commits a 1000 Genomes-derived VCF
  (`test-data/demo/demo_na12273_1000g.vcf`, from the NYGC phased panel).
- The **reanalysis** is Illumina's work, and Illumina has stated no terms for
  it. What these files take from it is small — the genotype at 484 positions
  for eight samples, about 375 KB — but "small" is not "licensed".

So: **may the DRAGEN-derived files be published in a public repository?**

### Why this gates the whole commit rather than just the data

The data is load-bearing for code that is also in the change set:

- `app/lib/widgets/sample_files.dart` names the four files in
  `app/assets/samples/`, and the three old synthetic assets are deleted in the
  same change. Committing the code without the assets leaves the picker
  pointing at files that are not there.
- `backend/tests/test_showcase_inputs.py` asserts that `demo/samples/` is
  non-empty and that every shipped sample declines CYP2D6. Without the data it
  fails in CI.

**If the answer is yes**, stage all three lists and commit as one change.

**If the answer is no**, the fallback is not just "drop list B": it needs
`test_showcase_inputs.py` to skip when `demo/samples/` is absent, and the
asset swap in `sample_files.dart` reverted so the picker keeps working on the
old synthetic files — which would also mean re-recording the scientific bundle
a third time, since `sample_files.dart` is in the hashed core. Say the word and
I will do that instead; it is a bigger change than leaving the files out.

A third option, if you want the record to land while the licence is settled:
commit only `demo/*.md` and the verification artifacts, which stand alone, and
hold all the code and data together. That costs nothing and unblocks nothing.

## List A — 54 paths, licence-independent

Application and client source (5): `app/lib/generated/capabilities.g.dart`,
`app/lib/widgets/outside_call_field.dart`, `app/lib/widgets/sample_files.dart`,
`backend/app/data/capabilities.json`, `backend/app/outside_calls.py`.

Tests (5): `app/test/live_render_test.dart`, `app/test/outside_call_test.dart`,
`app/test/keyboard_only_test.dart`, `backend/tests/test_demo_script.py`,
`backend/tests/test_showcase_inputs.py`.

Tooling (3): `scripts/build_showcase_inputs.py`,
`scripts/compatible_bundle.py`, `scripts/run_demo.py`.

Scientific identity (1): `backend/app/data/compatible_bundle.json`.

Re-run artifacts (2): `reports/integration_fidelity.json`,
`reports/testvcf_fidelity.json`.

Refreshed demo payloads (6): `test-data/demo/outputs/S{1..6}_*.json`.

Evaluation packages (22): every file under
`test-data/benchmark/current-candidate-2026-11-12-phase10s4/` and
`.../phase10s5/`.

Documentation (10): `demo/ACCEPTANCE.md`, `COHORT.md`, `DATA_SOURCES.md`,
`PRESENTATION_RUNBOOK.md`, `PRODUCT_POLISH.md`, `UNKNOWN_LEDGER.md`,
`VERIFICATION.md`, `COMMIT_PLAN.md`, and the three
`protected_files*.sha256` baselines.

> `test-data/demo/outputs/S3_cyp2d6_na12273.json` and
> `S4_dpyd_indeterminate.json` are deliberately **not** listed. They are
> tracked, unmodified, and still carry the pre-Phase-9 seven-gene shape —
> `run_demo.py` writes different filenames, so this phase never touched them.
> They are a latent version of the trap that caught `live_render_test.dart`:
> worth refreshing, but not by including an unchanged file in this commit.

## List B — 28 paths, licence-sensitive, ~375 KB

- `demo/samples/` — 24 files: 7 showcase VCFs plus the ambiguity exhibit, each
  with a `.provenance.json` and a `.cyp2d6.json` sidecar.
- `app/assets/samples/` — 4 files: `HG00525.vcf`, `HG02661.vcf`,
  `HG02684.vcf`, `HG02684_variants_only.vcf`.

## List C — 3 deletions

The old synthetic assets the picker no longer offers:
`pharmaguard_sample_normal.vcf`, `pharmaguard_sample_reduced_function.vcf`,
`pharmaguard_sample_variants_only.vcf`. They remain in `test-data/demo/`, where
`run_demo.py` still uses them and now labels them on screen.

## Not in any list, on purpose

`audit/phase9/`, `audit-output/`, `Report/`, `Report.zip`, `output/`, `tmp/`,
`paper/`, `pharmaguard.pdf`, `PharmaGuard_IEEE_Research_Paper.docx`,
`test-data/vcf-library-*`, `test-data/demo-showcase/`, `.claude/`, and the
untracked copies of `RELEASE-READINESS-REMEDIATION-PROMPTS.md` — per the
standing commit-scope rule, which exists because an earlier blanket
`git add -A` swept exactly these in.

## State at the time of writing

Backend **1271 passed**, client **499 passed**, bundle verifier **PASS**,
`release_status.py --run-required` **ready** (required checks True, artifact
hashes match True). Fifteen of the seventeen frozen invariant files are
byte-identical to `fdb27cb`; the two that moved are the CYP2D6 caller list and
the sentence that names it.

Nothing has been pushed. The deployed API remains `5ff0022`, which predates
§4, so codeine is Unknown on the public URL until a deploy.
