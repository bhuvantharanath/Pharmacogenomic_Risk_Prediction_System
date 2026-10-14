# Reproducible scientific record

The authoritative machine-readable identity is
`backend/app/data/compatible_bundle.json`. It binds the research result to one
compatible set of PharmCAT engine/data bytes, allele and phenotype definitions,
prescribing-guidance rows, evidence requirements, mapping rules, capability
registry, corpus, explanation store, review state, benchmark artifacts, and
declared runtime dependencies.

Verify it from the repository root:

```bash
backend/.venv/bin/python scripts/verify_compatible_bundle.py
```

A changed byte, missing component, source-row version change, or report-count
change makes the verifier fail. `scripts/release_status.py` consumes this result
as a required final-release prerequisite. The manifest is regenerated only by
`scripts/build_compatible_bundle.py` during a controlled whole-bundle upgrade;
regeneration is not a remedy for an unexplained mismatch.

## Portable application identity (hash policy v2)

`scripts/scientific_hash_policy.json` is the versioned allowlist for the
scientific application core. Its 90 paths include backend interpretation code
and data, the capability and position rules, explanation content and approval
data, Flutter application source, the mechanism corpus, dependency lockfiles,
and deployment configuration. The compatible-bundle manifest is excluded from
its own core digest and is checked separately. New scientific/application
sources must be deliberately enrolled in this policy during a controlled
upgrade; unlisted files do not enter the digest, even if they have a source-code
extension. The policy file itself is pinned by the bundle manifest.

For each listed input, the v2 hash reads raw bytes. It hashes a UTF-8 domain
identifier followed by a NUL byte, then each normalized repository-relative
POSIX path, NUL, file bytes, NUL, in lexical path order. Absolute parent paths,
file timestamps, Git metadata, Finder files, editor backups, caches, logs,
temporary output, and audit files do not contribute. Missing files and
symlinked inputs fail verification. The release candidate hash uses the same
method with a separate domain and explicitly includes the bundle manifest and
release gate files.

The external benchmark's original v1 application digest remains in its frozen
benchmark manifest. `scripts/application_hash_migration.json` records that the
old 91-file local walk contained exactly these 90 versioned inputs plus the
ignored `backend/app/.DS_Store`; it preserves both the old digest and the
portable v2 digest. The values are different hash identities and are not
compared as if they were equal. This migration did not rerun the benchmark or
change its truth, results, or denominators. A clean copy of the candidate's
declared files can now reproduce the v2 bundle without the Finder file.

## Current frozen result

- Evidence type: independently characterized CDC GeT-RM/PGx consensus truth
  paired with 1000 Genomes high-coverage genomic evidence.
- Sample unit: 208 individuals. The 1,456 sample×gene rows are repeated
  observations within individuals and are not independent people.
- Truth denominator: 596 evaluable diplotypes across seven genes; per-gene
  denominators and intervals are reported separately.
- Upstream layer: pinned PharmCAT 3.4.0 calls are compared with consensus truth.
- Application layer: 0 benchmark sample×gene rows meet the current evidence
  contract because the available genomic slices are polymorphic-only; the
  application abstains rather than infer omitted reference calls.
- Limitation: this supports bounded analytical statements only. It does not
  demonstrate clinical utility, calibrated patient risk, or prescribing authority.

The detailed metrics and discrepancy classes are in
`reports/external_analytical_benchmark.md`. Earlier n=1, synthetic-mask,
constructed-allele, population-frequency, and live-deployment reports remain in
the repository as historical/version-specific records and are labelled as such.

## Source deltas and upgrade policy

The pinned PharmCAT 3.4.0 data bundle has a single embedded data version and
hashes for each in-scope definition. Its July 13, 2026 data retains the older
CYP2C19 `*2` companion-base requirements. The manifest records the July 31
PharmVar 6.2.28 definition update as `not_included_in_pinned_bundle`, with
`local_bundle_status: coherent_older_definition` and `impact: known_version_delta`.
The current external core definition is c.681G>A alone; ClinPGx announced its
aligned representation on August 7. The pinned executable behavior is unchanged.
This is a known source-version gap, not an assertion that coherent version
pinning is itself incorrect. Exact primary-source dates, versions, allele bases,
and the controlled upgrade path are in
[the definition-delta record](../reports/cyp2c19_definition_delta.md).

The September 30, 2026 source check found PharmVar 6.2.29 and PharmCAT 3.4.0 as
their respective current versions. No newer official PharmCAT release was
available to evaluate for an upgrade. The manifest also tracks TPMT terminology
through its pinned definition identity. It records that the current DPYD prescribing row is
the pinned finalized material; pending or newer DPYD material is not mixed into
this baseline.

These deltas are not patched into isolated YAML or application rules. An upgrade
must update the compatible engine/data/definitions/guidance set, regenerate any
affected evidence and mapping artifacts, run targeted delta fixtures and all
regression tests, rerun the independent benchmark without tuning on its final
set, regenerate the manifest, and satisfy the explanation/review gate. Until
that process completes, the current coherent baseline remains authoritative.
