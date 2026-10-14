# Current candidate evaluation, version 3

Evaluation ID: `pharmaguard-external-current-candidate-v3-2026-10-14`.
Current portable scientific core: `bd20329df0c975a549f91640b785e35b9c5a7fe2afd081ea585413463c29a38f`.
Historic frozen protocol: `093fda85438a7b5408fb3fbc338962251a599c1f27aaf12c8c1dd5223968367e`. Truth and cohort locks are unchanged.

Why a new version: the 2026-10-14 remediation changed only user-facing wording (provenance disclaimer, CYP2D6 boundary, missing-position attribution, unusable-genotype explanation, drug-scope caption) and kept opened result rows alive while scrolling. Those files are inside the scientific-core allowlist, so the previous evaluation no longer bound the candidate. It is preserved unchanged as `current-candidate-2026-10-04/`.

The 208 public-cohort PharmCAT reports were reused only after all 208 report hashes, the exact combined VCF, pinned JAR, truth table, workbook and cohort lock were checked. No new 208-person PharmCAT caller run is claimed. The application reprojected each of the 208 people and rescored all 1,456 sample-gene rows using the frozen fixed candidate in an isolated copy. The two frozen F4 read-backed VCF controls were separately replayed through the live local API and pinned caller; they are bounded positives, not a replacement for the cohort.

Compared with both the historical run and the 2026-10-04 evaluation, per-gene metrics, exclusions and discrepancies are equal. The only changed field in all 1,456 eligibility rows is the temporary single-sample VCF SHA-256; a representative same-input replay shows the path-bearing bcftools command header changes the file bytes while genotype records stay identical.

| Gene | Evaluable truth rows | Application eligible | Application abstention |
|---|---:|---:|---:|
| CYP2C19 | 101 | 0 | 101 |
| CYP2C9 | 100 | 0 | 100 |
| DPYD | 83 | 0 | 83 |
| NUDT15 | 11 | 0 | 11 |
| SLCO1B1 | 87 | 0 | 87 |
| TPMT | 97 | 0 | 97 |
| CYP2D6 | 117 | 0 | 117 |

The source VCF is polymorphic-filtered. Missing required coordinates remain unknown. Independent phenotype and actionability truth are unavailable in this cohort, so false reassurance and false warning are not estimable. No pooled accuracy or clinical utility claim follows. The F4 read-backed controls cover only the qualified CYP2C19/clopidogrel path; ACS/PCI is a guideline qualifier, not a donor diagnosis.

Current generated explanations remain unapproved and use deterministic runtime fallback. Human adjudication is outstanding; this evaluation does not close the release gate.
