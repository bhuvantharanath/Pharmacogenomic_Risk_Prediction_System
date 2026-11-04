# Current candidate evaluation

Evaluation ID: `pharmaguard-external-current-candidate-2026-11-04-b2`.
Current portable scientific core: `ba8c7a21cad84899e48bb2514ae258a614d8be8361005a61b44576a6870e20b7`.
Historic frozen protocol: `093fda85438a7b5408fb3fbc338962251a599c1f27aaf12c8c1dd5223968367e`. Truth and cohort locks are unchanged.

Why a new version: B2: responses carry content hashes of the jar's CPIC data and allele definitions; provenance note names the weekly knowledge watch The changed file is inside the scientific-core allowlist, so the previous evaluation (`pharmaguard-external-current-candidate-2026-11-04-b1`) no longer bound the candidate. It is preserved unchanged.

The 208 public-cohort PharmCAT reports were reused only after all 208 report hashes, the exact combined VCF, pinned JAR, truth table, workbook and cohort lock were checked. No new 208-person PharmCAT caller run is claimed. The application reprojected each of the 208 people and rescored all 1,456 sample-gene rows in an isolated copy. The two frozen F4 read-backed VCF controls were replayed through a local API started from the candidate; they are bounded positives, not a replacement for the cohort.

Compared with the historical run and the previous evaluation, per-gene metrics, exclusions and discrepancies are equal. The only changed field in all 1,456 eligibility rows is the temporary single-sample VCF SHA-256, explained by the path-bearing bcftools header.

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
