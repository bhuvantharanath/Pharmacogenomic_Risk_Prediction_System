# Current candidate evaluation — Phase 10 §5

Evaluation ID: `pharmaguard-external-current-candidate-2026-11-12-phase10s5`.
Current portable scientific core: `b747d41c71f38e59be8935e4cfa03b3887e695a74bfc8255b8982f09ed1f1afb`.
Historic frozen protocol: `093fda85438a7b5408fb3fbc338962251a599c1f27aaf12c8c1dd5223968367e`. Truth and cohort locks are unchanged.

Why a new version: Phase 10 §5 replaced the four hand-built sample files the web client offered with real public genomes from the showcase cohort, and named the fifth accepted CYP2D6 caller in codeine's capability limitation. Three scientific-core files changed: `backend/app/data/capabilities.json`, its generated client constants `app/lib/generated/capabilities.g.dart`, and `app/lib/widgets/sample_files.dart`. The 2026-11-12-phase10s4 package is preserved unchanged.

What this rebind declares, with exact values and row counts: the limitation string is repeated verbatim into every CYP2D6 eligibility reason and discrepancy detail, so naming the fifth caller changes 208 eligibility rows and 117 discrepancy rows. Nothing else moved. Every scored metric, every exclusion and every discrepancy CLASSIFICATION is unchanged; no genotype, phenotype, label or abstention differs.

The 208 public-cohort PharmCAT reports were reused only after all 208 report hashes, the exact combined VCF, pinned JAR, truth table, workbook and cohort lock were checked. No new 208-person PharmCAT caller run is claimed. The application reprojected each of the 208 people and rescored all 1,456 sample-gene rows using the candidate in an isolated copy. The two frozen F4 read-backed VCF controls were separately replayed through the live local API and pinned caller; they are bounded positives, not a replacement for the cohort.

The only other changed field in all 1,456 eligibility rows is the temporary single-sample VCF SHA-256; a representative same-input replay shows the path-bearing bcftools command header changes the file bytes while genotype records stay identical.

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

This evaluation re-binds an identity, not a result. It establishes nothing new about accuracy, and it does not close the release gate. Current generated explanations remain unapproved and use deterministic runtime fallback; human adjudication is outstanding.
