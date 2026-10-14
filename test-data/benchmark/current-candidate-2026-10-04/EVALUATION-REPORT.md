# Current candidate evaluation, version 2

Evaluation ID: `pharmaguard-external-current-candidate-v2-2026-10-04`.
Current portable scientific core: `38451a563c6f6cfb52257626d41700eeff3a5621ebe91b3358f878b375a6a691`.
Historic frozen protocol: `093fda85438a7b5408fb3fbc338962251a599c1f27aaf12c8c1dd5223968367e`. Truth and cohort locks are unchanged.

The 208 public-cohort PharmCAT reports were reused only after all 208 report hashes, the exact combined VCF, pinned JAR, truth table, workbook and cohort lock were checked. No new 208-person PharmCAT caller run is claimed. The application reprojected each of the 208 people and rescored all 1,456 sample-gene rows using the current dirty candidate in an isolated copy. The two frozen F4 read-backed VCF controls were separately replayed through the live local API and pinned caller; they are bounded positives, not a replacement for the cohort.

Compared with the historical run, per-gene metrics, exclusions and discrepancies are equal. The only changed field in all 1,456 eligibility rows is the temporary single-sample VCF SHA-256. A representative same-input replay shows a path-bearing bcftools command header changes the file bytes while genotype records stay identical. Historical temporary single-sample VCF bytes are unavailable for exact bytewise comparison; no exact historical projection identity is claimed.

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
