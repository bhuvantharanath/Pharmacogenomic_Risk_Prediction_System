# Current candidate evaluation

Evaluation ID: `pharmaguard-external-current-candidate-2026-11-05-b7`.
Current portable scientific core: `5c1df3613fde11c0848c73fbfcb6f94561334dcf7e2f872e3c27d9f1bd07a37e`.
Historic frozen protocol: `093fda85438a7b5408fb3fbc338962251a599c1f27aaf12c8c1dd5223968367e`. Truth and cohort locks are unchanged.

Why a new version: Phase 9 B7 changed backend/app (a CORS-permissive /health reporting build, data identity and origin_allowed; derived Pages preview origins) and app/lib (connectivity states and error headings), which the scientific core includes. The changed file is inside the scientific-core allowlist, so the previous evaluation (`pharmaguard-external-current-candidate-2026-11-05-b6`) no longer bound the candidate. It is preserved unchanged.

The 208 public-cohort PharmCAT reports were reused only after all 208 report hashes, the exact combined VCF, pinned JAR, truth table, workbook and cohort lock were checked. No new 208-person PharmCAT caller run is claimed. The application reprojected each of the 208 people and rescored all 1,456 sample-gene rows in an isolated copy. The two frozen F4 read-backed VCF controls were replayed through a local API started from the candidate; they are bounded positives, not a replacement for the cohort.

Compared with the previous evaluation, per-gene metrics, exclusions and discrepancies are equal, and the only changed field in all 1,456 eligibility rows is the temporary single-sample VCF SHA-256, explained by the path-bearing bcftools header. Compared with the historical run, metrics, exclusions and discrepancy classifications are equal, and eligibility and discrepancy detail also differ exactly as earlier re-binds declared, carried forward from the previous package's verified comparison: eligibility_reason in 208 CYP2C9 rows (Phase 9 B5: a refusal names the missing genes a file could supply before the limitation, and warfarin's limitation now quotes CPIC's algorithm text.); missing_dependency_genes in 208 CYP2C9 rows (Phase 9 B5: warfarin depends on CYP2C9 and VKORC1; the benchmark slices carry no chr16 rows, so VKORC1 is missing for every individual.); detail in 100 CYP2C9 rows (Phase 9 B5: the discrepancy detail repeats the warfarin eligibility reason, which now names CYP2C9 and VKORC1 and quotes CPIC.). The re-bind asserts that no other value changed.

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
