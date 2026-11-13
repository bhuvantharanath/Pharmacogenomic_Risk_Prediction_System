# Current candidate evaluation — Phase 10 §5 follow-up

Evaluation ID: `pharmaguard-external-current-candidate-2026-11-12-phase10s6`.
Current portable scientific core: `4e34250123515a1f38aba593b0fd23060ba54d2e7337b6a423a387459b9470e8`.
Historic frozen protocol: `093fda85438a7b5408fb3fbc338962251a599c1f27aaf12c8c1dd5223968367e`. Truth and cohort locks are unchanged.

Why a new version: Phase 10 §5 follow-up added one name to the accepted CYP2D6 outside-call list — four callers to five — so that a diplotype produced by DRAGEN's targeted CYP2D6 caller can be supplied beside a VCF under its own name instead of under another tool's, and the matching string in the client dropdown. Both files (`backend/app/outside_calls.py`, `app/lib/widgets/outside_call_field.dart`) are inside the scientific-core allowlist, so the previous evaluation no longer bound the candidate. It is preserved unchanged as `current-candidate-2026-11-07-f20/`.

What did NOT change, and why that was expected: the benchmark supplies no outside calls, so the accepted-caller list is never read on any benchmark path. Nothing about the gate, the grammar, the pinned gene, the phenotype mapping or the refusal to call CYP2D6 from a VCF was touched. This rebind therefore declares no eligibility change of its own.

The 208 public-cohort PharmCAT reports were reused only after all 208 report hashes, the exact combined VCF, pinned JAR, truth table, workbook and cohort lock were checked. No new 208-person PharmCAT caller run is claimed. The application reprojected each of the 208 people and rescored all 1,456 sample-gene rows using the candidate in an isolated copy. The two frozen F4 read-backed VCF controls were separately replayed through the live local API and pinned caller; they are bounded positives, not a replacement for the cohort.

Compared with the 2026-11-07-f20 evaluation, per-gene metrics, exclusions and discrepancies are byte-identical. The only changed field in all 1,456 eligibility rows is the temporary single-sample VCF SHA-256; a representative same-input replay shows the path-bearing bcftools command header changes the file bytes while genotype records stay identical. Against the historical benchmark the package also carries the eligibility and discrepancy wording that Phase 9 B5 and B10 already declared, recorded here as inherited rather than new.

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
