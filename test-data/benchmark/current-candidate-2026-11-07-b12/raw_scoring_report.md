# Independent external analytical benchmark

> Research/educational analytical evaluation only. This is not clinical validation,
> clinical utility evidence, a calibrated patient-risk estimate, or prescribing authority.

## Frozen sources and cohort

- Frozen protocol: `093fda85438a7b5408fb3fbc338962251a599c1f27aaf12c8c1dd5223968367e`.
- CDC GeT-RM truth: [Consolidated_PGx-HLA_table_1-22-25-V4.xlsx](https://www.cdc.gov/lab-quality/media/files/2025/08/Consolidated_PGx-HLA_table_1-22-25-V4.xlsx) (`c66174befa7a7bbb6cfaf174cc500a269565407807467204bd7bc6eaae3be109`).
- Genomic evidence: [1000G_2504_high_coverage/working/20220422_3202_phased_SNV_INDEL_SV](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/working/20220422_3202_phased_SNV_INDEL_SV) (GRCh38, polymorphic-filtered VCF).
- 1000 Genomes sample manifest: `4e164b717433fc9bfc16e29b20e5b4659b4216185b3275322d421fe3d323c132` (3202 samples).
- Deterministic intersection: 208 individuals.
- Frozen sample × gene rows: 1456 (`{"evaluable": 596, "truth_blank": 816, "truth_nomenclature_not_safely_parseable": 42, "truth_unresolved_or_discordant": 2}`).
- PharmCAT reports produced: 208/208.
- Raw report hashes are retained in `pharmcat_report_manifest.json`; bulky raw reports are a local rerunnable cache.
- Missing positions were retained as absent; no omitted genotype was synthesized as reference.

## Results by gene

No pooled accuracy is reported. Each denominator is the number of unique individuals for that gene.

### CYP2C19

- Independent evaluable diplotypes: 101.
- Layer A exact concordance: 93/101 (92.1%; 95% Wilson CI 85.1–95.9%).
- Layer A candidate-compatible concordance: 94/101 (93.1%; 95% Wilson CI 86.4–96.6%).
- Layer A exact-assertion coverage: 100/101 (99.0%; 95% Wilson CI 94.6–99.8%).
- Layer A candidate-set assertion coverage: 101/101 (100.0%; 95% Wilson CI 96.3–100.0%); abstention: 0/101 (0.0%; 95% Wilson CI 0.0–3.7%).
- Layer A conditional exact accuracy: 93/100 (93.0%; 95% Wilson CI 86.3–96.6%).
- Application input eligibility: 0/208 (0.0%; 95% Wilson CI 0.0–1.8%).
- Layer B exact concordance: 0/101 (0.0%; 95% Wilson CI 0.0–3.7%).
- Layer B exact-assertion coverage: 0/101 (0.0%; 95% Wilson CI 0.0–3.7%).
- Layer B candidate-set assertion coverage: 0/101 (0.0%; 95% Wilson CI 0.0–3.7%); abstention: 101/101 (100.0%; 95% Wilson CI 96.3–100.0%).
- Layer B conditional exact accuracy: not estimable (0 denominator).
- Discrepancy classifications: `{"evidence_gate": 101, "upstream_caller_disagreement": 7, "upstream_candidate_ambiguity": 1}`.
- Phenotype concordance, false reassurance, and false warning: not estimable; the independent
  source does not supply phenotype/drug-context truth, and no label was derived from the systems under test.

### CYP2C9

- Independent evaluable diplotypes: 100.
- Layer A exact concordance: 79/100 (79.0%; 95% Wilson CI 70.0–85.8%).
- Layer A candidate-compatible concordance: 100/100 (100.0%; 95% Wilson CI 96.3–100.0%).
- Layer A exact-assertion coverage: 79/100 (79.0%; 95% Wilson CI 70.0–85.8%).
- Layer A candidate-set assertion coverage: 100/100 (100.0%; 95% Wilson CI 96.3–100.0%); abstention: 0/100 (0.0%; 95% Wilson CI 0.0–3.7%).
- Layer A conditional exact accuracy: 79/79 (100.0%; 95% Wilson CI 95.4–100.0%).
- Application input eligibility: 0/208 (0.0%; 95% Wilson CI 0.0–1.8%).
- Layer B exact concordance: 0/100 (0.0%; 95% Wilson CI 0.0–3.7%).
- Layer B exact-assertion coverage: 0/100 (0.0%; 95% Wilson CI 0.0–3.7%).
- Layer B candidate-set assertion coverage: 0/100 (0.0%; 95% Wilson CI 0.0–3.7%); abstention: 100/100 (100.0%; 95% Wilson CI 96.3–100.0%).
- Layer B conditional exact accuracy: not estimable (0 denominator).
- Discrepancy classifications: `{"evidence_gate": 100, "upstream_candidate_ambiguity": 21}`.
- Phenotype concordance, false reassurance, and false warning: not estimable; the independent
  source does not supply phenotype/drug-context truth, and no label was derived from the systems under test.

### DPYD

- Independent evaluable diplotypes: 83.
- Layer A exact concordance: 0/83 (0.0%; 95% Wilson CI 0.0–4.4%).
- Layer A candidate-compatible concordance: 0/83 (0.0%; 95% Wilson CI 0.0–4.4%).
- Layer A exact-assertion coverage: 83/83 (100.0%; 95% Wilson CI 95.6–100.0%).
- Layer A candidate-set assertion coverage: 83/83 (100.0%; 95% Wilson CI 95.6–100.0%); abstention: 0/83 (0.0%; 95% Wilson CI 0.0–4.4%).
- Layer A conditional exact accuracy: 0/83 (0.0%; 95% Wilson CI 0.0–4.4%).
- Application input eligibility: 0/208 (0.0%; 95% Wilson CI 0.0–1.8%).
- Layer B exact concordance: 0/83 (0.0%; 95% Wilson CI 0.0–4.4%).
- Layer B exact-assertion coverage: 0/83 (0.0%; 95% Wilson CI 0.0–4.4%).
- Layer B candidate-set assertion coverage: 0/83 (0.0%; 95% Wilson CI 0.0–4.4%); abstention: 83/83 (100.0%; 95% Wilson CI 95.6–100.0%).
- Layer B conditional exact accuracy: not estimable (0 denominator).
- Discrepancy classifications: `{"evidence_gate": 83, "truth_output_nomenclature_mismatch": 83}`.
- Phenotype concordance, false reassurance, and false warning: not estimable; the independent
  source does not supply phenotype/drug-context truth, and no label was derived from the systems under test.

### NUDT15

- Independent evaluable diplotypes: 11.
- Layer A exact concordance: 6/11 (54.5%; 95% Wilson CI 28.0–78.7%).
- Layer A candidate-compatible concordance: 6/11 (54.5%; 95% Wilson CI 28.0–78.7%).
- Layer A exact-assertion coverage: 11/11 (100.0%; 95% Wilson CI 74.1–100.0%).
- Layer A candidate-set assertion coverage: 11/11 (100.0%; 95% Wilson CI 74.1–100.0%); abstention: 0/11 (0.0%; 95% Wilson CI 0.0–25.9%).
- Layer A conditional exact accuracy: 6/11 (54.5%; 95% Wilson CI 28.0–78.7%).
- Application input eligibility: 0/208 (0.0%; 95% Wilson CI 0.0–1.8%).
- Layer B exact concordance: 0/11 (0.0%; 95% Wilson CI 0.0–25.9%).
- Layer B exact-assertion coverage: 0/11 (0.0%; 95% Wilson CI 0.0–25.9%).
- Layer B candidate-set assertion coverage: 0/11 (0.0%; 95% Wilson CI 0.0–25.9%); abstention: 11/11 (100.0%; 95% Wilson CI 74.1–100.0%).
- Layer B conditional exact accuracy: not estimable (0 denominator).
- Discrepancy classifications: `{"evidence_gate": 11, "upstream_caller_disagreement": 5}`.
- Phenotype concordance, false reassurance, and false warning: not estimable; the independent
  source does not supply phenotype/drug-context truth, and no label was derived from the systems under test.

### SLCO1B1

- Independent evaluable diplotypes: 87.
- Layer A exact concordance: 29/87 (33.3%; 95% Wilson CI 24.3–43.8%).
- Layer A candidate-compatible concordance: 29/87 (33.3%; 95% Wilson CI 24.3–43.8%).
- Layer A exact-assertion coverage: 44/87 (50.6%; 95% Wilson CI 40.3–60.8%).
- Layer A candidate-set assertion coverage: 87/87 (100.0%; 95% Wilson CI 95.8–100.0%); abstention: 0/87 (0.0%; 95% Wilson CI 0.0–4.2%).
- Layer A conditional exact accuracy: 29/44 (65.9%; 95% Wilson CI 51.1–78.1%).
- Application input eligibility: 0/208 (0.0%; 95% Wilson CI 0.0–1.8%).
- Layer B exact concordance: 0/87 (0.0%; 95% Wilson CI 0.0–4.2%).
- Layer B exact-assertion coverage: 0/87 (0.0%; 95% Wilson CI 0.0–4.2%).
- Layer B candidate-set assertion coverage: 0/87 (0.0%; 95% Wilson CI 0.0–4.2%); abstention: 87/87 (100.0%; 95% Wilson CI 95.8–100.0%).
- Layer B conditional exact accuracy: not estimable (0 denominator).
- Discrepancy classifications: `{"evidence_gate": 87, "truth_output_nomenclature_or_definition_mismatch": 24, "upstream_caller_disagreement": 34}`.
- Phenotype concordance, false reassurance, and false warning: not estimable; the independent
  source does not supply phenotype/drug-context truth, and no label was derived from the systems under test.

### TPMT

- Independent evaluable diplotypes: 97.
- Layer A exact concordance: 94/97 (96.9%; 95% Wilson CI 91.3–98.9%).
- Layer A candidate-compatible concordance: 94/97 (96.9%; 95% Wilson CI 91.3–98.9%).
- Layer A exact-assertion coverage: 97/97 (100.0%; 95% Wilson CI 96.2–100.0%).
- Layer A candidate-set assertion coverage: 97/97 (100.0%; 95% Wilson CI 96.2–100.0%); abstention: 0/97 (0.0%; 95% Wilson CI 0.0–3.8%).
- Layer A conditional exact accuracy: 94/97 (96.9%; 95% Wilson CI 91.3–98.9%).
- Application input eligibility: 0/208 (0.0%; 95% Wilson CI 0.0–1.8%).
- Layer B exact concordance: 0/97 (0.0%; 95% Wilson CI 0.0–3.8%).
- Layer B exact-assertion coverage: 0/97 (0.0%; 95% Wilson CI 0.0–3.8%).
- Layer B candidate-set assertion coverage: 0/97 (0.0%; 95% Wilson CI 0.0–3.8%); abstention: 97/97 (100.0%; 95% Wilson CI 96.2–100.0%).
- Layer B conditional exact accuracy: not estimable (0 denominator).
- Discrepancy classifications: `{"evidence_gate": 97, "upstream_caller_disagreement": 3}`.
- Phenotype concordance, false reassurance, and false warning: not estimable; the independent
  source does not supply phenotype/drug-context truth, and no label was derived from the systems under test.

### CYP2D6

- Independent evaluable diplotypes: 117.
- Layer A exact concordance: 0/117 (0.0%; 95% Wilson CI 0.0–3.2%).
- Layer A candidate-compatible concordance: 0/117 (0.0%; 95% Wilson CI 0.0–3.2%).
- Layer A exact-assertion coverage: 0/117 (0.0%; 95% Wilson CI 0.0–3.2%).
- Layer A candidate-set assertion coverage: 0/117 (0.0%; 95% Wilson CI 0.0–3.2%); abstention: 117/117 (100.0%; 95% Wilson CI 96.8–100.0%).
- Layer A conditional exact accuracy: not estimable (0 denominator).
- Application input eligibility: 0/208 (0.0%; 95% Wilson CI 0.0–1.8%).
- Layer B exact concordance: 0/117 (0.0%; 95% Wilson CI 0.0–3.2%).
- Layer B exact-assertion coverage: 0/117 (0.0%; 95% Wilson CI 0.0–3.2%).
- Layer B candidate-set assertion coverage: 0/117 (0.0%; 95% Wilson CI 0.0–3.2%); abstention: 117/117 (100.0%; 95% Wilson CI 96.8–100.0%).
- Layer B conditional exact accuracy: not estimable (0 denominator).
- Discrepancy classifications: `{"intentional_cyp2d6_abstention": 117, "upstream_caller_abstention": 117}`.
- Phenotype concordance, false reassurance, and false warning: not estimable; the independent
  source does not supply phenotype/drug-context truth, and no label was derived from the systems under test.

## Nomenclature boundary

The comparator was frozen to allele-order normalization only. It does not equate CDC legacy star
labels with PharmCAT's current variant-component labels (especially DPYD), or collapse revised
SLCO1B1 definitions. Therefore an exact mismatch can be a nomenclature/definition mismatch rather
than a demonstrated biological genotype disagreement. The raw pairs and classifications remain in
`discrepancies.tsv`; no post-result equivalence was introduced.

## Interpretation and limitations

The 1000 Genomes source is a polymorphic-filtered research VCF. Under the application's frozen
evidence contract, coordinate omission is unknown rather than homozygous reference. Consequently,
Layer B may correctly abstain even where Layer A makes a call. This benchmark therefore supports only
bounded statements about diplotype agreement, input eligibility, assertion coverage, and abstention for
this exact source combination. It does not establish assay validity, clinical benefit, individualized drug
safety, or performance on complete all-sites VCFs.

All exclusions and discrepancies are retained in the companion TSV files; negative findings were not
removed or used to tune the application.
