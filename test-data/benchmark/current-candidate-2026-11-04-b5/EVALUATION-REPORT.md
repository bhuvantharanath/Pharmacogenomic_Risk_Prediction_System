# Current candidate evaluation

Evaluation ID: `pharmaguard-external-current-candidate-2026-11-04-b5`.
Current portable scientific core: `5fba129eec8150a4c0d38cad0bde2ae07a7c18b2f1ee3fb6a7d2007f4d6a47df`.
Historic frozen protocol: `093fda85438a7b5408fb3fbc338962251a599c1f27aaf12c8c1dd5223968367e`. Truth and cohort locks are unchanged.

Why a new version: B5: VKORC1 and CYP4F2 are parsed and coverage-gated; warfarin shows per-gene findings and quotes CPIC, label stays Unknown The changed file is inside the scientific-core allowlist, so the previous evaluation (`pharmaguard-external-current-candidate-2026-11-04-b4`) no longer bound the candidate. It is preserved unchanged.

The 208 public-cohort PharmCAT reports were reused only after all 208 report hashes, the exact combined VCF, pinned JAR, truth table, workbook and cohort lock were checked. No new 208-person PharmCAT caller run is claimed. The application reprojected each of the 208 people and rescored all 1,456 sample-gene rows in an isolated copy. The two frozen F4 read-backed VCF controls were replayed through a local API started from the candidate; they are bounded positives, not a replacement for the cohort.

Compared with the historical run and the previous evaluation, per-gene metrics, exclusions and discrepancy classifications are equal. Besides the temporary single-sample VCF SHA-256 in all 1,456 eligibility rows, the changes are exactly those declared before the run: eligibility_reason in 208 CYP2C9 rows (Phase 9 B5: a refusal names the missing genes a file could supply before the limitation, and warfarin's limitation now quotes CPIC's algorithm text.); missing_dependency_genes in 208 CYP2C9 rows (Phase 9 B5: warfarin depends on CYP2C9 and VKORC1; the benchmark slices carry no chr16 rows, so VKORC1 is missing for every individual.); detail in 100 CYP2C9 rows (Phase 9 B5: the discrepancy detail repeats the warfarin eligibility reason, which now names CYP2C9 and VKORC1 and quotes CPIC.). The re-bind asserts that no other value changed.

| Gene | Evaluable truth rows | Application input eligible (individuals) |
|---|---:|---:|
| CYP2C19 | 101 | 0/208 |
| CYP2C9 | 100 | 0/208 |
| DPYD | 83 | 0/208 |
| NUDT15 | 11 | 0/208 |
| SLCO1B1 | 87 | 0/208 |
| TPMT | 97 | 0/208 |
| CYP2D6 | 117 | 0/208 |

The source VCF is polymorphic-filtered; missing required coordinates remain unknown. No pooled accuracy or clinical utility claim follows. Generated explanations remain unapproved and use the deterministic runtime fallback; human adjudication is outstanding.
