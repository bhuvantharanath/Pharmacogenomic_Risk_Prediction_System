# Candidate-bound benchmark denominators

These are Prompt5 application-stage results verified against unchanged current bytes, not a new cohort caller execution in Prompt7. All 208 upstream caller reports were reused under the controlled protocol.

| Gene | Truth evaluable | Upstream exact | Upstream candidate-compatible | Conditional exact | Application eligible | Application abstention | Discrepancies |
|---|---:|---|---|---|---|---|---|
| CYP2C19 | 101 | 93/101 | 94/101 | 93/100 | 0/208 | 101/101 | {"evidence_gate": 101, "upstream_caller_disagreement": 7, "upstream_candidate_ambiguity": 1} |
| CYP2C9 | 100 | 79/100 | 100/100 | 79/79 | 0/208 | 100/100 | {"evidence_gate": 100, "upstream_candidate_ambiguity": 21} |
| DPYD | 83 | 0/83 | 0/83 | 0/83 | 0/208 | 83/83 | {"evidence_gate": 83, "truth_output_nomenclature_mismatch": 83} |
| NUDT15 | 11 | 6/11 | 6/11 | 6/11 | 0/208 | 11/11 | {"evidence_gate": 11, "upstream_caller_disagreement": 5} |
| SLCO1B1 | 87 | 29/87 | 29/87 | 29/44 | 0/208 | 87/87 | {"evidence_gate": 87, "truth_output_nomenclature_or_definition_mismatch": 24, "upstream_caller_disagreement": 34} |
| TPMT | 97 | 94/97 | 94/97 | 94/97 | 0/208 | 97/97 | {"evidence_gate": 97, "upstream_caller_disagreement": 3} |
| CYP2D6 | 117 | 0/117 | 0/117 | 0/0 | 0/208 | 117/117 | {"intentional_cyp2d6_abstention": 117, "upstream_caller_abstention": 117} |

208 unique individuals; 1,456 sample-gene rows; 596 evaluable; 816 blank; 42 unsafe nomenclature; 2 unresolved/discordant truth. No pooled accuracy. Phenotype, false reassurance, false warning and clinical utility are not estimable without independent corresponding truth. Every application evaluable row abstains; this does not demonstrate broad positive-pathway accuracy.

All gene metrics, exclusions and discrepancy classifications equal the historical evaluation. All 1,456 input-eligibility rows have a changed temporary projected-VCF hash. A representative comparison has 172 identical genotype rows and different path-bearing tool headers. The old temporary bytes are unavailable, so historical per-file byte equivalence is not asserted.
