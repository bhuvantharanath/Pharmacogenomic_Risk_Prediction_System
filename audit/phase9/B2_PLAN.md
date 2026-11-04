# B2 — Knowledge provenance and staleness watcher: plan and pre-committed criteria

Written 2026-11-04 before any B2 code change.

## Facts that shape the design (checked before writing this plan)

- PharmCAT 3.4.0 records no PharmVar release number: its definition files carry
  `version: 2026-07-13-11-40`, `source: CLINPGX`, and its release notes say only
  "update from PharmVar". The response will therefore not state a PharmVar
  number; `pharmvar_release` stays empty and the note says why. Inventing one
  would break the no-fabrication rule.
- `backend/app/data/compatible_bundle.json` records the SHA-256 of the jar's
  `prescribing_guidance.json` and of each gene's definition file. Serving the
  same hashes lets a test prove the data a response was built from is the data
  that was validated (Part A verification edge E13).

## Changes

1. `GuidelineProvenance` (Pydantic and Dart, additive): `cpic_guidance_sha256`,
   `allele_definitions_version`, `allele_definitions_sha256`, `pharmvar_release`.
   Computed once per process from the jar the runner resolves, on `/analyze`,
   `/coverage` and `/provenance`. `allele_definitions_sha256` is the SHA-256 of
   the sorted lines `<member> <sha256>` over the target genes' definition files,
   so it can be recomputed from the bundle's per-file records.
2. The results/home footer shows CPIC data version + guidance hash prefix and the
   allele-definition version + hash prefix.
3. The provenance note stops saying the build "does not monitor": it states the
   weekly repository check and that a running analysis does not check freshness.
4. `scripts/cpic_snapshot.py --check-live`: fetch CPIC's current tables, compare
   them with the vendored snapshot (content, order-independent), check
   PharmCAT's latest GitHub release against the pinned 3.4.0; exit 1 on any
   change, 2 when the check could not run; write a markdown summary.
5. `.github/workflows/knowledge-watch.yml`: weekly + manual; opens (or comments
   on) one issue when something changed; the job is red on change and on
   failure to check.

## Acceptance criteria (pre-committed)

| id | criterion |
|---|---|
| AC1 | `/analyze`, `/coverage`, `/provenance` carry the four new fields; the hashes equal values recomputed independently from the pinned jar, and `cpic_guidance_sha256` / `allele_definitions_sha256` equal the values derived from `compatible_bundle.json` |
| AC2 | Every new Pydantic field is read by the Dart model (`test_client_parity.py`); a Dart test parses them and asserts the footer shows CPIC data version, guidance hash prefix and definition version |
| AC3 | Watcher, offline mode: identical tables → no change, exit 0; a mutated recommendation text, a changed allele function, and an added row are each reported, exit 1 — "a deliberately stale table makes CI red" |
| AC4 | PharmCAT release watch: same tag → no change; a newer tag → reported, exit 1 |
| AC5 | Workflow: weekly schedule + `workflow_dispatch`; `permissions` limited to `contents: read`, `issues: write`; a change opens or updates exactly one issue and fails the job; a failed check (exit 2) fails the job; no `|| true` |
| AC6 | The provenance note no longer claims the build does not monitor; it names the weekly check and says a running analysis does not check freshness |

Zero-regression condition: Part B harness vs `B1` — S1–S6 6/6 labels; cohort
0 label shifts; 74 test VCFs 0 mismatches. Provenance fields may change
response bodies; no label may change.

Sabotage: (a) knowledge hashes return empty → AC1 test red; (b) the comparison
ignores text differences → AC3 test red; (c) Dart stops reading a new field →
parity test red.

If a criterion fails, stop and report rather than adjust it.
