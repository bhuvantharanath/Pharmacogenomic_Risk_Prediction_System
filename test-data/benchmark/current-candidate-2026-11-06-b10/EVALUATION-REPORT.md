# Current candidate evaluation

Evaluation ID: `pharmaguard-external-current-candidate-2026-11-06-b10`.
Current portable scientific core: `7da41669dceeedc78c72d6b08344ef947423c9b1712f93feec47688902a127aa`.
Historic frozen protocol: `093fda85438a7b5408fb3fbc338962251a599c1f27aaf12c8c1dd5223968367e`. Truth and cohort locks are unchanged.

Why a new version: Phase 9 B10 added CYP2D6 outside calls (backend/app/outside_calls.py; pharmcat_runner, cpic_engine, coverage, main, models, explanation; the codeine capability), one codeine phrase in label_mapping.yaml, and the client's input and provenance; no supplied call is involved in the evaluation. Declared: the reworded codeine limitation in CYP2D6 eligibility and discrepancy detail (audit/phase9/B10_ZR_AMENDMENT.md). The changed file is inside the scientific-core allowlist, so the previous evaluation (`pharmaguard-external-current-candidate-2026-11-06-b9`) no longer bound the candidate. It is preserved unchanged.

The 208 public-cohort PharmCAT reports were reused only after all 208 report hashes, the exact combined VCF, pinned JAR, truth table, workbook and cohort lock were checked. No new 208-person PharmCAT caller run is claimed. The application reprojected each of the 208 people and rescored all 1,456 sample-gene rows in an isolated copy. The two frozen F4 read-backed VCF controls were replayed through a local API started from the candidate; they are bounded positives, not a replacement for the cohort.

Compared with the historical run and the previous evaluation, per-gene metrics, exclusions and discrepancy classifications are equal. Besides the temporary single-sample VCF SHA-256 in all 1,456 eligibility rows, the changes are exactly those declared before the run: eligibility_reason in 208 CYP2D6 rows (Phase 9 B10: codeine's capability limitation now says guidance comes only from a CYP2D6 diplotype supplied by a dedicated caller; the evaluation records that limitation as CYP2D6's reason. Owner decision: "Accept, declare it" (audit/phase9/B10_ZR_AMENDMENT.md).); detail in 117 CYP2D6 rows (Phase 9 B10: codeine's capability limitation now says guidance comes only from a CYP2D6 diplotype supplied by a dedicated caller; the evaluation records that limitation as CYP2D6's reason, and the discrepancy detail repeats it. Owner decision: "Accept, declare it" (audit/phase9/B10_ZR_AMENDMENT.md).). The re-bind asserts that no other value changed. Against the historical run they compose with earlier re-binds' declarations: eligibility_reason in 208 CYP2C9 rows (Phase 9 B5: a refusal names the missing genes a file could supply before the limitation, and warfarin's limitation now quotes CPIC's algorithm text.); missing_dependency_genes in 208 CYP2C9 rows (Phase 9 B5: warfarin depends on CYP2C9 and VKORC1; the benchmark slices carry no chr16 rows, so VKORC1 is missing for every individual.); eligibility_reason in 208 CYP2D6 rows (Phase 9 B10: codeine's capability limitation now says guidance comes only from a CYP2D6 diplotype supplied by a dedicated caller; the evaluation records that limitation as CYP2D6's reason. Owner decision: "Accept, declare it" (audit/phase9/B10_ZR_AMENDMENT.md).); detail in 100 CYP2C9 rows (Phase 9 B5: the discrepancy detail repeats the warfarin eligibility reason, which now names CYP2C9 and VKORC1 and quotes CPIC.); detail in 117 CYP2D6 rows (Phase 9 B10: codeine's capability limitation now says guidance comes only from a CYP2D6 diplotype supplied by a dedicated caller; the evaluation records that limitation as CYP2D6's reason, and the discrepancy detail repeats it. Owner decision: "Accept, declare it" (audit/phase9/B10_ZR_AMENDMENT.md).).

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
